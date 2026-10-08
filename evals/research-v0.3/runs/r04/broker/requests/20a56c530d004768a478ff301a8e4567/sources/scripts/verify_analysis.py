"""Known-answer event/uncertainty checks and current-revision transitive audit."""
import importlib.util
import json
from pathlib import Path
import sys
import datetime
import numpy as np
sys.path.insert(0,str(Path('study').resolve()))
from common import write_json,ref,sha
path=Path('scripts/analyze_v1_1.py')
spec=importlib.util.spec_from_file_location('analyzer',path)
an=importlib.util.module_from_spec(spec);spec.loader.exec_module(an)
sys.path.insert(0,str(Path('.allagma/bundles/b-9a39b70665ba909edb8abc13').resolve()))
from allagma.contracts import validate_record
from allagma.campaigns import audit_evidence
from allagma.bundles import verify_study,resolve_entry

def curve(generalization_start):
    return [{'step':i,'train_accuracy':1. if i>=100 else 0.,'test_accuracy':1. if i>=generalization_start else 0.,'train_loss':1.,'test_loss':1.} for i in range(0,2100,100)]
checks={}
t=an.transitions(curve(1100))
checks['first_of_triple_and_confirmation']=t['memorization']['time']==100 and t['memorization']['confirmed_at']==300 and t['generalization']['time']==1100 and t['generalization']['confirmed_at']==1300
checks['primary_delay_boundary']=t['lag']==1000 and t['delayed_grokking_observed']
checks['below_delay_boundary']=not an.transitions(curve(1000))['delayed_grokking_observed']
tail=an.transitions(curve(1900))
checks['incomplete_triple_censored']=tail['generalization']['censored'] and tail['generalization']['time'] is None and tail['generalization']['censor_at']==2000 and tail['lag'] is None
dip=curve(1100);dip[12]['test_accuracy']=0.
checks['persistence_resets_after_dip']=an.transitions(dip)['generalization']['time']==1300
u=an.uncertainty([1,1,1,1])
checks['known_uncertainty']=u['mean']==1 and u['sd']==0 and u['ci95_student_t']==[1,1] and u['paired_sign_flip_two_sided_p']==.125
u0=an.uncertainty([0,0,0,0]);checks['zero_effect_control']=u0['ci95_student_t']==[0,0] and u0['paired_sign_flip_two_sided_p']==1
checks['all_controls_pass']=all(checks.values())
assert checks['all_controls_pass'],checks
lock=verify_study(Path('.'))
resolved=resolve_entry(Path('.'),'recipe/research','c001')
for record in Path('campaigns/c001').rglob('*.json'):
    value=json.loads(record.read_text())
    if isinstance(value,dict) and 'record_type' in value:
        validate_record(value)
    audit_evidence(Path('.'),value)
code_manifest=json.loads(Path('campaigns/c001/code-manifest.json').read_text())
audit_evidence(Path('.'),code_manifest)
protocol=json.loads(Path('campaigns/c001/protocol.json').read_text())
assert all(sha(p)==digest for p,digest in protocol['source_hashes'].items())
for claim in json.loads(Path('analysis/primary/claims.json').read_text()):
    validate_record(claim);audit_evidence(Path('.'),claim)
primary=Path('analysis/primary');repeat=Path('analysis/recomputed')
comp=json.loads((repeat/'comparison.json').read_text());assert comp['passed']
for f in ['summary.json','per-seed.json','validation.json','raw-manifest.json','sensitivity-summary.json']:
    assert (primary/f).read_bytes()==(repeat/f).read_bytes()
raw=json.loads((primary/'raw-manifest.json').read_text())
audit_evidence(Path('.'),raw)
amend=json.loads(Path('campaigns/c001/amendments/evaluator-v1.1.json').read_text())
audit_evidence(Path('.'),amend)
data=json.loads(Path('measurements.json').read_text())
assert data['format']=='research-measurements-v1' and data['task_id']=='modular-addition' and len(data['runs'])==8
assert {(r['seed'],r['weight_decay']) for r in data['runs']}=={(s,w) for s in [1001,1002,1003,1004] for w in [0,1]}
assert all(r['updates']==100000 and r['phase']=='confirmation' for r in data['runs'])
for r in data['runs']:
    a=np.load(r['arrays'],allow_pickle=False);w=np.load(r['weights'],allow_pickle=False)
    assert a['logits'].dtype==np.float32 and w['input_weight'].dtype==np.float32 and w['output_weight'].dtype==np.float32
    assert w['input_weight'].shape==(128,194) and w['output_weight'].shape==(97,128)
    assert all(np.issubdtype(a[k].dtype,np.integer) for k in ['pairs','labels','train_indices','test_indices','predictions'])
    result=json.loads(Path(r['result']).read_text())
    assert datetime.datetime.fromisoformat(result['started_at'])>datetime.datetime.fromisoformat(protocol['frozen_at'])
manuscript=Path('REPORT.md').read_text()
rows=json.loads(Path('analysis/primary/per-seed.json').read_text())
summary=json.loads(Path('analysis/primary/summary.json').read_text())
endpoint_rows=[];paired_rows=[]
for line in manuscript.splitlines():
    if not line.startswith('| '):continue
    cells=[c.strip() for c in line.split('|')[1:-1]]
    if not cells or cells[0] not in ['1001','1002','1003','1004']:continue
    if len(cells)==10:endpoint_rows.append(cells)
    elif len(cells)==3:paired_rows.append(cells)
assert len(endpoint_rows)==8 and len(paired_rows)==4
for cells in endpoint_rows:
    row=next(r for r in rows if r['seed']==int(cells[0]) and r['weight_decay']==int(cells[1]))
    for cell,key in zip(cells[2:6],['train_accuracy','test_accuracy','train_loss','test_loss']):
        assert np.isclose(float(cell),row['metrics'][key],atol=5.1e-7,rtol=5.1e-6)
    t=row['transition']
    for cell,key in zip(cells[6:8],['memorization','generalization']):
        assert cell==(str(t[key]['time']) if t[key]['event'] else f">{t[key]['censor_at']} (censored)")
    assert cells[8]==(str(t['lag']) if t['lag'] is not None else 'unobserved')
    assert cells[9]==str(t['delayed_grokking_observed'])
for cells in paired_rows:
    row=next(r for r in summary['per_seed'] if r['seed']==int(cells[0]))
    assert abs(float(cells[1])-row['test_accuracy'])<5.1e-10
    assert abs(float(cells[2])-row['test_loss'])<5.1e-10
verification={'passed':True,'analysis_controls':checks,'all_eight_cells_verified':True,
 'recomputation':ref(repeat/'comparison.json'),'checkpoint_and_array_checks':ref(primary/'validation.json'),
 'raw_manifest':ref(primary/'raw-manifest.json'),'material':ref('REPORT.md'),
 'evaluator_amendment':ref('campaigns/c001/amendments/evaluator-v1.1.json'),
 'transitive_evidence_digests':True,'allagma_contract_validation':True,'study_lock_verified':True,
 'manuscript_endpoint_and_paired_tables_independently_parsed':True,
 'coverage':'Known-answer transition/persistence/censoring and uncertainty controls; exact repeated analysis JSONs; all-eight-cell endpoint/NPZ/checkpoint validation; all referenced evidence digests and Allagma schemas. No independent peer review and no second full fresh training execution.',
 'controls_timing':'Metric/optimizer/split/resume controls ran before confirmation; these extra threshold-logic and audit controls ran after confirmation without changing primary definitions.'}
write_json('verification.json',verification)
print(json.dumps(verification,indent=2))
