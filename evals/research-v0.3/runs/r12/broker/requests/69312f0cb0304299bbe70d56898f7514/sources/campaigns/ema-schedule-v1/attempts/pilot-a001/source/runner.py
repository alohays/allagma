"""AI-generated adaptation of supplied reference runner; all work via broker.

Training/sample mechanism preserved; orchestration, policy crossing and artifact
retention added. License: ../LICENSE-AI-Scientist.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
from common import ROOT,CAMP,read,write,sha,ref,now,start_attempt,array_hash,source_revision

def imports():
    global np,torch,Denoiser,dataset,draw,schedule,sliced_wasserstein,mode_coverage
    import numpy as np
    import torch
    from reference import Denoiser,dataset,draw,schedule,sliced_wasserstein,mode_coverage
    torch.set_num_threads(1)

def sync(device):
    if device=='mps': torch.mps.synchronize()

def make_inputs(name,seed):
    torch.manual_seed(seed)
    initial=Denoiser()
    state={k:v.detach().numpy().copy() for k,v in initial.state_dict().items()}
    train=dataset(name,100000,seed+1000000)
    heldout=dataset(name,2048,seed+2000000)
    rng=np.random.default_rng(seed+100000)
    indices=rng.integers(0,len(train),(10000,256))
    noise=rng.normal(size=(10000,256,2)).astype(np.float32)
    timesteps=rng.integers(0,100,(10000,256))
    generation_noise=np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32)
    return initial,state,dict(train=train,heldout=heldout,indices=indices,noise=noise,timesteps=timesteps,generation_noise=generation_noise)

def input_hashes(state,a):
    prefix=hashlib.sha256()
    for x in [a['indices'][:5000],a['noise'][:5000],a['timesteps'][:5000],a['train'][a['indices'][:5000]]]: prefix.update(np.ascontiguousarray(x).tobytes())
    return {'initial_weights_sha256':array_hash(np.concatenate([state[k].ravel() for k in sorted(state)])),
            'training_prefix_5000_sha256':prefix.hexdigest(),'heldout_sha256':array_hash(a['heldout']),
            'generation_noise_sha256':array_hash(a['generation_noise'])}

def lr_at(step,policy,horizon):
    return 3e-4 if policy=='constant' else 3e-4*.5*(1+np.cos(np.pi*(step-1)/horizon))

def train_model(initial,a,device,policy,horizon,steps,dest=None,evaluate_steps=()):
    model=copy.deepcopy(initial).to(device)
    emas={k:copy.deepcopy(model).requires_grad_(False) for k in ['ema099','ema0999']}
    parameters=list(model.parameters())
    cnp=schedule(); c={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in cnp.items()}
    noisy_np=(cnp['sqrt_abar'][a['timesteps'],None]*a['train'][a['indices']]+cnp['sqrt_one_minus'][a['timesteps'],None]*a['noise']).astype(np.float32)
    noisy=torch.tensor(noisy_np,device=device); noise=torch.tensor(a['noise'],device=device)
    ts=torch.tensor(a['timesteps'],dtype=torch.float32,device=device)
    opt=torch.optim.AdamW(parameters,lr=3e-4,weight_decay=.01,foreach=True)
    trace=[]; cells=[]; times=[]
    sync(device); begin=time.monotonic(); eval_seconds=0
    for step in range(1,steps+1):
        opt.zero_grad(set_to_none=True)
        loss=torch.nn.functional.mse_loss(model(noisy[step-1],ts[step-1]),noise[step-1])
        loss.backward()
        norm=torch.nn.utils.clip_grad_norm_(parameters,.5,foreach=False)
        opt.param_groups[0]['lr']=lr_at(step,policy,horizon); opt.step()
        with torch.no_grad():
            for name,decay in [('ema099',.99),('ema0999',.999)]:
                torch._foreach_lerp_(list(emas[name].parameters()),parameters,1-decay)
        if step==1 or step%250==0 or step==steps:
            val=float(loss.detach().cpu()); assert np.isfinite(val)
            row={'step':step,'noise_mse':val,'lr':float(opt.param_groups[0]['lr']),'preclip_gradient_norm':float(norm.detach().cpu()),'elapsed_seconds':time.monotonic()-begin}
            trace.append(row)
            if dest:
                with (dest/'trace.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
            if step==1 or step%1000==0: print(json.dumps(row),flush=True)
        if step in evaluate_steps:
            sync(device); tick=time.monotonic()
            out=dest/f'step-{step}'; out.mkdir()
            weights={f'{k}__{n}':v.detach().cpu().numpy().copy() for k,m in {'raw':model,**emas}.items() for n,v in m.state_dict().items()}
            assert all(np.isfinite(v).all() and v.dtype==np.float32 for v in weights.values())
            np.savez(out/'weights.npz',**weights)
            arrays={'heldout':a['heldout'],'generation_noise':a['generation_noise']}
            evnoise=torch.tensor(a['generation_noise'],device=device)
            for k,m in {'raw':model,**emas}.items():
                arrays[k]=draw(m,evnoise,c); assert np.isfinite(arrays[k]).all()
            np.savez(out/'arrays.npz',**arrays)
            sync(device); eval_seconds+=time.monotonic()-tick
            cells.append({'updates':step,'weights':str((out/'weights.npz').relative_to(ROOT)),'arrays':str((out/'arrays.npz').relative_to(ROOT))})
    sync(device)
    return model,emas,trace,cells,{'training_seconds':time.monotonic()-begin-eval_seconds,'sampling_and_save_seconds':eval_seconds,'updates':steps}

def metrics(a):
    out={}
    for k in ['raw','ema099','ema0999']:
        v={'sw1':sliced_wasserstein(a[k],a['heldout'])}
        m=mode_coverage(a[k]); v.update(mode_counts=m['counts'],covered_modes=m['covered'],inlier_fraction=m['inlier_fraction'],inlier_count=sum(m['counts']))
        out[k]=v
    return out

def controls(dest):
    rng=np.random.default_rng(71)
    x=rng.normal(size=(128,2))
    from reference import projections,mixture_centers
    checks={}
    checks['sw1_identity']=sliced_wasserstein(x,x)==0
    checks['sw1_permutation']=sliced_wasserstein(x,x[::-1])==0
    z=np.zeros((128,2)); delta=np.array([1.,-.75])
    expected=float(np.abs(projections()@delta).mean())
    checks['sw1_translation']=abs(sliced_wasserstein(z,z+delta)-expected)<1e-12
    checkx=np.full((2048,2),100.)
    checkx[:20]=mixture_centers()[0]; checkx[20:41]=mixture_centers()[1]
    cm=mode_coverage(checkx)
    checks['coverage_all_draws_threshold']=cm['covered']==1 and cm['counts'][:2]==[20,21] and cm['inlier_fraction']==41/2048
    checkx=np.array([[2.45,0.],[2.4500001,0.]])
    checks['coverage_radius']=mode_coverage(checkx)['counts'][0]==1
    checks['lr_horizons']=lr_at(1,'cosine',5000)==3e-4 and lr_at(5000,'cosine',5000)<1e-10 and lr_at(5000,'cosine',10000)>1e-4 and lr_at(10000,'cosine',10000)<1e-10
    torch.manual_seed(71); m=Denoiser(); em=copy.deepcopy(m)
    checks['parameter_count']=sum(p.numel() for p in m.parameters())==296450
    checks['ema_initial_copy']=all(torch.equal(a,b) for a,b in zip(m.parameters(),em.parameters()))
    with torch.no_grad():
        expected_params=[p.clone()+.01 for p in m.parameters()]
        for p in m.parameters(): p.add_(1.)
        torch._foreach_lerp_(list(em.parameters()),list(m.parameters()),.01)
    checks['ema_recurrence']=all(torch.allclose(a,b,rtol=1e-6,atol=1e-7) for a,b in zip(em.parameters(),expected_params))
    checks['float32_buffers']=all(v.dtype==torch.float32 for v in m.state_dict().values()) and 'time.frequencies' in m.state_dict()
    write(dest/'controls.json',{'checks':checks,'translation_expected':expected,'coverage_example':cm,'passed':all(checks.values())})
    assert all(checks.values()),checks

def pilot(args,dest):
    controls(dest)
    results=[]
    for name,seed in [('moons',71),('gmm8',81)]:
        initial,state,a=make_inputs(name,seed)
        np.savez(dest/f'{name}-initial.npz',**state)
        np.savez(dest/f'{name}-inputs.npz',**a)
        for device in ['mps','cpu']:
            if device=='mps' and not torch.backends.mps.is_available(): continue
            out=dest/f'{name}-{device}'; out.mkdir()
            model,emas,tr,_,timing=train_model(initial,a,device,'cosine',5000,args.steps,out,(args.steps,))
            # Load saved raw state and independently regenerate all 2048 samples.
            weights=np.load(out/f'step-{args.steps}'/'weights.npz',allow_pickle=False)
            restored=Denoiser().to(device)
            restored.load_state_dict({k.removeprefix('raw__'):torch.tensor(weights[k],device=device) for k in weights.files if k.startswith('raw__')})
            c={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in schedule().items()}
            regenerated=draw(restored,torch.tensor(a['generation_noise'],device=device),c)
            retained=np.load(out/f'step-{args.steps}'/'arrays.npz',allow_pickle=False)['raw']
            max_error=float(np.max(np.abs(regenerated-retained)))
            assert np.allclose(regenerated,retained,rtol=1e-5,atol=1e-6)
            # Repeat two updates from exact same initial state; no quality-based selection.
            r1=train_model(initial,a,device,'cosine',5000,2)[0]
            r2=train_model(initial,a,device,'cosine',5000,2)[0]
            max_train_error=max(float((v-r2.state_dict()[k]).abs().max().cpu()) for k,v in r1.state_dict().items())
            assert max_train_error<=1e-6
            results.append({'dataset':name,'seed':seed,'device':device,**timing,'seconds_per_update':timing['training_seconds']/args.steps,
                'seconds_per_state':timing['sampling_and_save_seconds']/3,'regeneration_max_abs_error':max_error,'short_repeat_max_abs_error':max_train_error,
                **input_hashes(state,a)})
    write(dest/'pilot.json',{'phase':'pilot','results':results,'passed':True})
    print(json.dumps(results),flush=True)

def train(args,dest):
    freeze=read(CAMP/'confirmation-freeze.json')
    assert sha(CAMP/'protocol.json')==freeze['protocol_sha256']
    for f,h in freeze['source_hashes'].items(): assert sha(ROOT/f)==h,f
    assert args.seed in read(CAMP/'protocol.json')['seeds']['confirmation'][args.dataset]
    device=freeze['device']; initial,state,a=make_inputs(args.dataset,args.seed)
    shared=CAMP/'inputs'/f'{args.dataset}-{args.seed}'
    if not shared.exists():
        shared.mkdir(parents=True)
        np.savez(shared/'initial.npz',**state); np.savez(shared/'inputs.npz',**a)
        write(shared/'hashes.json',input_hashes(state,a))
    else:
        stored=np.load(shared/'inputs.npz',allow_pickle=False)
        assert all(np.array_equal(a[k],stored[k]) for k in a)
        assert input_hashes(state,a)==read(shared/'hashes.json')
    checkpoints=[5000,10000] if args.policy=='constant' else [args.horizon]
    _,_,tr,cells,timing=train_model(initial,a,device,args.policy,args.horizon,args.horizon,dest,checkpoints)
    for cell in cells:
        cell.update(dataset=args.dataset,seed=args.seed,schedule=args.policy,phase='confirmation',device=device,
          **input_hashes(state,a), source_revision=freeze['runner_revision'],attempt_id=args.attempt,
          training_trace=str((dest/'trace.jsonl').relative_to(ROOT)),inputs=str((shared/'inputs.npz').relative_to(ROOT)),initial_weights=str((shared/'initial.npz').relative_to(ROOT)))
        arrays=np.load(ROOT/cell['arrays'],allow_pickle=False); cell['metrics']=metrics(arrays)
        if args.dataset=='moons':
            cell['metrics']={k:{'sw1':v['sw1']} for k,v in cell['metrics'].items()}
    write(dest/'result.json',{'runs':cells,'timing':timing,'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,'device':device,'dtype':'float32'}})

def main():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['pilot','train']); p.add_argument('--attempt',required=True)
    p.add_argument('--steps',type=int,default=500); p.add_argument('--dataset',choices=['moons','gmm8']); p.add_argument('--seed',type=int)
    p.add_argument('--policy',choices=['constant','cosine']); p.add_argument('--horizon',type=int,choices=[5000,10000])
    args=p.parse_args(); begin=time.monotonic(); dest=start_attempt(args.attempt,vars(args))
    try:
        imports()
        (pilot if args.mode=='pilot' else train)(args,dest)
        write(dest/'finished.json',{'status':'succeeded','ended_at':now(),'wall_seconds':time.monotonic()-begin})
    except BaseException as e:
        write(dest/'finished.json',{'status':'failed','ended_at':now(),'wall_seconds':time.monotonic()-begin,'error':repr(e)})
        raise

if __name__=='__main__': main()
