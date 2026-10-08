"""Submission-only driver: every scientific action is delegated to compute.py.

No scientific functions are imported or run here. Commands are sequential.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=24);p.add_argument('--prefix',default='confirm')
    a=p.parse_args();plan=json.loads((ROOT/'campaigns/ema-schedule-v1/plan.json').read_text())
    freeze=json.loads((ROOT/'campaigns/ema-schedule-v1/confirmation-freeze.json').read_text())
    if not freeze['authorized_to_confirm']: raise SystemExit('Forecast gate is closed')
    for i,cfg in enumerate(plan[a.start:a.start+a.count],a.start):
        attempt=f'{a.prefix}-{i+1:03d}-{cfg["id"]}'
        cmd=[sys.executable,'inputs/compute.py','--category','compute','--label',attempt,'--timeout','45','--',
             '.venv/bin/python','study/runner.py','train','--attempt',attempt,'--dataset',cfg['dataset'],'--seed',str(cfg['seed']),
             '--policy',cfg['policy'],'--horizon',str(cfg['horizon'])]
        print(json.dumps({'dispatch':i+1,'total':len(plan),'attempt':attempt,'argv':cmd}),flush=True)
        outcome=subprocess.run(cmd,cwd=ROOT)
        if outcome.returncode:raise SystemExit(outcome.returncode)

if __name__=='__main__':main()
