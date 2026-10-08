"""Broker-only orchestration for a fresh environment and the complete study.

This orchestrator performs no training or scientific analysis itself. Each
setup/scientific subprocess is a call to the supplied local broker client.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

def broker(category,label,timeout,argv):
    command=[sys.executable,'inputs/compute.py','--category',category,'--label',label,
             '--timeout',str(timeout),'--',*argv]
    print('Broker request:',label,flush=True)
    subprocess.run(command,check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--environment',default='.venv-reproduction')
    p.add_argument('--output',default='reproduction')
    args=p.parse_args()
    env=Path(args.environment)
    out=Path(args.output)
    if env.exists() or out.exists():
        raise SystemExit('Fresh reproduction requires nonexistent environment and output paths.')
    broker('setup','reproduce-fresh-environment',70,['python3','-m','venv',str(env)])
    python=str(env/'bin/python')
    broker('setup','reproduce-offline-packages',150,[python,'-m','pip','install','--no-index','--find-links',
        'inputs/materials/wheels','numpy','torch','scipy','matplotlib'])
    for seed in [1001,1002,1003,1004]:
        for wd in [0,1]:
            segment=0
            while True:
                segment+=1
                label=f'reproduce-{seed}-wd{wd}-segment{segment}'
                broker('compute',label,175,[python,'study.py','run','--seed',str(seed),'--wd',str(wd),
                    '--device','cpu','--implementation','dense','--target','100000','--seconds','155',
                    '--output',str(out),'--label',label])
                endpoint=json.loads((out/'confirmation'/f'seed_{seed}_wd_{wd}'/'endpoint.json').read_text())
                if endpoint['updates']==100000:
                    break
    broker('compute','reproduce-analysis',90,[python,'analyze.py','--data',str(out),'--out',str(out/'analysis'),'--verify'])

if __name__=='__main__':
    main()
