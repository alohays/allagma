"""Independent numerical audit of retained arrays, provenance and saved weights.

AI-generated checker; deterministic assurance, not independent peer review.
All computation is run through the local broker.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
from common import ROOT,CAMP,BUNDLE,read,write,sha,ref,array_hash
os.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO']='0.1'
import numpy as np
import torch
torch.set_num_threads(1)
from reference import Denoiser,draw,schedule

def independent_sw1(x,y):
    angles=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    dirs=np.stack([np.cos(angles),np.sin(angles)])
    px=np.sort(np.asarray(x,np.float64)@dirs,axis=0)
    py=np.sort(np.asarray(y,np.float64)@dirs,axis=0)
    return float(np.abs(px-py).mean())

def independent_modes(x):
    theta=np.arange(8)*2*np.pi/8
    centers=2*np.stack([np.cos(theta),np.sin(theta)],axis=1)
    distances=np.sqrt(((np.asarray(x,np.float64)[:,None,:]-centers[None,:,:])**2).sum(axis=2))
    nearest=distances.argmin(axis=1); valid=distances[np.arange(len(x)),nearest]<=.45
    counts=[int(np.sum(valid & (nearest==i))) for i in range(8)]
    return counts,sum(c>=21 for c in counts),float(valid.mean())

def main():
    p=argparse.ArgumentParser();p.add_argument('--measurements',default='analysis/measurements.json');p.add_argument('--output',default='evidence/verification.json');p.add_argument('--regenerate',action='store_true')
    args=p.parse_args();begin=time.monotonic();runs=read(ROOT/args.measurements)['runs']
    expected={(d,s,T,P) for d,seeds in [('moons',range(4001,4005)),('gmm8',range(5001,5005))] for s in seeds for T in [5000,10000] for P in ['constant','cosine']}
    observed={(r['dataset'],r['seed'],r['updates'],r['schedule']) for r in runs}
    assert observed<=expected and len(observed)==len(runs)
    results=[];groups={};cached={};sources=read(CAMP/'confirmation-freeze.json')
    assert sha(CAMP/'protocol.json')==sources['protocol_sha256']
    for f,h in sources['source_hashes'].items():assert sha(ROOT/f)==h,f
    for r in runs:
        key=(r['dataset'],r['seed']);groups.setdefault(key,[]).append(r)
        if key not in cached:
            inp=np.load(ROOT/r['inputs'],allow_pickle=False); initial=np.load(ROOT/r['initial_weights'],allow_pickle=False)
            assert inp['train'].shape==(100000,2)
            assert inp['indices'].shape==(10000,256) and inp['noise'].shape==(10000,256,2) and inp['timesteps'].shape==(10000,256)
            pref=hashlib.sha256()
            for x in [inp['indices'][:5000],inp['noise'][:5000],inp['timesteps'][:5000],inp['train'][inp['indices'][:5000]]]:pref.update(np.ascontiguousarray(x).tobytes())
            cached[key]={'input':inp,'initial':initial,'initial_hash':array_hash(np.concatenate([initial[k].ravel() for k in sorted(initial.files)])),'prefix_hash':pref.hexdigest()}
        c=cached[key];assert r['initial_weights_sha256']==c['initial_hash'];assert r['training_prefix_5000_sha256']==c['prefix_hash']
        a=np.load(ROOT/r['arrays'],allow_pickle=False);w=np.load(ROOT/r['weights'],allow_pickle=False)
        assert np.array_equal(a['heldout'],c['input']['heldout']) and np.array_equal(a['generation_noise'],c['input']['generation_noise'])
        assert array_hash(a['heldout'])==r['heldout_sha256'] and array_hash(a['generation_noise'])==r['generation_noise_sha256']
        assert a['heldout'].shape==(2048,2) and a['generation_noise'].shape==(100,2048,2)
        trace=[json.loads(line) for line in (ROOT/r['training_trace']).read_text().splitlines()]
        endpoint=next(t for t in trace if t['step']==r['updates'])
        expect_lr=3e-4 if r['schedule']=='constant' else 3e-4*(1+np.cos(np.pi*(r['updates']-1)/r['updates']))/2
        assert abs(endpoint['lr']-expect_lr)<1e-15
        assert len(trace)>=r['updates']//250
        schema=Denoiser().state_dict();assert set(w.files)=={f'{v}__{k}' for v in ['raw','ema099','ema0999'] for k in schema}
        result={k:r[k] for k in ['dataset','seed','updates','schedule','device']};result['variants']={}
        for variant in ['raw','ema099','ema0999']:
            sample=a[variant];assert sample.shape==(2048,2) and np.isfinite(sample).all()
            metric=independent_sw1(sample,a['heldout']);err=abs(metric-r['metrics'][variant]['sw1']);assert err<1e-12
            for k,v in schema.items():
                value=w[f'{variant}__{k}'];assert value.shape==tuple(v.shape) and value.dtype==np.float32 and np.isfinite(value).all()
                if k.endswith('frequencies'):assert np.array_equal(value,c['initial'][k])
            row={'independent_sw1':metric,'metric_abs_error':err,'state_keys':len(schema)}
            if r['dataset']=='gmm8':
                counts,covered,frac=independent_modes(sample);m=r['metrics'][variant]
                assert counts==m['mode_counts'] and covered==m['covered_modes'] and frac==m['inlier_fraction']
                row['independent_coverage']={'mode_counts':counts,'covered_modes':covered,'inlier_fraction':frac}
            if args.regenerate:
                model=Denoiser().to(r['device']);model.load_state_dict({k:torch.tensor(w[f'{variant}__{k}'],device=r['device']) for k in schema})
                coeffs={k:torch.tensor(v,dtype=torch.float32,device=r['device']) for k,v in schedule().items()}
                regenerated=draw(model,torch.tensor(a['generation_noise'],device=r['device']),coeffs)
                diff=float(np.max(np.abs(regenerated-sample)));assert np.allclose(regenerated,sample,rtol=1e-5,atol=1e-6)
                row.update(regeneration_max_abs_error=diff,regenerated_sha256=array_hash(regenerated),retained_sha256=array_hash(sample),bitwise_equal=bool(np.array_equal(regenerated,sample)))
            result['variants'][variant]=row
        results.append(result)
    for key,rr in groups.items():
        for h in ['initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256']:
            assert len({r[h] for r in rr})==1,(key,h)
        constants=[r for r in rr if r['schedule']=='constant']
        if len(constants)==2:assert constants[0]['attempt_id']==constants[1]['attempt_id']
        cosines=[r for r in rr if r['schedule']=='cosine']
        if len(cosines)==2:assert cosines[0]['attempt_id']!=cosines[1]['attempt_id']
    env={'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'torch':torch.__version__,'numpy':np.__version__,'torch_threads':torch.get_num_threads(),
         'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},'mps_available':torch.backends.mps.is_available()}
    result={'status':'pass','complete_cells':len(runs),'expected_cells':32,'missing_cells':[list(k) for k in sorted(expected-observed)],'regenerated_states':len(runs)*3 if args.regenerate else 0,
            'coverage':'Independent vectorized SW1 and coverage calculation, array/input hashes, matched prefixes, state schema including buffers, LR endpoints, every saved state resampled when requested. No full retraining in this check.',
            'checks':results,'environment':env,'wall_seconds':time.monotonic()-begin,'source':ref(Path(__file__)),'measurements':ref(ROOT/args.measurements)}
    write(ROOT/args.output,result)
    print(json.dumps({k:result[k] for k in ['status','complete_cells','expected_cells','regenerated_states','wall_seconds']}))

if __name__=='__main__':main()
