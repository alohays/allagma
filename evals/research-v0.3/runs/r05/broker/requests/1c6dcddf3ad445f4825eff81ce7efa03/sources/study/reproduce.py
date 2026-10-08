"""Full fresh-environment reproduction orchestrator; all work uses local broker."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',default='reproduced-study');args=p.parse_args()
assert not Path(args.output).exists(),'Choose a fresh --output directory'
def submit(category,label,timeout,command,cwd='.'):
    argv=[sys.executable,'inputs/compute.py','--category',category,'--label',label,'--timeout',str(timeout),'--cwd',cwd,'--',*command]
    result=subprocess.run(argv)
    if result.returncode:raise SystemExit('Broker request failed/stopped. Preserve its receipt; do not infer permission to exceed resource ceilings.')
submit('setup','reproduction-fresh-environment',120,[sys.executable,'study/stage_reproduction.py','--out',args.output])
py=str((Path(args.output)/'.venv/bin/python').resolve())
submit('compute','reproduction-pilot',35,[py,'study/native_pilot.py','--out','evidence/pilot-reproduction','--steps','5000'],args.output)
for seed in (1001,1002,1003,1004):
    for wd in (0,1):
        for end in (50000,100000):
            aid=f'reproduction-s{seed}-wd{wd}-to{end:06d}'
            submit('compute',aid,125,[py,'study/train.py','--seed',str(seed),'--weight-decay',str(wd),'--end-step',str(end),'--attempt-id',aid],args.output)
submit('compute','reproduction-analysis',60,[py,'study/analyze.py','--out','analysis','--verify-checkpoints'],args.output)
submit('compute','reproduction-reanalysis',45,[py,'study/analyze.py','--out','analysis-repeat','--compare','analysis'],args.output)
print('Complete fresh training and retained-data analyses are under '+args.output)
