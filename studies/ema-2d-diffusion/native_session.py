"""Capture actual Codex CLI sessions without model overrides or auth copying."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("prompt",type=Path)
    parser.add_argument("--codex",default="codex",help="Native CLI executable; never a model override")
    parser.add_argument("--interrupt-after-attempt",action="store_true")
    args=parser.parse_args()
    directory=ROOT/"evidence/native"/args.label
    directory.mkdir(parents=True,exist_ok=False)
    prompt=args.prompt.read_text()
    (directory/"prompt.txt").write_text(prompt)
    command=[args.codex,"-a","never","exec","--sandbox","danger-full-access","--json","-C",str(ROOT),
             "-o",str(directory/"final.txt"),"-"]
    receipt={"command":command,"started_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "cli_version":subprocess.check_output([args.codex,"--version"],text=True).strip(),
             "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"model_override":None,
             "authentication":"Existing ChatGPT CLI login; no credentials exported",
             "sandbox":"danger-full-access on the user-authorized local host; not a security containment claim",
             "fresh_session":True,"host_interrupted":False}
    with (directory/"events.jsonl").open("w") as out,(directory/"stderr.log").open("w") as err:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,start_new_session=True)
        receipt["pid"]=process.pid
        (directory/"session.json").write_text(json.dumps(receipt,indent=2)+"\n")
        process.stdin.write(prompt)
        process.stdin.close()
        deadline=time.monotonic()+900
        while process.poll() is None:
            if args.interrupt_after_attempt and not receipt["host_interrupted"]:
                entries=list((ROOT/"evidence/compute").glob("*-interrupt-*.json"))
                if entries and json.loads(entries[-1].read_text()).get("status")=="completed":
                    receipt["host_interrupted"]=True
                    receipt["interruption_reason"]="SIGINT after the bounded 100-update pilot interruption and its compute receipt, before session continuation"
                    receipt["interrupted_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    os.killpg(process.pid,signal.SIGINT)
                    deadline=time.monotonic()+20
            if time.monotonic()>deadline:
                os.killpg(process.pid,signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                receipt["session_timeout"]=True
                break
            time.sleep(.1)
        process.wait()
    receipt.update(exit_code=process.returncode,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    events=[]
    for line in (directory/"events.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    receipt["thread_ids"]=[e["thread_id"] for e in events if e.get("type")=="thread.started"]
    receipt["usage"]=[e["usage"] for e in events if "usage" in e]
    receipt["events_sha256"]=hashlib.sha256((directory/"events.jsonl").read_bytes()).hexdigest()
    (directory/"session.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    main()
