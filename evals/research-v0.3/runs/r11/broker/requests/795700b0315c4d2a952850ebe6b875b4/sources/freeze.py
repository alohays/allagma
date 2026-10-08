"""Preconfirmation cost forecast and content-addressed protocol/source freeze."""
import datetime, hashlib, json, shutil
from pathlib import Path
from study import source_hashes, json_write, file_hash

def main():
    if Path('freeze.json').exists(): raise RuntimeError('Freeze is immutable')
    q=json.loads(Path('evidence/qualification.json').read_text()); assert q['status']=='passed'
    results=[json.loads(p.read_text()) for p in Path('evidence/attempts').glob('pilot-*/result.json')]
    assert results
    per_step=max(r['training_seconds']/(r['last_update']-r['first_update']+1) for r in results)
    per_cell=max(r['evaluation_seconds']/len(r['records']) for r in results)
    receipts=[json.loads(p.read_text()) for p in Path('.compute/responses').glob('*.json')]
    requests={p.stem:json.loads(p.read_text()) for p in Path('.compute/requests').glob('*.json')}
    consumed={cat:sum(r['result'].get('charged_seconds',0) for r in receipts if requests.get(r['request_id'],{}).get('category')==cat) for cat in ('setup','compute')}
    # Conservative overhead accounts for fresh workers and input/file preparation.
    costs=dict(training_200000_updates=200000*per_step,endpoint_evaluation_32_cells=32*per_cell,
               workers_and_io=24*3,analysis_and_verification=70,regenerate_all_32_cells=32*per_cell)
    nominal=sum(costs.values()); contingency=.15*(costs['training_200000_updates']+costs['endpoint_evaluation_32_cells'])
    forecast=dict(pilot_result_count=len(results),seconds_per_update=per_step,seconds_per_cell_evaluation=per_cell,
                  components_seconds=costs,nominal_remaining_seconds=nominal,contingency_seconds=contingency,
                  conservative_remaining_seconds=nominal+contingency,already_charged_seconds=consumed,
                  ceiling_compute_seconds=1800,ceiling_setup_seconds=300,planned_confirmation_requests=24,
                  forecast_within_ceiling=consumed['compute']+nominal+contingency<1800,
                  assumptions='Maximum observed pilot rates, serial workers, 15% training/evaluation contingency; actual broker receipts govern stopping.')
    json_write('evidence/forecast.json',forecast)
    if not forecast['forecast_within_ceiling']: raise RuntimeError('Forecast exceeds ceiling; do not open confirmation')
    sources=source_hashes();rev='science-v1-'+hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()[:16]
    archive=Path('evidence/source')/rev;archive.mkdir(parents=True)
    for path in sources: shutil.copyfile(path,archive/Path(path).name)
    shutil.copyfile('LICENSE',archive/'LICENSE')
    out=dict(format='ema-schedule-freeze-v1',frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             source_revision=rev,source_hashes=sources,protocol_sha256=file_hash('protocol.json'),
             qualification='evidence/qualification.json',qualification_sha256=file_hash('evidence/qualification.json'),
             forecast='evidence/forecast.json',forecast_sha256=file_hash('evidence/forecast.json'),
             archive=str(archive),device=q['device'],confirmation_data_seen=False)
    json_write('freeze.json',out);print(json.dumps(dict(freeze=out,forecast=forecast)),flush=True)

if __name__=='__main__':main()
