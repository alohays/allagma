"""Sequential orchestration only. All child computation goes through common broker."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from common import ROOT, digest, read, ref, tree_manifest, write


def main():
    args_list = sys.argv[1:]
    boundary = args_list.index("--")
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["setup", "compute"], required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--attempt", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--artifacts")
    args = parser.parse_args(args_list[:boundary])
    command = args_list[boundary + 1:]
    folder = ROOT / "evidence/broker" / args.label
    folder.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now(timezone.utc).isoformat()
    invocation = [sys.executable, "inputs/compute.py", "--category", args.category, "--label", args.label,
                  "--timeout", str(args.timeout)] + (["--attempt"] if args.attempt else []) + ["--", *command]
    write(folder / "launch.json", {"started_at": started_at, "category": args.category,
          "label": args.label, "argv": invocation, "worker_argv": command,
          "timeout": args.timeout, "marked_attempt": args.attempt,
          "launcher": ref(ROOT / "study/broker_run.py"), "code": tree_manifest((ROOT / "study").glob("*.py"))})
    record = None
    rdir = None
    if args.run_id:
        run = ROOT / "campaigns/culp-v1/runs" / args.run_id
        rdir = run / "attempts" / args.label
        number = len(list((run / "attempts").glob("*"))) + 1
        rdir.mkdir(parents=True, exist_ok=False)
        record = {"schema_version": "0.2", "record_type": "RunRecord", "run_id": args.run_id,
            "attempt_id": args.label, "attempt_number": number, "campaign_id": "culp-v1",
            "experiment_id": args.run_id, "started_at": started_at, "ended_at": None,
            "inputs": [ref(run / "spec.json"), ref(ROOT / "campaigns/culp-v1/protocol.json"),
                       ref(ROOT / "campaigns/culp-v1/code-manifest.json"), ref(ROOT / "provenance/source-manifest.json")],
            "outputs": [], "environment": {"metadata": ref(ROOT / "provenance/environment.json"),
                "broker": "inputs/compute.py", "device": "cpu"}, "model_revision": None,
            "data_revision": digest(ROOT / "provenance/source-manifest.json"),
            "usage": {"wall_seconds": 0, "money_usd": 0, "tokens": 0}, "status": "running", "error": None,
            "protocol_revision": "culp-protocol-v1", "bundle_id": "b-9a39b70665ba909edb8abc13",
            "split": "pilot" if args.run_id == "synthetic-pilot" else "confirmation", "command": command, "exit_code": None}
        write(rdir / "started.json", record)
    result = subprocess.run(invocation, cwd=ROOT, capture_output=True, text=True)
    (folder / "client.stdout.txt").write_text(result.stdout)
    (folder / "client.stderr.txt").write_text(result.stderr)
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", file=sys.stderr, flush=True)
    response, _ = json.JSONDecoder().raw_decode(result.stdout)
    request_id = response["request_id"]
    write(folder / "response.json", response)
    request = ROOT / ".compute/requests" / f"{request_id}.json"
    if request.exists():
        shutil.copyfile(request, folder / "request.json")
    for name in ("stdout.txt", "stderr.txt"):
        path = ROOT / ".compute/responses" / f"{request_id}-{name}"
        if path.exists():
            shutil.copyfile(path, folder / name)
    if response.get("status") == "observation_timeout":
        write(folder / "pending.json", {"request_id": request_id, "action": "Inspect same response and process state; no retry authorized from timeout alone"})
        raise SystemExit(2)
    outcome = response["result"]
    if record is not None:
        status = "interrupted" if response.get("injected_interruption") else ("succeeded" if outcome["status"] == "completed" else "failed")
        record.update({"status": status, "ended_at": outcome["ended_at"], "exit_code": outcome["exit_code"],
            "usage": {"wall_seconds": outcome["charged_seconds"], "money_usd": 0, "tokens": 0},
            "error": None if status == "succeeded" else {"kind": "controlled_interruption" if status == "interrupted" else outcome["status"], "message": "See authoritative broker response; this attempt remains permanent history."}})
        record["environment"]["broker_response"] = ref(folder / "response.json")
        record["environment"]["request_id"] = request_id
        outputs = list(folder.glob("*"))
        if args.artifacts:
            outputs += list((ROOT / args.artifacts).rglob("*"))
        record["outputs"] = tree_manifest(outputs)
        write(rdir / "record.json", record)
    write(folder / "terminal.json", {"request_id": request_id, "category": args.category,
          "status": outcome["status"], "injected_interruption": response.get("injected_interruption", False),
          "charged_seconds": outcome["charged_seconds"], "artifacts": args.artifacts,
          "run_record": ref(rdir / "record.json") if rdir else None})
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
