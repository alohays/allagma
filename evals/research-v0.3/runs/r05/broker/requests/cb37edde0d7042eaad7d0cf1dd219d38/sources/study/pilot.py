"""Pilot seed 61 only: algebra, optimizer and local throughput qualification."""
import argparse
import json
import os
from pathlib import Path
import platform
import time

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--steps', type=int, default=300)
args = p.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=False)
(out / 'started.json').write_text(json.dumps({'seed':61, 'phase':'pilot', 'started_at':time.time(), 'argv':__import__('sys').argv}))
import numpy as np
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.manual_seed(61)
np.random.seed(61)
pairs=np.stack(np.meshgrid(np.arange(97),np.arange(97),indexing='ij'),axis=-1).reshape(-1,2)
labels=(pairs[:,0]+pairs[:,1])%97
order=np.random.default_rng(61).permutation(9409)
tr,te=order[:2822],order[2822:]
assert len(tr)==2822 and len(te)==6587 and len(set(tr)&set(te))==0
assert labels[0]==0 and labels[96*97+96]==95 and labels[1*97+96]==0
x=np.eye(97,dtype=np.float32)[pairs].reshape(9409,194)
np.savez(out/'partition.npz',pairs=pairs,labels=labels,train_indices=tr,test_indices=te)
results={'seed':61,'environment':{'torch':torch.__version__,'numpy':np.__version__,'platform':platform.platform(),'processor':platform.processor(),'mps_available':torch.backends.mps.is_available()},'known_answer_checks':'passed','benchmarks':[]}
(out/'progress.json').write_text(json.dumps(results,indent=2))
for dev in ['cpu']+(['mps'] if torch.backends.mps.is_available() else []):
  for sparse in [False,True]:
    torch.manual_seed(61)
    w1=torch.nn.Parameter(torch.empty(128,194,device='cpu'))
    w2=torch.nn.Parameter(torch.empty(97,128,device='cpu'))
    torch.nn.init.kaiming_uniform_(w1,a=5**.5); torch.nn.init.kaiming_uniform_(w2,a=5**.5)
    w1=torch.nn.Parameter(w1.to(dev)); w2=torch.nn.Parameter(w2.to(dev))
    xt=torch.tensor(x[tr],device=dev); yt=torch.tensor(labels[tr],device=dev)
    aa=torch.tensor(pairs[tr,0],device=dev); bb=torch.tensor(pairs[tr,1]+97,device=dev)
    opt=torch.optim.AdamW([w1,w2],lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=1,foreach=False)
    def step():
      opt.zero_grad(set_to_none=True)
      h=(w1[:,aa]+w1[:,bb]).T if sparse else xt@w1.T
      z=h.relu()@w2.T
      loss=torch.nn.functional.cross_entropy(z,yt)
      loss.backward();opt.step()
      return loss
    for _ in range(10):step()
    if dev=='mps':torch.mps.synchronize()
    start=time.perf_counter()
    for _ in range(args.steps):loss=step()
    if dev=='mps':torch.mps.synchronize()
    seconds=time.perf_counter()-start
    result={'device':dev,'sparse':sparse,'steps':args.steps,'seconds':seconds,'seconds_per_update':seconds/args.steps,'projected_800000_updates_seconds':seconds/args.steps*800000,'loss':float(loss.detach().cpu())}
    results['benchmarks'].append(result)
    (out/'progress.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(result),flush=True)
(out/'qualification.json').write_text(json.dumps(results,indent=2))
