"""Broker-run final audit, receipt preservation and artifact manifest."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

def load(path): return json.loads(Path(path).read_text())
def dump(path,value): Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    sub=load('submission.json')
    assert sub['task_id']=='modular-addition'
    assert sub['execution_status'] in ['complete','partial','blocked']
    for field in ['manuscript','review','measurements']:
        p=Path(sub[field]); assert not p.is_absolute() and p.is_file()
    assert sub['artifact_manifest']=='artifact-manifest.json'
    for field in ['reproduce','recompute']:
        assert isinstance(sub[field]['argv'],list) and all(isinstance(a,str) for a in sub[field]['argv'])
        assert sub[field]['cwd']=='.'
    measurement=load(sub['measurements'])
    assert measurement['format']=='research-measurements-v1'
    assert measurement['task_id']=='modular-addition'
    assert Path(measurement['protocol']).is_file()
    runs=measurement['runs']
    if sub['execution_status']=='complete':
        assert len(runs)==8
        assert {(r['seed'],r['weight_decay']) for r in runs}=={(s,w) for s in [1001,1002,1003,1004] for w in [0,1]}
        assert not measurement['incomplete_runs'] and not measurement['missing_runs']
    for r in runs:
        assert r['phase']=='confirmation' and r['updates']==100000
        assert isinstance(r['curve'],list) and len(r['curve'])==1001
        assert r['curve'][0]['step']==0 and r['curve'][-1]['step']==100000
        assert all(r['curve'][i+1]['step']-r['curve'][i]['step']==100 for i in range(1000))
        for key in ['arrays','weights','checkpoint','configuration','initial_weights','partition','curve_path']:
            assert Path(r[key]).is_file() and not Path(r[key]).is_absolute()
        assert 0<=r['metrics']['train_accuracy']<=1 and 0<=r['metrics']['test_accuracy']<=1
        assert r['attempt_id'] in r['attempt_history']
    freeze=load('artifacts/protocol-freeze.json')
    for path,digest in freeze['source_sha256'].items(): assert sha(path)==digest,path
    assert load('analysis/verification.json')['status']=='passed'
    assert load('recomputed/verification.json')['status']=='passed'
    assert load('analysis/results.json')==load('recomputed/results.json')
    assert load('analysis/measurements.json')==load('recomputed/measurements.json')
    assert load('analysis/sensitivity.json')==load('recomputed/sensitivity.json')
    links=[]
    for document in ['REPORT.md','REPRODUCE.md','PROTOCOL.md']:
        for target in re.findall(r'\]\(([^)]+)\)',Path(document).read_text()):
            if '://' in target or target.startswith('#'): continue
            target=target.split('#')[0]
            assert Path(target).exists(),(document,target)
            links.append(dict(document=document,target=target))
    receipt_dir=Path('evidence/receipts')
    receipt_dir.mkdir(parents=True,exist_ok=True)
    attempts=[]
    for rp in sorted(Path('.compute/responses').glob('*.json')):
        response=load(rp)
        request_id=response['request_id']
        qp=Path('.compute/requests')/(request_id+'.json')
        request=load(qp)
        for original,name in [(qp,request_id+'-request.json'),(rp,request_id+'-response.json'),
            (rp.with_name(request_id+'-stdout.txt'),request_id+'-stdout.txt'),
            (rp.with_name(request_id+'-stderr.txt'),request_id+'-stderr.txt')]:
            if original.exists(): shutil.copyfile(original,receipt_dir/name)
        attempts.append(dict(request=request,response=response))
    attempts.sort(key=lambda x:x['response']['result'].get('ended_at',''))
    dump('analysis/final-attempts.json',attempts)
    usage={category:sum(a['response']['result'].get('charged_seconds',0) for a in attempts if a['request']['category']==category)
           for category in ['setup','compute']}
    counts={category:sum(a['request']['category']==category for a in attempts) for category in ['setup','compute']}
    injected=[a for a in attempts if a['response'].get('injected_interruption')]
    assert len(injected)==1
    assert usage['compute']<1800 and usage['setup']<300 and counts['compute']<64
    assert all(a['request']['timeout_seconds']<=180 for a in attempts)
    audit=dict(status='passed',task_id='modular-addition',execution_status=sub['execution_status'],
        completed_runs=len(runs),all_expected_updates=all(r['updates']==100000 for r in runs),
        all_frozen_source_and_protocol_hashes_match=True,
        evidence_only_recomputation='Results, measurements and all sensitivity objects exactly equal',
        document_links_checked=links,resource_usage_before_this_audit=usage,request_counts_before_this_audit=counts,
        interrupted_request_id=injected[0]['request']['request_id'],
        receipt_scope='All completed broker requests through the start of this audit. The current audit receipt is emitted afterwards under .compute/responses.',
        network='none',worker_concurrency=1)
    dump('analysis/package-verification.json',audit)
    include=[]
    for path in sorted(Path('.').rglob('*')):
        parts=path.parts
        if any(part.startswith('.venv') or part in ['.compute','.tmp','__pycache__','.git'] for part in parts): continue
        if not path.is_file() or path.is_symlink(): continue
        if str(path)=='artifact-manifest.json': continue
        role='input' if parts[0]=='inputs' else 'evidence' if parts[0] in ['artifacts','analysis','evidence','recomputed'] else 'source_or_document'
        include.append(dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size,role=role))
    manifest=dict(format='research-artifact-manifest-v1',task_id='modular-addition',
        created_at_utc=datetime.now(timezone.utc).isoformat(),files=include,
        exclusions=['artifact-manifest.json (self-reference)', '.venv* (rebuildable environments)',
            '.tmp and __pycache__ (temporary/cache files)',
            '.compute (live broker delivery area; completed receipts copied into evidence/receipts)'],
        source_revision=sha('study.py'),protocol_sha256=sha('protocol.json'),
        receipt_scope=audit['receipt_scope'])
    dump('artifact-manifest.json',manifest)
    for item in include:
        assert sha(item['path'])==item['sha256']
    print(json.dumps(dict(status='passed',manifest_files=len(include),resource_usage_before_this_audit=usage,
        request_counts_before_this_audit=counts,completed_runs=len(runs)),indent=2))

if __name__=='__main__': main()
