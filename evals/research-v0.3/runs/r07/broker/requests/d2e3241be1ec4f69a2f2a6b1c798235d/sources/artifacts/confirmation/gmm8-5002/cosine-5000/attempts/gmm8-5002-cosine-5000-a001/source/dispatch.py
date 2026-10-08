"""Sequential broker client orchestration; this process performs no science.

Each training/analysis/setup command is independently supervised by the common
client. Do not run the dispatcher itself inside a broker worker (no nesting).
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def broker(category,label,timeout,argv):
    command=[sys.executable,str(ROOT/'inputs/compute.py'),'--category',category,'--label',label,'--timeout',str(timeout),'--',*argv]
    process=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    # Keep full authoritative client output, avoid flooding the interactive log.
    log=ROOT/'dispatch-logs'/f'{label}-{time.time_ns()}.txt'
    log.parent.mkdir(exist_ok=True)
    log.write_text(process.stdout+'\nSTDERR:\n'+process.stderr)
    print(json.dumps({'label':label,'client_exit':process.returncode,'client_log':str(log.relative_to(ROOT))}),flush=True)
    if process.returncode:
        print(process.stdout[-2500:],flush=True)
        print(process.stderr[-2500:],flush=True)
        raise SystemExit(process.returncode)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--fresh',action='store_true')
    p.add_argument('--environment',default='.venv')
    p.add_argument('--base',default='artifacts')
    p.add_argument('--analyze-out')
    p.add_argument('--only-dataset',choices=['moons','gmm8'])
    args=p.parse_args()
    python=str(ROOT/args.environment/'bin/python')
    if args.fresh:
        if (ROOT/args.environment).exists():raise SystemExit('Fresh environment path already exists; choose a new path.')
        broker('setup','reproduce-environment',60,[sys.executable,'-m','venv',args.environment])
        broker('setup','reproduce-packages',120,[python,'-m','pip','install','--no-index','--find-links','inputs/materials/wheels','-r','inputs/materials/requirements-reference.lock'])
    if list((ROOT/args.base/'confirmation').glob('*/*/attempts/*/result.json')):
        broker('compute','verify-existing-before-resume',30,[python,'study/check_existing.py','--base',args.base])
    for cfg in json.loads((ROOT/'campaigns/ema-schedule-v1/run-plan.json').read_text()):
        if args.only_dataset and cfg['dataset']!=args.only_dataset:continue
        destination=ROOT/args.base/'confirmation'/f"{cfg['dataset']}-{cfg['seed']}"/f"{cfg['policy']}-{cfg['duration']}"/'attempts'
        successes=list(destination.glob('*/result.json'))
        if successes:
            print(json.dumps({'verified_existing_terminal_record':str(successes[0].relative_to(ROOT))}),flush=True)
            continue
        count=len(list(destination.glob('*/started.json')))+1
        attempt=cfg['id']+f'-a{count:03d}'
        argv=[python,'study/runner.py','--dataset',cfg['dataset'],'--seed',str(cfg['seed']),
              '--phase','confirmation','--policy',cfg['policy'],'--duration',str(cfg['duration']),
              '--device',cfg['device'],'--attempt-id',attempt,'--base',args.base]
        broker('compute',attempt,45 if cfg['duration']==10000 else 30,argv)
    if args.analyze_out:
        broker('compute','reproduce-analysis',60,[python,'study/analyze.py','--base',args.base,'--out',args.analyze_out])

if __name__=='__main__':main()
