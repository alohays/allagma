"""Independent raw-evidence audit; no reference metric helper calls."""
import argparse, hashlib, itertools, json, math, os
os.environ.setdefault('PYTORCH_MPS_LOW_WATERMARK_RATIO','0.1')
from pathlib import Path
import numpy as np
from study import array_hash, file_hash, json_write, state_hash

def independent_sw1(x,y):
    angles=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    matrix=np.stack([np.cos(angles),np.sin(angles)],axis=0)
    a=np.sort(np.asarray(x,dtype=np.float64)@matrix,axis=0)
    b=np.sort(np.asarray(y,dtype=np.float64)@matrix,axis=0)
    return float(np.mean(np.abs(a-b)))

def main():
    p=argparse.ArgumentParser();p.add_argument('--measurements',default='measurements.json');p.add_argument('--analysis',default='analysis');p.add_argument('--out',default='evidence/verification.json')
    a=p.parse_args();measurements=json.loads(Path(a.measurements).read_text());runs=measurements['runs']
    protocol=json.loads(Path('protocol.json').read_text());freeze=json.loads(Path('freeze.json').read_text())
    assert file_hash('protocol.json')==freeze['protocol_sha256']
    expected={(d,s,u,p) for d,seeds in protocol['confirmation_seeds'].items() for s in seeds for u in (5000,10000) for p in ('constant','cosine')}
    keys={(r['dataset'],r['seed'],r['updates'],r['schedule']) for r in runs}
    assert keys==expected and len(runs)==32
    checks=[]; metric_by={};seen_inputs={};max_error=0.
    from science import Denoiser, schedule
    model=Denoiser();state_keys=set(model.state_dict())
    for r in runs:
        with np.load(r['arrays'],allow_pickle=False) as ar:
            assert ar['heldout'].shape==(2048,2) and ar['generation_noise'].shape==(100,2048,2)
            assert array_hash(ar['heldout'])==r['heldout_sha256'] and array_hash(ar['generation_noise'])==r['generation_noise_sha256']
            for v in ('raw','ema099','ema0999'):
                samples=ar[v];assert samples.shape==(2048,2) and np.isfinite(samples).all() and samples.dtype==np.float32
                score=independent_sw1(samples,ar['heldout']);error=abs(score-r['metrics'][v]['sw1']);max_error=max(error,max_error);assert error<1e-12
                metric_by[r['dataset'],r['seed'],r['updates'],r['schedule'],v]=score
                if r['dataset']=='gmm8':
                    angle=np.arange(8)*math.pi/4;centers=2*np.stack([np.cos(angle),np.sin(angle)],axis=1)
                    distances=np.sum((samples.astype(np.float64)[:,None]-centers[None])**2,axis=2)
                    index=distances.argmin(axis=1);inside=distances[np.arange(2048),index]<=.45**2
                    counts=np.array([np.sum(inside&(index==i)) for i in range(8)])
                    m=r['metrics'][v];assert counts.tolist()==m['mode_counts'] and int((counts>=21).sum())==m['covered_modes']
                    assert int(inside.sum())==m['inlier_count'] and float(inside.mean())==m['inlier_fraction']
        with np.load(r['weights'],allow_pickle=False) as weights:
            assert set(weights.files)=={v+'__'+k for v in ('raw','ema099','ema0999') for k in state_keys}
            for v in weights.files:assert weights[v].dtype==np.float32 and np.isfinite(weights[v]).all()
        pair=(r['dataset'],r['seed']);provenance=tuple(r[k] for k in ('initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256'))
        if pair in seen_inputs: assert provenance==seen_inputs[pair]
        else:
            seen_inputs[pair]=provenance
            meta=json.loads(Path(r['provenance']).read_text())
            for name,h in meta['files'].items():assert file_hash(Path(meta['directory'])/name)==h
            with np.load(r['initial_state'],allow_pickle=False) as init:
                assert set(init.files)==state_keys and state_hash(init)==r['initial_weights_sha256']
            with np.load(r['retained_inputs'],allow_pickle=False) as inp:
                assert inp['train'].shape==(100000,2) and inp['indices'].shape==(10000,256)
                assert array_hash(inp['noisy'][:5000],inp['noise'][:5000],inp['timesteps'][:5000])==r['training_prefix_5000_sha256']
                c=schedule();ts=inp['timesteps'];reference=(c['sqrt_abar'][ts,None]*inp['train'][inp['indices']]+c['sqrt_one_minus'][ts,None]*inp['noise']).astype(np.float32)
                assert np.array_equal(reference,inp['noisy'])
        cfg=json.loads(Path(r['config']).read_text());assert cfg['source_hashes']==freeze['source_hashes']
        assert r['source_revision']==freeze['source_revision']
        if r['schedule']=='cosine':assert r['updates']==r['trajectory_terminal_updates']
        trace=[json.loads(line) for line in Path(r['training_trace']).read_text().splitlines()]
        assert any(z['step']==r['updates'] for z in trace)
        checks.append(dict(dataset=r['dataset'],seed=r['seed'],updates=r['updates'],schedule=r['schedule'],passed=True))
    summary=json.loads((Path(a.analysis)/'summary.json').read_text());stat_checks=[]
    for group in ('conditions','contrasts','absolute_sw1'):
        for c in summary[group]:
            dataset=c['dataset'];variant=c['variant']
            def val(seed,u,pol):
                score=metric_by[dataset,seed,u,pol,variant]
                if group=='conditions' or (group=='contrasts' and c['target']=='delta_vs_raw'):
                    score-=metric_by[dataset,seed,u,pol,'raw']
                return score
            values=[]
            for seed in c['seeds']:
                if group!='contrasts':v=val(seed,c['updates'],c['schedule'])
                elif c['contrast'].startswith('schedule_at_'):
                    u=int(c['contrast'].split('_')[-1]);v=val(seed,u,'cosine')-val(seed,u,'constant')
                elif c['contrast'].startswith('duration_'):
                    policy=c['contrast'].split('_')[-1];v=val(seed,10000,policy)-val(seed,5000,policy)
                else:v=val(seed,10000,'cosine')-val(seed,10000,'constant')-val(seed,5000,'cosine')+val(seed,5000,'constant')
                values.append(v)
            x=np.array(values);assert len(x)==4 and np.allclose(x,c['values'],rtol=0,atol=1e-12)
            mean=float(x.mean());half=3.182446305284263*float(np.std(x,ddof=1))/2
            assert abs(mean-c['mean'])<1e-12 and np.allclose([mean-half,mean+half],c['ci95'],rtol=0,atol=1e-12)
            signs=np.array(list(itertools.product([-1,1],repeat=4)))
            pvalue=float((np.abs((signs*x).mean(axis=1))>=abs(mean)-1e-12).mean())
            assert pvalue==c['exact_signflip_p']
            stat_checks.append(dict(group=group,dataset=dataset,variant=variant,passed=True))
    result=dict(status='passed',cells=len(checks),matched_seed_inputs=len(seen_inputs),checks=checks,
                summary_statistics_checked=len(stat_checks),max_sw1_absolute_disagreement=max_error,
                method='Independent vectorized float64 projection/sort, squared-distance coverage, literal df=3 critical value and sign enumeration',
                limitation='Shared raw evidence and model definitions; computational audit, not independent scientific peer review')
    json_write(a.out,result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
