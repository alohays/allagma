"""Sequential retained-data analysis and final plotting, inside one broker job."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--compare',default='analysis');args=p.parse_args()
subprocess.run([sys.executable,'study/analyze.py','--out',args.out,'--verify-checkpoints','--compare',args.compare],check=True)
subprocess.run([sys.executable,'study/plot.py','--measurements',str(Path(args.out)/'measurements.json'),'--out',str(Path(args.out)/'figures')],check=True)
