"""Recompute all endpoints and threshold analyses solely from retained evidence."""
import argparse
import itertools
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path("study").resolve()))
import numpy as np
from common import numpy_metrics,write_json,ref,sha

def transition(curve,key,threshold,persistence):
    for i in range(len(curve)-persistence+1):
        if all(row[key]>=threshold for row in curve[i:i+persistence]):
            return {'event':True,'time':curve[i]['step'],'confirmed_at':curve[i+persistence-1]['step'],
                    'censored':False,'censor_at':None}
    return {'event':False,'time':None,'confirmed_at':None,'censored':True,'censor_at':curve[-1]['step']}

def transitions(curve,threshold=.95,persistence=3,lag_min=1000,ratio_min=2):
    m=transition(curve,'train_accuracy',.99,persistence)
    g=transition(curve,'test_accuracy',threshold,persistence)
    lag=g['time']-m['time'] if m['event'] and g['event'] else None
    ratio=g['time']/m['time'] if m['event'] and g['event'] and m['time']>0 else None
    delayed=lag is not None and lag>=lag_min and g['time']>=ratio_min*m['time']
    return {'memorization':m,'generalization':g,'lag':lag,'time_ratio':ratio,
            'lag_lower_bound_if_generalization_censored':curve[-1]['step']-m['time'] if m['event'] and g['censored'] else None,
            'delayed_grokking_observed':bool(delayed),'observed_horizon':curve[-1]['step'],
            'definition':{'train_threshold':.99,'test_threshold':threshold,'persistence':persistence,'minimum_lag':lag_min,'minimum_time_ratio':ratio_min}}

