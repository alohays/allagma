"""Independent pilot controls, update math, checkpoint recovery, and cost gate."""
import argparse
import copy
import json
from pathlib import Path
import time
import numpy as np
import torch
import torch.nn.functional as F
from common import configure,data,inputs,model,optimizer,evaluate,numpy_metrics,write_json,state_np

p=argparse.ArgumentParser()
p.add_argument('--out',required=True)
p.add_argument('--pilot',required=True)
args=p.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
configure()
pairs,y,tr,te=data(61)
checks={}
checks['known_labels']=all(int(y[a*97+b])==(a+b)%97 for a,b in [(0,0),(0,96),(96,0),(96,96),(96,1),(48,49)])
checks['exhaustive_labels']=np.array_equal(y,(pairs[:,0]+pairs[:,1])%97)
checks['class_balance']=np.array_equal(np.bincount(y),np.full(97,97))
checks['split']=len(tr)==2822 and len(te)==6587 and len(np.unique(np.r_[tr,te]))==9409 and not np.intersect1d(tr,te).size
checks['split_repeatable']=np.array_equal(tr,data(61)[2])
x=inputs(pairs);yt=torch.from_numpy(y)
net=model(61); opt=optimizer(net,1)
assert sum(p.numel() for p in net.parameters())==37248
checks['architecture']=all(p.dtype==torch.float32 for p in net.parameters()) and len(list(net.parameters()))==2
# First AdamW step from its scalar closed form, including decoupled shrinkage.
before=[p.detach().clone() for p in net.parameters()]
F.cross_entropy(net(x[tr]),yt[tr]).backward()
grads=[p.grad.detach().clone() for p in net.parameters()]
expected=[w*(1-.001)-.001*g/(g.abs()+1e-8) for w,g in zip(before,grads)]
opt.step()
adam_error=max((a-b).abs().max().item() for a,b in zip(net.parameters(),expected))
checks['adamw_first_step']=adam_error<2e-7
# Identical 12-step trajectory with and without save/reload at step 5.
net=model(61);opt=optimizer(net,1)
for i in range(12):
    opt.zero_grad(set_to_none=True);F.cross_entropy(net(x[tr]),yt[tr]).backward();opt.step()
    if i==4:
        torch.save({'model':net.state_dict(),'optimizer':opt.state_dict()},out/'resume-control.pt')
full=state_np(net)
ck=torch.load(out/'resume-control.pt',weights_only=False)
net2=model(61);opt2=optimizer(net2,1)
net2.load_state_dict(ck['model']);opt2.load_state_dict(ck['optimizer'])
for _ in range(7):
    opt2.zero_grad(set_to_none=True);F.cross_entropy(net2(x[tr]),yt[tr]).backward();opt2.step()
checks['resume_bitwise']=all(np.array_equal(a,state_np(net2)[k]) for k,a in full.items())
row,logits=evaluate(net,x,yt,tr,te,12)
nm=numpy_metrics(logits,y,tr,te)
metric_error=max(abs(nm[k]-row[k]) for k in nm)
checks['independent_metric_formula']=metric_error<2e-6
uniform=np.zeros((9409,97),dtype=np.float32)
un=numpy_metrics(uniform,y,tr,te)
checks['known_uniform_cross_entropy']=abs(un['test_loss']-np.log(97))<1e-12
perfect=np.full((9409,97),-30,dtype=np.float32);perfect[np.arange(9409),y]=30
checks['known_perfect_predictions']=numpy_metrics(perfect,y,tr,te)['test_accuracy']==1
pilot=json.loads(Path(args.pilot).read_text())
pa=np.load(pilot['arrays'],allow_pickle=False)
ck=torch.load(pilot['checkpoint'],weights_only=False,map_location='cpu')
reload_net=model(61);reload_net.load_state_dict(ck['model'])
with torch.no_grad():
    reload_logits=reload_net(inputs(pa['pairs'])).numpy()
checks['pilot_checkpoint_reload']=np.array_equal(pa['logits'],reload_logits)
rate=pilot['training_seconds']/(pilot['updates']-pilot['start_step'])
projected=rate*800000
# Reserve 120 seconds for verification, analysis and broker/process overhead,
# and 25% runtime margin beyond the end-to-end pilot rate.
qualified_cost=projected*1.25+120
checks['cost_feasible']=qualified_cost<1700
result={'passed':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},
        'adamw_first_step_max_abs_error':adam_error,'metric_max_abs_error':metric_error,
        'seconds_per_update_including_evaluation':rate,'projected_training_seconds':projected,
        'margin_and_verification_seconds':qualified_cost,'budget_seconds':1800,
        'pilot':args.pilot,'device':'cpu','seed':61,'mps_excluded':'Earlier pilot failed allocator configuration; CPU qualified independently.'}
write_json(out/'qualification.json',result)
print(json.dumps(result,indent=2))
assert result['passed'], 'Pilot qualification gate failed'
