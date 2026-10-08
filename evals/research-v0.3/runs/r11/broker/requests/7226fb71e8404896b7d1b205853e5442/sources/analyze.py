"""Recompute measurements, paired contrasts, figures and tables from raw samples."""
from __future__ import annotations
import argparse, csv, itertools, json, math, os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('.tmp/matplotlib').resolve()))
import numpy as np
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from science import sliced_wasserstein
from study import VARIANTS, metrics, json_write, file_hash

def stats(values):
    a=np.array(values,dtype=float); n=len(a); mean=float(a.mean())
    se=float(a.std(ddof=1)/np.sqrt(n)) if n>1 else None
    half=float(t.ppf(.975,n-1)*se) if n>1 else None
    signs=np.array(list(itertools.product((-1,1),repeat=n)))
    perm=np.abs((signs*a).mean(axis=1))
    p=float((perm>=abs(mean)-1e-14).mean())
    return dict(n=n,values=a.tolist(),mean=mean,se=se,
                ci95=[mean-half,mean+half] if half is not None else None,
                exact_signflip_p=p,seeds_negative=int((a<0).sum()),
                leave_one_out_means=[float(np.delete(a,i).mean()) for i in range(n)] if n>1 else [])

def write_csv(path,rows):
    if not rows: Path(path).write_text(''); return
    with open(path,'w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def analyze(root='evidence',out='analysis',measurement_path='measurements.json'):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[json.loads(p.read_text()) for p in sorted((root/'cells'/'confirmation').glob('*/update-*/record.json'))]
    by={}; metric_rows=[]; raw_checks=[]
    for r in records:
        key=(r['dataset'],r['seed'],r['updates'],r['schedule'])
        if key in by: raise ValueError(f'Duplicate scientific cell {key}')
        with np.load(r['arrays'],allow_pickle=False) as a:
            recomputed={v:metrics(r['dataset'],a[v],a['heldout']) for v in VARIANTS}
        raw_checks.append(dict(cell=list(key),recorded_metrics_equal=recomputed==r['metrics']))
        if recomputed!=r['metrics']: raise ValueError(f'Recorded metric mismatch {key}')
        r['metrics']=recomputed;by[key]=r
        for v in VARIANTS:
            m=r['metrics'][v]
            metric_rows.append(dict(dataset=r['dataset'],seed=r['seed'],updates=r['updates'],schedule=r['schedule'],variant=v,
                                    sw1=m['sw1'],delta_vs_raw=m['sw1']-r['metrics']['raw']['sw1'],
                                    covered_modes=m.get('covered_modes',''),inlier_count=m.get('inlier_count',''),inlier_fraction=m.get('inlier_fraction','')))
    json_write(measurement_path,dict(format='research-measurements-v1',task_id='ema-schedule',protocol='protocol.json',runs=records))
    write_csv(out/'seed-metrics.csv',metric_rows)
    protocol=json.loads(Path('protocol.json').read_text()); conditions=[]; contrasts=[]; seed_contrasts=[]; controls=[]; absolute=[]; coverage=[]
    for dataset,seeds in protocol['confirmation_seeds'].items():
        for seed in seeds:
            ev=root/'inputs-retained'/'confirmation'/f'{dataset}-{seed}'/'evaluation.npz'
            if ev.exists():
                with np.load(ev,allow_pickle=False) as a:
                    controls.append(dict(dataset=dataset,seed=seed,heldout_vs_independent_sw1=sliced_wasserstein(a['heldout'],a['independent_heldout'])))
        for updates in (5000,10000):
            for policy in ('constant','cosine'):
                available=[seed for seed in seeds if (dataset,seed,updates,policy) in by]
                if not available: continue
                for v in VARIANTS:
                    absolute.append(dict(dataset=dataset,updates=updates,schedule=policy,variant=v,seeds=available,
                                         **stats([by[dataset,s,updates,policy]['metrics'][v]['sw1'] for s in available])))
                for v in VARIANTS[1:]:
                    values=[by[dataset,s,updates,policy]['metrics'][v]['sw1']-by[dataset,s,updates,policy]['metrics']['raw']['sw1'] for s in available]
                    conditions.append(dict(dataset=dataset,updates=updates,schedule=policy,variant=v,seeds=available,**stats(values)))
                if dataset=='gmm8':
                    for v in VARIANTS:
                        cells=[by[dataset,s,updates,policy]['metrics'][v] for s in available]
                        coverage.append(dict(updates=updates,schedule=policy,variant=v,seeds=available,
                          covered_modes=[c['covered_modes'] for c in cells],inlier_counts=[c['inlier_count'] for c in cells],
                          inlier_fraction=stats([c['inlier_fraction'] for c in cells])))
        complete=[s for s in seeds if all((dataset,s,u,p) in by for u in (5000,10000) for p in ('constant','cosine'))]
        if not complete: continue
        for variant in VARIANTS:
            for target in (('absolute_sw1',) if variant=='raw' else ('delta_vs_raw','absolute_sw1')):
                def value(seed,updates,policy):
                    m=by[dataset,seed,updates,policy]['metrics']
                    return m[variant]['sw1']-(m['raw']['sw1'] if target=='delta_vs_raw' else 0)
                definitions=[('schedule_at_5000',lambda s:value(s,5000,'cosine')-value(s,5000,'constant')),
                             ('schedule_at_10000',lambda s:value(s,10000,'cosine')-value(s,10000,'constant')),
                             ('duration_constant',lambda s:value(s,10000,'constant')-value(s,5000,'constant')),
                             ('duration_cosine',lambda s:value(s,10000,'cosine')-value(s,5000,'cosine')),
                             ('interaction',lambda s:(value(s,10000,'cosine')-value(s,10000,'constant'))-(value(s,5000,'cosine')-value(s,5000,'constant')))]
                for name,fn in definitions:
                    values=[fn(s) for s in complete]
                    contrasts.append(dict(dataset=dataset,variant=variant,target=target,contrast=name,seeds=complete,**stats(values)))
                    for seed,v in zip(complete,values):seed_contrasts.append(dict(dataset=dataset,seed=seed,variant=variant,target=target,contrast=name,value=v))
    summary=dict(format='ema-schedule-analysis-v1',cell_count=len(records),expected_cell_count=32,
                 uncertainty='seed-paired Student t, 95%, df=n-1; unadjusted; exact sign flips; n=4 planned',
                 conditions=conditions,contrasts=contrasts,absolute_sw1=absolute,coverage=coverage,finite_sample_controls=controls,
                 source_revision=json.loads(Path('freeze.json').read_text())['source_revision'] if Path('freeze.json').exists() else None,
                 arrays=[dict(path=r['arrays'],sha256=file_hash(r['arrays'])) for r in records])
    json_write(out/'summary.json',summary);json_write(out/'metric-recomputation.json',raw_checks)
    write_csv(out/'seed-contrasts.csv',seed_contrasts)
    write_csv(out/'finite-sample-controls.csv',controls)
    fig,axes=plt.subplots(2,2,figsize=(11,7.5),sharex=True)
    for i,dataset in enumerate(('moons','gmm8')):
        for j,variant in enumerate(VARIANTS[1:]):
            ax=axes[i,j];ax.axhline(0,color='0.6',lw=1)
            for k,(u,p) in enumerate(((5000,'constant'),(5000,'cosine'),(10000,'constant'),(10000,'cosine'))):
                found=[c for c in conditions if (c['dataset'],c['variant'],c['updates'],c['schedule'])==(dataset,variant,u,p)]
                if not found: continue
                c=found[0];color='#1f77b4' if p=='constant' else '#d97706'
                ax.scatter(k+np.linspace(-.13,.13,c['n']),c['values'],c=color,s=30,zorder=3)
                if c['ci95']:
                    ax.errorbar(k,c['mean'],yerr=[[c['mean']-c['ci95'][0]],[c['ci95'][1]-c['mean']]],fmt='D',color='black',capsize=4,markersize=5,zorder=4)
            ax.set_title(f'{dataset} · {variant}');ax.set_xticks(range(4),['5k\nconstant','5k\ncosine','10k\nconstant','10k\ncosine'])
            ax.set_ylabel('EMA − raw SW1');ax.grid(axis='y',alpha=.2)
    fig.suptitle('Schedule policy changes the apparent EMA benefit\nDots: seeds; diamonds and bars: paired mean and unadjusted 95% t interval')
    fig.tight_layout();fig.savefig(out/'main-figure.png',dpi=180);fig.savefig(out/'main-figure.pdf');plt.close(fig)
    lines=['| Dataset | Updates | Policy | EMA | Mean Δ SW1 | 95% t interval | Seeds improved |','|---|---:|---|---|---:|---|---:|']
    for c in conditions:
        ci=c['ci95'];interval=f'[{ci[0]:.6f}, {ci[1]:.6f}]' if ci else 'unavailable'
        lines.append(f"| {c['dataset']} | {c['updates']} | {c['schedule']} | {c['variant']} | {c['mean']:.6f} | {interval} | {c['seeds_negative']}/{c['n']} |")
    lines+=['','| Dataset | EMA | Contrast on Δ SW1 | Mean | 95% t interval |','|---|---|---|---:|---|']
    for c in contrasts:
        if c['target']!='delta_vs_raw':continue
        ci=c['ci95'];interval=f'[{ci[0]:.6f}, {ci[1]:.6f}]' if ci else 'unavailable'
        lines.append(f"| {c['dataset']} | {c['variant']} | {c['contrast']} | {c['mean']:.6f} | {interval} |")
    (out/'tables.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(cell_count=len(records),conditions=len(conditions),contrasts=len(contrasts),outputs=str(out))),flush=True)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='evidence');p.add_argument('--out',default='analysis');p.add_argument('--measurements',default='measurements.json')
    a=p.parse_args();analyze(a.root,a.out,a.measurements)
