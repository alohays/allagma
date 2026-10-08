"""Artifact handoffs, substantive review and final snapshot/audit through broker."""
import argparse
import datetime
import importlib.metadata
import json
import os
import platform
from pathlib import Path
import sys
sys.path.insert(0,str(Path('study').resolve()))
from common import write_json,ref,sha
sys.path.insert(0,str(Path('.allagma/bundles/b-9a39b70665ba909edb8abc13').resolve()))
from allagma.contracts import validate_record
from allagma.composition import review as checklist
from allagma.composition import select_context
from allagma.campaigns import audit_evidence

def prepare():
    summary=json.loads(Path('analysis/primary/summary.json').read_text())
    per_seed=json.loads(Path('analysis/primary/per-seed.json').read_text())
    complete=summary['execution_status']=='complete'
    assert complete,'Partial execution requires a revised assessment, not this complete-package path'
    # Fulfill the portable ExperimentSpec handoff names with references to the
    # native scientific artifacts and the actual evaluator output.
    measured=json.loads(Path('measurements.json').read_text())
    validations=json.loads(Path('analysis/primary/validation.json').read_text())
    for run in measured['runs']:
        run_dir=Path(f"campaigns/c001/runs/s{run['seed']}-wd{run['weight_decay']}")
        write_json(run_dir/'raw.json',{'format':'modular-addition-artifact-handoff-v1',
            'result':ref(run['result']),'arrays':ref(run['arrays']),'weights':ref(run['weights']),
            'curve':ref(run['curve']),'checkpoint':ref(run['checkpoint']),'initial_weights':ref(run['initial_weights'])})
        validation=next(v for v in validations if v['seed']==run['seed'] and v['weight_decay']==run['weight_decay'])
        write_json(run_dir/'evaluation.json',{'valid':True,'coverage':validation,
            'evaluation_evidence':ref('analysis/primary/validation.json')})
    write_json('campaigns/c001/runs/pilot61/raw.json',{'result':ref('evidence/pilot-a003/result.json'),
        'excluded_from_confirmation':True})
    write_json('campaigns/c001/runs/pilot61/evaluation.json',{'valid':True,
        'qualification':ref('evidence/qualification-a004/qualification.json')})
    sensitivity=[]
    for variant in per_seed[0]['sensitivity']:
        name,value=variant['varied'],variant['value']
        outcomes=[next(v['outcome'] for v in row['sensitivity'] if v['varied']==name and v['value']==value) for row in per_seed]
        sensitivity.append({'varied':name,'value':value,'generalized_count':sum(x['generalization']['event'] for x in outcomes),
                            'delayed_grokking_count':sum(x['delayed_grokking_observed'] for x in outcomes),
                            'n_runs':len(outcomes)})
    write_json('analysis/primary/sensitivity-summary.json',sensitivity)
    # Generated findings supply concrete interpretation without revising frozen definitions.
    acc=summary['uncertainty']['test_accuracy'];loss=summary['uncertainty']['test_loss']
    paragraph=(f"\n## Interpretation of the verified endpoints\n\n"
      f"The mean paired accuracy change was {acc['mean']*100:.6f} percentage points and the mean paired cross-entropy change was {loss['mean']:.6f} nats (decay 1 minus 0). "
      f"All four per-seed differences and their intervals are shown above; these describe this finite set of seeds. "
      f"Memorization occurred in {summary['memorized_count']} cells, threshold-level generalization in {summary['generalized_count']}, and delayed grokking in {summary['delayed_grokking_count']}. "
      "A relative improvement in held-out metrics is not sufficient to claim a 95%-accuracy transition.\n\n"
      "The prespecified one-factor sensitivity results were:\n\n"
      "| Varied component | Value | Generalization events | Delayed-grokking events |\n|---|---:|---:|---:|\n"+
      '\n'.join(f"| {v['varied']} | {v['value']} | {v['generalized_count']}/8 | {v['delayed_grokking_count']}/8 |" for v in sensitivity)+
      "\n\nThe primary classifier and all sensitivity classifiers are retained per seed. Censoring is not a zero transition time.\n\n"
      "A numerical-validator amendment used absolute tolerance 1e-6 plus relative tolerance 1e-6 for float32-versus-float64 loss comparisons. "
      "The triggering discrepancy was 1.9929633e-5 nats at a loss of about 165.7; final logits reloaded bitwise. "
      "The original analyzer, failed check and [explicit handoff](campaigns/c001/amendments/evaluator-v1.1.json) remain retained. "
      "No training setting or primary scientific analysis formula changed.\n")
    manuscript=Path('REPORT.md').read_text()
    assert '## Interpretation of the verified endpoints' not in manuscript
    manuscript=manuscript.replace('## Reference\n',paragraph+'\n## Reference\n')
    Path('REPORT.md').write_text(manuscript)
    # Supplement claim evidence with the generated sensitivity analysis.
    claims=json.loads(Path('analysis/primary/claims.json').read_text())
    claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':'definition-sensitivity',
      'text':'Prespecified one-factor threshold sensitivity outcomes are '+json.dumps(sensitivity),
      'supporting':[ref('analysis/primary/sensitivity-summary.json')],'contradicting':[],
      'dependencies':[ref('analysis/primary/per-seed.json'),ref('campaigns/c001/protocol.json')],
      'scope':'Only the listed definition changes and prescribed finite horizon',
      'limitations':['Sensitivity analyses do not add independent seeds or establish a mechanism'],'status':'supported','supersedes':None})
    write_json('analysis/primary/claims.json',claims)
    raw=json.loads(Path('analysis/primary/raw-manifest.json').read_text())
    record={'schema_version':'0.2','record_type':'AnalysisRecord','analysis_id':'c001-a001-evaluator-v1.1',
      'raw_manifest':ref('analysis/primary/raw-manifest.json'),'analysis_revision':sha('scripts/analyze_v1_1.py'),
      'code':ref('scripts/analyze_v1_1.py'),'configuration':summary['primary_definition'],
      'outputs':[ref(p) for p in sorted(Path('analysis/primary').glob('*')) if p.is_file() and p.name!='raw-manifest.json'],
      'exclusions':raw['exclusions'],'uncertainty':summary['uncertainty']['test_accuracy']['method'],
      'dependencies':[ref('campaigns/c001/protocol.json'),ref('campaigns/c001/amendments/evaluator-v1.1.json'),ref('analysis/recomputed/comparison.json')]}
    validate_record(record);write_json('campaigns/c001/records/analysis.json',record)
    findings=[
      {'id':'R1','status':'resolved','severity':'execution','finding':'Controlled interruption left no trained endpoint; it cannot count as a scientific replicate.',
       'resolution':'Retained pilot-a001 start/log/receipt and recovered under new attempt IDs; confirmation uses only seeds 1001--1004.','evidence':['attempts.json','evidence/pilot-a001/started.json']},
      {'id':'R2','status':'resolved','severity':'implementation','finding':'Pilot MPS allocation failed after CPU benchmarking.',
       'resolution':'Kept failed attempt and separately qualified CPU with the full runner before freezing confirmation. No MPS measurements are analyzed.','evidence':['evidence/pilot-a002/qualification.json','evidence/qualification-a004/qualification.json']},
      {'id':'R3','status':'resolved','severity':'numerical validation','finding':'Fixed absolute 1e-5 endpoint tolerance failed on high cross-entropy despite identical checkpoint logits.',
       'resolution':'Explicit evaluator-v1.1 handoff uses atol=rtol=1e-6; original analyzer and failed request persist. Endpoints are recomputed in float64, and all final checkpoint/NPZ logits must still match bitwise.','evidence':['campaigns/c001/amendments/evaluator-v1.1.json','analysis/primary/validation.json']},
      {'id':'R4','status':'unresolved','severity':'inferential limitation','finding':'Four independent paired seeds provide weak population uncertainty; t intervals assume a suitable sampling distribution and sign-flip p-values are coarse.',
       'resolution':'Report each paired difference, SD, SE, 95% df=3 t interval and all-16 sign-flip calculation; make no broad population/significance claim. More independent seeds would be needed.','evidence':['analysis/primary/summary.json','REPORT.md']},
      {'id':'R5','status':'unresolved','severity':'scope limitation','finding':'A 100000-update horizon cannot establish whether censored runs ever generalize; only two decay levels and one MLP/optimizer/split fraction were tested.',
       'resolution':'Use explicit censoring/null event times, separate memorization/improvement/grokking claims, and restrict every conclusion to this configuration.','evidence':['analysis/primary/per-seed.json','REPORT.md']},
      {'id':'R6','status':'unresolved','severity':'review limitation','finding':'The installed checklist supplies schema/direct-digest assurance, and this substantive critique is by the same agent.',
       'resolution':'Label scientific critique provisional; do not claim independent scientific peer review. Independent review remains a future requirement for stronger assurance.','evidence':['review-checklist.json']},
      {'id':'R7','status':'resolved within stated scope','severity':'reproducibility','finding':'Code paths and training records alone do not verify saved predictions or reported numbers.',
       'resolution':'Reload every final checkpoint and NPZ weight set, recompute every endpoint, verify raw digests, and repeat the numerical analysis in a second directory. A second complete fresh-environment training execution was not run.','evidence':['analysis/primary/validation.json','analysis/recomputed/comparison.json','REPRODUCE.md']},
      {'id':'R8','status':'unresolved','severity':'measurement convention','finding':'100-update evaluations and a first-of-three rule discretize event times; a three-point window is not proof of permanent generalization.',
       'resolution':'Report both initial and confirming evaluation times plus one-factor definition sensitivity. No change to the frozen primary analysis.','evidence':['analysis/primary/per-seed.json','analysis/primary/sensitivity-summary.json']},
      {'id':'R9','status':'unresolved','severity':'external validity','finding':'Held-out ordered pairs share the same modular operation and may include swapped versions of training pairs; examples are not independent tasks.',
       'resolution':'Use seed as the independent unit and avoid extrapolating to new operations or architectures. The supplied split is followed exactly.','evidence':['campaigns/c001/protocol.json','REPORT.md']}
    ]
    write_json('review-findings.json',{'review_scope':'same-agent substantive critique of the exact current report and raw evidence','independent_peer_review':False,'findings':findings})
    payload={'study':str(Path('.').resolve()),'material':ref('REPORT.md'),'criteria':['fixed protocol adherence','raw-evidence provenance','censoring and uncertainty','reproduction and stated limitations'],
             'claims':claims}
    write_json('review-input.json',payload)
    result=checklist(payload,strict=False);write_json('review-checklist.json',result)
    assert result['verdict']=='pass',result
    rr={'schema_version':'0.2','record_type':'ReviewRecord','review_id':'c001-r001',
        'reviewer':'same-agent substantive critique plus locked reviewer/checklist',
        'backend':'Allagma reviewer/checklist direct locked Python implementation + current-session critique',
        'backend_version':'0.3.0rc1 / b-9a39b70665ba909edb8abc13','material':ref('REPORT.md'),'criteria':payload['criteria'],
        'verdict':'pass','findings':[f"{x['id']} ({x['status']}): {x['finding']} {x['resolution']}" for x in findings],
        'trace':[ref('review-findings.json'),ref('review-input.json'),ref('review-checklist.json'),ref('analysis/primary/validation.json'),ref('analysis/recomputed/comparison.json')],
        'assurance':'provisional','coverage':'Substantive same-agent review of methods, endpoints, uncertainty, censoring and scope; offline adapter checks schemas/material/direct-evidence digests. Does not constitute independent scientific review.'}
    validate_record(rr);write_json('review.json',rr);write_json('campaigns/c001/records/review.json',rr)
    brief=json.loads(Path('brief.json').read_text())
    context=select_context({'context_id':'c001-audit','required':['question','constraints','stop_rules','protocol','unresolved'],
       'relevant':['analysis','report','review'],'max_chars':12000,
       'records':{'question':brief['question'],'constraints':brief['constraints'],'stop_rules':brief['stop_rules'],
          'protocol':ref('campaigns/c001/protocol.json'),'unresolved':[x for x in findings if x['status']=='unresolved'],
          'analysis':ref('analysis/primary/summary.json'),'report':ref('REPORT.md'),'review':ref('review.json')}},'context/active-brief')
    validate_record(context);write_json('campaigns/c001/context-audit.json',context)
    env={'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'device':'cpu','threads':1,
         'packages':{n:importlib.metadata.version(n) for n in ['torch','numpy','scipy','matplotlib']},
         'environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','PYTORCH_MPS_HIGH_WATERMARK_RATIO']}}
    write_json('environment.json',env)
    print(json.dumps({'review_verdict':rr['verdict'],'assurance':rr['assurance'],'sensitivity':sensitivity}))

