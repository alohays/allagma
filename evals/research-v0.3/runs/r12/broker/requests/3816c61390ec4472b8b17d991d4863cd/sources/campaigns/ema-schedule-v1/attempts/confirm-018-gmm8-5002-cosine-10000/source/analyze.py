"""AI-generated retained-evidence reanalysis. Run via common broker."""
import argparse
import csv
import itertools
import json
import math
import os
from pathlib import Path
from common import ROOT,CAMP,read,write,ref,sha
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mpl-cache'))
import numpy as np
from scipy.stats import t as student_t
from reference import sliced_wasserstein,mode_coverage

VARIANTS=['raw','ema099','ema0999']

def summarize(values):
    a=np.asarray(values,dtype=float); n=len(a)
    if not n: return {'n':0,'mean':None,'ci95':None,'values':[],'signflip_p':None,'leave_one_out':[]}
    mean=float(a.mean()); ci=None
    if n>=2:
        half=float(student_t.ppf(.975,n-1)*a.std(ddof=1)/np.sqrt(n)); ci=[mean-half,mean+half]
    signs=np.array(list(itertools.product([-1,1],repeat=n)))
    p=float(np.mean(np.abs((signs*a).mean(axis=1))>=abs(mean)-1e-14))
    return {'n':n,'mean':mean,'ci95':ci,'values':a.tolist(),'signflip_p':p,
            'leave_one_out':[float(np.delete(a,i).mean()) for i in range(n)] if n>=2 else []}

def recompute(output,manifest_path=None):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    if manifest_path:
        raw=read(manifest_path)
        for r in raw['files']: assert sha(ROOT/r['path'])==r['sha256'],r['path']
        candidates=[ROOT/p for p in raw['results']]
    else:
        candidates=sorted(CAMP.glob('attempts/*/result.json'))
    runs=[]; allrefs={}; resultrefs=[]; excluded=[]
    for p in candidates:
        value=read(p)
        if not value.get('runs'): continue
        if read(p.parent/'finished.json')['status']!='succeeded': continue
        resultrefs.append(str(p.relative_to(ROOT))); allrefs[str(p.relative_to(ROOT))]=ref(p)
        for original in value['runs']:
            run=dict(original)
            if run['phase']!='confirmation': continue
            a=np.load(ROOT/run['arrays'],allow_pickle=False)
            for key in ['heldout','raw','ema099','ema0999']: assert a[key].shape==(2048,2) and np.isfinite(a[key]).all()
            assert a['generation_noise'].shape==(100,2048,2)
            measured={}
            for variant in VARIANTS:
                v={'sw1':sliced_wasserstein(a[variant],a['heldout'])}
                assert abs(v['sw1']-original['metrics'][variant]['sw1'])<1e-12
                if run['dataset']=='gmm8':
                    m=mode_coverage(a[variant]); v.update(mode_counts=m['counts'],covered_modes=m['covered'],inlier_fraction=m['inlier_fraction'],inlier_count=sum(m['counts']))
                measured[variant]=v
            run['metrics']=measured; runs.append(run)
            for k in ['arrays','weights','training_trace','inputs','initial_weights']:
                allrefs[run[k]]=ref(ROOT/run[k])
    keys=[(r['dataset'],r['seed'],r['updates'],r['schedule']) for r in runs]
    assert len(keys)==len(set(keys)), 'Duplicate cells cannot be scientific replicates'
    for p in sorted(CAMP.glob('attempts/*/started.json')):
        if str((p.parent/'result.json').relative_to(ROOT)) not in resultrefs:
            excluded.append({'attempt':p.parent.name,'reason':'Pilot, failed, or interrupted; not confirmation evidence'})
    raw={'format':'ema-raw-manifest-v1','results':resultrefs,'files':list(allrefs.values()),'exclusions':excluded}
    write(output/'raw-manifest.json',raw)
    runs.sort(key=lambda r:(r['dataset'],r['seed'],r['updates'],r['schedule']))
    measurements={'format':'research-measurements-v1','task_id':'ema-schedule','protocol':'campaigns/ema-schedule-v1/protocol.json','runs':runs}
    write(output/'measurements.json',measurements)
    rows=[]
    for r in runs:
        for variant in VARIANTS:
            rows.append({k:r[k] for k in ['dataset','seed','updates','schedule']}|{'variant':variant,**{k:v for k,v in r['metrics'][variant].items() if k!='mode_counts'}})
    if rows:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (output/'seed-metrics.csv').open('w') as f:
            writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)
    lookup={(r['dataset'],r['seed'],r['updates'],r['schedule']):r for r in runs}
    effects=[]; contrasts=[]; valuesrows=[]; absolute=[]
    for dataset in ['moons','gmm8']:
        seeds=read(CAMP/'protocol.json')['seeds']['confirmation'][dataset]
        for variant in ['ema099','ema0999']:
            def D(seed,T,P):
                r=lookup[dataset,seed,T,P]['metrics'];return r[variant]['sw1']-r['raw']['sw1']
            for T in [5000,10000]:
                for P in ['constant','cosine']:
                    selected=[s for s in seeds if (dataset,s,T,P) in lookup]
                    effects.append({'dataset':dataset,'variant':variant,'updates':T,'schedule':P,'seeds':selected,**summarize([D(s,T,P) for s in selected])})
            specs=[('schedule',str(T),[(T,'cosine',1),(T,'constant',-1)]) for T in [5000,10000]]
            specs += [('duration',P,[(10000,P,1),(5000,P,-1)]) for P in ['constant','cosine']]
            specs += [('interaction','all',[(10000,'cosine',1),(10000,'constant',-1),(5000,'cosine',-1),(5000,'constant',1)])]
            for kind,at,terms in specs:
                selected=[s for s in seeds if all((dataset,s,T,P) in lookup for T,P,_ in terms)]
                vals=[sum(c*D(s,T,P) for T,P,c in terms) for s in selected]
                contrasts.append({'dataset':dataset,'variant':variant,'contrast':kind,'at':at,'seeds':selected,**summarize(vals)})
                valuesrows.extend({'dataset':dataset,'variant':variant,'contrast':kind,'at':at,'seed':s,'value':v} for s,v in zip(selected,vals))
        for variant in VARIANTS:
            for kind,at,terms in specs:
                selected=[s for s in seeds if all((dataset,s,T,P) in lookup for T,P,_ in terms)]
                vals=[sum(c*lookup[dataset,s,T,P]['metrics'][variant]['sw1'] for T,P,c in terms) for s in selected]
                absolute.append({'dataset':dataset,'variant':variant,'contrast':kind,'at':at,'seeds':selected,**summarize(vals)})
    coverage=[]
    for T in [5000,10000]:
        for P in ['constant','cosine']:
            rr=[r for r in runs if r['dataset']=='gmm8' and r['updates']==T and r['schedule']==P]
            for variant in VARIANTS:
                coverage.append({'updates':T,'schedule':P,'variant':variant,'counts':[r['metrics'][variant]['mode_counts'] for r in rr],
                    'covered_modes':summarize([r['metrics'][variant]['covered_modes'] for r in rr]),
                    'inlier_fraction':summarize([r['metrics'][variant]['inlier_fraction'] for r in rr])})
    summary={'complete_cells':len(runs),'required_cells':32,'complete':len(runs)==32,'effects':effects,'contrasts':contrasts,
             'absolute_sw1_contrasts':absolute,'coverage':coverage,'uncertainty':'Seed-level paired Student t 95% intervals, unadjusted; df=n-1; no interval n<2. Exact sign flips and leave-one-seed-out sensitivity.'}
    write(output/'summary.json',summary)
    write(output/'contrasts.json',{'ema_benefit_contrasts':contrasts,'absolute_sw1_contrasts':absolute})
    with (output/'seed-contrasts.csv').open('w') as f:
        wr=csv.DictWriter(f,['dataset','variant','contrast','at','seed','value']);wr.writeheader();wr.writerows(valuesrows)
    make_figure(summary,output)
    write(output/'record.json',{'schema_version':'0.2','record_type':'AnalysisRecord','analysis_id':output.name,
          'raw_manifest':ref(output/'raw-manifest.json'),'analysis_revision':sha(Path(__file__)),'code':ref(Path(__file__)),
          'configuration':{'protocol':str((CAMP/'protocol.json').relative_to(ROOT)),'independent_unit':'seed'},
          'outputs':[ref(output/p) for p in ['measurements.json','summary.json','contrasts.json','seed-contrasts.csv','main-figure.png','main-figure.pdf']],
          'exclusions':excluded,'uncertainty':summary['uncertainty'],'dependencies':[ref(CAMP/'protocol.json'),ref(ROOT/'study/reference.py')]})
    return summary

