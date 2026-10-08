"""Known-answer scientific qualification; pilot seeds only."""
import copy, json, math, time
from pathlib import Path
import numpy as np
import torch
from science import Denoiser, dataset, projections, sliced_wasserstein, mode_coverage, mixture_centers, schedule, draw
from study import learning_rate, state_arrays, load_state, state_hash, json_write

def main():
    start=time.monotonic(); torch.set_num_threads(1); checks=[]
    def check(name, ok, **evidence):
        checks.append(dict(name=name,passed=bool(ok),**evidence))
        if not ok: raise AssertionError(name)
    rng=np.random.default_rng(71); x=rng.normal(size=(2048,2)); v=np.array([.4,-.7])
    check('SW1 identity',sliced_wasserstein(x,x)==0)
    permutation_error=sliced_wasserstein(x,x[::-1])
    check('SW1 permutation invariance',permutation_error<1e-12,observed=permutation_error,tolerance=1e-12)
    expected=float(np.abs(projections()@v).mean()); observed=sliced_wasserstein(x,x+v)
    check('SW1 exact translation',abs(expected-observed)<1e-12,expected=expected,observed=observed)
    y=rng.normal(size=(2048,2))
    check('SW1 symmetry',abs(sliced_wasserstein(x,y)-sliced_wasserstein(y,x))<1e-15)
    invalid=False
    try: sliced_wasserstein(x,y[:100])
    except ValueError: invalid=True
    check('SW1 rejects unequal sizes',invalid)
    centers=mixture_centers()
    c=mode_coverage(np.repeat(centers,256,axis=0))
    check('coverage eight balanced exact centers',c['covered']==8 and c['counts']==[256]*8 and c['inlier_fraction']==1)
    z=np.full((2048,2),20.); z[:20]=centers[0]; z[20:41]=centers[1]
    c=mode_coverage(z)
    check('coverage denominator all draws and 21-count threshold',c['covered']==1 and c['counts'][:2]==[20,21] and c['inlier_fraction']==41/2048,observed=c)
    z=np.array([centers[0]+[.449,0],centers[0]+[.451,0]])
    c=mode_coverage(z)
    check('coverage radius',c['counts'][0]==1 and c['inlier_fraction']==.5)
    for total in (5000,10000):
        rates=np.array([learning_rate(i,total,'cosine') for i in range(1,total+1)])
        check(f'cosine endpoints and monotonicity T={total}',rates[0]==.0003 and rates[-1]==0 and np.all(np.diff(rates)<=0),lr_first=float(rates[0]),lr_last=float(rates[-1]),lr_sum=float(rates.sum()))
    check('cosine5000 differs from cosine10000 prefix',learning_rate(5000,5000,'cosine') != learning_rate(5000,10000,'cosine'))
    check('constant prefix exact',[learning_rate(i,5000,'constant') for i in (1,2000,5000)] == [.0003]*3)
    torch.manual_seed(71); model=Denoiser(); initial=state_arrays(model)
    check('reference parameter count',sum(p.numel() for p in model.parameters())==296450)
    check('reference embedding buffers retained',set(k for k in initial if k.endswith('frequencies'))=={'time.frequencies','coord.frequencies'})
    for decay in (.99,.999):
        a=torch.tensor([1.,2.,-3.]); b=torch.tensor([2.,0.,4.]); target=decay*a+(1-decay)*b
        torch._foreach_lerp_([a],[b],1-decay)
        check(f'EMA update decay={decay}',torch.allclose(a,target,rtol=1e-6,atol=1e-7))
    coef_np=schedule()
    check('DDPM beta endpoints and variance',coef_np['beta'].shape==(100,) and coef_np['beta'].max()<=.999 and coef_np['posterior_std'][0]==0 and coef_np['abar'][-1]<1e-5)
    device='mps' if torch.backends.mps.is_available() else 'cpu'
    model=model.to(device)
    coeff={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in coef_np.items()}
    noises=torch.tensor(rng.normal(size=(100,32,2)).astype(np.float32),device=device)
    sample1=draw(model,noises,coeff)
    target=Path('evidence/qualification');target.mkdir(parents=True,exist_ok=True)
    np.savez(target/'known-state.npz',**initial)
    restored=Denoiser().to(device)
    with np.load(target/'known-state.npz',allow_pickle=False) as a: load_state(restored,a)
    sample2=draw(restored,noises,coeff)
    error=float(np.max(np.abs(sample1-sample2)))
    check('NPZ state roundtrip and reference sampler determinism',error<1e-6 and np.isfinite(sample1).all(),device=device,max_absolute_error=error)
    check('initial state hash stable through load',state_hash(initial)==state_hash(state_arrays(restored)))
    for name,seed in [('moons',71),('gmm8',81)]:
        a=dataset(name,100000,seed+1000000); b=dataset(name,2048,seed+2000000)
        check(f'{name} finite float32 independent-shaped draws',a.dtype==np.float32 and a.shape==(100000,2) and b.shape==(2048,2) and np.isfinite(a).all() and not np.array_equal(a[:2048],b))
    out=dict(status='passed',checks=checks,seconds=time.monotonic()-start,device=device,confirmation_data_used=False)
    json_write('evidence/qualification.json',out); print(json.dumps(out),flush=True)

if __name__=='__main__': main()
