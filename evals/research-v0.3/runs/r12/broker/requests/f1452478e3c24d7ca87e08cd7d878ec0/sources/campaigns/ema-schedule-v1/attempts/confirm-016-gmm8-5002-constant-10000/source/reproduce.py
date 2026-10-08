"""Submission-only full reproduction driver: fresh env, training, sampling.

Every setup/scientific action invokes inputs/compute.py; no science runs in
this dispatcher. A fresh destination is mandatory and no existing run is erased.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def submit(category,label,timeout,command):
    argv=[sys.executable,'inputs/compute.py','--category',category,'--label',label,'--timeout',str(timeout),'--',*command]
    print(json.dumps({'argv':argv}),flush=True)
    subprocess.run(argv,cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',default='reproduction/full-r1');a=p.parse_args()
    dest=Path(a.destination)
    if dest.is_absolute() or '..' in dest.parts:raise SystemExit('Use a fresh relative destination within workspace')
    prefix=dest.name
    submit('setup',prefix+'-workspace',15,['python3','study/replay_setup.py','--destination',str(dest)])
    submit('setup',prefix+'-fresh-env',60,['python3','-m','venv',str(dest/'.venv')])
    python=str(dest/'.venv/bin/python')
    submit('setup',prefix+'-install',150,[python,'-m','pip','install','--no-index','--find-links','inputs/materials/wheels','-r','inputs/materials/requirements-reference.lock'])
    plan=json.loads((ROOT/'campaigns/ema-schedule-v1/plan.json').read_text())
    for i,cfg in enumerate(plan,1):
        attempt=f'replay-{i:03d}-{cfg["id"]}'
        submit('compute',prefix+'-'+attempt,45,[python,str(dest/'study/runner.py'),'train','--attempt',attempt,
              '--dataset',cfg['dataset'],'--seed',str(cfg['seed']),'--policy',cfg['policy'],'--horizon',str(cfg['horizon'])])
    submit('compute',prefix+'-analyze',30,[python,str(dest/'study/analyze.py'),'--output','analysis'])
    submit('compute',prefix+'-compare',30,[python,'study/compare_replay.py','--destination',str(dest)])

if __name__=='__main__':main()
