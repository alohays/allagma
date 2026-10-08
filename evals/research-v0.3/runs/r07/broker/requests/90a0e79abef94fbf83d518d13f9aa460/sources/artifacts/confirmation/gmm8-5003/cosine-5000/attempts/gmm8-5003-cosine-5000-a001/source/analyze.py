"""Recompute all measurements, paired contrasts and figures from retained arrays."""
from __future__ import annotations
import argparse
import csv
import itertools
import json
import os
from pathlib import Path
import numpy as np
from scipy.stats import t
from common import ROOT, CAMPAIGN, write, ref, sha, array_hash, named_hash
from science import sliced_wasserstein, mode_coverage, Denoiser

VARIANTS=('raw','ema099','ema0999')
CONDITIONS=(('constant',5000),('cosine',5000),('constant',10000),('cosine',10000))

def statistics(values,seeds):
    a=np.array(values,dtype=float)
    n=len(a); mean=float(a.mean())
    sd=float(a.std(ddof=1)) if n>1 else None
    se=sd/n**.5 if n>1 else None
    radius=float(t.ppf(.975,n-1))*se if n>1 else None
    p=float(np.mean([abs(np.mean(a*np.array(signs)))>=abs(mean)-1e-15 for signs in itertools.product((-1,1),repeat=n)]))
    return {'n':n,'seeds':seeds,'values':values,'mean':mean,'sd':sd,'se':se,
            'ci95':[mean-radius,mean+radius] if n>1 else None,'sign_flip_p':p,
            'leave_one_out_means':[float(np.delete(a,i).mean()) for i in range(n)] if n>1 else []}

