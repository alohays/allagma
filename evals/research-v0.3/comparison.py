"""Descriptive, lossless comparison of the twelve assigned frozen outcomes.

This postprocessing helper does not score candidates or change frozen criteria.
Missing numerical or usage evidence remains missing, never silently zero-filled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

TASKS = ('core-culp', 'modular-addition', 'ema-schedule')
CONDITIONS = ('plain', 'allagma')
USAGE = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')
METRICS = ('numerical_fraction', 'evidence_score', 'completed', 'compute_seconds',
           'setup_seconds', 'native_wall_seconds', 'input_tokens', 'cached_input_tokens',
           'output_tokens', 'reasoning_output_tokens')


def compact(row):
    numerical = row.get('numerical') or {}
    correct, total = numerical.get('correct'), numerical.get('total')
    evidence = row.get('evidence_completeness')
    value = {name: row.get(name) for name in (
        'run_id', 'task', 'condition', 'replicate', 'native_status',
        'claimed_execution_status', 'verified_completion', 'compute_seconds',
        'setup_seconds', 'compute_requests', 'job_outcomes', 'native_wall_seconds',
        'peak_native_rss_bytes', 'peak_worker_rss_bytes', 'peak_native_storage_bytes',
        'observed_model_settings_match', 'inputs_unchanged', 'scoring_correction_applied')}
    value.update(numerical_correct=correct, numerical_total=total,
                 numerical_fraction=correct / total if total else None,
                 evidence_score=sum(item['score'] for item in evidence) if evidence is not None else None,
                 evidence_items=evidence,
                 completed=int(row['verified_completion']) if row.get('verified_completion') is not None else None,
                 intervention_count=len(row.get('interventions', [])),
                 interventions=row.get('interventions', []))
    # These fields may overlap by provider definition. Never add them together.
    events = row.get('native_usage_events', [])
    for field in USAGE:
        value[field] = sum(e[field] for e in events) if events and all(e.get(field) is not None for e in events) else None
    original = row.get('original_scorer_outcome') or {}
    value['original_scorer_status'] = original.get('status', 'scored' if original.get('numerical') else 'missing')
    value['original_scorer_error'] = original.get('error')
    return value


def compare(summary, *, allow_partial=False):
    rows = summary['runs']
    expected = {(task, condition, replicate) for task in TASKS for condition in CONDITIONS for replicate in (1, 2)}
    assignments = {(r['task'], r['condition'], r['replicate']) for r in rows}
    if len(rows) != 12 or len({r['run_id'] for r in rows}) != 12 or assignments != expected:
        raise ValueError('Exactly twelve unique assigned task/condition/replicate runs are required')
    pending = [r['run_id'] for r in rows if r.get('verified_completion') is None
               or r.get('native_status') in ('not_started', 'running')]
    if pending and not allow_partial:
        raise ValueError('Unfinished evaluation or reviews: ' + ', '.join(pending))
    compact_rows = [compact(r) for r in rows]
    pairs = []
    grouped = []
    for task in TASKS:
        for replicate in (1, 2):
            values = {r['condition']: r for r in compact_rows if r['task'] == task and r['replicate'] == replicate}
            plain, allagma = values['plain'], values['allagma']
            differences = {metric: allagma[metric] - plain[metric]
                           if allagma['completed'] is not None and plain['completed'] is not None
                           and allagma[metric] is not None and plain[metric] is not None else None
                           for metric in METRICS}
            pairs.append({'task': task, 'replicate': replicate,
                          'plain_run': plain['run_id'], 'allagma_run': allagma['run_id'],
                          'direction': 'Allagma minus plain Codex', 'differences': differences})
        for condition in CONDITIONS:
            selected = [r for r in compact_rows if r['task'] == task and r['condition'] == condition]
            metrics = {}
            for name in METRICS:
                values = [r[name] for r in selected if r['completed'] is not None and r[name] is not None]
                metrics[name] = {'observed': len(values), 'assigned': 2,
                                 'mean': statistics.mean(values) if values else None,
                                 'minimum': min(values) if values else None,
                                 'maximum': max(values) if values else None}
            grouped.append({'task': task, 'condition': condition, 'metrics': metrics})
    return {'format': 'allagma-descriptive-comparison-v1',
            'status': 'partial' if pending else 'complete', 'pending_runs': pending,
            'runs': compact_rows, 'paired_contrasts': pairs, 'within_task_variability': grouped,
            'verified_complete_packages': sum(r['completed'] == 1 for r in compact_rows),
            'scope': 'All assigned runs retained. Task-specific two-session descriptive ranges and six paired agent-session contrasts; no population confidence interval or general superiority claim. Repeated agent sessions do not add independent scientific seeds.'}


def number(value, digits=2):
    return 'NA' if value is None else f'{value:,.{digits}f}'


def render(result):
    lines = ['# Frozen local research-workflow comparison', '',
             f"Status: **{result['status']}**. Verified complete original packages: {result['verified_complete_packages']}/12.", '',
             'This report is generated from retained scoring, review and resource receipts.',
             'A native process exit, numerical correctness and package completion are distinct.',
             'Missing evidence is shown as NA; it is not converted to zero or removed from the assigned cohort.', '']
    if result['pending_runs']:
        lines += ['Pending runs/reviews: ' + ', '.join(result['pending_runs']) + '. This is an interim report, not a completed evaluation.', '']
    lines += ['## Assigned outcomes', '',
              '| Run | Task | Condition | Replicate | Native | Numerical | Evidence /8 | Verified complete |',
              '| --- | --- | --- | ---: | --- | ---: | ---: | --- |']
    for r in result['runs']:
        numeric = f"{r['numerical_correct']}/{r['numerical_total']}" if r['numerical_total'] else 'NA'
        completion = 'pending' if r['completed'] is None else 'yes' if r['completed'] else 'no'
        lines.append(f"| {r['run_id']} | {r['task']} | {r['condition']} | {r['replicate']} | {r['native_status']} | {numeric} | {number(r['evidence_score'], 0)} | {completion} |")
    lines += ['', '## Per-run evidence gaps and process outcomes', '']
    for r in result['runs']:
        if r['completed'] is None:
            lines += [f"- {r['run_id']}: review pending; no completion determination."]
            continue
        gaps = [item['reason'] for item in r['evidence_items'] or [] if item['score'] == 0]
        text = '; '.join(gaps).rstrip('.') if gaps else 'all eight evidence items pass'
        jobs = ', '.join(f'{k}={v}' for k, v in sorted((r['job_outcomes'] or {}).items()))
        lines += [f"- {r['run_id']}: {text}. Process outcomes: {jobs}. Subsequent recorded interventions: {r['intervention_count']}."]
        if r['original_scorer_error']:
            lines += [f"  Original scorer: {r['original_scorer_status']}; {r['original_scorer_error']}. Compatibility-corrected evidence is reported separately."]
    lines += ['', '## Resource use', '',
              'Seconds are measured/charged by the retained supervisors. RSS and storage are sampled observations,',
              'not proofs of a strict instantaneous bound; RSS omits some GPU allocations.', '',
              '| Run | Compute s | Setup s | Compute requests | Native s | Input tokens | Cached input | Output tokens | Reasoning output |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in result['runs']:
        lines.append('| ' + ' | '.join([r['run_id'], number(r['compute_seconds']), number(r['setup_seconds']),
                     number(r['compute_requests'], 0), number(r['native_wall_seconds']),
                     *[number(r[k], 0) for k in USAGE]]) + ' |')
    lines += ['', 'Cached-input and reasoning-output fields are reported separately and are never added again to other token fields.',
              'Scientific requests, including failures, are counted separately from the planned interruption and any coordinator intervention.', '',
              '## Six paired contrasts', '',
              'Each contrast is Allagma minus plain Codex within the same task and replicate block.',
              'Positive correctness/evidence/completion values favor Allagma; positive time/token differences indicate greater recorded use.', '',
              '| Task | Replicate | Numerical fraction Δ | Evidence Δ | Completion Δ | Compute s Δ | Native s Δ |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for pair in result['paired_contrasts']:
        d = pair['differences']
        lines.append('| ' + ' | '.join([pair['task'], str(pair['replicate']), number(d['numerical_fraction'], 4),
                     number(d['evidence_score'], 0), number(d['completed'], 0),
                     number(d['compute_seconds']), number(d['native_wall_seconds'])]) + ' |')
    lines += ['', 'The companion JSON retains all token contrasts and within-task means, ranges and observed/assigned denominators.',
              'Pending runs may show accrued costs, but do not enter paired contrasts or within-task outcome averages.',
              'Means with fewer observed values do not summarize unobserved outcomes; consult the full assigned-outcome table.', '',
              '## Interpretation limits', '',
              'Two fresh sessions per condition and three selected task families cannot establish broad research superiority.',
              'The families were used during development; final sessions and confirmation seeds are separate, but the task families are not unseen.',
              'Repeated agents executing the same seed plan do not increase a study’s independent scientific sample size.', '',
              'CULP is a locally selected CORE-Bench training task with a curated wheelhouse and added evidence requirements, not a leaderboard result.',
              'Both conditions receive the same broker, measurement contract and finite ceilings. Model/settings/input matches and any violations',
              'remain per-run observations; a service-side model revision that is not exposed cannot be claimed controlled.', '',
              'The frozen shared broker has a reproduced MPS allocator high/low-watermark mismatch. CPU fallback or other candidate recovery',
              'is part of these frozen outcomes. These results do not measure the GPU performance of a later correction.',
              'The inline-curve parser correction is applied uniformly in a separate scorer; original receipts and the exact correction are retained.',
              'Post-evaluation package repairs and controller validation costs must be reported separately from these original agent outcomes.', '',
              'No population confidence interval is presented for workflow effects: the two-session task-specific ranges are descriptive.',
              'Same-model author critique and controller checks are provisional; neither is independent scientific peer review.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    result = compare(json.loads(args.summary.read_text()), allow_partial=args.allow_partial)
    result['source_summary_sha256'] = hashlib.sha256(args.summary.read_bytes()).hexdigest()
    result['postprocessor_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.destination.mkdir(parents=True, exist_ok=False)
    (args.destination / 'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    (args.destination / 'REPORT.md').write_text(render(result))
    print(json.dumps({'status': result['status'], 'pending_runs': result['pending_runs'],
                      'verified_complete_packages': result['verified_complete_packages']}))