def package():
    v=json.loads(Path('verification.json').read_text());assert v['passed']
    assert v['material']['sha256']==sha('REPORT.md')
    status=json.loads(Path('analysis/primary/summary.json').read_text())['execution_status']
    submission={'task_id':'modular-addition','execution_status':status,'manuscript':'REPORT.md','review':'review.json',
      'artifact_manifest':'artifact-manifest.json','measurements':'measurements.json',
      'reproduce':{'argv':['python3','scripts/driver.py','reproduce'],'cwd':'.'},
      'recompute':{'argv':['python3','scripts/driver.py','recompute'],'cwd':'.'},
      'verification':'verification.json','completion_assessment':'All eight prescribed cells completed 100000 updates, failed/interrupted attempts retained, endpoints and all checkpoints verified, and separate retained-data reanalysis agreed. Scientific review is provisional; a second fresh full training campaign was not repeated.'}
    write_json('submission.json',submission)
    write_json('campaigns/c001/state.json',{'phase':'audit','execution_status':'completed','assurance':'provisional',
      'stop_reason':'All prescribed cells and retained-data verification complete; known inferential/review limitations retained.',
      'submission':ref('submission.json'),'verification':ref('verification.json')})
    roots=['study','scripts','evidence','analysis','campaigns','inputs','.compute']
    paths={p for name in roots for p in Path(name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.tmp'}
    paths.update(p for p in Path('.').iterdir() if p.is_file() and p.suffix in ['.md','.json','.yaml'] and p.name!='artifact-manifest.json')
    paths.add(Path('.allagma/lock.yaml'))
    paths.update(p for p in Path('.allagma/bundles/b-9a39b70665ba909edb8abc13').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files=[{'path':p.as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)]
    write_json('artifact-manifest.json',{'format':'research-artifact-manifest-v1','task_id':'modular-addition',
      'snapshot_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,
      'exclusions':['artifact-manifest.json (self-reference)','disposable venv and caches','broker responses produced after this snapshot, including the final manifest audit'],
      'retention':'All raw scientific attempts and outputs retained; listed paths are workspace-relative regular files.'})
    print(json.dumps({'execution_status':status,'manifest_files':len(files)}))

def verify():
    manifest=json.loads(Path('artifact-manifest.json').read_text())
    for item in manifest['files']:
        p=Path(item['path']);assert p.is_file() and not p.is_symlink(),str(p)
        assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],str(p)
    for p in ['review.json','campaigns/c001/records/analysis.json']:
        record=json.loads(Path(p).read_text());validate_record(record);audit_evidence(Path('.'),record)
    s=json.loads(Path('submission.json').read_text())
    for name in ['manuscript','review','artifact_manifest','measurements']:assert Path(s[name]).is_file()
    for name in ['reproduce','recompute']:
        assert s[name]['cwd']=='.' and all(isinstance(x,str) for x in s[name]['argv'])
    totals={'compute':0.,'setup':0.};peaks={'rss':0,'storage':0}
    for receipt in Path('.compute/responses').glob('*.json'):
        payload=json.loads(receipt.read_text())
        assert payload.get('result',{}).get('status')!='running'
        request=json.loads((Path('.compute/requests')/(payload['request_id']+'.json')).read_text())
        result=payload.get('result',{})
        totals[request['category']]+=result.get('charged_seconds',0.)
        peaks['rss']=max(peaks['rss'],result.get('peak_rss_bytes',0))
        peaks['storage']=max(peaks['storage'],result.get('peak_storage_bytes',0))
    count=sum(json.loads(p.read_text())['category']=='compute' for p in Path('.compute/requests').glob('*.json'))
    assert totals['compute']<1800 and totals['setup']<300 and count<=64
    assert peaks['rss']<=8589934592 and peaks['storage']<=6442450944
    assert all(f['bytes']<=536870912 for f in manifest['files'])
    print(json.dumps({'passed':True,'manifest_sha256':sha('artifact-manifest.json'),'files_checked':len(manifest['files']),
                      'resource_snapshot_charged_seconds':totals,'compute_requests_including_this_audit':count,'observed_peaks_bytes':peaks,
                      'submission_status':s['execution_status'],'coverage':'Every manifest file size/SHA256; current report/review material and transitive evidence; required submission paths/argv; Allagma review/analysis schemas.'}))

p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','package','verify']);args=p.parse_args()
{'prepare':prepare,'package':package,'verify':verify}[args.mode]()
