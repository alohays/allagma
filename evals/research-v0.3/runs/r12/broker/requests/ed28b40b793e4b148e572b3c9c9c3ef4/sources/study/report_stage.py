"""Sequential record, raw-recomputation and manuscript handoffs; broker only."""
import subprocess
import sys
from common import ROOT
import records
import write_report

def main():
    records.reconcile()
    subprocess.run([sys.executable,'study/analyze.py','--raw-manifest','analysis/raw-manifest.json','--output','recomputed-r1','--compare','analysis'],cwd=ROOT,check=True)
    write_report.main()

if __name__=='__main__':main()
