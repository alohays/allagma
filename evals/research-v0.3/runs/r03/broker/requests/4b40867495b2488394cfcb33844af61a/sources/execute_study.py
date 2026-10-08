"""Sequential broker dispatcher; contains no scientific computation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='artifacts')
    p.add_argument('--python',default='.venv/bin/python')
    args=p.parse_args()
    logs=Path(args.output)/'dispatch'
    logs.mkdir(parents=True,exist_ok=True)
    for seed in [1001,1002,1003,1004]:
        for wd in [0,1]:
            endpoint=Path(args.output)/'confirmation'/f'seed_{seed}_wd_{wd}'/'endpoint.json'
            while not endpoint.exists() or json.loads(endpoint.read_text())['updates']<100000:
                sequence=len(list(logs.glob('*.txt')))+1
                label=f'confirmation-{seed}-wd{wd}-dispatch{sequence}'
                command=[sys.executable,'inputs/compute.py','--category','compute','--label',label,
                    '--timeout','175','--',args.python,'study.py','run','--seed',str(seed),'--wd',str(wd),
                    '--device','cpu','--implementation','dense','--target','100000','--seconds','155',
                    '--output',args.output,'--label',label]
                print(json.dumps(dict(event='dispatch',label=label)),flush=True)
                with (logs/(label+'.txt')).open('w') as log:
                    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
                if result.returncode:
                    print(json.dumps(dict(event='broker-stop',label=label,returncode=result.returncode)),flush=True)
                    raise SystemExit(result.returncode)
                ep=json.loads(endpoint.read_text())
                print(json.dumps(dict(event='segment-completed',label=label,updates=ep['updates'],
                    seconds=ep['elapsed_seconds'])),flush=True)
    print(json.dumps(dict(event='all-confirmation-complete')),flush=True)

if __name__=='__main__':
    main()
