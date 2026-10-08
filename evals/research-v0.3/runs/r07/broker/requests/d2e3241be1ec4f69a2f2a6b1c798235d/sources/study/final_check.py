"""Final package audit: independent contrast algebra and complete provenance."""
import json
import math
from pathlib import Path
import re
import shutil
import sys
import numpy as np
import runner as r
from common import ROOT,CAMPAIGN,write,sha,named_hash,ref,now
from publish import manifest,interval
from workflow import account

def main():
    r.libraries();torch=r.torch
    old=json.loads((ROOT/'artifact-manifest.json').read_text())
    for item in old['files']:
        p=ROOT/item['path'];assert p.is_file() and not p.is_symlink()
        assert sha(p)==item['sha256'],item['path']
        assert p.stat().st_size==item['bytes']
    sub=json.loads((ROOT/'submission.json').read_text())
    assert sub['task_id']=='ema-schedule' and sub['execution_status']=='complete'
    for field in ('manuscript','review','artifact_manifest','measurements'):
        assert not Path(sub[field]).is_absolute() and (ROOT/sub[field]).is_file()
    for field in ('reproduce','recompute'):
        assert isinstance(sub[field]['argv'],list) and all(isinstance(x,str) for x in sub[field]['argv'])
        assert sub[field]['cwd']=='.'
    review=json.loads((ROOT/sub['review']).read_text())
    assert sha(ROOT/sub['manuscript'])==review['material']['sha256']
    summary=json.loads((ROOT/'analysis/summary.json').read_text())
    verification=json.loads((ROOT/'verification/verification.json').read_text())
    assert verification['passed'] and verification['states_regenerated']==96
    independent={(c['dataset'],c['seed'],c['schedule'],c['updates'],v):info['independent_sw1']
                 for c in verification['checks'] for v,info in c['variants'].items()}
    conditions=[('constant',5000),('cosine',5000),('constant',10000),('cosine',10000)]
    rows={'schedule_cosine_minus_constant':{5000:[-1,1,0,0],10000:[0,0,-1,1]},
          'duration_10000_minus_5000':{'constant':[-1,0,1,0],'cosine':[0,-1,0,1]},
          'interaction':[1,-1,-1,1]}
    checked_contrasts=0
    for collection in ('effects','absolute_sw1'):
        for entry in summary[collection]:
            ds=entry['dataset'];v=entry['variant'];seeds=entry['seeds']
            matrix=np.array([[independent[ds,s,p,u,v] for p,u in conditions] for s in seeds])
            if collection=='effects':
                matrix-=np.array([[independent[ds,s,p,u,'raw'] for p,u in conditions] for s in seeds])
            if entry['contrast']=='cell':
                expected=matrix[:,conditions.index((entry['schedule'],entry['updates']))]
            else:
                weights=rows[entry['contrast']]
                if isinstance(weights,dict):weights=weights[entry.get('schedule',entry.get('updates'))]
                expected=matrix@weights
            assert np.allclose(expected,entry['values'],atol=1e-12,rtol=0)
            checked_contrasts+=1
    # Check every table value as rendered against the verified analysis.
    report=(ROOT/'REPORT.md').read_text()
    for e in summary['effects']:
        assert interval(e) in report
    for e in summary['absolute_sw1']:
        if e['contrast']=='cell':assert f"{e['mean']:.6f}" in report
    for e in summary['coverage']:
        if e['metric']=='inlier_fraction':assert f"{e['mean']:.6f}" in report
    # Check the interpretation's exhaustive statements rather than selected cells.
    schedules=[e for e in summary['effects'] if e['contrast']=='schedule_cosine_minus_constant']
    assert all(e['mean']>0 for e in schedules)
    for e in schedules:
        if e['dataset']=='moons' and e['updates']==5000:assert e['ci95'][0]>0
        else:assert e['ci95'][0]<0<e['ci95'][1]
    assert all(e['ci95'][0]<0<e['ci95'][1] for e in summary['effects'] if e['contrast'] in ('interaction','duration_10000_minus_5000'))
    assert all(e['mean']<0 for e in summary['effects'] if e['contrast']=='interaction')
    # Reconstruct every input stream and initialization from the frozen rules.
    input_checks=[]
    coeff=r.schedule()
    for path in sorted((ROOT/'artifacts/confirmation').glob('*/inputs/metadata.json')):
        meta=json.loads(path.read_text());seed=meta['seed'];d=meta['dataset'];folder=path.parent
        torch.manual_seed(seed);initial=r.cpu_state(r.Denoiser())
        assert named_hash(initial)==meta['initial_weights_sha256']
        rng=np.random.default_rng(seed+100000)
        indices=rng.integers(0,100000,(10000,256)).astype(np.int32)
        noise=rng.normal(size=(10000,256,2)).astype(np.float32)
        times=rng.integers(0,100,(10000,256)).astype(np.int16)
        train=r.dataset(d,100000,seed+1000000)
        noisy=(coeff['sqrt_abar'][times,None]*train[indices]+coeff['sqrt_one_minus'][times,None]*noise).astype(np.float32)
        with np.load(folder/'training.npz',allow_pickle=False) as data:
            for name,expected in [('train',train),('indices',indices),('noise',noise),('timesteps',times),('noisy',noisy)]:
                assert np.array_equal(expected,data[name])
        with np.load(folder/'evaluation.npz',allow_pickle=False) as data:
            assert np.array_equal(data['heldout'],r.dataset(d,2048,seed+2000000))
            generation=np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32)
            assert np.array_equal(data['generation_noise'],generation)
        input_checks.append({'dataset':d,'seed':seed,'all_input_streams_exact':True,'initialization_exact':True})
    updates=0;traces=[]
    for path in sorted((ROOT/'artifacts/confirmation').glob('*/*/attempts/*/result.json')):
        result=json.loads(path.read_text());cfg=result['inputs'];folder=path.parent
        expected_updates=cfg['duration'];updates+=expected_updates
        with np.load(folder/'recovery.npz',allow_pickle=False) as recovery:
            assert int(recovery['completed_updates'])==expected_updates
            steps=[float(recovery[k]) for k in recovery.files if k.startswith('optimizer__') and k.endswith('__step')]
            assert steps and all(s==expected_updates for s in steps)
        trace=[json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
        assert trace[0]['step']==1 and trace[-1]['step']==expected_updates
        assert {t['step'] for t in trace}=={1,*range(500,expected_updates+1,500)}
        for t in trace:
            rate=.0003 if cfg['policy']=='constant' else .00015*(1+math.cos(math.pi*(t['step']-1)/cfg['duration']))
            assert abs(t['lr']-rate)<1e-15
        traces.append({'attempt_id':cfg['attempt_id'],'optimizer_updates':expected_updates,'trace_and_lr_verified':True})
    assert updates==200000
    freeze=json.loads((CAMPAIGN/'confirmation-freeze.json').read_text())
    for path,digest in freeze['scientific_sources'].items():assert sha(ROOT/path)==digest
    # Check all local links in the delivered English documents.
    checked_links=0
    for name in ('REPORT.md','REPRODUCE.md','CRITIQUE.md'):
        for target in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text()):
            if target.startswith(('http://','https://','#')):continue
            assert (ROOT/target.split('#')[0]).exists(),(name,target)
            checked_links+=1
    shutil.copyfile(ROOT/'evidence/resource-ledger.json',ROOT/'evidence/resource-ledger-at-report-r1.json')
    ledger=account()
    assert ledger['charged_seconds']['compute']<1800 and ledger['charged_seconds']['setup']<300
    assert ledger['compute_requests']<64
    result={'passed':True,'checked_at':now(),'submission':ref(ROOT/'submission.json'),'material':ref(ROOT/'REPORT.md'),
        'prior_manifest_files_verified':len(old['files']),'independently_verified_effect_and_absolute_contrast_rows':checked_contrasts,
        'report_tables_and_interpretation_verified':True,'independent_input_reconstruction':input_checks,
        'training_traces_and_final_optimizer_steps':traces,'confirmation_optimizer_updates':updates,
        'all_local_document_links_verified':checked_links,'frozen_scientific_sources_unchanged':True,
        'resource_usage_before_this_check':{k:v for k,v in ledger.items() if k!='receipts'},
        'limitations':['Current broker request receipt appears after this check; final authoritative resource accounting remains with the broker.','No independent scientific peer review.']}
    write(ROOT/'evidence/final-verification.json',result)
    manifest()
    inventory=json.loads((ROOT/'artifact-manifest.json').read_text())
    for item in inventory['files']:
        assert sha(ROOT/item['path'])==item['sha256']
    print(json.dumps({'passed':True,'manifest_files_verified':len(inventory['files']),
        'confirmation_cells':32,'states_regenerated':96,'confirmation_optimizer_updates':updates,
        'independently_verified_contrast_rows':checked_contrasts,
        'compute_seconds_before_final_check':ledger['charged_seconds']['compute'],
        'setup_seconds':ledger['charged_seconds']['setup'],'report_sha256':sha(ROOT/'REPORT.md')},indent=2))

if __name__=='__main__':main()
