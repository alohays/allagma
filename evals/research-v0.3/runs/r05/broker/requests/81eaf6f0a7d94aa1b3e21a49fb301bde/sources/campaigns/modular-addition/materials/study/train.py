"""One append-only, resumable confirmation segment; invoked only via broker."""
import argparse,hashlib,json,os,platform,sys,time
from pathlib import Path
from datetime import datetime,timezone

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def utc():return datetime.now(timezone.utc).isoformat()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,required=True);parser.add_argument('--weight-decay',type=int,choices=[0,1],required=True)
    parser.add_argument('--end-step',type=int,required=True);parser.add_argument('--attempt-id',required=True)
    parser.add_argument('--root',default='evidence/confirmation');parser.add_argument('--protocol',default='campaigns/modular-addition/protocol.json')
    args=parser.parse_args()
    assert args.seed in (1001,1002,1003,1004) and 0<args.end_step<=100000 and args.end_step%100==0
    root=Path(args.root);out=root/'attempts'/args.attempt_id;out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    protocol=json.loads(Path(args.protocol).read_text());assert protocol['frozen']
    sources={p:sha(p) for p in protocol['training_code']}
    assert sources==protocol['training_source_hashes'],'Training code changed after protocol freeze'
    write(out/'started.json',{'attempt_id':args.attempt_id,'started_at':utc(),'command':sys.argv,'configuration':vars(args),'protocol_sha256':sha(args.protocol),'source_hashes':sources,'environment':{'platform':platform.platform(),'python':sys.version,'VECLIB_MAXIMUM_THREADS':os.environ.get('VECLIB_MAXIMUM_THREADS')}})
    import numpy as np
    from engine import Engine,make_data,initial,metrics
    shared=root/'seeds'/str(args.seed);shared.mkdir(parents=True,exist_ok=True)
    ipath=shared/'initial.npz'
    if not ipath.exists():
        pairs,labels,tr,te=make_data(args.seed);u,v=initial(args.seed)
        np.savez(ipath,input_weight=u.T,output_weight=v,pairs=pairs,labels=labels,train_indices=tr,test_indices=te)
        write(shared/'configuration.json',{'seed':args.seed,'partition_rng':'NumPy PCG64 default_rng(seed)','initialization_rng':'PyTorch CPU Generator manual_seed(seed)','initial_weights_sha256':sha(ipath),'partition_order':'lexicographic ordered pairs, shuffled indices'})
    with np.load(ipath,allow_pickle=False) as data:
        pairs=data['pairs'];labels=data['labels'];tr=data['train_indices'];te=data['test_indices'];u=data['input_weight'].T.copy();v=data['output_weight']
    cell=f's{args.seed}-wd{args.weight_decay}'
    pointer=root/(cell+'-latest.json');curve=[];parents=[]
    if pointer.exists():
        previous=json.loads(pointer.read_text())
        for key in ('checkpoint','curve'):
            assert sha(previous[key])==previous[key+'_sha256'],'Continuation evidence digest mismatch'
        with np.load(previous['checkpoint'],allow_pickle=False) as state:
            e=Engine(pairs[tr],labels[tr],state['u'],state['v'],state=state)
        curve=json.loads(Path(previous['curve']).read_text());parents=previous['attempt_chain']
        assert curve[-1]['step']==e.step
        write(out/'resume.json',previous)
    else:
        e=Engine(pairs[tr],labels[tr],u,v)
        curve=[dict(step=0,**metrics(e.forward(pairs),labels,tr,te))]
    assert e.step<args.end_step,'Already completed or invalid continuation'
    first=e.step
    for step in range(e.step+100,args.end_step+1,100):
        e.advance(100,args.weight_decay)
        logits=e.forward(pairs)
        assert np.isfinite(logits).all(),'Nonfinite logits'
        curve.append(dict(step=step,**metrics(logits,labels,tr,te)))
        if step%10000==0 or step==args.end_step:
            checkpoint=out/f'checkpoint-{step:06d}.npz'
            np.savez(checkpoint,**e.state())
            cpath=out/f'curve-{step:06d}.json';write(cpath,curve)
            latest={'seed':args.seed,'weight_decay':args.weight_decay,'step':step,'checkpoint':str(checkpoint),'checkpoint_sha256':sha(checkpoint),'curve':str(cpath),'curve_sha256':sha(cpath),'attempt_chain':parents+[args.attempt_id],'initial_weights_sha256':sha(ipath)}
            temp=pointer.with_suffix('.tmp');write(temp,latest);temp.replace(pointer)
            print(json.dumps({'seed':args.seed,'weight_decay':args.weight_decay,'step':step,'elapsed':time.perf_counter()-start}),flush=True)
    if e.step==100000:
        np.savez(out/'arrays.npz',pairs=pairs,labels=labels,train_indices=tr,test_indices=te,logits=logits,predictions=logits.argmax(1))
        np.savez(out/'weights.npz',input_weight=e.u.T,output_weight=e.v)
        write(out/'curve.json',curve)
        measurement={'seed':args.seed,'weight_decay':args.weight_decay,'updates':e.step,'phase':'confirmation','device':'cpu','arrays':str(out/'arrays.npz'),'weights':str(out/'weights.npz'),'curve':curve,'curve_path':str(out/'curve.json'),'metrics':{k:v for k,v in curve[-1].items() if k!='step'},'initial_weights_sha256':sha(ipath),'source_revision':protocol['training_source_revision'],'attempt_id':args.attempt_id,'attempt_chain':parents+[args.attempt_id],'initial_weights':str(ipath),'checkpoint':str(checkpoint),'configuration':str(out/'started.json')}
        write(out/'measurement.json',measurement)
    e.close()
    write(out/'completed.json',{'attempt_id':args.attempt_id,'started_step':first,'ended_step':args.end_step,'ended_at':utc(),'elapsed_seconds':time.perf_counter()-start,'status':'succeeded','outputs':{str(p):sha(p) for p in out.iterdir() if p.is_file() and p.name!='completed.json'}})

if __name__=='__main__':main()
