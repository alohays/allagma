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
import sys

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

    def _snapshot_sources(self, destination):
        manifest = {}
        for root, dirs, files in os.walk(self.workspace, followlinks=False):
            dirs[:] = [name for name in dirs if name not in (".venv", ".tmp", ".compute", "__pycache__", ".git", "site-packages")
                       and not (Path(root)/name).is_symlink()]
            for name in files:
                path = Path(root)/name
                if path.is_symlink() or path.suffix not in (".py", ".sh", ".toml", ".yaml"):
                    continue
                relative = path.relative_to(self.workspace)
                if path.stat().st_size > 2_000_000:
                    raise AllagmaError("Source snapshot exceeds the per-file control limit")
                output = destination/relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(path.read_bytes())
                manifest[str(relative)] = file_hash(output)
        write_json(destination.parent/"source-manifest.json", manifest, immutable=True)
        return manifest

    def poll(self, process=None, remaining=None):
        """Service at most one request. Suitable for the native adapter callback."""
        for path in sorted((self.queue/"requests").glob("*.json")):
            request_id = path.stem
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
                "ALLAGMA_COMPUTE_REQUEST="+request_id,
                "MPLCONFIGDIR="+str(self.workspace/".tmp/matplotlib")]
            (self.workspace/".tmp").mkdir(exist_ok=True)
            command = [*environment, "/usr/bin/sandbox-exec", "-p", self.isolation, *request["argv"]]
            try:
                result = resources.execute(self.ledger, command, label=request["label"],
                    category=request["category"], timeout=timeout, attempt=request["attempt"], workdir=cwd)
            except (AllagmaError, OSError, ValueError) as exc:
                result = {"status": "rejected", "error": str(exc)}
            response = {"request_id": request_id, "injected_interruption": injected,
                        "isolation_sha256": self.profile_hash, "result": result}
            if "job" in result:
                for name in ("stdout.txt", "stderr.txt"):
                    data = (Path(result["job"])/name).read_bytes()
                    (destination/name).write_bytes(data)
                    # Convenience copies; authoritative logs remain protected.
                    (self.queue/"responses"/(request_id+"-"+name)).write_bytes(data)
            write_json(destination/"response.json", response, immutable=True)
            write_json(self.queue/"responses"/(request_id+".json"), response)
            return response
        return None
