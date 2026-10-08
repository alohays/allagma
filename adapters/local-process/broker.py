"""Controller-owned local computation queue; no study science or model calls.

The candidate writes requests inside its workspace. The controller keeps the
authoritative policy, receipts and source snapshots outside candidate access.
Scientific commands use a macOS filesystem/network sandbox that permits MPS.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from allagma import resources
from allagma.files import AllagmaError, file_hash, read_json, utcnow, write_json


def profile(workspace, readonly=(), protected=()):
    workspace = Path(workspace).resolve()
    q = lambda p: json.dumps(str(Path(p).resolve()))
    # Do not inherit unrestricted personal files or the evaluator repository.
    # All immutable inputs and isolated environments are inside this workspace.
    rules = ["(version 1)", "(allow default)", "(deny network*)",
        f"(deny file-write* (require-not (require-any (subpath {q(workspace)}) (literal \"/dev/null\") (literal \"/dev/tty\"))))"]
    for root in [Path.home(), *protected]:
        rules.append(f"(deny file-read-data (require-all (subpath {q(root)}) (require-not (subpath {q(workspace)}))))")
    for path in readonly:
        rules.append(f"(deny file-write* (subpath {q(path)}))")
    return "\n".join(rules)+"\n"


class Broker:
    def __init__(self, workspace, ledger, record, *, readonly=(), protected=(), interrupt_first_attempt=False):
        self.workspace, self.ledger, self.record = (Path(p).resolve() for p in (workspace, ledger, record))
        if self.workspace == self.record or self.workspace in self.record.parents:
            raise AllagmaError("Broker evidence must be outside the candidate workspace")
        if self.workspace == self.ledger or self.workspace in self.ledger.parents:
            raise AllagmaError("Broker ledger must be outside the candidate workspace")
        self.queue = self.workspace/".compute"
        for name in ("requests", "responses"):
            (self.queue/name).mkdir(parents=True, exist_ok=True)
        self.record.mkdir(parents=True, exist_ok=True)
        self.isolation = profile(self.workspace, readonly, [self.ledger, self.record, *protected])
        self.interrupt_first_attempt = interrupt_first_attempt
        self.profile_hash = hashlib.sha256(self.isolation.encode()).hexdigest()
        path = self.record/"sandbox.sb"
        if path.exists() and path.read_text() != self.isolation:
            raise AllagmaError("Broker isolation changed; use a new controller record")
        if not path.exists():
            path.write_text(self.isolation)
        inherited=self.record/"preexisting-requests.json"
        if not inherited.exists():
            # A new controller must not replay a previous controller's queue.
            write_json(inherited,[path.stem for path in (self.queue/"requests").glob("*.json")],immutable=True)
        self.preexisting=set(read_json(inherited))

    def _snapshot_sources(self, destination):
        manifest = {}
        for root, dirs, files in os.walk(self.workspace, followlinks=False):
            dirs[:] = [name for name in dirs if name not in (".venv", ".tmp", ".compute", "__pycache__", ".git", "site-packages")
                       and not name.startswith(".venv-") and not (Path(root)/name/"pyvenv.cfg").is_file()
                       and not (Path(root)/name).is_symlink()]
            for name in files:
                path = Path(root)/name
                if path.is_symlink() or path.suffix not in (".py", ".sh", ".toml", ".yaml", ".json"):
                    continue
                relative = path.relative_to(self.workspace)
                if path.stat().st_size > 2_000_000:
                    manifest[str(relative)] = {"sha256": file_hash(path), "captured": False,
                                               "reason": "file exceeds 2 MB snapshot threshold"}
                    continue
                output = destination/relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(path.read_bytes())
                manifest[str(relative)] = file_hash(output)
        write_json(destination.parent/"source-manifest.json", manifest, immutable=True)
        return manifest

    def _publish(self, request_id, result, injected=False, reconciled=False):
        destination = self.record/"requests"/request_id
        response = {"request_id": request_id, "injected_interruption": injected,
                    "isolation_sha256": self.profile_hash, "result": result,
                    "reconciled_after_controller_restart": reconciled}
        if "job" in result:
            for name in ("stdout.txt", "stderr.txt"):
                source = Path(result["job"])/name
                if source.exists():
                    data = source.read_bytes()
                    (destination/name).write_bytes(data)
                    (self.queue/"responses"/(request_id+"-"+name)).write_bytes(data)
        write_json(destination/"response.json", response, immutable=True)
        write_json(self.queue/"responses"/(request_id+".json"), response)
        return response

    def recover(self):
        """Explicitly reconcile a stopped controller; never repeat its request."""
        with resources._mutex(self.record):
            # This refuses live resource operations/groups/observed descendants.
            resources.recover(self.ledger)
            with resources._mutex(self.ledger):
                entries = resources.summary(self.ledger)["entries"]
                recovered = []
                for destination in sorted((self.record/"requests").glob("*")):
                    if (destination/"response.json").exists():
                        continue
                    request_id = destination.name
                    matches = [entry for entry in entries if
                        entry["reservation"].get("request_id") == request_id or
                        "ALLAGMA_COMPUTE_REQUEST="+request_id in entry["reservation"]["command"]]
                    if len(matches) > 1:
                        raise AllagmaError("Multiple resource jobs have the same computation request ID")
                    if matches:
                        entry = matches[0]
                        result = {"job": str(self.ledger/"jobs"/entry["job"]), **entry["result"]}
                    else:
                        # Reservations precede process launch, and both mutexes
                        # exclude live dispatch. This request never launched.
                        result = {"status": "not_started", "charged_seconds": 0,
                                  "error": "Controller stopped before a resource reservation; submit a new request"}
                    marker = self.record/"interruption.json"
                    injected = marker.exists() and read_json(marker)["request_id"] == request_id
                    recovered.append(self._publish(request_id, result, injected, reconciled=True))
                return recovered

    def poll(self, process=None, remaining=None):
        """Service at most one request. Suitable for the native adapter callback."""
        with resources._mutex(self.record):
            return self._poll(process, remaining)

    def _poll(self, process, remaining):
        for path in sorted((self.queue/"requests").glob("*.json")):
            request_id = path.stem
            if request_id in self.preexisting:continue
            if not re.fullmatch(r"[0-9a-f]{32}", request_id) or path.is_symlink():
                raise AllagmaError("Invalid or symlinked computation request")
            destination = self.record/"requests"/request_id
            if destination.exists():
                # Restore delivery from the protected outcome without rerunning.
                retained = destination/"response.json"
                delivery = self.queue/"responses"/(request_id+".json")
                if retained.exists() and not delivery.exists():
                    for name in ("stdout.txt", "stderr.txt"):
                        if (destination/name).exists():
                            (self.queue/"responses"/(request_id+"-"+name)).write_bytes((destination/name).read_bytes())
                    write_json(delivery, read_json(retained))
                continue
            if path.stat().st_size > 65536:
                raise AllagmaError("Computation request exceeds 64 KiB")
            try:
                request = read_json(path)
                expected = {"request_id", "argv", "cwd", "category", "timeout_seconds", "attempt", "label"}
                if set(request) != expected or request["request_id"] != request_id:
                    raise AllagmaError("Computation request fields do not match the contract")
                if type(request["attempt"]) is not bool or not isinstance(request["cwd"], str):
                    raise AllagmaError("Invalid attempt flag or working directory")
                if not isinstance(request["argv"], list) or not request["argv"] or not all(isinstance(x, str) and x and "\0" not in x for x in request["argv"]):
                    raise AllagmaError("Computation argv must be a nonempty string array")
                resources._positive(request["timeout_seconds"], "timeout_seconds")
                limits = resources._policy(self.ledger)["profile"]["command_timeout_seconds"]
                if request["category"] not in limits or request["timeout_seconds"] > limits[request["category"]]:
                    raise AllagmaError("Requested category or timeout exceeds the frozen resource policy")
                cwd = (self.workspace/request["cwd"]).resolve()
                if cwd != self.workspace and self.workspace not in cwd.parents:
                    raise AllagmaError("Computation cwd escapes its candidate workspace")
            except (AllagmaError, ValueError, TypeError) as exc:
                destination.mkdir(parents=True, exist_ok=False)
                response = {"request_id": request_id, "result": {"status": "rejected", "error": str(exc)}}
                write_json(destination/"response.json", response, immutable=True)
                write_json(self.queue/"responses"/(request_id+".json"), response)
                return response
            destination.mkdir(parents=True, exist_ok=False)
            write_json(destination/"request.json", request, immutable=True)
            self._snapshot_sources(destination/"sources")
            injected = bool(self.interrupt_first_attempt and request["attempt"]
                            and not (self.record/"interruption.json").exists())
            timeout = request["timeout_seconds"]
            resources._positive(timeout, "timeout_seconds")
            if remaining is not None:
                timeout = min(timeout, max(.05, remaining-5))
            if injected:
                timeout = min(timeout, .5)
                write_json(self.record/"interruption.json", {"request_id": request_id,
                    "at": utcnow(), "mechanism": "First attempt receives a 0.5-second timeout; preserve its actual outcome"}, immutable=True)
            environment = ["/usr/bin/env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                "HOME="+str(Path.home()), "LANG=en_US.UTF-8", "TMPDIR="+str(self.workspace/".tmp"),
                "OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1", "MKL_NUM_THREADS=1",
                "PYTORCH_ENABLE_MPS_FALLBACK=0", "PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.2",
                "PYTORCH_MPS_LOW_WATERMARK_RATIO=0.1",
                "ALLAGMA_COMPUTE_REQUEST="+request_id,
                "MPLCONFIGDIR="+str(self.workspace/".tmp/matplotlib")]
            (self.workspace/".tmp").mkdir(exist_ok=True)
            command = [*environment, "/usr/bin/sandbox-exec", "-p", self.isolation, *request["argv"]]
            try:
                result = resources.execute(self.ledger, command, label=request["label"],
                    category=request["category"], timeout=timeout, attempt=request["category"]=="compute", workdir=cwd,
                    request_id=request_id)
            except (AllagmaError, OSError, ValueError) as exc:
                result = {"status": "rejected", "error": str(exc)}
            return self._publish(request_id, result, injected)
        return None


def run_driver(broker, command, *, timeout, destination):
    """Execute a study-owned reproduction driver while servicing its requests.

    The driver coordinates requests and is timed separately from computation.
    It is confined to the same workspace and does not receive controller files.
    """
    resources._positive(timeout,"driver timeout")
    if timeout>7200:raise AllagmaError("Driver deadline must not exceed two hours")
    destination=Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=False)
    policy=resources._policy(broker.ledger)["profile"]
    environment=["/usr/bin/env","-i","PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                 "HOME="+str(Path.home()),"LANG=en_US.UTF-8","TMPDIR="+str(broker.workspace/".tmp")]
    (broker.workspace/".tmp").mkdir(exist_ok=True)
    invocation=[*environment,"/usr/bin/sandbox-exec","-p",broker.isolation,*command]
    record={"command":command,"started_at":utcnow(),"timeout_seconds":timeout,"status":"running"}
    write_json(destination/"record.json",record)
    started=time.monotonic();process=None;known={};peak_rss=0;peak_storage=0
    try:
        with (destination/"stdout.txt").open("wb") as out,(destination/"stderr.txt").open("wb") as err:
            process=subprocess.Popen(invocation,cwd=broker.workspace,stdout=out,stderr=err,start_new_session=True)
            record["pid"]=process.pid;write_json(destination/"record.json",record)
            while process.poll() is None:
                table=resources.process_table();known=resources._family(table,process.pid,known)
                peak_rss=max(peak_rss,sum(table[pid]["rss"] for pid in known))
                peak_storage=max(peak_storage,resources.storage_bytes(broker.workspace))
                remaining=timeout-(time.monotonic()-started)
                if remaining<=0 or peak_rss>policy["rss_limit_bytes"] or peak_storage>policy["storage_limit_bytes"]:
                    record["status"]="timed_out" if remaining<=0 else "resource_exceeded"
                    resources._stop(process,known,.5);break
                broker.poll(remaining=remaining)
                time.sleep(.1)
            process.wait()
            if record["status"]=="running":record["status"]="completed" if process.returncode==0 else "failed"
    except BaseException:
        record["status"]="interrupted"
        if process is not None:resources._stop(process,known,.5)
        raise
    finally:
        record.update(ended_at=utcnow(),wall_seconds=time.monotonic()-started,
            exit_code=process.returncode if process else None,peak_rss_bytes=peak_rss,peak_storage_bytes=peak_storage)
        write_json(destination/"record.json",record)
    return record


if __name__=="__main__":
    import argparse
    argv=sys.argv[1:]
    if "--" not in argv:raise SystemExit("Place the study-owned driver command after --")
    split=argv.index("--");parser=argparse.ArgumentParser()
    for name in ("workspace","ledger","record","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--timeout",type=float,required=True)
    parser.add_argument("--readonly",type=Path,action="append",default=[])
    parser.add_argument("--protected",type=Path,action="append",default=[])
    args=parser.parse_args(argv[:split])
    broker=Broker(args.workspace,args.ledger,args.record,readonly=args.readonly,protected=args.protected)
    broker.recover()
    result=run_driver(broker,argv[split+1:],timeout=args.timeout,destination=args.output)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result["status"]=="completed" else 1)
