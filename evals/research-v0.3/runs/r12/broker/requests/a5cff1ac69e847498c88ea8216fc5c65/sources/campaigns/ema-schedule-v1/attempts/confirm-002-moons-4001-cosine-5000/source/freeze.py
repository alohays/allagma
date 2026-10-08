"""Preconfirmation forecast, provenance freeze, and portable Allagma records."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from common import ROOT,CAMP,BUNDLE,read,write,ref,sha,now
sys.path.insert(0,str(BUNDLE))
from allagma.contracts import validate_record
from allagma.composition import select_context

def resource_usage():
    totals={'compute':0.,'setup':0.}; attempts=0; receipts=[]
    for p in sorted((ROOT/'.compute/responses').glob('*.json')):
        v=read(p);request=ROOT/'.compute/requests'/p.name
        if 'result' not in v or not request.exists():continue
        q=read(request); totals[q['category']]+=v['result'].get('charged_seconds',0)
        attempts+=q['category']=='compute';receipts.append({'request':ref(request),'receipt':ref(p),'label':q['label'],'category':q['category'],'status':v['result']['status'],'charged_seconds':v['result'].get('charged_seconds',0)})
    return {'seconds':totals,'compute_requests':attempts,'receipts':receipts}

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',required=True);a=p.parse_args()
    pilot=CAMP/'attempts'/a.pilot
    data=read(pilot/'pilot.json');assert data['passed'] and read(pilot/'controls.json')['passed']
    candidates=[]
    for device in {r['device'] for r in data['results']}:
        rr=[r for r in data['results'] if r['device']==device]
        # Worst observed dataset; use 15% headroom and fixed startup/input allowance.
        step=max(r['seconds_per_update'] for r in rr); sample=max(r['seconds_per_state'] for r in rr)
        candidates.append({'device':device,'seconds_per_update':step,'seconds_per_state':sample,
            'forecast_seconds':1.15*(200000*step+96*sample+24*2)+60})
    chosen=min(candidates,key=lambda c:c['forecast_seconds']);usage=resource_usage()
    remaining=1800-usage['seconds']['compute']
    decision={'created_at':now(),'pilot':ref(pilot/'pilot.json'),'controls':ref(pilot/'controls.json'),
       'candidate_forecasts':candidates,'remaining_compute_seconds':remaining,'chosen':chosen,
       'feasible':chosen['forecast_seconds']<=remaining,'usage_before_confirmation':usage,
       'formula':'1.15*(200000*worst_dataset_step_seconds + 96*worst_dataset_sample_seconds + 48 startup/input seconds)+60 verification seconds',
       'confirmation_opened':False}
    write(CAMP/'forecast.json',decision)
    protocol=read(CAMP/'protocol.json');lock=read(CAMP/'lock.yaml')
    source_hashes={str((ROOT/'study'/s).relative_to(ROOT)):sha(ROOT/'study'/s) for s in ['runner.py','reference.py','common.py','analyze.py']}
    revision=hashlib.sha256(json.dumps(source_hashes,sort_keys=True).encode()).hexdigest()
    snapshot=CAMP/'frozen-source';snapshot.mkdir()
    for path in source_hashes: (snapshot/Path(path).name).write_bytes((ROOT/path).read_bytes())
    write(CAMP/'confirmation-freeze.json',{'created_at':now(),'protocol_sha256':sha(CAMP/'protocol.json'),
          'source_hashes':source_hashes,'runner_revision':revision,'device':chosen['device'],
          'qualification':ref(pilot/'pilot.json'),'forecast':ref(CAMP/'forecast.json'),'authorized_to_confirm':decision['feasible']})
    brief={'study_id':'ema-schedule','question':protocol['question'],'motivation':'Prior duration comparison followed one cosine trajectory and confounded duration with schedule position.',
       'success_criteria':[protocol['completion'],'Negative and inconclusive findings count as scientific success when design and evidence are complete.'],
       'constraints':['All computation/setup through supplied broker','Offline','AI-generated adaptation disclosure and source license retained','No confirmation tuning','Float32 reference mechanism'],
       'output':'REPORT.md, review.json, REPRODUCE.md, artifact-manifest.json, submission.json and measurements',
       'stop_rules':protocol['stops']}
    spec={'schema_version':'0.2','record_type':'StudySpec',**brief,'resources':lock['effective_configuration']['budget'],
       **{k:lock[k] for k in ['capabilities','release','bundle_id','profile_provenance','effective_configuration','configuration_origins']},
       'lock':ref(CAMP/'lock.yaml'),'protocol_revision':protocol['revision'],'protocol':ref(CAMP/'protocol.json')}
    validate_record(spec);write(CAMP/'study.json',spec);write(CAMP/'brief.json',brief)
    context=select_context({'context_id':'confirmation-v1','required':['question','constraints','stops','protocol','unresolved'],
      'relevant':['pilot','forecast','lock'], 'records':{'question':protocol['question'],'constraints':brief['constraints'],
      'stops':protocol['stops'],'protocol':ref(CAMP/'protocol.json'),'unresolved':['Four-seed uncertainty and multiplicity; no independent peer review','Offline literature limits'],
      'pilot':ref(pilot/'pilot.json'),'forecast':ref(CAMP/'forecast.json'),'lock':ref(CAMP/'lock.yaml'),'historical_report':'inputs/materials/prior-study/prior-report.md'},'max_chars':12000},'context/active-brief')
    validate_record(context);write(CAMP/'context.json',context)
    plan=[]
    for dataset,seeds in protocol['seeds']['confirmation'].items():
        for seed in seeds:
            for policy,horizon in [('constant',10000),('cosine',5000),('cosine',10000)]:
                runid=f'{dataset}-{seed}-{policy}-{horizon}'
                cfg={'dataset':dataset,'seed':seed,'policy':policy,'horizon':horizon,'phase':'confirmation','device':chosen['device']}
                run=CAMP/'plan'/runid;write(run/'input.json',cfg)
                exp={'schema_version':'0.2','record_type':'ExperimentSpec','experiment_id':runid,'hypothesis':protocol['hypotheses'][0],
                    'inputs':[ref(run/'input.json')],'runner':ref(ROOT/'study/runner.py'),'evaluator':ref(ROOT/'study/reference.py'),
                    'seed_policy':{'seed':seed,'split':'confirmation','paired_conditions':True,'disjoint_confirmation':True},
                    'budget':lock['effective_configuration']['budget'],'expected_artifacts':['result.json','trace.jsonl','weights.npz','arrays.npz'],
                    'editable':[],'fixed':['runner','evaluator','protocol','seed','float32','optimizer','sampling'],
                    'protocol_revision':protocol['revision'],'split':'confirmation','parameters':cfg}
                validate_record(exp);write(run/'spec.json',exp);plan.append({'id':runid,**cfg})
    write(CAMP/'plan.json',plan)
    write(CAMP/'state.json',{'phase':'confirmation' if decision['feasible'] else 'resource-stop','execution_status':'ready' if decision['feasible'] else 'partial','reason':None if decision['feasible'] else 'Forecast exceeds remaining ceiling'})
    print(json.dumps(decision,indent=2))

if __name__=='__main__':main()
