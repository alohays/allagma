"""Independent PyTorch agreement, restart equivalence and measured full cadence cost."""
import argparse,json,time,platform
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--steps',type=int,default=3000);args=p.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
(out/'started.json').write_text(json.dumps({'seed':61,'phase':'pilot','started_at':time.time(),'argv':__import__('sys').argv}))
import numpy as np
import torch
from engine import Engine,make_data,initial,metrics
torch.set_num_threads(1);torch.set_num_interop_threads(1)
pairs,y,tr,te=make_data(61);u,v=initial(61)
np.savez(out/'initial.npz',input_weight=u.T,output_weight=v,pairs=pairs,labels=y,train_indices=tr,test_indices=te)
x=torch.tensor(np.eye(97,dtype=np.float32)[pairs[tr]].reshape(-1,194));yt=torch.tensor(y[tr].astype(np.int64))
checks=[]
for wd in (0,1):
    e=Engine(pairs[tr],y[tr],u,v)
    a=torch.nn.Parameter(torch.tensor(u.T.copy()));b=torch.nn.Parameter(torch.tensor(v))
    opt=torch.optim.AdamW([a,b],lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=wd,foreach=False)
    z=x@a.T;z=z.relu()@b.T;loss=torch.nn.functional.cross_entropy(z,yt);loss.backward()
    g1,g2=e.gradients()
    gradient_error=max(float(np.max(np.abs(g1-a.grad.numpy().T))),float(np.max(np.abs(g2-b.grad.numpy()))))
    assert gradient_error<2e-7
    forward_error=float(np.max(np.abs(e.forward(pairs[tr])-z.detach().numpy())))
    assert forward_error<2e-6
    trace=[]
    for s in range(50):
        opt.zero_grad();loss=torch.nn.functional.cross_entropy((x@a.T).relu()@b.T,yt);loss.backward();opt.step();e.advance(1,wd)
        if s in (0,1,4,9,19,49):
            trace.append({'step':s+1,'w1_max_error':float(np.max(np.abs(e.u-a.detach().numpy().T))),'w2_max_error':float(np.max(np.abs(e.v-b.detach().numpy())))})
    error=max(float(np.max(np.abs(e.u-a.detach().numpy().T))),float(np.max(np.abs(e.v-b.detach().numpy()))))
    (out/f'agreement-wd{wd}.json').write_text(json.dumps({'forward':forward_error,'gradient':gradient_error,'trace':trace,'max_error_50':error},indent=2))
    print(json.dumps({'wd':wd,'trace':trace,'forward':forward_error,'gradient':gradient_error}),flush=True)
    # ReLU activation-boundary changes amplify tiny float32 reduction differences
    # in free trajectories. Test the optimizer at IDENTICAL weights/moments too.
    aligned_errors=[]
    for s in range(50,70):
        sa=opt.state[a];sb=opt.state[b]
        same={'m1':sa['exp_avg'].numpy().T.copy(),'q1':sa['exp_avg_sq'].numpy().T.copy(),
              'm2':sb['exp_avg'].numpy().copy(),'q2':sb['exp_avg_sq'].numpy().copy(),'step':s}
        anchored=Engine(pairs[tr],y[tr],a.detach().numpy().T,b.detach().numpy(),state=same)
        opt.zero_grad();loss=torch.nn.functional.cross_entropy((x@a.T).relu()@b.T,yt);loss.backward()
        gg1,gg2=anchored.gradients()
        assert np.max(np.abs(gg1-a.grad.numpy().T))<2e-7
        assert np.max(np.abs(gg2-b.grad.numpy()))<2e-7
        anchored.advance(1,wd);opt.step()
        ae=max(float(np.max(np.abs(anchored.u-a.detach().numpy().T))),float(np.max(np.abs(anchored.v-b.detach().numpy()))))
        aligned_errors.append(ae);anchored.close()
        assert ae<2e-6,ae
    np.savez(out/f'checkpoint-wd{wd}.npz',**e.state())
    with np.load(out/f'checkpoint-wd{wd}.npz',allow_pickle=False) as state:
        resumed=Engine(pairs[tr],y[tr],state['u'],state['v'],state=state)
    e.advance(50,wd);resumed.advance(50,wd)
    assert all(np.array_equal(e.state()[k],resumed.state()[k]) for k in e.state())
    checks.append({'weight_decay':wd,'forward_max_abs_error':forward_error,'gradient_max_abs_error':gradient_error,'free_trajectory_weights_after_50_max_abs_error':error,'initial_20_update_max_error':max(max(t['w1_max_error'],t['w2_max_error']) for t in trace if t['step']<=20),'aligned_optimizer_updates_51_to_70_max_abs_error':max(aligned_errors),'resume_50_plus_50_exact':True})
    e.close();resumed.close()
e=Engine(pairs[tr],y[tr],u,v)
start=time.perf_counter();curve=[dict(step=0,**metrics(e.forward(pairs),y,tr,te))]
for s in range(100,args.steps+1,100):
    e.advance(100,1);curve.append(dict(step=s,**metrics(e.forward(pairs),y,tr,te)))
elapsed=time.perf_counter()-start
np.savez(out/'benchmark-final.npz',**e.state());e.close()
for a,b,c in [(0,0,0),(96,96,95),(1,96,0),(0,96,96),(48,49,0)]:assert y[a*97+b]==c
assert len(tr)==2822 and len(te)==6587 and len(set(tr)&set(te))==0 and sorted(np.r_[tr,te])==list(range(9409))
result={'qualification_passed':True,'seed':61,'checks':checks,'known_answer_labels':5,'split_disjoint_exhaustive':True,'training_dtype':'float32','backend':'CPU Accelerate via C','steps':args.steps,'seconds_including_evaluation':elapsed,'seconds_per_update':elapsed/args.steps,'projected_complete_study_seconds':elapsed/args.steps*800000,'torch':torch.__version__,'numpy':np.__version__,'platform':platform.platform()}
(out/'curve.json').write_text(json.dumps(curve,indent=2))
(out/'qualification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
