"""Read-only outcome/accounting aggregation under the frozen criteria."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from allagma.resources import summary

BASE=ROOT/'evals/research-v0.3'


def read(path,default=None):
    return json.loads(path.read_text()) if path.is_file() else default


def run_row(assignment):
    root=BASE/'runs'/assignment['run_id']
    native=read(root/'sessions/evaluation/native/session.json')
    outcome=read(root/'outcome.json',{})
    interruption=read(root/'broker/interruption.json')
    planned=None
    if interruption:
        response=read(root/'broker/requests'/interruption['request_id']/'response.json',{})
        result=response.get('result',{})
        planned={**interruption,'observed_status':result.get('status'),
                 'actual_timeout_observed':result.get('status')=='timed_out',
                 'charged_seconds':result.get('charged_seconds')}
    resources=summary(root/'resources')
    jobs=resources['entries'];statuses={}
    for entry in jobs:
        state=entry['result']['status'] if entry['result'] else 'unresolved'
        statuses[state]=statuses.get(state,0)+1
    row={**assignment,'native_status':native['status'] if native else 'not_started',
        'claimed_execution_status':None,'verified_completion':None,
        'numerical':None,'evidence_completeness':None,
        'interventions':read(root/'interventions.json',[]),
        'compute_seconds':resources['charged_seconds'].get('compute'),
        'setup_seconds':resources['charged_seconds'].get('setup'),
        'compute_requests':resources['attempts'],'job_outcomes':statuses,
        'native_wall_seconds':native.get('wall_seconds') if native else None,
        'native_usage_events':native.get('usage',[]) if native else [],
        'peak_native_rss_bytes':native.get('peak_rss_bytes') if native else None,
        'peak_worker_rss_bytes':max((entry['result'].get('peak_rss_bytes') or 0 for entry in jobs if entry['result']),default=None),
        'peak_native_storage_bytes':native.get('peak_storage_bytes') if native else None,
        'observed_model_settings_match':outcome.get('observed_model_settings_match'),
        'inputs_unchanged':outcome.get('common_inputs_unchanged'),
        'runtime_settings_unchanged':outcome.get('runtime_settings_unchanged'),
        'fresh_single_session':outcome.get('fresh_single_session'),
        'subsequent_coordinator_messages':outcome.get('subsequent_coordinator_messages'),
        'planned_interruption':planned,
        'scope':'Raw usage fields are reported separately; cached/reasoning counts are not added again to other token fields.'}
    score=read(root/'score.json')
    row['original_scorer_outcome']=score
    corrected=read(root/'score-corrected.json')
    row['scoring_correction_applied']=corrected is not None
    if corrected:score=corrected
    if score:
        row['claimed_execution_status']=score.get('claimed_execution_status')
        row['numerical']=score.get('numerical',{'status':score.get('status'),'error':score.get('error')})
    review=read(root/'substantive-review.json')
    if review:
        row['verified_completion']=review.get('completion_verified')
        row['evidence_completeness']=review.get('evidence_items')
    return row


def aggregate():
    frozen=read(BASE/'frozen/freeze.json')
    rows=[run_row(item) for item in frozen['run_order']]
    return {'format':'research-comparison-outcomes-v1','assigned_runs':12,
        'terminal_native_runs':sum(row['native_status'] not in ('running','not_started') for row in rows),
        'verified_complete_packages':sum(row['verified_completion'] is True for row in rows),
        'pending_reviews':sum(row['verified_completion'] is None for row in rows),'runs':rows,
        'limits':'Three selected task families, two sessions per condition. No general superiority inference. Scientific replicate counts are study-owned and are not increased by repeated agent runs.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    value=aggregate();args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():raise SystemExit('Use a new summary path to retain previous snapshots')
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:value[key] for key in ('assigned_runs','terminal_native_runs','verified_complete_packages','pending_reviews')}))
