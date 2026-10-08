"""Final artifact accounting and validation, run through the local broker."""
import datetime,json,re,shutil
from pathlib import Path
from study import file_hash,json_write

def ledger():
    rows=[]
    for request in sorted(Path('.compute/requests').glob('*.json')):
        q=json.loads(request.read_text());response=Path('.compute/responses')/(q['request_id']+'.json')
        row=dict(request_id=q['request_id'],category=q['category'],label=q['label'],argv=q['argv'],cwd=q['cwd'],
                 timeout_seconds=q['timeout_seconds'],marked_attempt=q['attempt'],request=str(request),request_sha256=file_hash(request))
        if response.exists():
            r=json.loads(response.read_text());row.update(response=str(response),response_sha256=file_hash(response),
                status=r['result']['status'],charged_seconds=r['result'].get('charged_seconds',0),
                injected_interruption=r.get('injected_interruption',False),ended_at=r['result'].get('ended_at'),
                peak_rss_bytes=r['result'].get('peak_rss_bytes'),peak_storage_bytes=r['result'].get('peak_storage_bytes'))
            for stream in ('stdout','stderr'):
                path=Path('.compute/responses')/(q['request_id']+f'-{stream}.txt')
                if path.exists():row[stream]=str(path);row[stream+'_sha256']=file_hash(path)
        else:row['status']='current request awaiting its final broker receipt'
        rows.append(row)
    totals={c:sum(r.get('charged_seconds',0) for r in rows if r['category']==c) for c in ('setup','compute')}
    result=dict(format='broker-ledger-v1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),requests=rows,
                charged_seconds_for_completed_receipts=totals,compute_request_count=sum(r['category']=='compute' for r in rows),
                accounting_note='Current package request has no completed receipt yet; its authoritative receipt remains under .compute/responses after this process exits. No receipt is overwritten.',
                ceilings=json.loads(Path('inputs/RESOURCES.json').read_text())['profile'])
    assert totals['compute']<1800 and totals['setup']<300 and result['compute_request_count']<=64
    json_write('evidence/broker-ledger.json',result)
    return result

def report_check():
    from build_report import render
    report=Path('REPORT.md').read_text();expected=render('report-r2')
    assert report==expected, 'Report differs from audited rendering'
    assert Path('analysis/tables.md').read_text() in report
    s=json.loads(Path('analysis/summary.json').read_text());v=json.loads(Path('evidence/verification.json').read_text())
    assert v['status']=='passed' and v['cells']==32 and v['summary_statistics_checked']==90
    supporting=json.loads(Path('evidence/supporting-verification.json').read_text())
    assert supporting['status']=='passed' and len(supporting['coverage_summary_checks'])==12 and len(supporting['independent_reference_checks'])==8
    freeze=json.loads(Path('freeze.json').read_text())
    for path,h in {**freeze['source_hashes'],**freeze['auxiliary_hashes']}.items():assert file_hash(path)==h
    regenerated=[]
    for d in ('moons','gmm8'):
        r=json.loads(Path(f'evidence/regeneration-{d}.json').read_text());assert r['status']=='passed' and r['variants_checked']==48
        regenerated+=r['results']
    assert len(regenerated)==96
    assert all(x['exact_equal'] for x in regenerated)
    review=json.loads(Path('review.json').read_text())
    assert file_hash(review['material']['path'])==review['material']['sha256']
    assert review['material']['revision']=='report-r1' and review['response_revision']=='report-r2'
    links=re.findall(r'\]\(([^)]+)\)',report)
    missing=[link for link in links if not link.startswith(('http:','https:')) and not Path(link).is_file()]
    # The artifact manifest is generated after this check.
    missing=[link for link in missing if link!='artifact-manifest.json']
    assert not missing,missing
    return dict(status='passed',manuscript_sha256=file_hash('REPORT.md'),review_sha256=file_hash('review.json'),
                report_revision='report-r2',raw_data_audit='evidence/verification.json',
                verified_cells=32,verified_model_states=96,verified_seed_summaries=90,
                regenerated_states=len(regenerated),regeneration_all_bitwise_exact=all(x['exact_equal'] for x in regenerated),
                max_regeneration_absolute_error=max(x['max_absolute_error'] for x in regenerated),
                report_render_matches_verified_analysis=True,all_report_evidence_links_exist=True,
                supporting_summaries_verified=True,frozen_sources_unchanged=True,
                confirmation_retraining_repeated=False,full_reproduction_entrypoint_provided=True)

def main():
    accounting=ledger()
    submission=dict(task_id='ema-schedule',execution_status='complete',manuscript='REPORT.md',review='review.json',
                    artifact_manifest='artifact-manifest.json',measurements='measurements.json',
                    reproduce=dict(argv=['python3','reproduce.py','--env','.reproduce-venv','--root','reproduced'],cwd='.'),
                    recompute=dict(argv=['python3','inputs/compute.py','--category','compute','--label','recompute-retained-analysis','--timeout','60','--','.venv/bin/python','analyze.py'],cwd='.'),
                    completion_assessment='All 32 confirmation cells from 24 trajectories completed. All 96 saved model states and sample arrays retained, independently recomputed and regenerated. Four seeds per dataset limit inference; no general mechanism or universal EMA benefit claimed.',
                    verification='evidence/final-verification.json',license='LICENSE',disclosure='AI-generated/adapted code and reporting; author self-review, not independent peer review')
    json_write('submission.json',submission)
    audit=report_check();audit['budget_accounting']='evidence/broker-ledger.json'
    json_write('evidence/final-verification.json',audit)
    files=[]
    for root in ('evidence','analysis','inputs'):
        files.extend(p for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(p for p in Path('.').iterdir() if p.is_file() and p.name not in ('artifact-manifest.json',))
    # Include broker request/response files that already exist. The current receipt
    # necessarily appears only after this process returns; its request is indexed.
    files.extend(p for root in ('.compute/requests','.compute/responses') for p in Path(root).glob('*') if p.is_file())
    files=sorted(set(files),key=str)
    artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=file_hash(p)) for p in files]
    manifest=dict(format='research-artifact-manifest-v1',task_id='ema-schedule',material_revision='report-r2',
                  generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),artifacts=artifacts,
                  exclusions=['.venv and .reproduce-venv environments (rebuild from locked wheels)',
                              '.tmp and Python caches (non-scientific scratch)',
                              'this manifest (self-reference)',
                              'broker response for the currently running package request, which is retained after process exit'],
                  canonical_measurements='measurements.json',canonical_protocol='protocol.json',canonical_report='REPORT.md',
                  regular_npz_arrays_load_with_allow_pickle_false=True)
    json_write('artifact-manifest.json',manifest)
    # Verify the complete declared closure after writing it.
    for item in artifacts:
        p=Path(item['path']);assert p.is_file() and p.stat().st_size==item['bytes'] and file_hash(p)==item['sha256']
    print(json.dumps(dict(status='passed',artifact_count=len(artifacts),audit=audit,
                         completed_receipt_charges=accounting['charged_seconds_for_completed_receipts'],
                         compute_request_count=accounting['compute_request_count'])),flush=True)

if __name__=='__main__':main()
