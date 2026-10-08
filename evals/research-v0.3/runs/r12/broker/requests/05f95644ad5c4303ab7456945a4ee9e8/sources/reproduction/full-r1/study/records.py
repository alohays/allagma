"""Reconcile authoritative delivered receipts into portable run records."""
import json
from pathlib import Path
import sys
from common import ROOT,CAMP,BUNDLE,read,write,ref,sha
sys.path.insert(0,str(BUNDLE))
from allagma.contracts import validate_record
from freeze import resource_usage

def reconcile():
    by_attempt={}
    for p in (ROOT/'.compute/requests').glob('*.json'):
        q=read(p);argv=q['argv']
        if 'study/runner.py' not in argv or '--attempt' not in argv:continue
        name=argv[argv.index('--attempt')+1];rp=ROOT/'.compute/responses'/p.name
        if rp.exists():by_attempt[name]=(q,read(rp),p,rp)
    refs=[]
    for started in sorted(CAMP.glob('attempts/*/started.json')):
        dest=started.parent;s=read(started);name=dest.name
        q,receipt,request_path,receipt_path=by_attempt[name]
        v=receipt['result'];status={'completed':'succeeded','timed_out':'interrupted' if receipt.get('injected_interruption') else 'failed'}.get(v['status'],'failed')
        cfg=read(dest/'input.json');phase='pilot' if cfg['mode']=='pilot' else 'confirmation'
        inp=[ref(dest/'input.json'),s['protocol'],s['lock'],ref(request_path)]
        inp.extend(ref(p) for p in sorted((dest/'source').glob('*.py')))
        output=[ref(p) for p in sorted(dest.rglob('*')) if p.is_file() and 'source' not in p.parts and p.name not in ['input.json','started.json','run-record.json']]
        output.append(ref(receipt_path))
        value={'schema_version':'0.2','record_type':'RunRecord','run_id':name,'attempt_id':name,
           'attempt_number':int(name[-3:]) if name.startswith('pilot-a') else 1,'campaign_id':'ema-schedule-v1','experiment_id':'pilot-qualification' if phase=='pilot' else name.removeprefix(name.split('-')[0]+'-'+name.split('-')[1]+'-'),
           'started_at':s['started_at'],'ended_at':v['ended_at'],'inputs':inp,'outputs':output,
           'environment':read(dest/'result.json').get('environment',{}) if (dest/'result.json').exists() else {'interpreter':q['argv'][0],'qualification':phase},
           'model_revision':s['source_revision'],'data_revision':sha(dest/'input.json'),
           'usage':{'wall_seconds':v.get('charged_seconds',0),'money_usd':0,'tokens':0},'status':status,
           'error':None if status=='succeeded' else {'kind':v['status'],'message':'See retained broker receipt/stderr and attempt error; controlled interruption' if receipt.get('injected_interruption') else 'See retained broker receipt/stderr and attempt error'},
           'protocol_revision':'ema-schedule-v1','bundle_id':'b-9a39b70665ba909edb8abc13','split':phase,
           'command':q['argv'],'exit_code':v['exit_code']}
        validate_record(value);write(dest/'run-record.json',value);refs.append(ref(dest/'run-record.json'))
    write(CAMP/'run-manifest.json',{'format':'allagma-run-manifest-v1','records':refs,'replicate_unit':'seed within dataset; repeated attempts and fresh reproductions not new replicates'})
    write(ROOT/'evidence/resource-usage.json',resource_usage())
    return refs

if __name__=='__main__':
    print(json.dumps({'run_records':len(reconcile())}))