def uncertainty(values):
    a=np.array(values,dtype=np.float64)
    n=len(a);mean=float(a.mean())
    sd=float(a.std(ddof=1)) if n>1 else None
    se=sd/np.sqrt(n) if n>1 else None
    ci=[mean-3.182446305*se,mean+3.182446305*se] if n==4 else None
    null=np.array([np.mean(a*np.array(s)) for s in itertools.product([-1,1],repeat=n)])
    p=float((np.abs(null)>=abs(mean)-1e-14).mean())
    return {'n_independent_seeds':n,'mean':mean,'sd':sd,'standard_error':se,
            'ci95_student_t':ci,'df':n-1,'paired_sign_flip_two_sided_p':p,
            'method':'Paired seed differences, Student t 95% interval df=3 for n=4; all 16 sign flips; small-n assumptions are fragile.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='evidence/confirmation')
    p.add_argument('--out',required=True)
    p.add_argument('--protocol',default='campaigns/c001/protocol.json')
    p.add_argument('--measurements',default='measurements.json')
    p.add_argument('--read-measurements',action='store_true')
    args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads(Path(args.protocol).read_text())
    if args.read_measurements:
        raw=json.loads(Path(args.measurements).read_text())
        selected=[json.loads(Path(r['result']).read_text()) for r in raw['runs']]
    else:
        candidates=[json.loads(f.read_text()) for f in sorted(Path(args.root).glob('*/result.json'))]
        selected=[]
        for seed in protocol['confirmation_seeds']:
            for wd in [0,1]:
                found=[r for r in candidates if r['seed']==seed and r['weight_decay']==wd and r['complete'] and r['updates']==100000]
                assert len(found)<=1,'Repeated executions cannot be additional seeds'
                selected+=found
    runs=[];refs=[];validation=[];rows=[];curves={}
    import torch
    from common import configure,model,inputs,state_hash
    configure()
    for r in selected:
        a=np.load(r['arrays'],allow_pickle=False); w=np.load(r['weights'],allow_pickle=False)
        curve=json.loads(Path(r['curve']).read_text())
        assert a['pairs'].shape==(9409,2) and a['logits'].shape==(9409,97)
        assert np.array_equal(a['pairs'],np.array([(i,j) for i in range(97) for j in range(97)]))
        labels=(a['pairs'][:,0]+a['pairs'][:,1])%97
        assert np.array_equal(labels,a['labels'])
        tr,te=a['train_indices'],a['test_indices']
        assert len(tr)==2822 and len(te)==6587 and len(np.unique(np.r_[tr,te]))==9409
        perm=np.random.default_rng(r['seed']).permutation(9409)
        assert np.array_equal(tr,perm[:2822]) and np.array_equal(te,perm[2822:])
        assert np.array_equal(a['predictions'],a['logits'].argmax(1)) and np.isfinite(a['logits']).all()
        metrics=numpy_metrics(a['logits'],labels,tr,te)
        metric_error=max(abs(metrics[k]-r['metrics'][k]) for k in metrics)
        assert all(np.isclose(metrics[k],r['metrics'][k],atol=1e-6,rtol=1e-6) for k in metrics),(r['seed'],metric_error)
        assert [c['step'] for c in curve]==list(range(0,100001,100))
        assert all(np.isclose(curve[-1][k],metrics[k],atol=1e-6,rtol=1e-6) for k in metrics)
        # Independent checkpoint reload and separately instantiated NPZ weight model.
        ck=torch.load(r['checkpoint'],map_location='cpu',weights_only=False)
        assert ck['step']==100000
        assert all(float(v['step'])==100000 for v in ck['optimizer']['state'].values())
        net=model(r['seed']);net.load_state_dict(ck['model'])
        npz_net=model(r['seed'])
        with torch.no_grad():
            npz_net[0].weight.copy_(torch.from_numpy(w['input_weight']))
            npz_net[2].weight.copy_(torch.from_numpy(w['output_weight']))
            z=net(inputs(a['pairs'])).numpy()
            zn=npz_net(inputs(a['pairs'])).numpy()
        assert np.array_equal(z,a['logits']) and np.array_equal(zn,a['logits'])
        # NumPy forward uses the one-hot identity; separate linear algebra and no torch model.
        nz=np.maximum(w['input_weight'][:,a['pairs'][:,0]].T+w['input_weight'][:,a['pairs'][:,1]+97].T,0)@w['output_weight'].T
        np_error=float(np.abs(nz-a['logits']).max())
        assert np.allclose(nz,a['logits'],atol=1e-4,rtol=1e-5)
        initial=np.load(r['initial_weights'],allow_pickle=False)
        net0=model(r['seed'])
        assert np.array_equal(initial['input_weight'],net0[0].weight.detach().numpy())
        assert np.array_equal(initial['output_weight'],net0[2].weight.detach().numpy())
        assert state_hash(net0)==r['initial_weights_sha256']
        primary=transitions(curve)
        sensitivity=[]
        for name,values in [('threshold',[.90,.99]),('persistence',[1,5]),('lag_min',[500,5000]),('ratio_min',[1,5])]:
            for value in values:
                sensitivity.append({'varied':name,'value':value,'outcome':transitions(curve,**{name:value})})
        row={'seed':r['seed'],'weight_decay':r['weight_decay'],'updates':r['updates'],
             'metrics':metrics,'transition':primary,'sensitivity':sensitivity}
        rows.append(row);curves[(r['seed'],r['weight_decay'])]=curve
        result_path=str(Path(r['arrays']).parent/'result.json')
        run={k:r[k] for k in ['seed','weight_decay','updates','phase','arrays','weights','curve','initial_weights_sha256','source_revision','attempt_id']}
        run.update({'metrics':metrics,'device':'cpu','result':result_path,'initial_weights':r['initial_weights'],'checkpoint':r['checkpoint']})
        runs.append(run)
        for path in [r['arrays'],r['weights'],r['curve'],r['initial_weights'],r['checkpoint'],result_path]: refs.append(ref(path))
        validation.append({'seed':r['seed'],'weight_decay':r['weight_decay'],'metric_max_abs_error':metric_error,
                           'checkpoint_reload_bitwise':True,'npz_reload_bitwise':True,'numpy_forward_max_abs_error':np_error,
                           'split_labels_initialization_optimizer_step_and_curve_checks':True})
    paired=[]
    for seed in protocol['confirmation_seeds']:
        group={r['weight_decay']:r for r in rows if r['seed']==seed}
        if len(group)<2:continue
        originals={r['weight_decay']:r for r in selected if r['seed']==seed}
        assert originals[0]['initial_weights_sha256']==originals[1]['initial_weights_sha256']
        a0=np.load(originals[0]['arrays'],allow_pickle=False);a1=np.load(originals[1]['arrays'],allow_pickle=False)
        assert np.array_equal(a0['train_indices'],a1['train_indices']) and np.array_equal(a0['test_indices'],a1['test_indices'])
        paired.append({'seed':seed,**{k:group[1]['metrics'][k]-group[0]['metrics'][k] for k in ['test_accuracy','test_loss']}})
    complete=len(rows)==8
    summary={'execution_status':'complete' if complete else 'partial','n_runs':len(rows),'n_paired_seeds':len(paired),
             'direction':'weight_decay_1_minus_weight_decay_0','per_seed':paired,
             'uncertainty':{k:uncertainty([r[k] for r in paired]) for k in ['test_accuracy','test_loss']} if len(paired)==4 else {},
             'memorized_count':sum(r['transition']['memorization']['event'] for r in rows),
             'generalized_count':sum(r['transition']['generalization']['event'] for r in rows),
             'delayed_grokking_count':sum(r['transition']['delayed_grokking_observed'] for r in rows),
             'protocol':args.protocol,'primary_definition':protocol['transitions'],
             'limitations':['Four independent paired seeds, not eight independent replicates','Finite 100000-update horizon','No extrapolation beyond this MLP or fixed optimizer','95% Student t intervals rely on small-sample distributional assumptions']}
    write_json(out/'per-seed.json',rows)
    write_json(out/'summary.json',summary)
    write_json(out/'validation.json',validation)
    write_json(out/'raw-manifest.json',{'raw':refs,'protocol':ref(args.protocol),
        'exclusions':[{'path':'evidence/pilot-a001','reason':'controlled interruption before training'},
                      {'path':'evidence/pilot-a002','reason':'pilot; MPS allocation failure'},
                      {'path':'evidence/pilot-a003','reason':'pilot seed 61, not confirmation'}]})
    if not args.read_measurements:
        write_json(args.measurements,{'format':'research-measurements-v1','task_id':'modular-addition','protocol':args.protocol,'runs':runs})
    if rows:
        os.environ.setdefault('MPLCONFIGDIR',str(Path('.tmp/matplotlib').resolve()))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(4,2,figsize=(12,13),sharex=True)
        for i,seed in enumerate(protocol['confirmation_seeds']):
            for wd,color in [(0,'#3f6cb5'),(1,'#c25527')]:
                cs=curves.get((seed,wd),[])
                if not cs:continue
                steps=[c['step'] for c in cs]
                for kind,style in [('train','-'),('test','--')]:
                    axes[i,0].plot(steps,[c[kind+'_accuracy'] for c in cs],style,color=color,label=f'decay {wd}, {kind}',linewidth=1)
                    axes[i,1].plot(steps,np.maximum([c[kind+'_loss'] for c in cs],1e-10),style,color=color,linewidth=1)
            axes[i,0].set(title=f'Seed {seed}',ylabel='Accuracy',ylim=(-.02,1.02))
            axes[i,0].axhline(.95,color='gray',linewidth=.5)
            axes[i,1].set(title=f'Seed {seed}',ylabel='Cross-entropy (nats)',yscale='log')
            for ax in axes[i]:ax.grid(alpha=.2)
        axes[0,0].legend(loc='best',fontsize=8)
        for ax in axes[-1]:ax.set_xlabel('Optimizer updates')
        fig.suptitle('Modular addition: individual training and held-out trajectories')
        fig.tight_layout()
        fig.savefig(out/'learning-curves.png',dpi=160)
        fig.savefig(out/'learning-curves.svg',metadata={'Date':None})
        plt.close(fig)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