def make_figure(summary,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,7),sharey=True)
    conditions=[(5000,'constant'),(5000,'cosine'),(10000,'constant'),(10000,'cosine')]
    for i,d in enumerate(['moons','gmm8']):
        for j,v in enumerate(['ema099','ema0999']):
            ax=axes[i,j];ax.axhline(0,color='.4',lw=1)
            for x,(T,P) in enumerate(conditions):
                e=next(e for e in summary['effects'] if (e['dataset'],e['variant'],e['updates'],e['schedule'])==(d,v,T,P))
                if e['n']:
                    ax.scatter(x+np.linspace(-.1,.1,e['n']),e['values'],color='#356AA0',s=22)
                    if e['ci95']: ax.errorbar(x,e['mean'],yerr=[[e['mean']-e['ci95'][0]],[e['ci95'][1]-e['mean']]],color='black',fmt='D',capsize=4)
            ax.set_xticks(range(4),['5k\nconstant','5k\ncosine','10k\nconstant','10k\ncosine'])
            ax.set_title(f'{d}: {v}');ax.set_ylabel('EMA − raw Sliced W1');ax.grid(axis='y',alpha=.2)
    fig.suptitle('Full schedule policy and terminal duration\nDots: independent seeds; diamonds: mean; bars: unadjusted 95% t intervals')
    fig.tight_layout();fig.savefig(out/'main-figure.png',dpi=180);fig.savefig(out/'main-figure.pdf');plt.close(fig)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--raw-manifest');p.add_argument('--compare')
    a=p.parse_args();s=recompute(ROOT/a.output,ROOT/a.raw_manifest if a.raw_manifest else None)
    if a.compare:
        for n in ['summary.json','measurements.json','contrasts.json','seed-contrasts.csv']:
            assert (ROOT/a.output/n).read_bytes()==(ROOT/a.compare/n).read_bytes(),n
        write(ROOT/a.output/'comparison.json',{'status':'pass','compared_against':a.compare,'files':['summary.json','measurements.json','contrasts.json','seed-contrasts.csv']})
    print(json.dumps({'complete_cells':s['complete_cells'],'complete':s['complete']}))

if __name__=='__main__': main()
