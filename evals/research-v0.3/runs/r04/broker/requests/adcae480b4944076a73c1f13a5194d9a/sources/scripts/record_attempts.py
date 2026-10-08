"""Convert broker history into portable Allagma artifact handoffs."""
import datetime
import json
import platform
from pathlib import Path
import sys
sys.path.insert(0,str(Path('study').resolve()))
from common import write_json,ref,sha
sys.path.insert(0,str(Path('.allagma/bundles/b-9a39b70665ba909edb8abc13').resolve()))
from allagma.contracts import validate_record

attempts=[];totals={'setup':0.,'compute':0.}
protocol=json.loads(Path('campaigns/c001/protocol.json').read_text())
for request in sorted(Path('.compute/requests').glob('*.json')):
    req=json.loads(request.read_text()); response=Path('.compute/responses')/(req['request_id']+'.json')
    if not response.exists():continue
    receipt=json.loads(response.read_text());res=receipt['result']
    charge=res.get('charged_seconds',0.);totals[req['category']]+=charge
    item={'request_id':req['request_id'],'category':req['category'],'label':req['label'],'command':req['argv'],
          'cwd':req['cwd'],'requested_timeout_seconds':req['timeout_seconds'],'receipt':ref(response),
          'request':ref(request),'status':res['status'],'charged_seconds':charge,
          'injected_interruption':receipt.get('injected_interruption',False),'ended_at':res.get('ended_at')}
    attempts.append(item)
    argv=req['argv']
    if 'study/train.py' not in argv and 'study/pilot.py' not in argv:continue
    out=Path(argv[argv.index('--out')+1]);pilot='study/pilot.py' in argv or (('--phase' in argv) and argv[argv.index('--phase')+1]=='pilot')
    metadata=json.loads((out/'started.json').read_text()) if (out/'started.json').exists() else {}
    ended=res['ended_at'];started=metadata.get('started_at')
    if not started:
        started=(datetime.datetime.fromisoformat(ended)-datetime.timedelta(seconds=charge)).isoformat()
    state='interrupted' if item['injected_interruption'] else ('succeeded' if res['status']=='completed' else 'failed')
    run_id='pilot61' if pilot else out.name.split('-a')[0]
    record={'schema_version':'0.2','record_type':'RunRecord','run_id':run_id,'attempt_id':req['request_id'],
      'attempt_number':int(out.name.rsplit('a',1)[-1]),'campaign_id':'c001','experiment_id':run_id,
      'started_at':started,'ended_at':ended,'inputs':[ref(request),ref('PROTOCOL-DRAFT.md' if pilot else 'campaigns/c001/protocol.json')],
      'outputs':[ref(p) for p in sorted(out.rglob('*')) if p.is_file()]+[ref(response)],
      'environment':{'python':platform.python_version(),'platform':platform.platform(),'broker_isolation_sha256':receipt['isolation_sha256'],'device':'cpu' if not pilot else 'pilot (CPU success; MPS failure retained)'},
      'model_revision':None,'data_revision':sha(out/'partition.npz') if (out/'partition.npz').exists() else sha(request),
      'usage':{'wall_seconds':charge,'money_usd':0,'tokens':0},'status':state,
      'error':None if state=='succeeded' else {'kind':'controlled_interruption' if item['injected_interruption'] else res['status'],'message':f"See immutable broker receipt and logs for {req['label']}"},
      'protocol_revision':'pilot-draft-v1' if pilot else protocol['revision'],'bundle_id':'b-9a39b70665ba909edb8abc13',
      'split':'pilot' if pilot else 'confirmation','command':argv,'exit_code':res.get('exit_code')}
    validate_record(record)
    write_json(Path('campaigns/c001/records/runs')/(out.name+'.json'),record)
attempts.sort(key=lambda r:r['ended_at'] or '')
write_json('attempts.json',{'attempts':attempts,'cutoff':'completed broker receipts at package assembly; final verification requests remain in .compute','charged_seconds':totals,'compute_request_count':sum(r['category']=='compute' for r in attempts)})
write_json('resource-usage.json',{'charged_seconds':totals,'ceilings_seconds':{'compute':1800,'setup':300},'compute_requests':sum(r['category']=='compute' for r in attempts),
 'attempt_limit':64,'source':'Workspace copies of authoritative broker receipts; final packaging/audit request charges occur after this snapshot.'})
print(json.dumps({'retained_attempts':len(attempts),'charged_seconds':totals}))
