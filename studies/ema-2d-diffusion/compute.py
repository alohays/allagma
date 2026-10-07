"""Serial, crash-conservative wall-time accounting for all study computation.

Environment installation, source editing and model deliberation are not study
computation. Scientific checks, training, sampling, evaluation, analysis and
recomputation are. Launch those only through this supervisor.
"""
from __future__ import annotations

import datetime
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
CEILING = 1800.0
ATTEMPTS = 18


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+"\n")
    temp.replace(path)


def ledger():
    directory = ROOT/"evidence/compute"
    entries = [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]
    charged = 15.3  # Conservatively include the user-reported pre-goal estimate.
    for entry in entries:
        charged += entry.get("charged_seconds", entry["reservation_seconds"])
    return {"ceiling_seconds": CEILING, "prior_probe_estimate_charged_seconds": 15.3,
            "prior_probe_is_scientific_evidence": False,
            "charged_seconds": charged, "remaining_seconds": max(0., CEILING-charged),
            "attempt_limit": ATTEMPTS, "attempts": sum(e["attempt"] for e in entries), "entries": entries}


def execute(label, command, limit, *, attempt=False):
    (ROOT/"evidence/compute").mkdir(parents=True, exist_ok=True)
    with (ROOT/"evidence/compute.lock").open("a") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = ledger()
        if current["remaining_seconds"] < limit+2:
            raise RuntimeError(f"Insufficient compute reserve: {current['remaining_seconds']:.2f}s left; need {limit+2:.2f}s")
        if attempt and current["attempts"] >= ATTEMPTS:
            raise RuntimeError("Study-wide attempt ceiling reached")
        index = len(current["entries"])+1
        stem = f"{index:03d}-{label}"
        record = ROOT/"evidence/compute"/(stem+".json")
        event = {"label": label, "command": command, "cwd": str(ROOT), "attempt": bool(attempt),
                 "started_at": now(), "reservation_seconds": limit+2, "timeout_seconds": limit,
                 "status": "running", "pid": os.getpid()}
        dump(record, event)
        started = time.monotonic()
        process = None
        try:
            env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                   "MPLCONFIGDIR": str(ROOT/".cache/matplotlib"), "PYTORCH_ENABLE_MPS_FALLBACK": "0",
                   "ALLAGMA_STUDY_COMPUTE_RECEIPT": str(record)}
            with record.with_suffix(".stdout.txt").open("w") as out, record.with_suffix(".stderr.txt").open("w") as err:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err, start_new_session=True)
                event["child_pid"] = process.pid
                dump(record, event)
                try:
                    code = process.wait(timeout=limit)
                    event["status"] = "completed" if code == 0 else "failed"
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=.5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    code = 124
                    event["status"] = "timeout"
        except BaseException:
            # Reserve the whole timeout on uncertainty, including any bounded
            # Allagma worker in a separate process group. Never infer zero cost.
            event.update(status="uncertain", ended_at=now())
            dump(record, event)
            raise
        else:
            event.update(exit_code=code, ended_at=now(), charged_seconds=time.monotonic()-started)
            dump(record, event)
            dump(ROOT/"evidence/compute-summary.json", {k:v for k,v in ledger().items() if k != "entries"})
            print(json.dumps({"receipt": str(record.relative_to(ROOT)), **event}, indent=2))
            if code:
                print(record.with_suffix(".stderr.txt").read_text()[-6000:], file=sys.stderr)
            return code


if __name__ == "__main__":
    print(json.dumps(ledger(), indent=2))
