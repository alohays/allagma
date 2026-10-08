"""Broker-only serial full reproduction; this launcher does no science itself."""
import argparse,json,subprocess,sys
from pathlib import Path

def submit(category,label,timeout,argv,marked=False):
    cmd=[sys.executable,'inputs/compute.py','--category',category,'--label',label,'--timeout',str(timeout)]
    if marked:cmd+=['--attempt']
    result=subprocess.run(cmd+['--']+argv,text=True,capture_output=True)
    print(result.stdout,end='',flush=True);print(result.stderr,end='',file=sys.stderr,flush=True)
    if result.returncode:
        raise RuntimeError(f'Broker request stopped: {label}. Inspect its retained response; no automatic duplicate request.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--env',default='.reproduce-venv');p.add_argument('--root',default='reproduced')
    args=p.parse_args()
    if Path(args.env).exists() or Path(args.root).exists():raise RuntimeError('Use new environment and output paths; retained runs must not be overwritten.')
    submit('setup','reproduction-new-environment',60,[sys.executable,'-m','venv',args.env])
    python=str(Path(args.env)/'bin/python')
    submit('setup','reproduction-offline-packages',120,[python,'-m','pip','install','--no-index','--find-links','inputs/materials/wheels','-r','inputs/materials/requirements-reference.lock'])
    protocol=json.loads(Path('protocol.json').read_text())
    for dataset,seeds in protocol['confirmation_seeds'].items():
        for seed in seeds:
            for policy,total in [('constant',10000),('cosine',5000),('cosine',10000)]:
                label=f'reproduce-{dataset}-{seed}-{policy}-{total}'
                submit('compute',label,60,[python,'study.py','--phase','confirmation','--dataset',dataset,'--seed',str(seed),
                       '--policy',policy,'--total',str(total),'--stop',str(total),'--attempt-id',label,'--root',args.root])
    analysis=str(Path(args.root)/'analysis');measurement=str(Path(args.root)/'measurements.json')
    submit('compute','reproduction-analysis',60,[python,'analyze.py','--root',args.root,'--out',analysis,'--measurements',measurement])
    submit('compute','reproduction-verification',60,[python,'verify.py','--measurements',measurement,'--analysis',analysis,'--out',str(Path(args.root)/'verification.json')])
    for dataset in protocol['datasets']:
        submit('compute',f'reproduction-regenerate-{dataset}',60,[python,'regenerate.py','--dataset',dataset,'--measurements',measurement,'--out',str(Path(args.root)/f'regeneration-{dataset}.json')])

if __name__=='__main__':main()