def analyze(base,out,allow_partial=False):
    base=ROOT/base; out=ROOT/out
    out.mkdir(parents=True,exist_ok=False)
    cells=[]; raw_refs=[]; exclusions=[]; result_refs=[]
    validated_inputs=set()
    state_keys=set(Denoiser().state_dict())
    for start in sorted(base.glob('*/*/*/attempts/*/started.json')):
        value=json.loads(start.read_text()); folder=start.parent
        if value['inputs']['phase']!='confirmation':
            exclusions.append({'attempt_id':value['attempt_id'],'reason':'pilot excluded from confirmation','evidence':str(start.relative_to(ROOT))})
            continue
        if not (folder/'result.json').exists():
            exclusions.append({'attempt_id':value['attempt_id'],'reason':'no successful terminal record','evidence':str(start.relative_to(ROOT))})
            continue
        result=json.loads((folder/'result.json').read_text())
        if result['status']!='succeeded':
            exclusions.append({'attempt_id':value['attempt_id'],'reason':result['status']})
            continue
        for artifact in result['outputs']:
            assert sha(ROOT/artifact['path'])==artifact['sha256'],artifact['path']
        result_refs.append(ref(folder/'result.json'))
        for mpath in result['measurements']:
            cell=json.loads((ROOT/mpath).read_text())
            if cell['schedule']=='cosine':
                assert cell['updates']==cell['actual_schedule_duration']
            with np.load(ROOT/cell['arrays'],allow_pickle=False) as arrays:
                assert arrays['heldout'].shape==(2048,2)
                assert arrays['generation_noise'].shape==(100,2048,2)
                assert array_hash(arrays['heldout'])==cell['heldout_sha256']
                assert array_hash(arrays['generation_noise'])==cell['generation_noise_sha256']
                for variant in VARIANTS:
                    assert arrays[variant].shape==(2048,2) and np.isfinite(arrays[variant]).all()
                    expected=cell['metrics'][variant]
                    metric={'sw1':sliced_wasserstein(arrays[variant],arrays['heldout'])}
                    assert abs(metric['sw1']-expected['sw1'])<1e-12
                    if cell['dataset']=='gmm8':
                        mode=mode_coverage(arrays[variant])
                        metric.update(mode_counts=mode['counts'],covered_modes=mode['covered'],
                                      inlier_fraction=mode['inlier_fraction'],inlier_count=sum(mode['counts']))
                        assert all(metric[k]==expected[k] for k in metric)
                    cell['metrics'][variant]=metric
            with np.load(ROOT/cell['weights'],allow_pickle=False) as weights:
                assert set(weights.files)=={name+'__'+k for name in VARIANTS for k in state_keys}
                assert all(np.isfinite(weights[k]).all() for k in weights.files)
            ipath=ROOT/cell['input_metadata']
            if ipath not in validated_inputs:
                meta=json.loads(ipath.read_text()); inputs=ipath.parent
                for name,digest in meta['file_hashes'].items():
                    assert sha(inputs/name)==digest
                with np.load(inputs/'initial.npz',allow_pickle=False) as initial:
                    assert named_hash({k:initial[k] for k in initial.files})==cell['initial_weights_sha256']
                with np.load(inputs/'training.npz',allow_pickle=False) as train:
                    prefix=named_hash({k:train[k] if k=='train' else train[k][:5000] for k in ('train','indices','noise','timesteps','noisy')})
                    assert prefix==cell['training_prefix_5000_sha256']
                validated_inputs.add(ipath)
                raw_refs.extend([ref(ipath),*(ref(inputs/name) for name in meta['file_hashes'])])
            raw_refs.extend(ref(ROOT/cell[k]) for k in ('arrays','weights','training_trace'))
            raw_refs.append(ref(ROOT/mpath))
            cells.append(cell)
    cells.sort(key=lambda c:(c['dataset'],c['seed'],c['updates'],c['schedule']))
    keys=[(c['dataset'],c['seed'],c['schedule'],c['updates']) for c in cells]
    assert len(set(keys))==len(keys),'Duplicate scientific cells are not replicates'
    expected={(d,s,p,u) for d,seeds in [('moons',range(4001,4005)),('gmm8',range(5001,5005))] for s in seeds for p,u in CONDITIONS}
    complete=set(keys)==expected
    if not allow_partial:
        assert complete, f'Incomplete cells: {len(cells)}/32'
    bykey={key:c for key,c in zip(keys,cells)}
    matching=[]
    for dataset,seeds in [('moons',range(4001,4005)),('gmm8',range(5001,5005))]:
        for seed in seeds:
            group=[c for c in cells if c['dataset']==dataset and c['seed']==seed]
            for field in ('initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256'):
                assert len({c[field] for c in group})<=1
            matching.append({'dataset':dataset,'seed':seed,'cells':len(group),'all_available_input_hashes_match':True})
    write(out/'measurements.json',{'format':'research-measurements-v1','task_id':'ema-schedule','protocol':'PROTOCOL.md','runs':cells})
    raw_manifest={'format':'ema-raw-manifest-v1','eligible_attempts':result_refs,
                  'raw':list({item['path']:item for item in raw_refs}.values()),'exclusions':exclusions,
                  'protocol':ref(ROOT/'PROTOCOL.md'),'complete':complete}
    write(out/'raw-manifest.json',raw_manifest)
    effects=[]; absolute=[]; coverage=[]; perseed=[]
    for dataset,seeds0 in [('moons',range(4001,4005)),('gmm8',range(5001,5005))]:
        seeds=[s for s in seeds0 if all((dataset,s,p,u) in bykey for p,u in CONDITIONS)]
        if not seeds:
            continue
        def values(variant,policy,updates,delta):
            return [bykey[dataset,s,policy,updates]['metrics'][variant]['sw1']-
                    (bykey[dataset,s,policy,updates]['metrics']['raw']['sw1'] if delta else 0) for s in seeds]
        for variant in VARIANTS:
            for delta in ([False] if variant=='raw' else [False,True]):
                target=effects if delta else absolute
                table={(p,u):np.array(values(variant,p,u,delta)) for p,u in CONDITIONS}
                def emit(kind,arr,**fields):
                    target.append({'dataset':dataset,'variant':variant,'contrast':kind,**fields,**statistics(arr.tolist(),seeds)})
                for (policy,updates),arr in table.items():
                    emit('cell',arr,schedule=policy,updates=updates)
                    if delta:
                        perseed.extend({'dataset':dataset,'seed':s,'variant':variant,'schedule':policy,'updates':updates,'ema_minus_raw':float(v)} for s,v in zip(seeds,arr))
                for u in (5000,10000):
                    emit('schedule_cosine_minus_constant',table['cosine',u]-table['constant',u],updates=u)
                for policy in ('constant','cosine'):
                    emit('duration_10000_minus_5000',table[policy,10000]-table[policy,5000],schedule=policy)
                emit('interaction',table['cosine',10000]-table['constant',10000]-table['cosine',5000]+table['constant',5000])
        if dataset=='gmm8':
            for p,u in CONDITIONS:
                for variant in VARIANTS:
                    for metric in ('covered_modes','inlier_fraction'):
                        v=[bykey[dataset,s,p,u]['metrics'][variant][metric] for s in seeds]
                        coverage.append({'dataset':dataset,'variant':variant,'schedule':p,'updates':u,'metric':metric,**statistics(v,seeds)})
    summary={'complete':complete,'cells':len(cells),'independent_seeds_per_dataset':4 if complete else None,
             'effects':effects,'absolute_sw1':absolute,'coverage':coverage,
             'uncertainty':'Unadjusted descriptive two-sided 95% Student t intervals over paired seeds; exact two-sided sign flips; no sample/projection pseudoreplication',
             'matching':matching,'recomputed_metric_agreement':True}
    write(out/'summary.json',summary)
    write(out/'contrasts.json',{'effects':effects,'absolute_sw1':absolute,'coverage':coverage})
    with (out/'paired-differences.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['dataset','seed','variant','schedule','updates','ema_minus_raw'])
        writer.writeheader();writer.writerows(perseed)
    rows=[{'dataset':c['dataset'],'seed':c['seed'],'schedule':c['schedule'],'updates':c['updates'],'variant':v,**c['metrics'][v]} for c in cells for v in VARIANTS]
    write(out/'seed-level.json',rows)
    if effects:
        plot(effects,out)
    write(out/'record.json',{'schema_version':'0.2','record_type':'AnalysisRecord','analysis_id':out.name,
        'raw_manifest':ref(out/'raw-manifest.json'),'analysis_revision':sha(Path(__file__)),
        'code':ref(Path(__file__)),'configuration':{'complete':complete,'independent_unit':'seed within dataset'},
        'outputs':[ref(p) for p in sorted(out.iterdir()) if p.name not in ('record.json','raw-manifest.json')],
        'exclusions':exclusions,'uncertainty':summary['uncertainty'],
        'dependencies':[ref(ROOT/'PROTOCOL.md'),ref(CAMPAIGN/'confirmation-freeze.json'),*result_refs]})
    print(json.dumps({'cells':len(cells),'complete':complete,'output':str(out.relative_to(ROOT))}))
    return summary

def plot(effects,out):
    os.environ['MPLCONFIGDIR']=str(ROOT/'.tmp/mpl')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(10,7),sharex=True)
    colors={'constant':'#0072B2','cosine':'#D55E00'}
    for i,d in enumerate(('moons','gmm8')):
        for j,v in enumerate(('ema099','ema0999')):
            ax=axes[i,j]
            for k,(p,u) in enumerate(CONDITIONS):
                entry=next((e for e in effects if e['dataset']==d and e['variant']==v and e['contrast']=='cell' and e['schedule']==p and e['updates']==u),None)
                if entry is None:continue
                ax.scatter(np.arange(entry['n'])*.055-.0825+k,entry['values'],s=24,color=colors[p],alpha=.75)
                ci=entry['ci95']
                ax.errorbar(k,entry['mean'],yerr=[[entry['mean']-ci[0]],[ci[1]-entry['mean']]],fmt='D',color='black',capsize=4,markersize=5)
            ax.axhline(0,color='gray',lw=.8)
            ax.set_title(d+' · '+v.replace('ema','EMA '))
            ax.set_xticks(range(4),['Constant\n5k','Cosine\n5k','Constant\n10k','Cosine\n10k'])
            ax.set_ylabel('EMA − raw Sliced W1')
            ax.grid(axis='y',alpha=.2)
    fig.suptitle('EMA benefit across learning-rate policy and duration\nDots: paired seeds; diamonds: mean; bars: unadjusted 95% t interval')
    fig.tight_layout()
    fig.savefig(out/'main-figure.png',dpi=180,metadata={'Software':'ema-schedule study'})
    fig.savefig(out/'main-figure.pdf',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='artifacts')
    parser.add_argument('--out',required=True)
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    analyze(args.base,args.out,args.allow_partial)
