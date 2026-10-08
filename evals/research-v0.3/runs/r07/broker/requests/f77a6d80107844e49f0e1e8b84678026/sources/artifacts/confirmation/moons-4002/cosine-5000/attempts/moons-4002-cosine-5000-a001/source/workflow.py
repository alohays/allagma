"""Portable Allagma handoffs, preconfirmation freeze, and attempt accounting."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from common import ROOT, CAMPAIGN, now, write, ref, sha, sources

def receipts():
    entries=[]
    for path in sorted((ROOT/'.compute/requests').glob('*.json')):
        request=json.loads(path.read_text())
        response=ROOT/'.compute/responses'/(request['request_id']+'.json')
        if response.exists():
            outcome=json.loads(response.read_text())
            entries.append({'request':request,'response':outcome,'request_artifact':ref(path),'response_artifact':ref(response)})
    return entries

def account():
    entries=receipts()
    ledger={'receipts':entries,'charged_seconds':{category:sum(e['response'].get('result',{}).get('charged_seconds',0) for e in entries if e['request']['category']==category) for category in ('compute','setup')},
            'compute_requests':sum(e['request']['category']=='compute' for e in entries),
            'note':'Convenience receipt copies; authoritative receipts remain controller-owned. The currently executing request is absent until its response exists.'}
    write(ROOT/'evidence/resource-ledger.json',ledger)
    lock=json.loads((CAMPAIGN/'lock.yaml').read_text())
    for start in sorted((ROOT/'artifacts').glob('*/*/*/attempts/*/started.json')):
        directory=start.parent
        if (directory/'record.json').exists():continue
        value=json.loads(start.read_text());cfg=value['inputs']
        matched=[e for e in entries if '--attempt-id' in e['request']['argv'] and e['request']['argv'][e['request']['argv'].index('--attempt-id')+1]==cfg['attempt_id']]
        if not matched:continue
        entry=matched[-1]; response=entry['response']; result=response.get('result',{})
        success=(directory/'result.json').exists() and result.get('status')=='completed'
        interrupted=response.get('injected_interruption',False) or result.get('status')=='timed_out'
        status='succeeded' if success else 'interrupted' if interrupted else 'failed'
        record={'schema_version':'0.2','record_type':'RunRecord','run_id':directory.parent.parent.name+'-'+directory.parents[3].name,
            'attempt_id':cfg['attempt_id'],'attempt_number':int(cfg['attempt_id'].rsplit('a',1)[-1]),
            'campaign_id':'ema-schedule-v1','experiment_id':f"{cfg['dataset']}-{cfg['seed']}-{cfg['policy']}-{cfg['duration']}",
            'started_at':value['started_at'],'ended_at':result.get('ended_at',now()),
            'inputs':[ref(directory/'input.json'),ref(directory/'started.json'),entry['request_artifact']],
            'outputs':[ref(p) for p in sorted(directory.iterdir()) if p.is_file()]+[entry['response_artifact']],
            'environment':{'broker':'common local-process','device_requested':cfg['device'],'dtype':'float32'},
            'model_revision':value['source_revision'],'data_revision':sha(directory/'input.json'),
            'usage':{'wall_seconds':result.get('charged_seconds',0),'money_usd':0,'tokens':0},
            'status':status,'error':None if success else {'kind':result.get('status','unknown'),'message':'See retained broker receipt and stderr; this attempt is excluded from confirmation.'},
            'protocol_revision':'v1','bundle_id':lock['bundle_id'],'split':cfg['phase'],
            'command':entry['request']['argv'],'exit_code':result.get('exit_code')}
        write(directory/'record.json',record)
    return ledger

def freeze():
    assert not (CAMPAIGN/'confirmation-freeze.json').exists()
    assert not list((ROOT/'artifacts/confirmation').glob('*/inputs/metadata.json'))
    qual=json.loads((ROOT/'evidence/qualification.json').read_text())
    assert qual['passed']
    for path,digest in qual['scientific_sources'].items():
        assert sha(ROOT/path)==digest
    pilots=[json.loads(p.read_text()) for p in (ROOT/'artifacts/pilot').glob('*/*/attempts/*/result.json')]
    assert {p['inputs']['dataset'] for p in pilots}=={'moons','gmm8'}
    ledger=account()
    train_rate=max(p['timing']['training_seconds']/p['completed_updates'] for p in pilots)
    sample_rate=max(p['timing']['evaluation_seconds']/3 for p in pilots)
    components={'training_200000_updates':200000*train_rate,
        'sampling_96_states':96*sample_rate,'process_start_data_io_24_jobs':24*4.,
        'analysis_plot_recompute_regeneration_audit_reserve':100.}
    forecast=sum(components.values())*1.35
    forecast_record={'pilot_attempts':[p['attempt_id'] for p in pilots],'seconds_per_update_conservative':train_rate,
        'seconds_per_state_sampling':sample_rate,'components_seconds':components,'safety_factor':1.35,
        'forecast_remaining_compute_seconds':forecast,'already_charged_compute_seconds':ledger['charged_seconds']['compute'],
        'projected_total_compute_seconds':forecast+ledger['charged_seconds']['compute'],
        'ceiling_compute_seconds':1800,'projected_requests_total':ledger['compute_requests']+24+8,
        'storage_forecast_bytes':2400000000,'storage_ceiling_bytes':6442450944,
        'peak_observed_pilot_rss_bytes':max(e['response'].get('result',{}).get('peak_rss_bytes',0) for e in ledger['receipts']),
        'device':'mps','feasible':forecast+ledger['charged_seconds']['compute']<1800}
    assert forecast_record['feasible'] and forecast_record['projected_requests_total']<=64
    write(ROOT/'evidence/forecast.json',forecast_record)
    lock=json.loads((CAMPAIGN/'lock.yaml').read_text())
    bundle=ROOT/'.allagma/bundles'/lock['bundle_id']
    sys.path.insert(0,str(bundle))
    from allagma.contracts import validate_record
    def record(path,value):
        validate_record(value);write(path,value)
    shutil.copyfile(ROOT/'PROTOCOL.md',CAMPAIGN/'protocol.md')
    (CAMPAIGN/'materials').mkdir(exist_ok=False)
    for path in sources():
        shutil.copyfile(ROOT/path,CAMPAIGN/'materials'/Path(path).name)
    shutil.copyfile(ROOT/'LICENSE-AI-SCIENTIST',CAMPAIGN/'materials/LICENSE')
    scope={'schema_version':'0.2','record_type':'StudySpec','study_id':'ema-schedule',
        'question':'How does full learning-rate policy change apparent weight-EMA benefit independently of terminal duration?',
        'motivation':'The supplied prior study confounded checkpoint age and schedule position.',
        'success_criteria':['32 paired confirmation cells with honest uncertainty','Retained raw data and loadable states','Regenerated samples and retained-data recomputation','Revision-bound critical review'],
        'resources':lock['effective_configuration']['budget'],'capabilities':lock['capabilities'],
        'constraints':['Float32 reference model and specified datasets/metrics','Pilot/confirmation separation','All computation through local broker; no network','Native session 3600 seconds; setup 300 seconds; compute 1800 seconds','No outcome-based exclusions or required EMA benefit'],
        'output':'REPORT.md, review.json, REPRODUCE.md, artifact-manifest.json, submission.json and measurements',
        'stop_rules':['Completion','Resource insufficiency','Failed qualification','Repeated uncorrectable failure'],
        'release':lock['release'],'bundle_id':lock['bundle_id'],'lock':ref(CAMPAIGN/'lock.yaml'),
        'profile_provenance':lock['profile_provenance'],'effective_configuration':lock['effective_configuration'],
        'configuration_origins':lock['configuration_origins'],'protocol_revision':'v1','protocol':ref(CAMPAIGN/'protocol.md')}
    record(CAMPAIGN/'study.json',scope)
    selected=['inputs/BRIEF.md','inputs/COMPUTE.md','inputs/RESOURCES.json','inputs/materials/MEASUREMENTS.md','inputs/materials/SOURCES.md','PROTOCOL.md','evidence/qualification.json','evidence/forecast.json']
    record(CAMPAIGN/'context.json',{'schema_version':'0.2','record_type':'ContextRecord','context_id':'confirmation-v1',
        'method_id':'context/active-brief','required':selected,'selected':selected+['inputs/materials/prior-study/science.py','inputs/materials/prior-study/REFERENCE.md'],
        'omitted':['Historical upstream evidence paths unavailable in supplied package; prior numerical results are contextual only'],
        'content':{'question':scope['question'],'artifacts':[ref(ROOT/p) for p in selected],
                   'constraints':scope['constraints'],'stop_rules':scope['stop_rules'],'protocol_revision':'v1','unresolved_findings':[]},
        'limitations':['Offline source map; no literature search or independent bibliographic verification','Sequential artifact handoffs; no independent reviewer model']})
    plan=[]
    for dataset,seeds in [('moons',range(4001,4005)),('gmm8',range(5001,5005))]:
        for seed in seeds:
            for policy,duration in [('constant',10000),('cosine',5000),('cosine',10000)]:
                cfg={'dataset':dataset,'seed':seed,'phase':'confirmation','policy':policy,'duration':duration,'device':'mps'}
                run_id=f'{dataset}-{seed}-{policy}-{duration}'
                plan.append({'id':run_id,**cfg})
                record(CAMPAIGN/'specs'/(run_id+'.json'),{'schema_version':'0.2','record_type':'ExperimentSpec',
                    'experiment_id':run_id,'hypothesis':'EMA-minus-raw quality may depend on full schedule policy and duration; negative and inconclusive results are valid.',
                    'inputs':[ref(CAMPAIGN/'protocol.md')],'runner':ref(ROOT/'study/runner.py'),'evaluator':ref(ROOT/'study/science.py'),
                    'seed_policy':{'paired_seeds':True,'condition_id':policy+'-'+str(duration),'pilot':{'moons':71,'gmm8':81}},
                    'budget':lock['effective_configuration']['budget'],
                    'expected_artifacts':['initial/training/evaluation NPZ','trace','raw/EMA weights and samples','measurement JSON','attempt source/input/receipt'],
                    'editable':['Reporting code only; scientific changes require amendment'],
                    'fixed':['Architecture, optimizer, data, RNG streams, seed list, evaluation and EMA rule'],
                    'protocol_revision':'v1','split':'confirmation','parameters':cfg})
    write(CAMPAIGN/'run-plan.json',plan)
    write(CAMPAIGN/'confirmation-freeze.json',{'created_at':now(),'protocol':ref(ROOT/'PROTOCOL.md'),
        'campaign_protocol':ref(CAMPAIGN/'protocol.md'),'scientific_sources':sources(),'qualification':ref(ROOT/'evidence/qualification.json'),
        'forecast':ref(ROOT/'evidence/forecast.json'),'lock':ref(CAMPAIGN/'lock.yaml'),
        'confirmation_inputs_preexisting':False,'device':'mps','plan':ref(CAMPAIGN/'run-plan.json')})
    write(CAMPAIGN/'state.json',{'phase':'campaign','execution_status':'ready','assurance':'unreviewed','protocol_revision':'v1'})
    print(json.dumps(forecast_record,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['freeze','account'])
    args=parser.parse_args()
    if args.operation=='freeze':freeze()
    else:print(json.dumps({k:v for k,v in account().items() if k!='receipts'},indent=2))
