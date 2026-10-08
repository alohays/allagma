"""Host orchestration only: every setup, training and analysis command uses broker."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def broker(category,label,timeout,command):
    argv=[sys.executable,'inputs/compute.py','--category',category,'--label',label,'--timeout',str(timeout),'--',*map(str,command)]
    print(json.dumps({'broker_argv':argv}),flush=True)
    done=subprocess.run(argv,cwd=ROOT)
    if done.returncode:
        raise SystemExit(f'Broker request {label} did not complete. Preserve its response; do not retry an uncertain observation automatically.')

def training(python,root,seeds):
    for seed in seeds:
        for wd in [0,1]:
            resume=None
            existing=sorted(root.glob(f's{seed}-wd{wd}-a*/result.json'))
            if existing:
                last=json.loads(existing[-1].read_text())
                # Existing outputs must be checked before reuse; recomputation checks full evidence.
                if last['complete']:
                    broker('compute',f'validate-existing-s{seed}-wd{wd}',12,
                           [python,'scripts/check_existing.py',str(existing[-1])])
                    continue
                resume=last['checkpoint']
            attempt=len(existing)+1
            while True:
                target=root/f's{seed}-wd{wd}-a{attempt:03d}'
                if target.exists():raise SystemExit(f'Uncertain/failed existing attempt {target}; inspect its broker receipt before manual recovery.')
                command=[python,'study/train.py','--seed',seed,'--wd',wd,'--phase','confirmation','--out',target,'--max-seconds',155]
                if resume:command+=['--resume',resume]
                broker('compute',f'{root.name}-s{seed}-wd{wd}-a{attempt:03d}',175,command)
                value=json.loads((target/'result.json').read_text())
                if value['complete']:break
                resume=value['checkpoint'];attempt+=1

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['continue','reproduce','recompute'])
    p.add_argument('--destination')
    p.add_argument('--seeds',type=int,nargs='+',default=[1001,1002,1003,1004])
    args=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    dest=Path(args.destination or f'{args.mode}-outputs/{stamp}')
    if dest.is_absolute() or '..' in dest.parts:raise SystemExit('Destination must be workspace-relative')
    if args.mode=='continue':
        training(Path('.venv/bin/python'),Path('evidence/confirmation'),args.seeds)
        return
    if dest.exists():raise SystemExit('Use a new destination; evidence is never overwritten')
    python=Path('.venv/bin/python')
    if args.mode=='reproduce':
        python=dest/'venv/bin/python'
        broker('setup','reproduce-fresh-environment',60,['python3','-m','venv',dest/'venv'])
        broker('setup','reproduce-offline-packages',120,[python,'-m','pip','install','--no-index','--no-cache-dir','--find-links','inputs/materials/wheels',
                 'torch==2.14.1','numpy==2.4.6','scipy==1.17.1','matplotlib==3.11.2'])
        pilot=dest/'pilot'
        broker('compute','reproduce-pilot',35,[python,'study/train.py','--seed',61,'--wd',1,'--updates',3000,'--phase','pilot','--out',pilot,'--protocol','PROTOCOL-DRAFT.md','--max-seconds',25])
        broker('compute','reproduce-qualification',20,[python,'study/qualify.py','--pilot',pilot/'result.json','--out',dest/'qualification'])
        training(python,dest/'raw',[1001,1002,1003,1004])
        broker('compute','reproduce-analysis',45,[python,'study/analyze.py','--root',dest/'raw','--out',dest/'analysis','--measurements',dest/'measurements.json'])
        broker('compute','reproduce-report',15,[python,'study/write_report.py','--analysis',dest/'analysis','--output',dest/'REPORT.md'])
    else:
        broker('compute','retained-evidence-recompute',45,[python,'study/analyze.py','--out',dest,'--read-measurements'])
        broker('compute','recompute-numerical-comparison',10,[python,'scripts/compare.py','analysis/primary',dest])

if __name__=='__main__':main()
