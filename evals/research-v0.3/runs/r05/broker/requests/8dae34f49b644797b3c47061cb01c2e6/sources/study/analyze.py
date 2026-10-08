"""Retained-data reanalysis: no training and no dependence on reported metrics."""
import argparse,csv,hashlib,itertools,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('.tmp/matplotlib').resolve()))
import numpy as np
from scipy.special import logsumexp
from scipy.stats import t as student_t

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def ref(path):
    p=Path(path)
    return {'path':str(p),'sha256':sha(p),'media_type':'application/json' if p.suffix=='.json' else 'application/octet-stream','retention':'retained'}

def threshold(curve,key,level,sustain):
    mask=np.array([row[key]>=level for row in curve],dtype=bool)
    for i in range(len(mask)-sustain+1):
        if mask[i:i+sustain].all():
            return {'observed':True,'time':curve[i]['step'],'confirmation_time':curve[i+sustain-1]['step'],'censor_time':None}
    return {'observed':False,'time':None,'confirmation_time':None,'censor_time':curve[-1]['step']}

def transitions(curve,test_level=.95,sustain=3,min_lag=1000):
    mem=threshold(curve,'train_accuracy',.99,sustain)
    gen=threshold(curve,'test_accuracy',test_level,sustain)
    lag=None;stable=None
    if mem['observed'] and gen['observed']:
        lag=gen['time']-mem['time']
        stable=all(r['train_accuracy']>=.99 for r in curve if mem['time']<=r['step']<=gen['confirmation_time']) if lag>=0 else False
    grok=bool(lag is not None and lag>=min_lag and stable)
    lower=None
    if mem['observed'] and not gen['observed']:
        lower=curve[-1]['step']-(sustain-1)*100-mem['time']
    return {'memorization':mem,'generalization':gen,'lag':lag,'lag_lower_bound_exclusive':lower,'memorization_retained_until_generalization_confirmation':stable,'delayed_grokking':grok,'classification':'observed' if grok else ('not_delayed' if mem['observed'] and gen['observed'] else 'not_observed_censored'),'generalization_level':test_level,'sustain':sustain,'minimum_lag':min_lag}

def endpoint_metrics(z,y,tr,te):
    answer={}
    for name,ix in [('train',tr),('test',te)]:
        scores=z[ix].astype(np.float64)
        answer[name+'_accuracy']=float(np.mean(np.argmax(scores,axis=1)==y[ix]))
        answer[name+'_loss']=float(np.mean(logsumexp(scores,axis=1)-scores[np.arange(len(ix)),y[ix]]))
    return answer

