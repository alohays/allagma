"""AI-generated runner adapting the supplied licensed reference mechanism.

All execution must go through the common local broker. The scientific model,
sampling equations and metric definitions are unchanged in science.py.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
from common import ROOT, CAMPAIGN, now, write, ref, sha, named_hash, array_hash, sources

def lr_at(policy, duration, step):
    import math
    return 3e-4 if policy == 'constant' else 3e-4*.5*(1+math.cos(math.pi*(step-1)/duration))

def libraries():
    global np, torch, Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage
    import numpy as np
    import torch
    from science import Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage
    torch.set_num_threads(1)

def synchronize(device):
    if device == 'mps':
        torch.mps.synchronize()

def cpu_state(model):
    return {k:v.detach().cpu().numpy().copy() for k,v in model.state_dict().items()}

def load_state(model, arrays, prefix=''):
    model.load_state_dict({k:torch.from_numpy(arrays[prefix+k].copy()) for k in model.state_dict()})

def seed_inputs(dataset_name, seed, phase, base):
    folder = base/phase/f'{dataset_name}-{seed}'/'inputs'
    metadata = folder/'metadata.json'
    if metadata.exists():
        meta = json.loads(metadata.read_text())
        for name, digest in meta['file_hashes'].items():
            if sha(folder/name) != digest:
                raise RuntimeError('Existing input digest mismatch: '+name)
        return folder, meta
    folder.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    initial = cpu_state(Denoiser())
    train = dataset(dataset_name, 100000, seed+1000000)
    heldout = dataset(dataset_name, 2048, seed+2000000)
    rng = np.random.default_rng(seed+100000)
    # Match the supplied generator ordering and integer draws before compact cast.
    indices = rng.integers(0, len(train), (10000,256)).astype(np.int32)
    noise = rng.normal(size=(10000,256,2)).astype(np.float32)
    timesteps = rng.integers(0,100,(10000,256)).astype(np.int16)
    coeff = schedule()
    noisy = (coeff['sqrt_abar'][timesteps,None]*train[indices]
             +coeff['sqrt_one_minus'][timesteps,None]*noise).astype(np.float32)
    gen = np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32)
    np.savez(folder/'initial.npz', **initial)
    np.savez(folder/'training.npz', train=train, indices=indices, noise=noise, timesteps=timesteps, noisy=noisy)
    np.savez(folder/'evaluation.npz', heldout=heldout, generation_noise=gen)
    meta = {'dataset':dataset_name,'seed':seed,'phase':phase,
        'initial_weights_sha256':named_hash(initial),
        'training_prefix_5000_sha256':named_hash({'train':train,'indices':indices[:5000],
            'noise':noise[:5000],'timesteps':timesteps[:5000],'noisy':noisy[:5000]}),
        'heldout_sha256':array_hash(heldout), 'generation_noise_sha256':array_hash(gen),
        'file_hashes':{name:sha(folder/name) for name in ('initial.npz','training.npz','evaluation.npz')},
        'hash_convention':'array_hash=SHA256(C-order bytes); named_hash=sorted name,dtype,shape JSON newline then C-order bytes',
        'created_at':now()}
    write(metadata,meta)
    return folder,meta

def models_optimizer(folder, device):
    initial = np.load(folder/'initial.npz', allow_pickle=False)
    model = Denoiser().to(device)
    load_state(model,initial)
    models = {'raw':model,'ema099':copy.deepcopy(model),'ema0999':copy.deepcopy(model)}
    for key in ('ema099','ema0999'):
        models[key].requires_grad_(False)
    opt = torch.optim.AdamW(list(model.parameters()),lr=3e-4,weight_decay=.01,foreach=True)
    return models,opt

def checkpoint(path,models,opt,step):
    arrays = {f'{name}__{key}':a for name,m in models.items() for key,a in cpu_state(m).items()}
    arrays['completed_updates'] = np.array(step,dtype=np.int64)
    for i,p in enumerate(models['raw'].parameters()):
        for key,value in opt.state[p].items():
            arrays[f'optimizer__{i}__{key}'] = value.detach().cpu().numpy().copy()
    temporary = path.with_name(path.stem+'.tmp.npz')
    np.savez(temporary,**arrays)
    temporary.replace(path)

def restore(path,models,opt,device):
    with np.load(path,allow_pickle=False) as arrays:
        for name,m in models.items():
            load_state(m,arrays,name+'__')
        for i,p in enumerate(models['raw'].parameters()):
            for key in ('step','exp_avg','exp_avg_sq'):
                a = arrays[f'optimizer__{i}__{key}']
                opt.state[p][key] = torch.tensor(a.copy(),device='cpu' if key=='step' else device)
        return int(arrays['completed_updates'])

def training_tensors(folder,device):
    with np.load(folder/'training.npz',allow_pickle=False) as data:
        return {key:torch.tensor(data[key],dtype=torch.float32,device=device) for key in ('noisy','noise','timesteps')}

def update(models,opt,tensors,index,policy,duration):
    model=models['raw']
    parameters=list(model.parameters())
    opt.zero_grad(set_to_none=True)
    loss=torch.nn.functional.mse_loss(model(tensors['noisy'][index],tensors['timesteps'][index]),tensors['noise'][index])
    loss.backward()
    norm=torch.nn.utils.clip_grad_norm_(parameters,.5,foreach=False)
    opt.param_groups[0]['lr']=lr_at(policy,duration,index+1)
    opt.step()
    with torch.no_grad():
        for name,decay in (('ema099',.99),('ema0999',.999)):
            torch._foreach_lerp_(list(models[name].parameters()),parameters,1-decay)
    return loss,norm

def evaluate(models,folder,device,out,step,cfg,meta,source_revision):
    start=time.monotonic()
    with np.load(folder/'evaluation.npz',allow_pickle=False) as data:
        arrays={k:data[k].copy() for k in data.files}
    noise=torch.tensor(arrays['generation_noise'],device=device)
    coeff={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in schedule().items()}
    metrics={}
    weights={}
    for name,model in models.items():
        model.eval()
        for key,value in cpu_state(model).items():
            weights[name+'__'+key]=value
        arrays[name]=draw(model,noise,coeff)
        if not np.isfinite(arrays[name]).all():
            raise RuntimeError('Nonfinite samples')
        metrics[name]={'sw1':sliced_wasserstein(arrays[name],arrays['heldout'])}
        if cfg['dataset']=='gmm8':
            m=mode_coverage(arrays[name])
            metrics[name].update(mode_counts=m['counts'],covered_modes=m['covered'],
                                 inlier_count=sum(m['counts']),inlier_fraction=m['inlier_fraction'])
    np.savez(out/f'step-{step}-arrays.npz',**arrays)
    np.savez(out/f'step-{step}-weights.npz',**weights)
    cell={k:cfg[k] for k in ('dataset','seed','phase','device')}
    cell.update(updates=step,schedule=cfg['policy'],arrays=str((out/f'step-{step}-arrays.npz').relative_to(ROOT)),
        weights=str((out/f'step-{step}-weights.npz').relative_to(ROOT)),metrics=metrics,
        source_revision=source_revision,attempt_id=cfg['attempt_id'],
        training_trace=str((out/'trace.jsonl').relative_to(ROOT)),
        input_metadata=str((folder/'metadata.json').relative_to(ROOT)),
        actual_schedule_duration=cfg['duration'],
        **{k:meta[k] for k in ('initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256')})
    write(out/f'step-{step}-measurement.json',cell)
    synchronize(device)
    return cell,time.monotonic()-start

def run(cfg):
    begin=time.monotonic()
    base=ROOT/cfg.get('base','artifacts')
    out=base/cfg['phase']/f"{cfg['dataset']}-{cfg['seed']}"/f"{cfg['policy']}-{cfg['duration']}"/'attempts'/cfg['attempt_id']
    out.mkdir(parents=True,exist_ok=False)
    write(out/'input.json',cfg)
    source_map=sources()
    source_revision=__import__('hashlib').sha256(json.dumps(source_map,sort_keys=True).encode()).hexdigest()
    (out/'source').mkdir()
    for file in (ROOT/'study').glob('*.py'):
        shutil.copyfile(file,out/'source'/file.name)
    started={'attempt_id':cfg['attempt_id'],'started_at':now(),'status':'running',
             'command':[sys.executable,*sys.argv], 'inputs':cfg, 'source_hashes':source_map,
             'source_revision':source_revision,'protocol':ref(ROOT/'PROTOCOL.md')}
    write(out/'started.json',started)
    libraries()
    device=cfg['device']
    if device=='mps' and not torch.backends.mps.is_available():
        raise RuntimeError('Requested MPS unavailable; no implicit fallback')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='1':
        raise RuntimeError('Implicit backend fallback forbidden')
    if cfg['phase']=='confirmation':
        freeze=json.loads((CAMPAIGN/'confirmation-freeze.json').read_text())
        if sha(ROOT/'PROTOCOL.md')!=freeze['protocol']['sha256']:
            raise RuntimeError('Frozen protocol changed')
        for path,digest in freeze['scientific_sources'].items():
            if sha(ROOT/path)!=digest:
                raise RuntimeError('Frozen scientific source changed: '+path)
    folder,meta=seed_inputs(cfg['dataset'],cfg['seed'],cfg['phase'],base)
    models,opt=models_optimizer(folder,device)
    tensors=training_tensors(folder,device)
    step0=0
    if cfg.get('resume'):
        step0=restore(ROOT/cfg['resume'],models,opt,device)
    target=cfg.get('stop') or cfg['duration']
    synchronize(device)
    training_start=time.monotonic()
    evaluation_seconds=0.
    cells=[]
    for step in range(step0+1,target+1):
        loss,norm=update(models,opt,tensors,step-1,cfg['policy'],cfg['duration'])
        if step==1 or step%500==0 or step==target:
            value=float(loss.detach().cpu())
            if not np.isfinite(value):
                raise RuntimeError('Nonfinite training loss')
            trace={'step':step,'noise_mse':value,'gradient_norm_before_clip':float(norm.cpu()),
                   'lr':lr_at(cfg['policy'],cfg['duration'],step),'elapsed_seconds':time.monotonic()-begin}
            with (out/'trace.jsonl').open('a') as f:
                f.write(json.dumps(trace)+'\n')
            print(json.dumps(trace),flush=True)
        if step%1000==0 or step==target:
            checkpoint(out/'recovery.npz',models,opt,step)
            write(out/'recovery.json',{'step':step,'state':ref(out/'recovery.npz'),'input':ref(out/'input.json')})
        if (cfg['phase']=='confirmation' and ((cfg['policy']=='constant' and step in (5000,10000)) or
                 (cfg['policy']=='cosine' and step==cfg['duration']))) or (cfg['phase']=='pilot' and step==target):
            cell,seconds=evaluate(models,folder,device,out,step,cfg,meta,source_revision)
            cells.append(cell)
            evaluation_seconds+=seconds
    synchronize(device)
    result={**started,'status':'succeeded','ended_at':now(), 'completed_updates':target,
            'resumed_from_step':step0,'measurements':[str((out/f"step-{c['updates']}-measurement.json").relative_to(ROOT)) for c in cells],
            'timing':{'training_seconds':time.monotonic()-training_start-evaluation_seconds,
                      'evaluation_seconds':evaluation_seconds,'total_seconds':time.monotonic()-begin},
            'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,
                           'device':device,'dtype':'float32','threads':torch.get_num_threads()},
            'outputs':[ref(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('started.json','result.json')]}
    write(out/'result.json',result)
    print(json.dumps({'completed':cfg['attempt_id'],'timing':result['timing']}),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',choices=['moons','gmm8'],required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--phase',choices=['pilot','confirmation'],required=True)
    p.add_argument('--policy',choices=['constant','cosine'],required=True)
    p.add_argument('--duration',type=int,choices=[5000,10000],required=True)
    p.add_argument('--stop',type=int)
    p.add_argument('--device',choices=['mps','cpu'],default='mps')
    p.add_argument('--attempt-id',required=True)
    p.add_argument('--resume')
    p.add_argument('--base',default='artifacts')
    run(vars(p.parse_args()))

if __name__=='__main__':
    main()
