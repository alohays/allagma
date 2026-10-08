"""Pilot-only correctness and cost qualification; never uses confirmation seeds."""
import argparse
import json
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--steps', type=int, default=500)
args = p.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=False)
(out / 'started.json').write_text(json.dumps({'phase': 'pilot', 'seed': 61, 'started_unix': time.time()}) + '\n')
print('Pilot 61 started; importing numerical libraries', flush=True)

import numpy as np
import torch
import torch.nn.functional as F

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
pairs = np.array([(a,b) for a in range(97) for b in range(97)], dtype=np.int64)
labels = pairs.sum(axis=1) % 97
perm = np.random.default_rng(61).permutation(9409)
tr, te = perm[:2822], perm[2822:]
assert len(tr) == int(.3*9409) and len(te) == 6587
assert len(np.unique(np.concatenate([tr,te]))) == 9409
assert not set(tr) & set(te)
assert labels[0] == 0 and labels[96*97+96] == 95 and labels[96*97+1] == 0
assert np.array_equal(np.bincount(labels), np.full(97,97))
x = F.one_hot(torch.from_numpy(pairs),97).float().reshape(9409,194)
y = torch.from_numpy(labels)
torch.manual_seed(61)
base = torch.nn.Sequential(torch.nn.Linear(194,128,bias=False),torch.nn.ReLU(),torch.nn.Linear(128,97,bias=False))
state = {k:v.clone() for k,v in base.state_dict().items()}
np.savez(out/'inputs.npz',pairs=pairs,labels=labels,train_indices=tr,test_indices=te,
         input_weight=state['0.weight'].numpy(),output_weight=state['2.weight'].numpy())
results = {'seed':61,'torch':torch.__version__,'numpy':np.__version__,
           'mps_available':torch.backends.mps.is_available(), 'checks':{'labels_and_split':True},'timings':[]}
def save():
    (out/'qualification.json').write_text(json.dumps(results,indent=2)+'\n')
save()
for device in ['cpu'] + (['mps'] if torch.backends.mps.is_available() else []):
    for method in ['dense','gather']:
        model = torch.nn.Sequential(torch.nn.Linear(194,128,bias=False),torch.nn.ReLU(),torch.nn.Linear(128,97,bias=False))
        model.load_state_dict(state)
        model.to(device)
        opt = torch.optim.AdamW(model.parameters(),lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=1,foreach=False)
        xt, yt = x[tr].to(device), y[tr].to(device)
        ab = torch.from_numpy(pairs[tr]).to(device)
        def forward():
            if method == 'dense':
                return model(xt)
            w = model[0].weight
            h = (w[:,ab[:,0]] + w[:,ab[:,1]+97]).T.relu()
            return F.linear(h,model[2].weight)
        with torch.no_grad():
            err = (forward()-model(xt)).abs().max().item()
        assert err < 2e-6, (device,method,err)
        for _ in range(20):
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(forward(),yt).backward()
            opt.step()
        if device=='mps': torch.mps.synchronize()
        start = time.perf_counter()
        for step in range(args.steps):
            opt.zero_grad(set_to_none=True)
            F.cross_entropy(forward(),yt).backward()
            opt.step()
        if device=='mps': torch.mps.synchronize()
        elapsed = time.perf_counter()-start
        info = {'device':device,'method':method,'steps':args.steps,'seconds':elapsed,
                'seconds_per_update':elapsed/args.steps,'800000_updates_seconds':elapsed/args.steps*800000,
                'forward_max_abs_error':err, 'last_train_loss':float(F.cross_entropy(forward(),yt).item())}
        results['timings'].append(info)
        save()
        print(json.dumps(info),flush=True)
print('Pilot benchmarks and known-answer checks completed',flush=True)
