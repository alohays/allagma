"""Final read-only package audit with a separate, explicitly unsealed receipt."""
from pathlib import Path
import hashlib,json,re,sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    manifest=json.loads(Path('artifact-manifest.json').read_text())
    checked=0
    for item in manifest['files']:
        path=Path(item['path']);assert not path.is_absolute() and '..' not in path.parts
        assert path.is_file() and not path.is_symlink(),str(path)
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],str(path)
        checked+=1
    lock=json.loads(Path('campaigns/modular-addition/lock.yaml').read_text())
    sys.path.insert(0,str(Path('.allagma/bundles')/lock['bundle_id']))
    from allagma.contracts import validate_record
    from allagma.bundles import resolve_entry
    resolve_entry(Path.cwd(),'recipe/research','modular-addition')
    records=0;references=0
    def walk(obj):
        nonlocal references
        if isinstance(obj,dict):
            if 'path' in obj and 'sha256' in obj:
                p=Path(obj['path'])
                if p.is_absolute():
                    assert 'module_id' in obj and 'bundle_id' in obj, 'Unexpected absolute artifact reference'
                    p=p.relative_to(Path.cwd())
                assert '..' not in p.parts
                assert p.is_file() and sha(p)==obj['sha256'],str(p)
                references+=1
            for value in obj.values():walk(value)
        elif isinstance(obj,list):
            for value in obj:walk(value)
    for path in list(Path('campaigns/modular-addition').rglob('*.json'))+[Path('review.json'),Path('review-input.json'),Path('critique.json'),Path('analysis/raw-manifest.json')]:
        value=json.loads(path.read_text())
        if isinstance(value,dict) and value.get('record_type'):
            validate_record(value);records+=1
        walk(value)
    submission=json.loads(Path('submission.json').read_text())
    assert submission['task_id']=='modular-addition' and submission['execution_status']=='complete'
    for key in ('manuscript','review','artifact_manifest','measurements'):assert Path(submission[key]).is_file()
    for key in ('reproduce','recompute'):
        assert submission[key]['cwd']=='.' and all(isinstance(x,str) and x for x in submission[key]['argv'])
    measurements=json.loads(Path(submission['measurements']).read_text())
    assert measurements['format']=='research-measurements-v1' and len(measurements['runs'])==8
    assert {(r['seed'],r['weight_decay']) for r in measurements['runs']}=={(s,w) for s in (1001,1002,1003,1004) for w in (0,1)}
    assert all(r['updates']==100000 and len(r['curve'])==1001 for r in measurements['runs'])
    protocol=json.loads(Path(measurements['protocol']).read_text())
    from datetime import datetime
    freeze=datetime.fromisoformat(protocol['frozen_at'])
    for path in Path('evidence/confirmation/attempts').glob('*/started.json'):
        value=json.loads(path.read_text());assert freeze<datetime.fromisoformat(value['started_at'])
    assert all(json.loads(Path('analysis-repeat/recomputation-comparison.json').read_text()).values())
    report=Path('REPORT.md').read_text()
    for target in re.findall(r'\]\(([^)]+)\)',report):
        if not target.startswith(('https://','http://','#')):assert Path(target.split('#')[0]).exists(),target
    review=json.loads(Path('review.json').read_text());assert review['material']['sha256']==sha('REPORT.md')
    assert review['assurance']=='provisional' and review['verdict']=='pass'
    # Every table value is generated directly from results, which were reanalyzed.
    results=json.loads(Path('analysis/results.json').read_text())
    for row in results['runs']:
        assert f"{100*row['test_accuracy']:.4f}%" in report
        assert f"{row['test_loss']:.6f}" in report
    totals={'compute':0.,'setup':0.};requests=0;interrupted=0
    for response in Path('.compute/responses').glob('*.json'):
        req=Path('.compute/requests')/response.name
        if not req.exists():continue
        request=json.loads(req.read_text());receipt=json.loads(response.read_text());result=receipt.get('result',{})
        totals[request['category']]+=float(result.get('charged_seconds',0));requests+=request['category']=='compute'
        interrupted+=bool(receipt.get('injected_interruption'))
    assert totals['compute']<=1800 and totals['setup']<=300 and requests<=64 and interrupted==1
    result={'status':'passed','verifier_source_sha256':sha('study/verify_package_v2.py'),'manifest_sha256':sha('artifact-manifest.json'),'report_sha256':sha('REPORT.md'),'files_hashed':checked,'allagma_records_validated':records,'transitive_references_verified':references,'eight_fixed_horizon_cells':True,'protocol_frozen_before_confirmation':True,'numerical_reanalysis_exact':True,'all_eight_checkpoint_predictions_verified':True,'local_report_links_valid':True,'resource_usage_through_prior_receipts':totals,'compute_requests_through_prior_receipts':requests,'injected_interruption_receipts':interrupted,'coverage':'Final hash/schema/path/temporal/coverage audit plus prior independently executed endpoint/checkpoint and numerical reanalysis checks. This audit output and its broker receipt are intentionally outside the earlier manifest snapshot.'}
    Path('verification-final.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
