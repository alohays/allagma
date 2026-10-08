"""Publication figures from retained measurements; explicit, uncrowded axis ticks."""
import argparse,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('.tmp/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    p=argparse.ArgumentParser();p.add_argument('--measurements',default='analysis/measurements.json');p.add_argument('--out',default='figures');args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    runs=json.loads(Path(args.measurements).read_text())['runs']
    matplotlib.rcParams['svg.hashsalt']='modadd-final-v1'
    for metric in ('accuracy','loss'):
        fig,axes=plt.subplots(2,4,figsize=(14,6),sharex=True,sharey=True)
        for run in runs:
            ax=axes[run['weight_decay'],run['seed']-1001];curve=run['curve'];steps=[c['step'] for c in curve]
            ax.plot(steps,[c['train_'+metric] for c in curve],label='Train',color='#277da1',lw=1.2)
            ax.plot(steps,[c['test_'+metric] for c in curve],label='Held-out',color='#e76f51',lw=1.2)
            ax.set_xscale('symlog',linthresh=1000)
            ax.set_xticks([0,1000,10000,100000],labels=['0','1,000','10,000','100,000'])
            ax.set_title(f"Seed {run['seed']}, decay {run['weight_decay']}")
            if metric=='accuracy':ax.set_ylim(-.02,1.03);ax.axhline(.95,color='gray',ls=':',lw=.6)
            else:ax.set_yscale('symlog',linthresh=.001)
            ax.grid(alpha=.2);ax.set_xlabel('Optimizer updates')
        axes[0,0].legend(loc='center right');axes[0,0].set_ylabel(metric.title());axes[1,0].set_ylabel(metric.title())
        fig.suptitle('Individual learning curves; linear update axis to 1,000, logarithmic thereafter')
        fig.tight_layout();fig.savefig(out/f'learning-{metric}.png',dpi=180);fig.savefig(out/f'learning-{metric}.svg',metadata={'Date':None});plt.close(fig)
    (out/'README.md').write_text('Generated from the retained research-measurements-v1 curves by study/plot.py. The update axis is linear to 1000 and logarithmic thereafter; the loss axis uses symlog with a 0.001 linear threshold. This is a tick-label presentation revision only; earlier figures remain in analysis/ and analysis-repeat/.\n')

if __name__=='__main__':main()
