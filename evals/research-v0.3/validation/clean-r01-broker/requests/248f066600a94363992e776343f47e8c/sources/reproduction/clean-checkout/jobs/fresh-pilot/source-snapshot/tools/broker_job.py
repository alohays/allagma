"""Host-side orchestration only. Every executable workload goes via compute.py.

Never launches a second worker to recover an observation timeout.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from common import ROOT, now, ref, write_json

def invoke(identity, category, timeout, command, marked=False, history="evidence/jobs"):
    directory = ROOT / history / identity
    directory.mkdir(parents=True, exist_ok=False)
    sources = sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "source/adapted").rglob("*.py"))
    sources += [ROOT / x for x in ["protocol.json", "requirements.lock.txt"] if (ROOT / x).exists()]
    snapshots = []
    for path in sources:
        target = directory / "source-snapshot" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        snapshots.append(ref(target))
    command = [str(x) for x in command]
    argv = [sys.executable, "inputs/compute.py", "--category", category,
            "--label", identity, "--timeout", str(timeout)]
    if marked:
        argv.append("--attempt")
    argv += ["--", *command]
    write_json(directory / "before.json", {"identity": identity, "category": category,
        "started_at": now(), "command": command, "broker_argv": argv,
        "cwd": ".", "timeout_seconds": timeout, "marked_attempt": marked,
        "source_snapshot": snapshots,
        "environment": ref((ROOT / history).parent / "environment.json")
            if ((ROOT / history).parent / "environment.json").exists()
            else ref(ROOT / "evidence/setup/environment.json") if (ROOT / "evidence/setup/environment.json").exists() else None})
    proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
    (directory / "client-stdout.txt").write_text(proc.stdout)
    (directory / "client-stderr.txt").write_text(proc.stderr)
    print(proc.stdout, end="", flush=True)
    print(proc.stderr, end="", file=sys.stderr, flush=True)
    response, _ = json.JSONDecoder().raw_decode(proc.stdout.lstrip())
    write_json(directory / "client-result.json", response)
    if response.get("status") == "observation_timeout":
        write_json(directory / "pending.json", {"at": now(), "request_id": response["request_id"],
            "reason": "Observation ended; authoritative worker status unknown. No automatic retry."})
        raise RuntimeError("Observation timeout; inspect the same request before any further job")
    request_id = response["request_id"]
    for p in (ROOT / ".compute/responses").glob(request_id + "*"):
        shutil.copyfile(p, directory / p.name)
    request = ROOT / ".compute/requests" / (request_id + ".json")
    if request.exists():
        shutil.copyfile(request, directory / "request.json")
    write_json(directory / "after.json", {"ended_at": now(), "client_exit_code": proc.returncode,
                                          "response": ref(directory / "client-result.json")})
    return response

if __name__ == "__main__":
    split = sys.argv.index("--")
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--category", choices=["setup", "compute"], required=True)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--marked", action="store_true")
    args = parser.parse_args(sys.argv[1:split])
    value = invoke(args.id, args.category, args.timeout, sys.argv[split+1:], args.marked)
    raise SystemExit(0 if value["result"]["status"] == "completed" else 1)
