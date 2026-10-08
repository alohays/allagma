"""Known-answer controls and runner qualification; pilot evidence only."""
from pathlib import Path
import json
import math
import time
import runner as r
from common import ROOT, write, sha, named_hash, array_hash, now, ref

def main():
    start=time.monotonic()
    r.libraries()
    np,torch=r.np,r.torch
    checks=[]
    def check(name,ok,detail):
        checks.append({'name':name,'passed':bool(ok),'detail':detail})
        if not ok:
            write(ROOT/'evidence/qualification.json',{'passed':False,'checks':checks})
            raise AssertionError(name)
    x=np.array([[0.,0.],[1.,3.],[-2.,4.]])
    check('SW1 identity',r.sliced_wasserstein(x,x)==0,0)
    shift=np.array([3.,4.])
    from science import projections,mixture_centers
    expected=float(np.abs(projections()@shift).mean())
    observed=r.sliced_wasserstein(np.zeros((20,2)),np.tile(shift,(20,1)))
    check('SW1 analytic translation',abs(expected-observed)<1e-12,{'expected':expected,'observed':observed})
    axes=np.eye(2)
    y=np.array([[1.,2.],[2.,4.],[-1.,0.]])
    expected=(1+1/3)/2
    observed=r.sliced_wasserstein(x,y,axes)
    check('SW1 custom-axis order statistic',abs(expected-observed)<1e-12,{'expected':expected,'observed':observed})
    pts=np.full((2048,2),20.)
    centers=mixture_centers()
    pts[:20]=centers[0]
    pts[20:41]=centers[1]
    mode=r.mode_coverage(pts)
    check('Coverage all-draw denominator and threshold',mode['covered']==1 and mode['counts']==[20,21,0,0,0,0,0,0] and mode['inlier_fraction']==41/2048,mode)
    pts=np.array([centers[0]+[.44,0],centers[0]+[.46,0]])
    check('Coverage radius criterion',r.mode_coverage(pts)['counts'][0]==1,r.mode_coverage(pts))
    a=torch.tensor([1.,-2.]); b=torch.tensor([3.,2.])
    torch._foreach_lerp_([a],[b],.01)
    check('EMA post-update interpolation',bool(torch.allclose(a,torch.tensor([1.02,-1.96]),atol=1e-7)),a.tolist())
    model=r.Denoiser()
    check('Reference architecture',sum(p.numel() for p in model.parameters())==296450 and 'time.frequencies' in model.state_dict() and 'coord.frequencies' in model.state_dict(),sum(p.numel() for p in model.parameters()))
    coeff=r.schedule()
    check('DDPM schedule terminal/noise',len(coeff['beta'])==100 and coeff['abar'][-1]<1e-5 and coeff['posterior_std'][0]==0,float(coeff['abar'][-1]))
    check('Distinct cosine policies',r.lr_at('cosine',5000,1)==3e-4 and r.lr_at('cosine',5000,5000)<1e-10 and r.lr_at('cosine',10000,5000)>1e-4 and r.lr_at('constant',5000,5000)==3e-4,
          {str(d):r.lr_at('cosine',d,5000) for d in (5000,10000)})
    folder,meta=r.seed_inputs('moons',71,'pilot',ROOT/'artifacts')
    with np.load(folder/'training.npz',allow_pickle=False) as a:
        actual=named_hash({k:a[k] if k=='train' else a[k][:5000] for k in ('train','indices','noise','timesteps','noisy')})
        noisy=(coeff['sqrt_abar'][a['timesteps'][:2],None]*a['train'][a['indices'][:2]]+coeff['sqrt_one_minus'][a['timesteps'][:2],None]*a['noise'][:2]).astype(np.float32)
        check('Retained actual input prefix',actual==meta['training_prefix_5000_sha256'] and np.array_equal(noisy,a['noisy'][:2]),actual)
    tensors=r.training_tensors(folder,'mps')
    continuous,opt=r.models_optimizer(folder,'mps')
    for i in range(20):
        r.update(continuous,opt,tensors,i,'cosine',5000)
    split,opt2=r.models_optimizer(folder,'mps')
    for i in range(10):
        r.update(split,opt2,tensors,i,'cosine',5000)
    path=ROOT/'evidence/pilot-step10-recovery.npz'
    r.checkpoint(path,split,opt2,10)
    loaded,opt3=r.models_optimizer(folder,'mps')
    restored=r.restore(path,loaded,opt3,'mps')
    for i in range(restored,20):
        r.update(loaded,opt3,tensors,i,'cosine',5000)
    maximum=max(float(np.max(np.abs(r.cpu_state(continuous[n])[k]-r.cpu_state(loaded[n])[k]))) for n in continuous for k in continuous[n].state_dict())
    check('AdamW and EMA full-state resume',restored==10 and maximum<=1e-6,{'restored_step':restored,'max_abs_difference':maximum})
    with np.load(folder/'evaluation.npz',allow_pickle=False) as data:
        noise=torch.tensor(data['generation_noise'][:,:128],device='mps')
    c={k:torch.tensor(v,dtype=torch.float32,device='mps') for k,v in coeff.items()}
    sample1=r.draw(continuous['raw'],noise,c)
    np.savez(ROOT/'evidence/pilot-load-test.npz',**r.cpu_state(continuous['raw']))
    reload_model=r.Denoiser().to('mps')
    with np.load(ROOT/'evidence/pilot-load-test.npz',allow_pickle=False) as saved:
        r.load_state(reload_model,saved)
    sample2=r.draw(reload_model,noise,c)
    max_sample=float(np.max(np.abs(sample1-sample2)))
    check('Saved state reference sample regeneration',max_sample<=1e-6,{'max_abs_difference':max_sample,'draws':128})
    result={'passed':all(c['passed'] for c in checks),'checks':checks,'created_at':now(),
            'phase':'pilot','device':'mps','pilot_seed':71,'elapsed_seconds':time.monotonic()-start,
            'scientific_sources':{p:sha(ROOT/p) for p in ('study/science.py','study/runner.py','study/common.py','study/qualify.py')}}
    write(ROOT/'evidence/qualification.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
