"""Resolve the exact installed methods and snapshot a qualified campaign."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

bundle=Path('.allagma/bundles/b-9a39b70665ba909edb8abc13')
sys.path.insert(0,str(bundle.resolve()))
from allagma.bundles import verify_study,resolve_entry
from allagma.campaigns import start_campaign
from allagma.composition import select_context
from allagma.contracts import validate_record
from common import write_json,sha,ref

lock=verify_study(Path('.').resolve())
q=json.loads(Path('evidence/qualification-a004/qualification.json').read_text())
assert q['passed']
code=['study/common.py','study/train.py','study/pilot.py','study/qualify.py','study/analyze.py','study/write_report.py']
protocol={'revision':'modular-addition-v1','frozen_at':datetime.now(timezone.utc).isoformat(),
 'hypothesis':'Weight decay may improve held-out endpoints after memorization; delayed grokking may or may not occur within the fixed horizon.',
 'runner':'study/train.py','evaluator':'study/qualify.py','analyzer':'study/analyze.py','writer':'study/write_report.py',
 'code':code,'source_hashes':{s:sha(s) for s in code},'paired_seeds':True,'minimum_confirmation_runs':8,
 'confirmation_seeds':[1001,1002,1003,1004],'pilot_seeds':[61],'updates':100000,'evaluation_interval':100,
 'configuration':{'modulus':97,'split_fraction':.30,'n_train':2822,'n_test':6587,'dtype':'float32','device':'cpu','threads':1,
  'architecture':[194,128,97],'activation':'ReLU','bias':False,'optimizer':'AdamW','lr':.001,'betas':[.9,.98],'epsilon':1e-8,'weight_decay':[0,1]},
 'transitions':{'memorization_accuracy':.99,'generalization_accuracy':.95,'persistence':3,'event_time':'first point of first qualifying triple','minimum_lag':1000,'minimum_time_ratio':2,'right_censor_horizon':100000},
 'analysis':{'independent_unit':'paired seed','direction':'decay1-minus-decay0','metrics':['test_accuracy','test_loss'],
             'uncertainty':'95% Student t CI for mean paired difference with df=3; enumerate 16 sign flips as sensitivity',
             'sensitivity':'One at a time: generalization threshold .90/.99; persistence 1/5; minimum lag 500/5000; minimum ratio 1/5',
             'exclusions':'All pilot/failed/interrupted attempts; no imputation of incomplete endpoints'},
 'qualification':{'passed':True,'evidence':ref('evidence/qualification-a004/qualification.json')},
 'stop_rules':json.loads(Path('brief.json').read_text())['stop_rules'],
 'dispatch':'Portable Allagma artifact handoffs; direct common broker requests run study-owned command-line runner. No nested unsupervised scientific subprocesses.',
 'runs':[{'id':'pilot61','split':'pilot','input':{'seed':61,'updates':3000,'weight_decay':1}}]+
        [{'id':f's{seed}-wd{wd}','split':'confirmation','condition_id':f'wd{wd}',
          'input':{'seed':seed,'updates':100000,'weight_decay':wd}} for seed in [1001,1002,1003,1004] for wd in [0,1]]}
write_json('protocol.json',protocol)
spec=start_campaign(Path('.'),'c001')
Path('campaigns/c001/PROTOCOL.md').write_text(Path('PROTOCOL-DRAFT.md').read_text().replace('protocol draft, revision 1','frozen protocol, revision 1')+'\nCPU qualification passed before this campaign was frozen. See protocol.json for timestamp, qualification evidence and source hashes.\n')
entries={m:resolve_entry(Path('.'),m,'c001') for m in ['recipe/research','context','research/scope','research/protocol','research/experiment','research/analysis','research/writing','research/audit','reviewer','runner']}
write_json('campaigns/c001/resolved-methods.json',entries)
payload={'context_id':'c001-frozen','required':['question','constraints','stop_rules','protocol','unresolved'],
         'relevant':['qualification','sources'],'records':{'question':spec['question'],'constraints':spec['constraints'],
         'stop_rules':spec['stop_rules'],'protocol':ref('campaigns/c001/protocol.json'),'unresolved':['Confirmation, analysis and audit pending'],
         'qualification':ref('evidence/qualification-a004/qualification.json'),'sources':ref('literature.json')},'max_chars':12000}
context=select_context(payload,'context/active-brief');validate_record(context)
write_json('campaigns/c001/context.json',context)
print(json.dumps({'campaign':'c001','bundle_id':lock['bundle_id'],'frozen_at':protocol['frozen_at'],'qualification_passed':True}))
