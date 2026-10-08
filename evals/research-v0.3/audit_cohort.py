"""Read-only checks of frozen trial identity, accounting and terminal controls.

This supplements, and never replaces, per-run scientific/evidence review.
Current storage totals are not interpreted as continuous historical peak bounds.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from allagma.resources import storage_bytes, summary

BASE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(allow_partial=False):
    frozen = read(BASE / 'frozen/freeze.json')
    rows, pending, errors, seen_threads = [], [], [], set()
    for assignment in frozen['run_order']:
        run = assignment['run_id']
        base = BASE / 'runs' / run
        outcome_path = base / 'outcome.json'
        if not outcome_path.exists():
            pending.append(run)
            continue
        outcome = read(outcome_path)
        native_dir = base / 'sessions/evaluation/native'
        native = read(native_dir / 'session.json')
        policy = read(base / 'resources/policy.json')
        expected_profile = frozen['profiles']['profiles'][assignment['task']]
        resources = summary(base / 'resources')
        checks = {
            'common_inputs_unchanged_at_exit': outcome['common_inputs_unchanged'] is True,
            'observed_model_settings_match': outcome['observed_model_settings_match'] is True,
            'runtime_settings_unchanged': outcome['runtime_settings_unchanged'] is True,
            'fresh_single_session': outcome['fresh_single_session'] is True,
            'zero_subsequent_coordinator_messages': outcome['subsequent_coordinator_messages'] == 0,
            'requested_model_settings_match': native['settings'] == frozen['settings'],
            'cli_identity_matches': native['cli_sha256'] == frozen['cli_sha256'],
            'adapter_identity_matches': native['adapter_sha256'] == frozen['controller_files']['adapters/codex/session.py']
                and sha(native_dir / 'adapter.py') == native['adapter_sha256'],
            'runtime_config_receipt_matches': sha(native_dir / 'runtime-config.toml') == native['runtime_config_sha256'],
            'public_events_receipt_matches': sha(native_dir / 'events.jsonl') == native['events_sha256'],
            'no_project_model_pin_written': native['project_model_config_written'] is False,
            'native_deadline_matches': native['timeout_seconds'] == frozen['profiles']['native_wall_seconds'],
            'native_wall_within_deadline': native['wall_seconds'] <= native['timeout_seconds'],
            'resource_profile_matches': policy['profile'] == expected_profile,
            'resource_reservations_resolved': all(e['result'] is not None for e in resources['entries']),
            'charged_categories_within_budgets': all(resources['charged_seconds'][k] <= v for k, v in expected_profile['budgets_seconds'].items()),
            'compute_requests_within_limit': resources['attempts'] <= expected_profile['attempt_limit'],
            'supervisor_sources_match': all(e['reservation']['supervisor_sha256'] == frozen['controller_files']['allagma/resources.py'] for e in resources['entries']),
            'reservation_policy_hashes_match': all(e['reservation']['profile_sha256'] == policy['profile_sha256'] for e in resources['entries']),
            'command_timeouts_within_profile': all(e['reservation']['timeout_seconds'] <= expected_profile['command_timeout_seconds'][e['reservation']['category']] for e in resources['entries']),
        }
        threads = native['thread_ids']
        checks['one_unique_new_thread'] = len(threads) == 1 and threads[0] not in seen_threads
        seen_threads.update(threads)
        marker = read(base / 'broker/interruption.json') if (base / 'broker/interruption.json').exists() else None
        response = read(base / 'broker/requests' / marker['request_id'] / 'response.json') if marker else None
        checks['controlled_interruption_retained'] = response is not None and response.get('injected_interruption') is True
        workspace_bytes = storage_bytes(Path(policy['workdir']))
        runtime_bytes = storage_bytes(base / 'sessions/evaluation/runtime')
        checks['current_terminal_workspace_within_cap'] = workspace_bytes <= expected_profile['storage_limit_bytes']
        checks['current_terminal_native_storage_within_cap'] = workspace_bytes + runtime_bytes <= native['storage_limit_bytes']
        stops = [e['job'] for e in resources['entries'] if e['result'] and e['result']['status'] in
                 ('memory_exceeded', 'storage_exceeded', 'orphaned_children', 'abandoned')]
        failed = [name for name, passed in checks.items() if not passed]
        errors.extend({'run_id': run, 'check': name} for name in failed)
        rows.append({**assignment, 'status': 'pass' if not failed else 'fail', 'checks': checks,
                     'native_status': native['status'], 'thread_ids': threads,
                     'charged_seconds': resources['charged_seconds'], 'compute_requests': resources['attempts'],
                     'current_workspace_bytes': workspace_bytes, 'current_private_runtime_bytes': runtime_bytes,
                     'controlled_interruption_status': response['result']['status'] if response else None,
                     'resource_stop_jobs': stops})
    if pending and not allow_partial:
        errors.append({'check': 'all_assigned_runs_terminal', 'pending': pending})
    return {'format': 'allagma-frozen-cohort-control-audit-v1',
            'status': 'fail' if errors else 'partial' if pending else 'pass',
            'terminal_runs_checked': len(rows), 'unique_native_threads': len(seen_threads),
            'pending_runs': pending, 'runs': rows, 'errors': errors,
            'scope': 'Retained CLI/adapter/model/config/input observations, actual unique sessions, supervisor hashes, finite-accounting limits, controlled interruption and current terminal storage. Per-run scientific review remains separate; sampled RSS and unobserved historical storage peaks are not continuously bounded by this audit. No private runtime content is exported.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Use a new cohort-audit receipt')
    result = audit(args.allow_partial)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'terminal_runs_checked', 'unique_native_threads', 'pending_runs', 'errors')}))
    raise SystemExit(1 if result['errors'] else 0)