def uncertainty(values):
    a=np.array(values,dtype=np.float64);n=len(a)
    if not n:return None
    mean=float(a.mean())
    if n<2:return {'n':n,'mean':mean,'sample_sd':None,'ci95':None,'exact_signflip_two_sided_p':None}
    sd=float(a.std(ddof=1));se=sd/np.sqrt(n);critical=float(student_t.ppf(.975,n-1))
    randomized=[float(np.mean(a*np.array(s))) for s in itertools.product([-1,1],repeat=n)]
    prob=float(np.mean(np.abs(randomized)>=abs(mean)-1e-14))
    return {'n':n,'mean':mean,'sample_sd':sd,'standard_error':float(se),'t_df':n-1,'t_critical':critical,'ci95':[float(mean-critical*se),float(mean+critical*se)],'exact_signflip_two_sided_p':prob}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='evidence/confirmation');parser.add_argument('--out',required=True);parser.add_argument('--verify-checkpoints',action='store_true');parser.add_argument('--compare')
    args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    paths=sorted(Path(args.root).glob('attempts/*/measurement.json'))
    runs=[json.loads(p.read_text()) for p in paths]
    runs.sort(key=lambda r:(r['seed'],r['weight_decay']))
    assert len({(r['seed'],r['weight_decay']) for r in runs})==len(runs),'Duplicate endpoints'
    protocol=Path('campaigns/modular-addition/protocol.json');config=json.loads(protocol.read_text())
    raw_paths=set([str(protocol),'campaigns/modular-addition/PROTOCOL.md','build/engine.dylib','campaigns/modular-addition/materials/engine.dylib'])
    assert sha('build/engine.dylib')==sha('campaigns/modular-addition/materials/engine.dylib')
    for p,digest in config['training_source_hashes'].items():assert sha(p)==digest
    raw_paths.update(config['training_code']);raw_paths.update(str(p) for p in paths)
    rows=[];checks=[];seen_initial={}
    if args.verify_checkpoints:
        import torch
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
    for run,path in zip(runs,sorted(paths,key=lambda p:(json.loads(p.read_text())['seed'],json.loads(p.read_text())['weight_decay']))):
        assert run['phase']=='confirmation' and run['updates']==100000 and run['device']=='cpu'
        completion=path.parent/'completed.json'
        receipt=json.loads(completion.read_text())
        assert receipt['status']=='succeeded' and receipt['ended_step']==100000
        for recorded,digest in receipt['outputs'].items():assert sha(recorded)==digest
        raw_paths.add(str(completion))
        for aid in run['attempt_chain']:
            adir=Path(args.root)/'attempts'/aid
            start=json.loads((adir/'started.json').read_text())
            assert start['protocol_sha256']==sha(protocol)
            assert start['source_hashes']==config['training_source_hashes']
            assert start['configuration']['seed']==run['seed'] and start['configuration']['weight_decay']==run['weight_decay']
            raw_paths.add(str(adir/'started.json'))
            if (adir/'resume.json').exists():
                resume=json.loads((adir/'resume.json').read_text())
                for key in ('checkpoint','curve'):
                    assert sha(resume[key])==resume[key+'_sha256'];raw_paths.add(resume[key])
                raw_paths.add(str(adir/'resume.json'))
        for key in ['arrays','weights','curve_path','initial_weights','checkpoint','configuration']:raw_paths.add(run[key])
        assert sha(run['initial_weights'])==run['initial_weights_sha256']
        if run['seed'] in seen_initial:assert seen_initial[run['seed']]==run['initial_weights_sha256']
        seen_initial[run['seed']]=run['initial_weights_sha256']
        assert run['source_revision']==config['training_source_revision']
        with np.load(run['arrays'],allow_pickle=False) as data:
            pairs=data['pairs'];y=data['labels'];tr=data['train_indices'];te=data['test_indices'];z=data['logits'];pred=data['predictions']
        expected=np.array([(a,b) for a in range(97) for b in range(97)],dtype=np.int32)
        assert pairs.shape==(9409,2) and np.array_equal(pairs,expected)
        assert np.array_equal(y,(pairs[:,0]+pairs[:,1])%97)
        assert np.issubdtype(pairs.dtype,np.integer) and np.issubdtype(y.dtype,np.integer)
        order=np.random.default_rng(run['seed']).permutation(9409)
        assert np.array_equal(tr,order[:2822]) and np.array_equal(te,order[2822:])
        assert not set(tr)&set(te) and len(set(np.r_[tr,te]))==9409
        assert z.shape==(9409,97) and z.dtype==np.float32 and np.isfinite(z).all()
        assert np.array_equal(pred,z.argmax(1))
        computed=endpoint_metrics(z,y,tr,te)
        error=max(abs(computed[k]-run['metrics'][k]) for k in computed);assert error<1e-10,error
        curve=run['curve'];assert isinstance(curve,list) and curve==json.loads(Path(run['curve_path']).read_text())
        assert [c['step'] for c in curve]==list(range(0,100001,100))
        for row in curve:
            assert all(np.isfinite(row[k]) for k in computed)
            assert 0<=row['train_accuracy']<=1 and 0<=row['test_accuracy']<=1
        assert max(abs(curve[-1][k]-computed[k]) for k in computed)<1e-10
        with np.load(run['initial_weights'],allow_pickle=False) as initial:
            assert np.array_equal(initial['pairs'],pairs) and np.array_equal(initial['labels'],y)
            assert np.array_equal(initial['train_indices'],tr) and np.array_equal(initial['test_indices'],te)
            init_logits=np.maximum(initial['input_weight'][:,pairs[:,0]].T+initial['input_weight'][:,pairs[:,1]+97].T,0)@initial['output_weight'].T
        initial_metrics=endpoint_metrics(init_logits,y,tr,te)
        assert max(abs(curve[0][k]-initial_metrics[k]) for k in computed)<2e-7
        with np.load(run['weights'],allow_pickle=False) as weights:
            w1=weights['input_weight'];w2=weights['output_weight']
        assert w1.shape==(128,194) and w2.shape==(97,128) and w1.dtype==w2.dtype==np.float32
        x=np.eye(97,dtype=np.float32)[pairs].reshape(9409,194)
        dense=np.maximum(x@w1.T,0)@w2.T
        dense_error=float(np.max(np.abs(dense-z)))
        assert np.allclose(dense,z,atol=3e-5,rtol=3e-5),(run['seed'],dense_error)
        assert np.array_equal(dense.argmax(1),pred)
        checkpoint_error=None
        if args.verify_checkpoints:
            with np.load(run['checkpoint'],allow_pickle=False) as cp:
                assert int(cp['step'])==100000
                assert np.array_equal(cp['u'].T,w1) and np.array_equal(cp['v'],w2)
                assert all(np.isfinite(cp[k]).all() for k in ('m1','q1','m2','q2'))
                model=torch.nn.Sequential(torch.nn.Linear(194,128,bias=False),torch.nn.ReLU(),torch.nn.Linear(128,97,bias=False))
                model.load_state_dict({'0.weight':torch.tensor(cp['u'].T.copy()),'2.weight':torch.tensor(cp['v'])})
                with torch.no_grad():reloaded=model(torch.tensor(x)).numpy()
            checkpoint_error=float(np.max(np.abs(reloaded-z)))
            assert np.allclose(reloaded,z,atol=3e-5,rtol=3e-5)
            assert np.array_equal(reloaded.argmax(1),pred)
        transition=transitions(curve)
        sensitivity={}
        for level in (.90,.99):sensitivity[f'generalization_{level}']=transitions(curve,test_level=level)
        for sustain in (1,5):sensitivity[f'sustain_{sustain}']=transitions(curve,sustain=sustain)
        for delay in (500,5000):sensitivity[f'lag_{delay}']=transitions(curve,min_lag=delay)
        rows.append({'seed':run['seed'],'weight_decay':run['weight_decay'],'updates':100000,**computed,'transition':transition,'sensitivity':sensitivity,'evidence':str(path)})
        checks.append({'seed':run['seed'],'weight_decay':run['weight_decay'],'all_9409_labels_checked':True,'partition_exact_and_disjoint':True,'metrics_max_abs_error':error,'dense_numpy_logits_max_abs_error':dense_error,'dense_predictions_exact':True,'checkpoint_torch_logits_max_abs_error':checkpoint_error,'checkpoint_predictions_exact':True if args.verify_checkpoints else None,'curve_evaluations':len(curve)})
    paired=[]
    for seed in (1001,1002,1003,1004):
        group={r['weight_decay']:r for r in rows if r['seed']==seed}
        if set(group)=={0,1}:
            paired.append({'seed':seed,'test_accuracy_difference':group[1]['test_accuracy']-group[0]['test_accuracy'],'test_loss_difference':group[1]['test_loss']-group[0]['test_loss']})
    complete=len(runs)==8
    results={'task_id':'modular-addition','execution_status':'complete' if complete else 'partial','protocol_sha256':sha(protocol),'independent_unit':'seed','n_complete_pairs':len(paired),'runs':rows,'paired_differences':paired,'paired_uncertainty':{key:uncertainty([r[key] for r in paired]) for key in ('test_accuracy_difference','test_loss_difference')},'uncertainty_scope':'Approximate paired t intervals over four seeds; finite seed sample, not uncertainty over architectures or tasks. Sign-flip p values are descriptive, with minimum possible two-sided p=0.125 for n=4.'}
    dump(out/'results.json',results);dump(out/'verification.json',{'checks':checks,'complete_cells':len(checks),'checkpoint_backend':'independent dense PyTorch CPU' if args.verify_checkpoints else 'not requested'})
    dump(out/'measurements.json',{'format':'research-measurements-v1','task_id':'modular-addition','protocol':str(protocol),'runs':runs})
    raw_manifest={'format':'immutable-raw-manifest-v1','eligible_final_runs':[str(p) for p in paths],'files':[ref(p) for p in sorted(raw_paths)],'exclusions':[{'path':str(p),'reason':'pilot seed 61, qualification only; never an independent confirmation seed'} for p in sorted(Path('evidence').glob('pilot-*'))]}
    dump(out/'raw-manifest.json',raw_manifest)
    with (out/'per-seed-results.csv').open('w',newline='') as stream:
        fields=['seed','weight_decay','updates','train_accuracy','test_accuracy','train_loss','test_loss','memorization_time','generalization_time','lag','generalization_censored','delayed_grokking']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for r in rows:
            t=r['transition'];writer.writerow({**{k:r[k] for k in fields[:7]},'memorization_time':t['memorization']['time'],'generalization_time':t['generalization']['time'],'lag':t['lag'],'generalization_censored':not t['generalization']['observed'],'delayed_grokking':t['delayed_grokking']})
    with (out/'paired-differences.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['seed','test_accuracy_difference','test_loss_difference']);writer.writeheader();writer.writerows(paired)
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.hashsalt']='modadd-v1'
    for metric in ('accuracy','loss'):
        fig,axes=plt.subplots(2,4,figsize=(14,6),sharex=True,sharey=True)
        for run in runs:
            ax=axes[run['weight_decay'],run['seed']-1001];curve=run['curve'];steps=[c['step'] for c in curve]
            ax.plot(steps,[c['train_'+metric] for c in curve],label='Train',color='#277da1',lw=1)
            ax.plot(steps,[c['test_'+metric] for c in curve],label='Held-out',color='#e76f51',lw=1)
            ax.set_xscale('symlog',linthresh=1000);ax.set_title(f"Seed {run['seed']}, decay {run['weight_decay']}")
            if metric=='accuracy':
                ax.set_ylim(-.02,1.03);ax.axhline(.95,color='gray',ls=':',lw=.5)
            else:ax.set_yscale('symlog',linthresh=.001)
            ax.grid(alpha=.2);ax.set_xlabel('Optimizer updates')
        axes[0,0].legend();axes[0,0].set_ylabel(metric.title());axes[1,0].set_ylabel(metric.title())
        fig.suptitle('Individual modular-addition learning curves; symlog update axis')
        fig.tight_layout();fig.savefig(out/f'learning-{metric}.png',dpi=160);fig.savefig(out/f'learning-{metric}.svg',metadata={'Date':None});plt.close(fig)
    if args.compare:
        other=Path(args.compare)
        comparison={name:sha(out/name)==sha(other/name) for name in ('results.json','per-seed-results.csv','paired-differences.csv','measurements.json','raw-manifest.json')}
        assert all(comparison.values()),comparison
        dump(out/'recomputation-comparison.json',comparison)
    print(json.dumps({'complete_cells':len(runs),'n_complete_pairs':len(paired),'paired_uncertainty':results['paired_uncertainty'],'output':str(out)},indent=2))

if __name__=='__main__':main()
