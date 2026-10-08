"""CPU full-batch training with append-only attempts and resumable optimizer state."""
import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--wd',type=int,choices=[0,1],required=True)
    p.add_argument('--updates',type=int,default=100000)
    p.add_argument('--out',required=True)
    p.add_argument('--phase',choices=['pilot','confirmation'],required=True)
    p.add_argument('--resume')
    p.add_argument('--max-seconds',type=float,default=155)
    p.add_argument('--protocol',default='campaigns/c001/protocol.json')
    args=p.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=False)
    started=datetime.now(timezone.utc).isoformat()
    (out/'started.json').write_text(json.dumps({'started_at':started,'argv':sys.argv,'config':vars(args)})+'\n')
    print(f'Start {args.phase} seed={args.seed} decay={args.wd}',flush=True)
    import numpy as np
    import torch
    import torch.nn.functional as F
    from common import configure,data,inputs,model,optimizer,write_json,state_np,state_hash,evaluate,source_revision,sha
    configure()
    if args.phase=='confirmation':
        protocol=json.loads(Path(args.protocol).read_text())
        assert args.seed in protocol['confirmation_seeds'] and args.updates==100000
        assert protocol['qualification']['passed']
        for path,digest in protocol['source_hashes'].items():
            assert sha(path)==digest, f'Frozen source changed: {path}'
    pairs,labels,tr,te=data(args.seed)
    x,y=inputs(pairs),torch.from_numpy(labels)
    net=model(args.seed)
    initial_hash=state_hash(net)
    np.savez(out/'initial.npz',**state_np(net))
    np.savez(out/'partition.npz',pairs=pairs,labels=labels,train_indices=tr,test_indices=te)
    opt=optimizer(net,args.wd)
    step=0
    curve=[]
    if args.resume:
        ck=torch.load(args.resume,map_location='cpu',weights_only=False)
        assert ck['seed']==args.seed and ck['weight_decay']==args.wd and ck['initial_weights_sha256']==initial_hash
        net.load_state_dict(ck['model'])
        opt.load_state_dict(ck['optimizer'])
        step=ck['step']
        curve=ck['curve']
        assert curve[-1]['step']==step
    start_step=step
    train_x,train_y=x[tr],y[tr]
    if not curve:
        row,_=evaluate(net,x,y,tr,te,0)
        curve.append(row)
    revision=source_revision()
    config={'seed':args.seed,'weight_decay':args.wd,'updates':args.updates,'phase':args.phase,
            'device':'cpu','dtype':'float32','optimizer':'AdamW','lr':.001,'betas':[.9,.98],'eps':1e-8,
            'architecture':'Linear(194,128,bias=False),ReLU,Linear(128,97,bias=False)',
            'batch':'all 2822 training pairs','evaluation_interval':100,'split_rng':'numpy.default_rng(seed)',
            'initial_weights_sha256':initial_hash,'source_revision':revision,'resume':args.resume,
            'protocol':args.protocol,'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__}
    write_json(out/'config.json',config)
    def checkpoint():
        target=out/f'checkpoint-{step:06d}.pt'
        torch.save({'step':step,'seed':args.seed,'weight_decay':args.wd,'model':net.state_dict(),
                    'optimizer':opt.state_dict(),'curve':curve,'initial_weights_sha256':initial_hash,
                    'source_revision':revision},target)
        write_json(out/'progress.json',{'step':step,'checkpoint':target.as_posix()})
        return target
    checkpoint()
    start=time.perf_counter()
    with (out/'trace.jsonl').open('w') as trace:
        if start_step==0:
            trace.write(json.dumps(curve[0])+'\n'); trace.flush()
        while step<args.updates:
            opt.zero_grad(set_to_none=True)
            loss=F.cross_entropy(net(train_x),train_y)
            loss.backward()
            opt.step()
            step+=1
            if step%100==0:
                row,_=evaluate(net,x,y,tr,te,step)
                if not all(np.isfinite(v) for v in row.values()):
                    raise RuntimeError('Nonfinite evaluation')
                curve.append(row)
                trace.write(json.dumps(row)+'\n');trace.flush()
                if step%10000==0:
                    checkpoint()
                    print(f'step={step} elapsed={time.perf_counter()-start:.2f}',flush=True)
                if time.perf_counter()-start>=args.max_seconds:
                    break
    elapsed=time.perf_counter()-start
    final_checkpoint=out/f'checkpoint-{step:06d}.pt'
    if not final_checkpoint.exists(): checkpoint()
    row,logits=evaluate(net,x,y,tr,te,step)
    assert curve[-1]==row
    np.savez(out/'arrays.npz',pairs=pairs,labels=labels,train_indices=tr,test_indices=te,
             logits=logits,predictions=logits.argmax(axis=1))
    np.savez(out/'weights.npz',**state_np(net))
    write_json(out/'curve.json',curve)
    result={**config,'updates':step,'planned_updates':args.updates,'start_step':start_step,
            'complete':step==args.updates,'training_seconds':elapsed,'started_at':started,
            'ended_at':datetime.now(timezone.utc).isoformat(),'attempt_id':out.name,
            'arrays':(out/'arrays.npz').as_posix(),'weights':(out/'weights.npz').as_posix(),
            'curve':(out/'curve.json').as_posix(),'initial_weights':(out/'initial.npz').as_posix(),
            'checkpoint':final_checkpoint.as_posix(),'metrics':{k:v for k,v in row.items() if k!='step'}}
    write_json(out/'result.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__': main()
