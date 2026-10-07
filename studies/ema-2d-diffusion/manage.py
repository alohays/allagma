"""Human/native-agent entrypoint; every scientific process has a budget receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from compute import ROOT, dump, execute, ledger, now

PYTHON = str(ROOT/".venv/bin/python")
CAMPAIGN = ROOT/"campaigns/ema-v1"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def helper():
    lock=read(CAMPAIGN/"lock.yaml" if CAMPAIGN.exists() else ROOT/".allagma/lock.yaml")
    return str(ROOT/".allagma/bundles"/lock["bundle_id"]/"tools/allagma.py")


def command(operation, *extras):
    return [PYTHON,helper(),"campaign",operation,"--study",str(ROOT),"--campaign","ema-v1",*extras]


def records():
    return [(p,read(p)) for p in sorted(CAMPAIGN.glob("runs/*/attempts/*/record.json"))]


def next_run():
    success={r["run_id"] for _,r in records() if r["status"]=="succeeded"}
    return next((r for r in read(CAMPAIGN/"protocol.json")["runs"] if r["id"] not in success),None)


def freeze():
    path=ROOT/"confirmation-freeze.json"
    if path.exists():
        raise RuntimeError("Freeze already exists; never overwrite it")
    successful=[(p,r) for p,r in records() if r["split"]=="pilot" and r["status"]=="succeeded"]
    if len(successful)!=4 or any(CAMPAIGN.glob("runs/confirm-*/attempts/*/started.json")):
        raise RuntimeError("Exactly four completed pilots and untouched confirmation are required")
    checks=[e for e in ledger()["entries"] if e["label"].startswith("known-answer")]
    if not checks or checks[-1].get("exit_code")!=0:
        raise RuntimeError("Known-answer checks must pass")
    times=[r["usage"]["wall_seconds"] for _,r in successful]
    forecast=max(times)*10*1.15+120
    available=ledger()["remaining_seconds"]
    if forecast>available:
        raise RuntimeError(f"Pilot-based confirmation forecast {forecast:.1f}s exceeds {available:.1f}s left; request a consequential decision before any budget change")
    protocol=read(CAMPAIGN/"protocol.json")
    for _,record in successful:
        for reference in record["inputs"]+record["outputs"]:
            if sha(ROOT/reference["path"])!=reference["sha256"]:
                raise RuntimeError("Pilot evidence changed")
    dump(path,{"frozen_at":now(),"protocol_revision":protocol["revision"],"protocol_sha256":sha(CAMPAIGN/"protocol.json"),
        "lock_sha256":sha(CAMPAIGN/"lock.yaml"),"decision":"Proceed unchanged after four qualified pilots; no confirmation result observed",
        "pilot_records":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p,_ in successful],
        "code":{name:sha(CAMPAIGN/"materials"/name) for name in protocol["code"]},
        "orchestration":{name:sha(ROOT/name) for name in ("manage.py","compute.py","native_session.py","verify_results.py")},
        "pilot_attempt_seconds":times,"remaining_seconds_at_freeze":available,
        "forecast_seconds":forecast,"forecast_basis":"10 × longest pilot × 1.15 + 120s analysis/reproduction reserve",
        "confirmation_seeds":{name:[r["input"]["seed"] for r in protocol["runs"] if r["split"]=="confirmation" and r["input"]["dataset"]==name] for name in ("moons","gmm8")}})
    print(path.read_text())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("operation",choices=["start","check","interrupt","pilot","freeze","confirm","analyze","audit","verify","status"])
    args=parser.parse_args()
    if args.operation=="status":
        value={k:v for k,v in ledger().items() if k!="entries"}
        if CAMPAIGN.exists():
            value.update(state=read(CAMPAIGN/"state.json"),next_run=next_run())
        print(json.dumps(value,indent=2))
        return 0
    if args.operation=="start":
        return subprocess.call(command("start"),cwd=ROOT)
    if args.operation=="check":
        return execute("known-answer-final",[PYTHON,str(ROOT/"domain/test_science.py")],30)
    if args.operation=="freeze":
        freeze()
        return 0
    if args.operation=="verify":
        return execute("independent-verification",[PYTHON,str(ROOT/"verify_results.py")],120)
    if args.operation in ("interrupt","pilot","confirm"):
        run=next_run()
        if run is None:
            print("All declared trajectories already complete")
            return 0
        phase="confirmation" if args.operation=="confirm" else "pilot"
        if run["split"]!=phase:
            raise RuntimeError(f"Next run is {run['split']}; use the correct phase command")
        if phase=="confirmation" and not (ROOT/"confirmation-freeze.json").is_file():
            raise RuntimeError("Post-pilot confirmation freeze is required")
        extras=["--stop-after","1"]
        if args.operation=="interrupt":
            extras += ["--fault-run",run["id"],"--fault-mode","interrupt"]
        return execute(args.operation+"-"+run["id"],command("run",*extras),160,attempt=True)
    return execute(args.operation,command(args.operation),120)


if __name__=="__main__":
    raise SystemExit(main())
