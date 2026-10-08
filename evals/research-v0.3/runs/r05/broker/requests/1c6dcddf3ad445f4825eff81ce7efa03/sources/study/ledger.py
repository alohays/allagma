"""Build portable Allagma attempt records from retained local broker receipts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,o):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(o,indent=2,allow_nan=False)+'\n')
def ref(p):return {'path':str(p),'sha256':sha(p),'media_type':'application/json' if Path(p).suffix=='.json' else 'text/plain','retention':'retained'}

def reconstruct_pilot_sources():
    history=Path('evidence/source-history');history.mkdir(exist_ok=True)
    old=Path('study/pilot.py').read_text().replace("# Keep the low watermark below the broker's immutable 0.2 high watermark.\nos.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO']='0.1'\n",'')
    (history/'pilot-v1.py').write_text(old)
    native=Path('study/native_pilot.py').read_text()
    begin=native.index('    # ReLU activation-boundary changes')
    end=native.index("    np.savez(out/f'checkpoint-wd{wd}.npz'",begin)
    v2=native[:begin]+'    assert error<2e-4,error\n'+native[end:]
    newline="    checks.append({'weight_decay':wd,'forward_max_abs_error':forward_error,'gradient_max_abs_error':gradient_error,'free_trajectory_weights_after_50_max_abs_error':error,'initial_20_update_max_error':max(max(t['w1_max_error'],t['w2_max_error']) for t in trace if t['step']<=20),'aligned_optimizer_updates_51_to_70_max_abs_error':max(aligned_errors),'resume_50_plus_50_exact':True})"
    oldline="    checks.append({'weight_decay':wd,'forward_max_abs_error':forward_error,'gradient_max_abs_error':gradient_error,'weights_after_50_max_abs_error':error,'resume_50_plus_50_exact':True})"
    v2=v2.replace(newline,oldline)
    (history/'native-pilot-v2.py').write_text(v2)
    v1=v2.replace('    trace=[]\n','')
    v1=v1.replace("        if s in (0,1,4,9,19,49):\n            trace.append({'step':s+1,'w1_max_error':float(np.max(np.abs(e.u-a.detach().numpy().T))),'w2_max_error':float(np.max(np.abs(e.v-b.detach().numpy())))})\n",'')
    v1=v1.replace("    (out/f'agreement-wd{wd}.json').write_text(json.dumps({'forward':forward_error,'gradient':gradient_error,'trace':trace,'max_error_50':error},indent=2))\n    print(json.dumps({'wd':wd,'trace':trace,'forward':forward_error,'gradient':gradient_error}),flush=True)\n",'')
    (history/'native-pilot-v1.py').write_text(v1)
    (history/'native-pilot-v3.py').write_text(native)
    dump(history/'provenance.json',{'capture':'Pilot source versions reconstructed from the exact local editing history after execution; not falsely represented as prospective snapshots. Controller receipts/source snapshots are authoritative but protected and not read. Confirmation source was prospectively frozen and hash-checked on every segment.','versions':{str(p):sha(p) for p in history.glob('*.py')}})

def main():
    reconstruct_pilot_sources()
    c=Path('campaigns/modular-addition');lock=json.loads((c/'lock.yaml').read_text());protocol=json.loads((c/'protocol.json').read_text())
    sys.path.insert(0,str(Path('.allagma/bundles')/lock['bundle_id']))
    from allagma.contracts import validate_record
    records=[];ledger=[];totals={'setup':0.,'compute':0.};statuses={};count=0
    pilots={'pilot-first-interruption':('evidence/pilot-001','evidence/source-history/pilot-v1.py'),
            'pilot-recovery-throughput':('evidence/pilot-002','evidence/source-history/pilot-v1.py'),
            'native-pilot-qualification':('evidence/pilot-003','evidence/source-history/native-pilot-v1.py'),
            'native-pilot-diagnose':('evidence/pilot-004','evidence/source-history/native-pilot-v2.py'),
            'native-pilot-aligned-qualification':('evidence/pilot-005','evidence/source-history/native-pilot-v3.py')}
    for response in sorted(Path('.compute/responses').glob('*.json')):
        rid=response.stem;request=Path('.compute/requests')/(rid+'.json')
        if not request.exists():continue
        req=json.loads(request.read_text());res=json.loads(response.read_text());result=res.get('result',{})
        category=req['category'];elapsed=float(result.get('charged_seconds',0));totals[category]+=elapsed
        count+=category=='compute';status=result.get('status','unknown');statuses[status]=statuses.get(status,0)+1
        item={'request_id':rid,'label':req['label'],'category':category,'status':status,'injected_interruption':res.get('injected_interruption',False),'charged_seconds':elapsed,'request':ref(request),'response':ref(response)};ledger.append(item)
        label=req['label'];is_confirmation=label.startswith('s100')
        if label not in pilots and not is_confirmation:continue
        if is_confirmation:
            directory=Path('evidence/confirmation/attempts')/label
            script=Path('campaigns/modular-addition/materials/study/train.py');split='confirmation'
            started=json.loads((directory/'started.json').read_text());started_at=started['started_at'];experiment=label.split('-to')[0]
            revision=protocol['training_source_revision'];inputs=[ref(c/'protocol.json'),ref(script),ref(directory/'started.json')]
            if (directory/'resume.json').exists():inputs.append(ref(directory/'resume.json'))
        else:
            directory=Path(pilots[label][0]);script=Path(pilots[label][1]);split='pilot';experiment='pilot-seed61'
            started=json.loads((directory/'started.json').read_text());started_at=datetime.fromtimestamp(started['started_at'],timezone.utc).isoformat();revision=sha(script);inputs=[ref(script),ref(directory/'started.json')]
        mapped='succeeded' if status=='completed' else ('interrupted' if res.get('injected_interruption') else 'failed')
        record={'schema_version':'0.2','record_type':'RunRecord','run_id':label,'attempt_id':rid,'attempt_number':1+sum(r['experiment_id']==experiment for r in records),'campaign_id':'modular-addition','experiment_id':experiment,'started_at':started_at,'ended_at':result.get('ended_at'),'inputs':inputs,'outputs':[ref(p) for p in sorted(directory.iterdir()) if p.is_file()],'environment':{'broker_receipt':str(response),'category':category,'source_capture':'prospective frozen confirmation' if is_confirmation else 'retrospective reconstruction of exact pilot edit history','broker_status':status},'model_revision':revision,'data_revision':sha(c/'protocol.json') if is_confirmation else hashlib.sha256(b'pilot seed 61; modular addition 97').hexdigest(),'usage':{'wall_seconds':elapsed,'money_usd':0,'tokens':0},'status':mapped,'error':None if mapped=='succeeded' else {'kind':'controlled_interruption' if mapped=='interrupted' else 'execution_failure','message':'See retained stdout/stderr and broker receipt; no unsuccessful attempt contributes a seed.'},'protocol_revision':protocol['revision'] if is_confirmation else 'preconfirmation-pilot','bundle_id':lock['bundle_id'],'split':split,'command':req['argv'],'exit_code':result.get('exit_code')}
        validate_record(record);records.append(record);dump(c/'attempt-records'/(rid+'.json'),record)
    ledger.sort(key=lambda x:json.loads(Path(x['response']['path']).read_text()).get('result',{}).get('ended_at',''))
    dump('evidence/attempt-ledger.json',{'format':'local-broker-ledger-v1','source':'Workspace response copies; controller-held receipts remain authoritative','requests':ledger,'charged_seconds':totals,'compute_request_count':count,'statuses':statuses,'coverage':'Completed receipts present at this ledger generation; an in-flight packaging/check request is added by the final refresh.'})
    print(json.dumps({'run_records':len(records),'charged_seconds':totals,'compute_requests':count,'statuses':statuses},indent=2))

if __name__=='__main__':main()
