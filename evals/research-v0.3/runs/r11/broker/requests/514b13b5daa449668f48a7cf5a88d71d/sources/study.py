"""AI-generated follow-up runner; mechanism adapted under LICENSE.

All executable uses, including diagnostics, must be submitted to inputs/compute.py.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, os, platform, time
from pathlib import Path
os.environ.setdefault('PYTORCH_MPS_LOW_WATERMARK_RATIO','0.1')
import numpy as np
import torch
from science import Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage

VARIANTS = ('raw', 'ema099', 'ema0999')
SOURCE_FILES = ('science.py', 'study.py', 'qualify.py', 'analyze.py', 'protocol.json')

def json_write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
    tmp.replace(path)

def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()

def array_hash(*arrays):
    h = hashlib.sha256()
    for a in arrays: h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()

def state_arrays(model):
    return {k:v.detach().cpu().numpy().copy() for k,v in model.state_dict().items()}

def state_hash(state):
    return array_hash(*(state[k] for k in sorted(state)))

def source_hashes():
    return {p:file_hash(p) for p in SOURCE_FILES}

def load_state(model, arrays, prefix=''):
    state = {k:torch.from_numpy(np.array(arrays[prefix+k], copy=True)) for k in model.state_dict()}
    model.load_state_dict(state, strict=True)

def sync(device):
    if device == 'mps': torch.mps.synchronize()

def learning_rate(step, total, policy):
    return 3e-4 if policy == 'constant' else 3e-4*.5*(1+math.cos(math.pi*(step-1)/(total-1)))

def prepare_inputs(root, phase, name, seed):
    directory = root/'inputs-retained'/phase/f'{name}-{seed}'
    meta_path = directory/'provenance.json'
    if meta_path.exists(): return json.loads(meta_path.read_text())
    directory.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    initial = state_arrays(Denoiser())
    np.savez(directory/'initial.npz', **initial)
    train = dataset(name, 100000, seed+1000000)
    heldout = dataset(name, 2048, seed+2000000)
    rng = np.random.default_rng(seed+100000)
    # Draw with the reference int64 RNG call before lossless storage conversion.
    indices = rng.integers(0, len(train), (10000,256)).astype(np.int32)
    noise = rng.normal(size=(10000,256,2)).astype(np.float32)
    timesteps = rng.integers(0,100,(10000,256)).astype(np.int16)
    coeff = schedule()
    noisy = (coeff['sqrt_abar'][timesteps,None]*train[indices]+
             coeff['sqrt_one_minus'][timesteps,None]*noise).astype(np.float32)
    generation_noise = np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32)
    independent_heldout = dataset(name,2048,seed+4000000)
    np.savez(directory/'training.npz', train=train, indices=indices, noise=noise,
             timesteps=timesteps, noisy=noisy)
    np.savez(directory/'evaluation.npz', heldout=heldout, generation_noise=generation_noise,
             independent_heldout=independent_heldout)
    info = dict(dataset=name, seed=seed, phase=phase, directory=str(directory),
                initial_weights_sha256=state_hash(initial),
                training_prefix_5000_sha256=array_hash(noisy[:5000],noise[:5000],timesteps[:5000]),
                training_prefix_definition='SHA256(noisy[:5000] float32 bytes || noise[:5000] float32 bytes || timesteps[:5000] int16 bytes), C order',
                heldout_sha256=array_hash(heldout), generation_noise_sha256=array_hash(generation_noise),
                files={p:file_hash(directory/p) for p in ('initial.npz','training.npz','evaluation.npz')})
    json_write(meta_path, info)
    return info

def metrics(name, sample, heldout):
    m = dict(sw1=sliced_wasserstein(sample,heldout))
    if name == 'gmm8':
        c = mode_coverage(sample)
        m.update(mode_counts=c['counts'], covered_modes=c['covered'],
                 inlier_count=sum(c['counts']), inlier_fraction=c['inlier_fraction'])
    return m

def save_resume(path, models, optimizer, step, cfg):
    sync(cfg['device'])
    payload = dict(step=step, config=cfg, models={k:m.state_dict() for k,m in models.items()},
                   optimizer=optimizer.state_dict())
    temporary = path.with_suffix('.tmp')
    torch.save(payload, temporary)
    temporary.replace(path)

def execute(args):
    start=time.monotonic(); root=Path(args.root)
    torch.set_num_threads(1)
    if args.device == 'mps' and not torch.backends.mps.is_available(): raise RuntimeError('MPS unavailable')
    if os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK') == '1': raise RuntimeError('Implicit fallback forbidden')
    source=source_hashes()
    if args.phase == 'confirmation':
        freeze=json.loads(Path('freeze.json').read_text())
        if source != freeze['source_hashes']: raise RuntimeError('Frozen sources changed')
        allowed=json.loads(Path('protocol.json').read_text())['confirmation_seeds'][args.dataset]
        assert args.seed in allowed and args.total in (5000,10000)
        assert args.total == 10000 or args.policy == 'cosine'
        revision=freeze['source_revision']
    else: revision='pilot-'+hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()[:16]
    attempt=root/'attempts'/args.attempt_id
    attempt.mkdir(parents=True,exist_ok=False)
    cfg=vars(args).copy(); cfg['source_revision']=revision; cfg['source_hashes']=source
    json_write(attempt/'config.json',cfg)
    provenance=prepare_inputs(root,args.phase,args.dataset,args.seed)
    data_dir=Path(provenance['directory'])
    with np.load(data_dir/'training.npz',allow_pickle=False) as training:
        noisy=torch.tensor(training['noisy'],device=args.device)
        noise=torch.tensor(training['noise'],device=args.device)
        timesteps=torch.tensor(training['timesteps'],dtype=torch.float32,device=args.device)
    with np.load(data_dir/'evaluation.npz',allow_pickle=False) as evaluation:
        heldout=evaluation['heldout']; generation_noise=evaluation['generation_noise']
    models={k:Denoiser().to(args.device) for k in VARIANTS}
    with np.load(data_dir/'initial.npz',allow_pickle=False) as initial:
        for m in models.values(): load_state(m,initial)
    for k in VARIANTS[1:]: models[k].requires_grad_(False)
    parameters=list(models['raw'].parameters())
    optimizer=torch.optim.AdamW(parameters,lr=3e-4,weight_decay=.01,foreach=True)
    first=1; ancestors=[]
    if args.resume:
        saved=torch.load(args.resume,map_location=args.device,weights_only=False)
        for k in ('dataset','seed','policy','total','device','phase'):
            assert saved['config'][k]==cfg[k], f'Resume mismatch: {k}'
        for k,m in models.items(): m.load_state_dict(saved['models'][k])
        optimizer.load_state_dict(saved['optimizer']); first=saved['step']+1
        ancestors=[saved['config']['attempt_id']]
    coeff={k:torch.tensor(v,dtype=torch.float32,device=args.device) for k,v in schedule().items()}
    eval_noise=torch.tensor(generation_noise,device=args.device)
    sync(args.device); train_start=time.monotonic(); eval_seconds=0.; records=[]
    trace_path=attempt/'trace.jsonl'
    print(json.dumps(dict(event='training_start',first_update=first,config=cfg,inputs=provenance)),flush=True)
    with trace_path.open('x') as trace:
        for step in range(first,args.stop+1):
            optimizer.zero_grad(set_to_none=True)
            loss=torch.nn.functional.mse_loss(models['raw'](noisy[step-1],timesteps[step-1]),noise[step-1])
            loss.backward()
            grad_norm=torch.nn.utils.clip_grad_norm_(parameters,.5,foreach=False)
            lr=learning_rate(step,args.total,args.policy); optimizer.param_groups[0]['lr']=lr
            optimizer.step()
            with torch.no_grad():
                for k,decay in (('ema099',.99),('ema0999',.999)):
                    torch._foreach_lerp_(list(models[k].parameters()),parameters,1-decay)
            if step==first or step%100==0:
                loss_value=float(loss.detach().cpu()); norm_value=float(grad_norm.detach().cpu())
                if not math.isfinite(loss_value+norm_value): raise RuntimeError('Nonfinite training')
                row=dict(step=step,noise_mse=loss_value,gradient_norm_before_clip=norm_value,lr=lr,
                         elapsed_seconds=time.monotonic()-start)
                trace.write(json.dumps(row)+'\n');trace.flush()
                if step==first or step%1000==0: print(json.dumps(row),flush=True)
            if step%args.checkpoint_every==0 or step==args.stop:
                save_resume(attempt/'resume.pt',models,optimizer,step,cfg)
                json_write(attempt/'progress.json',dict(completed_updates=step,attempt_id=args.attempt_id,
                                                       elapsed_seconds=time.monotonic()-start))
            required=(args.policy=='constant' and step in (5000,10000)) or (args.policy=='cosine' and step==args.total)
            if args.phase=='pilot': required=step==args.stop
            if not required: continue
            sync(args.device); evaluation_start=time.monotonic()
            cell=root/'cells'/args.phase/f'{args.dataset}-{args.seed}-{args.policy}-{args.total}'/f'update-{step}'
            cell.mkdir(parents=True,exist_ok=False)
            arrays=dict(heldout=heldout,generation_noise=generation_noise); weights={}; measures={}
            for variant,m in models.items():
                state=state_arrays(m)
                for key,value in state.items(): weights[f'{variant}__{key}']=value
                m.eval(); sample=draw(m,eval_noise,coeff)
                assert sample.shape==(2048,2) and np.isfinite(sample).all()
                arrays[variant]=sample; measures[variant]=metrics(args.dataset,sample,heldout)
            np.savez(cell/'arrays.npz',**arrays); np.savez(cell/'weights.npz',**weights)
            record=dict(dataset=args.dataset,seed=args.seed,updates=step,schedule=args.policy,phase=args.phase,
                        device=args.device,arrays=str(cell/'arrays.npz'),weights=str(cell/'weights.npz'),metrics=measures,
                        source_revision=revision,attempt_id=args.attempt_id,training_trace=str(trace_path),
                        trajectory_terminal_updates=args.total,initial_state=str(data_dir/'initial.npz'),
                        retained_inputs=str(data_dir/'training.npz'),provenance=str(data_dir/'provenance.json'),
                        ancestors=ancestors,config=str(attempt/'config.json'))
            for key in ('initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256'):
                record[key]=provenance[key]
            json_write(cell/'record.json',record); records.append(str(cell/'record.json'))
            sync(args.device); eval_seconds+=time.monotonic()-evaluation_start
    sync(args.device)
    json_write(attempt/'result.json',dict(status='completed',first_update=first,last_update=args.stop,
               training_seconds=time.monotonic()-train_start-eval_seconds,evaluation_seconds=eval_seconds,
               total_seconds=time.monotonic()-start,records=records,ancestors=ancestors,
               source_revision=revision,device=args.device,parameter_count=sum(p.numel() for p in parameters)))
    print((attempt/'result.json').read_text(),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--phase',choices=['pilot','confirmation'],required=True)
    p.add_argument('--dataset',choices=['moons','gmm8'],required=True)
    p.add_argument('--seed',type=int,required=True); p.add_argument('--policy',choices=['constant','cosine'],required=True)
    p.add_argument('--total',type=int,required=True);p.add_argument('--stop',type=int,required=True)
    p.add_argument('--attempt-id',required=True);p.add_argument('--root',default='evidence')
    p.add_argument('--device',choices=['cpu','mps'],default='mps');p.add_argument('--resume')
    p.add_argument('--checkpoint-every',type=int,default=2500)
    args=p.parse_args(); assert 1<=args.stop<=args.total<=10000
    execute(args)

if __name__=='__main__': main()
