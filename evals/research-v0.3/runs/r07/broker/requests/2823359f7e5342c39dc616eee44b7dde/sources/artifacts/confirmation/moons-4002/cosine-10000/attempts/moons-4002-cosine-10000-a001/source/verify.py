"""Independent metric arithmetic and saved-weight regeneration (no retraining)."""
import argparse
import json
from pathlib import Path
import numpy as np
import runner as r
from common import ROOT, CAMPAIGN, ref, sha, write, named_hash, array_hash

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--measurements',default='analysis/measurements.json')
    parser.add_argument('--analysis',default='analysis')
    parser.add_argument('--reanalysis',default='reanalysis')
    parser.add_argument('--out',default='verification')
    args=parser.parse_args()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=False)
    r.libraries();torch=r.torch
    measurements=json.loads((ROOT/args.measurements).read_text())
    checks=[];max_metric=0.;max_sample=0.;source=sha(ROOT/'study/science.py')
    assert source==sha(ROOT/'inputs/materials/prior-study/science.py')
    theta=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    directions=np.stack((np.cos(theta),np.sin(theta)),axis=0)
    angles=np.arange(8)*2*np.pi/8
    centers=2*np.stack((np.cos(angles),np.sin(angles)),axis=1)
    coeff={k:torch.tensor(v,dtype=torch.float32,device='mps') for k,v in r.schedule().items()}
    for cell in measurements['runs']:
        assert cell['device']=='mps'
        arrays=np.load(ROOT/cell['arrays'],allow_pickle=False)
        weights=np.load(ROOT/cell['weights'],allow_pickle=False)
        noise=torch.tensor(arrays['generation_noise'],device='mps')
        regenerated={};details={}
        for variant in ('raw','ema099','ema0999'):
            # This metric path does not call science.sliced_wasserstein.
            x=arrays[variant].astype(np.float64);y=arrays['heldout'].astype(np.float64)
            sw=float(np.mean(np.abs(np.sort(x@directions,axis=0)-np.sort(y@directions,axis=0))))
            err=abs(sw-cell['metrics'][variant]['sw1']);max_metric=max(max_metric,err)
            assert err<1e-12
            if cell['dataset']=='gmm8':
                dist2=((x[:,None,:]-centers[None,:,:])**2).sum(axis=2)
                nearest=dist2.argmin(axis=1)
                valid=dist2[np.arange(len(x)),nearest]<=.45**2
                counts=np.bincount(nearest[valid],minlength=8)
                expected=cell['metrics'][variant]
                assert counts.tolist()==expected['mode_counts']
                assert int((counts>=21).sum())==expected['covered_modes']
                assert float(valid.mean())==expected['inlier_fraction']
            model=r.Denoiser().to('mps');r.load_state(model,weights,variant+'__')
            model.eval()
            regenerated[variant]=r.draw(model,noise,coeff)
            sample_err=float(np.max(np.abs(regenerated[variant]-arrays[variant])))
            max_sample=max(max_sample,sample_err)
            assert sample_err<=1e-6
            details[variant]={'independent_sw1':sw,'sw1_abs_error':err,'regenerated_sample_max_abs_error':sample_err}
        name=f"{cell['dataset']}-{cell['seed']}-{cell['schedule']}-{cell['updates']}.npz"
        np.savez(out/name,**regenerated)
        checks.append({'dataset':cell['dataset'],'seed':cell['seed'],'schedule':cell['schedule'],
                       'updates':cell['updates'],'variants':details,'regenerated':ref(out/name),
                       'weights':ref(ROOT/cell['weights']),'retained_samples':ref(ROOT/cell['arrays'])})
        print(json.dumps({'verified':name,'max_sample_error_so_far':max_sample}),flush=True)
    # Seed-level uncertainty and contrast arithmetic checked separately from analyzer.
    summary=json.loads((ROOT/args.analysis/'summary.json').read_text())
    for collection in ('effects','absolute_sw1','coverage'):
        for e in summary[collection]:
            vals=np.array(e['values'],dtype=float)
            assert abs(e['mean']-float(vals.sum()/len(vals)))<1e-12
            if len(vals)==4:
                se=float(np.sqrt(np.sum((vals-vals.mean())**2)/3)/2)
                radius=3.182446305284263*se
                assert np.allclose(e['ci95'],[vals.mean()-radius,vals.mean()+radius],atol=1e-12,rtol=0)
    compare={}
    for name in ('measurements.json','summary.json','contrasts.json','seed-level.json','paired-differences.csv','main-figure.png','main-figure.pdf'):
        a=ROOT/args.analysis/name;b=ROOT/args.reanalysis/name
        compare[name]={'original_sha256':sha(a),'reanalysis_sha256':sha(b),'equal':a.read_bytes()==b.read_bytes()}
        assert compare[name]['equal'],name
    freeze=json.loads((CAMPAIGN/'confirmation-freeze.json').read_text())
    starts=[]
    for path in (ROOT/'artifacts/confirmation').glob('*/*/attempts/*/started.json'):
        start=json.loads(path.read_text())
        assert start['started_at']>freeze['created_at']
        for name,digest in freeze['scientific_sources'].items():
            assert start['source_hashes'][name]==digest
        starts.append(ref(path))
    result={'passed':True,'cells_verified':len(checks),'states_regenerated':len(checks)*3,
        'max_metric_abs_error':max_metric,'max_sample_abs_error':max_sample,
        'regeneration_tolerance':1e-6,'independent_metric_tolerance':1e-12,
        'unchanged_reference_science_sha256':source,'checks':checks,'separate_reanalysis':compare,
        'source_and_freeze_checks':starts,'scope':'All retained confirmation cells; independent metric arithmetic, seed-level intervals, byte-identical separate analysis, actual reference sampling from saved weights. No retraining in this check.'}
    write(out/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_and_freeze_checks','separate_reanalysis')},indent=2))

if __name__=='__main__':main()
