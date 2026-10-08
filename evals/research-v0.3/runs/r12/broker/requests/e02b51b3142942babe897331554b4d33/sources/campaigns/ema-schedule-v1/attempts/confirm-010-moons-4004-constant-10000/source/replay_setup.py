"""Fresh-reproduction workspace setup, called through the broker."""
import argparse
from pathlib import Path
import shutil
from common import ROOT,CAMP,BUNDLE

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);a=p.parse_args()
    dst=(ROOT/a.destination).resolve();dst.relative_to(ROOT);dst.mkdir(parents=True,exist_ok=False)
    shutil.copytree(ROOT/'study',dst/'study',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(BUNDLE,dst/'.allagma/bundles'/BUNDLE.name,ignore=shutil.ignore_patterns('__pycache__'))
    (dst/'campaigns/ema-schedule-v1').mkdir(parents=True)
    for f in ['lock.yaml','protocol.json','confirmation-freeze.json','forecast.json','plan.json']:
        shutil.copyfile(CAMP/f,dst/'campaigns/ema-schedule-v1'/f)
    shutil.copyfile(ROOT/'LICENSE-AI-Scientist',dst/'LICENSE-AI-Scientist')
    print(str(dst.relative_to(ROOT)))

if __name__=='__main__':main()
