"""Common evaluation resource client; this supplies no research workflow."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid


def main():
    args_list = sys.argv[1:]
    if "--" not in args_list:
        raise SystemExit("Put the computation command after --")
    split = args_list.index("--")
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--category", choices=["compute", "setup"], default="compute")
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--attempt", action="store_true")
    args = parser.parse_args(args_list[:split])
    command = args_list[split+1:]
    if not command or not 0 < args.timeout <= 3600:
        raise SystemExit("Supply a command and a finite timeout of at most one hour")
    request_id = uuid.uuid4().hex
    queue = args.workspace.resolve()/".compute"
    (queue/"requests").mkdir(parents=True, exist_ok=True)
    request = {"request_id": request_id, "argv": command, "cwd": args.cwd,
        "category": args.category, "timeout_seconds": args.timeout, "attempt": args.attempt, "label": args.label}
    temporary = queue/"requests"/(request_id+".tmp")
    temporary.write_text(json.dumps(request)+"\n")
    temporary.replace(temporary.with_suffix(".json"))
    response = queue/"responses"/(request_id+".json")
    # Observation timeout does not cancel or restart the authoritative job.
    deadline = time.monotonic()+args.timeout+60
    while not response.exists():
        if time.monotonic() >= deadline:
            print(json.dumps({"request_id": request_id, "status": "observation_timeout",
                "instruction": "Inspect this same request and the controller before any retry."}))
            return 2
        time.sleep(.2)
    value = json.loads(response.read_text())
    print(json.dumps(value, indent=2))
    for name, stream in (("stdout.txt", sys.stdout), ("stderr.txt", sys.stderr)):
        path = queue/"responses"/(request_id+"-"+name)
        if path.exists():
            print(path.read_text(errors="replace"), end="", file=stream)
    return 0 if value["result"]["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
