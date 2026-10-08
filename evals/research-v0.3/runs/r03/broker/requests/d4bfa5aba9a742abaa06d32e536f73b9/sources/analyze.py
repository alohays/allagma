"""Recompute every reported numerical result from retained scientific evidence.

Run via the local broker. No training is performed here.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import math

import numpy as np
from scipy.stats import t

def dump(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def metrics(z,y,train,test):
    z=z.astype(np.float64)
    pred=z.argmax(1)
    mx=z.max(1)
    loss=mx+np.log(np.exp(z-mx[:,None]).sum(1))-z[np.arange(len(y)),y]
    ans={}
    for name,idx in [('train',train),('test',test)]:
        ans[name+'_accuracy']=float(np.mean(pred[idx]==y[idx]))
        ans[name+'_loss']=float(np.mean(loss[idx]))
    return ans

def onset(curve,field,threshold,n):
    for i in range(len(curve)-n+1):
        if all(r[field]>=threshold for r in curve[i:i+n]):
            return dict(observed=True,onset_step=curve[i]['step'],confirmed_step=curve[i+n-1]['step'],
                        censor_step=None,index=i)
    return dict(observed=False,onset_step=None,confirmed_step=None,censor_step=curve[-1]['step'],index=None)

def transition(curve,test_threshold=.95,n=3,delay=1000):
    m=onset(curve,'train_accuracy',.99,n)
    g=onset(curve,'test_accuracy',test_threshold,n)
    lag=None
    persistence=None
    below=None
    grok=False
    if m['observed'] and g['observed']:
        lag=g['onset_step']-m['onset_step']
        below=curve[m['index']]['test_accuracy']<test_threshold
        persistence=g['index']>=m['index'] and all(r['train_accuracy']>=.99 for r in curve[m['index']:g['index']+n])
        grok=lag>=delay and below and persistence
    for o in [m,g]: o.pop('index')
    return dict(memorization=m,generalization=g,lag_updates=lag,
                train_persistent=persistence,test_below_threshold_at_memorization=below,
                delayed_grokking=bool(grok),test_threshold=test_threshold,
                consecutive_evaluations=n,minimum_delay_updates=delay,
                planned_horizon=100000,observed_horizon=curve[-1]['step'])

def uncertainty(values):
    a=np.asarray(values,dtype=float)
    n=len(a)
    if not n:
        return dict(n=0,mean=None,sd=None,ci95=None,exact_sign_flip_p=None)
    mean=float(a.mean())
    sd=float(a.std(ddof=1)) if n>1 else None
    half=float(t.ppf(.975,n-1)*sd/math.sqrt(n)) if n>1 else None
    flips=[abs(np.mean(a*np.asarray(signs))) for signs in itertools.product([-1,1],repeat=n)]
    p=float(np.mean(np.asarray(flips)>=abs(mean)-1e-14))
    return dict(n=n,mean=mean,sd=sd,ci95=None if half is None else [mean-half,mean+half],
        exact_sign_flip_p=p,method='Student t 95% interval across independent paired seeds; paired absolute-mean sign flips',
        degrees_of_freedom=n-1,sign_flip_count=2**n,
        caveat='Four seeds give coarse inference; t intervals assume approximately normal seed differences.')

def receipts():
    entries=[]
    for path in sorted(Path('.compute/requests').glob('*.json')):
        request=json.loads(path.read_text())
        response=Path('.compute/responses')/(request['request_id']+'.json')
        if not response.exists(): continue
        result=json.loads(response.read_text())
        entries.append(dict(request=request,response=result,request_path=str(path),response_path=str(response),
            stdout_path=str(response.with_name(response.stem+'-stdout.txt')),
            stderr_path=str(response.with_name(response.stem+'-stderr.txt'))))
    return sorted(entries,key=lambda e:e['response']['result'].get('ended_at',''))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',default='artifacts')
    parser.add_argument('--out',default='analysis')
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    root=Path(args.data)
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    runs=[]
    incomplete=[]
    missing=[]
    checks=[]
    curves={}
    attempt_records=receipts()
    expected_pairs=np.stack(np.meshgrid(np.arange(97),np.arange(97),indexing='ij'),axis=-1).reshape(-1,2)
    protocol=json.loads(Path('protocol.json').read_text())
    if args.verify:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        xx=torch.from_numpy(np.concatenate([np.eye(97,dtype=np.float32)[expected_pairs[:,0]],
                    np.eye(97,dtype=np.float32)[expected_pairs[:,1]]],axis=1))
    for seed in protocol['confirmation_seeds']:
        pair_initial=[]
        pair_split=[]
        for wd in protocol['weight_decays']:
            folder=root/'confirmation'/f'seed_{seed}_wd_{wd}'
            if not (folder/'endpoint.json').exists():
                missing.append(dict(seed=seed,weight_decay=wd))
                continue
            ep=json.loads((folder/'endpoint.json').read_text())
            config=json.loads((folder/'config.json').read_text())
            curve=json.loads((folder/'curve.json').read_text())
            arrays=np.load(folder/'arrays.npz',allow_pickle=False)
            weights=np.load(folder/'weights.npz',allow_pickle=False)
            initial=np.load(folder/'initial_weights.npz',allow_pickle=False)
            p,y,train,test,z,pred=[arrays[k] for k in ['pairs','labels','train_indices','test_indices','logits','predictions']]
            assert np.array_equal(p,expected_pairs)
            assert np.array_equal(y,(expected_pairs[:,0]+expected_pairs[:,1])%97)
            assert len(train)==2822 and len(test)==6587
            assert np.array_equal(np.sort(np.r_[train,test]),np.arange(9409))
            assert np.intersect1d(train,test).size==0
            perm=np.random.Generator(np.random.PCG64(seed)).permutation(9409)
            assert np.array_equal(train,perm[:2822]) and np.array_equal(test,perm[2822:])
            partition=np.load(folder/'partition.npz',allow_pickle=False)
            for key in ['pairs','labels','train_indices','test_indices']:
                assert np.array_equal(partition[key],arrays[key])
            assert z.shape==(9409,97) and z.dtype==np.float32 and np.isfinite(z).all()
            assert np.array_equal(pred,z.argmax(1))
            assert curve[0]['step']==0 and curve[-1]['step']==ep['updates']
            steps=np.array([r['step'] for r in curve])
            assert np.all(np.diff(steps)==100)
            assert ep['updates']<=100000
            assert config['source_revision']==sha('study.py')
            assert config['protocol_sha256']==sha('protocol.json')
            assert config['initial_weights_sha256']==sha(folder/'initial_weights.npz')
            assert weights['input_weight'].shape==(128,194) and weights['output_weight'].shape==(97,128)
            assert all(weights[k].dtype==np.float32 for k in weights.files)
            recomputed=metrics(z,y,train,test)
            deltas={k:abs(recomputed[k]-curve[-1][k]) for k in recomputed}
            for k,diff in deltas.items():
                tol=1e-7 if 'accuracy' in k else max(3e-6,abs(recomputed[k])*2e-6)
                assert diff<tol,(seed,wd,k,diff,tol)
            # This NumPy implementation uses one-hot sparsity and differs from
            # the dense PyTorch training forward pass.
            hidden=np.maximum(weights['input_weight'][:,p[:,0]].T+weights['input_weight'][:,97+p[:,1]].T,0)
            independent=hidden@weights['output_weight'].T
            np_error=float(np.max(np.abs(independent-z)))
            np_agree=bool(np.array_equal(independent.argmax(1),pred))
            assert np.allclose(independent,z,atol=1e-4,rtol=5e-5)
            assert np_agree
            ck_error=None
            if args.verify:
                ck=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False)
                assert ck['step']==ep['updates']
                assert ck['curve']==curve
                assert ck['config']==config
                pg=ck['optimizer']['param_groups'][0]
                assert pg['lr']==.001 and tuple(pg['betas'])==(.9,.98) and pg['eps']==1e-8 and pg['weight_decay']==wd
                assert all(float(v['step'])==ep['updates'] for v in ck['optimizer']['state'].values())
                model=torch.nn.Sequential(torch.nn.Linear(194,128,bias=False),torch.nn.ReLU(),torch.nn.Linear(128,97,bias=False))
                model.load_state_dict({'0.weight':ck['model']['input.weight'],'2.weight':ck['model']['output.weight']})
                with torch.no_grad(): reload_z=model(xx).numpy()
                ck_error=float(np.max(np.abs(reload_z-z)))
                assert np.array_equal(reload_z,z),ck_error
                for key,ckkey in [('input_weight','input.weight'),('output_weight','output.weight')]:
                    assert np.array_equal(weights[key],ck['model'][ckkey].numpy())
                # Initialization is recreated from the documented RNG and constructor.
                torch.manual_seed(seed)
                first=torch.nn.Linear(194,128,bias=False)
                second=torch.nn.Linear(128,97,bias=False)
                assert np.array_equal(initial['input_weight'],first.weight.detach().numpy())
                assert np.array_equal(initial['output_weight'],second.weight.detach().numpy())
            attempt=next((a['request']['request_id'] for a in reversed(attempt_records) if a['request']['label']==ep['attempt_label']),None)
            assert attempt is not None,ep['attempt_label']
            trace=[a['request']['request_id'] for a in attempt_records
                if a['request']['category']=='compute' and 'study.py' in a['request']['argv']
                and '--seed' in a['request']['argv'] and '--wd' in a['request']['argv']
                and a['request']['argv'][a['request']['argv'].index('--seed')+1]==str(seed)
                and a['request']['argv'][a['request']['argv'].index('--wd')+1]==str(wd)
                and '--output' not in a['request']['argv']]
            entry=dict(seed=seed,weight_decay=wd,updates=ep['updates'],phase='confirmation',device=config['device'],
                arrays=str(folder/'arrays.npz'),weights=str(folder/'weights.npz'),curve=str(folder/'curve.json'),
                checkpoint=str(folder/'checkpoint.pt'),initial_weights=str(folder/'initial_weights.npz'),
                partition=str(folder/'partition.npz'),configuration=str(folder/'config.json'),
                metrics=recomputed,initial_weights_sha256=config['initial_weights_sha256'],
                source_revision=config['source_revision'],attempt_id=attempt,
                transition=transition(curve),complete=ep['updates']==100000)
            (runs if entry['complete'] else incomplete).append(entry)
            curves[(seed,wd)]=curve
            pair_initial.append((initial['input_weight'].copy(),initial['output_weight'].copy(),config['initial_weights_sha256']))
            pair_split.append((train.copy(),test.copy()))
            checks.append(dict(seed=seed,weight_decay=wd,updates=ep['updates'],evaluations=len(curve),
                max_endpoint_metric_abs_differences=deltas,numpy_logits_max_abs_error=np_error,
                numpy_all_9409_predictions_equal=np_agree,pytorch_reload_logits_max_abs_error=ck_error,
                checkpoint_reload='all logits bitwise equal' if args.verify else 'not requested',
                partition_and_initialization='passed'))
        if len(pair_initial)==2:
            assert pair_initial[0][2]==pair_initial[1][2]
            assert all(np.array_equal(a,b) for a,b in zip(pair_initial[0][:2],pair_initial[1][:2]))
            assert all(np.array_equal(a,b) for a,b in zip(pair_split[0],pair_split[1]))
    paired=[]
    for seed in protocol['confirmation_seeds']:
        both=[r for r in runs if r['seed']==seed]
        if len(both)==2:
            a=next(r for r in both if r['weight_decay']==0)
            b=next(r for r in both if r['weight_decay']==1)
            paired.append(dict(seed=seed,test_accuracy_difference=b['metrics']['test_accuracy']-a['metrics']['test_accuracy'],
                test_loss_difference=b['metrics']['test_loss']-a['metrics']['test_loss']))
    effects={metric:uncertainty([p[metric+'_difference'] for p in paired]) for metric in ['test_accuracy','test_loss']}
    sensitivity=[]
    for (seed,wd),curve in curves.items():
        for threshold,n,delay in itertools.product([.9,.95,.99],[1,3,5],[500,1000,5000]):
            sensitivity.append(dict(seed=seed,weight_decay=wd,**transition(curve,threshold,n,delay)))
    measurement=dict(format='research-measurements-v1',task_id='modular-addition',protocol='protocol.json',
        runs=runs,incomplete_runs=incomplete,missing_runs=missing)
    dump(out/'measurements.json',measurement)
    summary=dict(execution_status='complete' if len(runs)==8 else 'partial',planned_runs=8,
        completed_runs=len(runs),incomplete_runs=len(incomplete),missing_runs=missing,
        paired_differences=paired,effects=effects,primary_transitions=[dict(seed=r['seed'],weight_decay=r['weight_decay'],
            **r['transition']) for r in runs+incomplete],
        primary_memorization_count=sum(r['transition']['memorization']['observed'] for r in runs),
        primary_generalization_count=sum(r['transition']['generalization']['observed'] for r in runs),
        primary_delayed_grokking_count=sum(r['transition']['delayed_grokking'] for r in runs),
        analysis_source_sha256=sha(__file__),protocol_sha256=sha('protocol.json'))
    dump(out/'results.json',summary)
    dump(out/'sensitivity.json',sensitivity)
    dump(out/'verification.json',dict(status='passed',checks=checks,paired_partitions_and_initial_weights='passed',
        independent_label_and_split_checks='all 9409 labels and all eight partitions',
        replay_scope='all eight final checkpoints; pilot 10+reload+10 optimizer continuity; no second full training run'))
    dump(out/'attempts.json',attempt_records)
    with (out/'per_seed_results.csv').open('w',newline='') as f:
        fields=['seed','weight_decay','updates','train_accuracy','test_accuracy','train_loss','test_loss',
            'memorization_onset','generalization_onset','memorization_censor','generalization_censor','lag_updates','delayed_grokking']
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for r in sorted(runs+incomplete,key=lambda r:(r['seed'],r['weight_decay'])):
            tr=r['transition']
            w.writerow(dict(seed=r['seed'],weight_decay=r['weight_decay'],updates=r['updates'],**r['metrics'],
                memorization_onset=tr['memorization']['onset_step'],generalization_onset=tr['generalization']['onset_step'],
                memorization_censor=tr['memorization']['censor_step'],generalization_censor=tr['generalization']['censor_step'],
                lag_updates=tr['lag_updates'],delayed_grokking=tr['delayed_grokking']))
    figure(curves,out)
    print(json.dumps(summary,indent=2))

def figure(curves,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(4,2,figsize=(11,12),sharex=True,layout='constrained')
    colors={0:'#b85226',1:'#176c9e'}
    for i,seed in enumerate([1001,1002,1003,1004]):
        for wd in [0,1]:
            curve=curves.get((seed,wd))
            if curve is None: continue
            steps=[r['step'] for r in curve]
            for partition,ls in [('train',':'),('test','-')]:
                axes[i,0].plot(steps,[r[partition+'_accuracy'] for r in curve],ls,color=colors[wd],
                    label=f'WD {wd}, {partition}',linewidth=1.2)
                axes[i,1].plot(steps,np.maximum([r[partition+'_loss'] for r in curve],1e-9),ls,
                    color=colors[wd],label=f'WD {wd}, {partition}',linewidth=1.2)
        axes[i,0].axhline(.95,color='gray',lw=.7,ls='--')
        axes[i,0].axhline(.99,color='gray',lw=.7,ls=':')
        axes[i,0].set(ylim=(-.02,1.02),ylabel=f'Seed {seed}\nAccuracy',xlim=(0,100000))
        axes[i,1].set(yscale='log',ylabel='Cross-entropy (log scale)',xlim=(0,100000))
        axes[i,1].set_ylim(bottom=1e-9)
        for ax in axes[i]: ax.grid(alpha=.15)
    axes[0,0].legend(loc='lower right',ncol=2,fontsize=8)
    axes[-1,0].set_xlabel('Optimizer updates')
    axes[-1,1].set_xlabel('Optimizer updates')
    fig.suptitle('Modular addition: individual paired learning curves\nDotted: train; solid: held out. Loss values below 1e-9 are plotted at 1e-9.',fontsize=12)
    fig.savefig(out/'learning_curves.png',dpi=170)
    fig.savefig(out/'learning_curves.pdf')
    plt.close(fig)

if __name__=='__main__':
    main()
