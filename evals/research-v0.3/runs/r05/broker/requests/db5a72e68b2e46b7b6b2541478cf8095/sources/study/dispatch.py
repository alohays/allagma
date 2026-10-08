"""Orchestration only: every training segment is submitted to inputs/compute.py."""
import json,subprocess,sys
from pathlib import Path
p=__import__('argparse').ArgumentParser();p.add_argument('--root',default='evidence/confirmation');p.add_argument('--python',default='.venv/bin/python');p.add_argument('--timeout',type=int,default=125);args=p.parse_args()
for seed in (1001,1002,1003,1004):
  for wd in (0,1):
    for end in (50000,100000):
      pointer=Path(args.root)/f's{seed}-wd{wd}-latest.json'
      if pointer.exists() and json.loads(pointer.read_text())['step']>=end:continue
      attempt=f's{seed}-wd{wd}-to{end:06d}'
      base=Path(args.root)/'attempts'/attempt
      suffix=1
      while base.exists():
        suffix+=1;attempt=f's{seed}-wd{wd}-to{end:06d}-retry{suffix}';base=Path(args.root)/'attempts'/attempt
      argv=[sys.executable,'inputs/compute.py','--category','compute','--label',attempt,'--timeout',str(args.timeout),'--',args.python,'study/train.py','--seed',str(seed),'--weight-decay',str(wd),'--end-step',str(end),'--attempt-id',attempt,'--root',args.root]
      print('SUBMIT '+attempt,flush=True)
      result=subprocess.run(argv)
      if result.returncode:
        print('STOP: broker request did not complete; inspect retained receipt before continuation',flush=True)
        sys.exit(result.returncode)
print('All eight confirmation conditions reached 100000 updates.',flush=True)
