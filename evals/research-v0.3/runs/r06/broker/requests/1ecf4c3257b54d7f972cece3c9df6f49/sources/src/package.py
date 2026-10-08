"""Audit receipts, inventory deliverables, and verify the research package."""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import study as s


def ledger():
    root = Path('provenance')
    root.mkdir(exist_ok=True)
    copies = root / 'broker'
    copies.mkdir(exist_ok=True)
    entries = []
    totals = {'compute': 0., 'setup': 0.}
    for request in sorted(Path('.compute/requests').glob('*.json')):
        q = json.loads(request.read_text())
        rid = q['request_id']
        response = Path('.compute/responses') / (rid + '.json')
        if not response.exists():
            continue
        r = json.loads(response.read_text())
        category = q['category']
        charged = r.get('result', {}).get('charged_seconds', 0.)
        totals[category] += charged
        shutil.copyfile(request, copies / (rid + '-request.json'))
        for source in Path('.compute/responses').glob(rid + '*'):
            shutil.copyfile(source, copies / source.name)
        entries.append({'request_id': rid, 'category': category, 'label': q['label'],
                        'argv': q['argv'], 'timeout_seconds': q['timeout_seconds'],
                        'marked_attempt': q['attempt'], 'status': r['result']['status'],
                        'injected_interruption': r.get('injected_interruption', False),
                        'charged_seconds': charged, 'ended_at': r['result'].get('ended_at'),
                        'response': str(copies / (rid + '.json'))})
    entries.sort(key=lambda e: e['ended_at'] or '')
    compute_count = sum(e['category'] == 'compute' for e in entries)
    assert totals['compute'] <= 1800 and totals['setup'] <= 300 and compute_count <= 64
    obj = {'format': 'study-attempt-ledger-v1', 'cutoff_utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'All broker requests with available authoritative responses at ledger generation; the current packaging request and later final check remain in .compute.',
           'charged_seconds': totals, 'compute_request_count': compute_count, 'requests': entries}
    s.write_json(root / 'attempt-ledger.json', obj)
    return obj


def inventory():
    paths = []
    for directory in ['src', 'artifacts', 'analysis', 'provenance']:
        paths += [p for p in Path(directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [Path(p) for p in ['REPORT.md', 'review.json', 'REPRODUCE.md', 'submission.json', 'PROTOCOL.md', 'PLAN.md', 'research-workspace.json']]
    items = []
    for p in sorted(set(paths)):
        if not p.exists():
            raise RuntimeError('Missing deliverable: ' + str(p))
        role = ('training_evidence' if p.parts[0] == 'artifacts' else
                'derived_analysis' if p.parts[0] == 'analysis' else
                'execution_provenance' if p.parts[0] == 'provenance' else
                'source' if p.parts[0] == 'src' else 'document')
        items.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': s.sha(p), 'role': role})
    manifest = {'format': 'research-artifact-manifest-v1', 'task_id': 'modular-addition',
                'hash_algorithm': 'sha256', 'artifacts': items,
                'excluded': ['.venv (recreated from offline wheels and frozen dependency lock)',
                             'inputs binaries (supplied input hashes are in research-workspace.json)',
                             '.tmp and Python caches', '.compute live queue (portable cutoff snapshot in provenance/broker)',
                             'artifact-manifest.json itself (self-reference)', 'package-verification.json (generated after inventory)']}
    s.write_json('artifact-manifest.json', manifest)
    return manifest


def verify_package(manifest):
    for item in manifest['artifacts']:
        path = Path(item['path'])
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == item['bytes'] and s.sha(path) == item['sha256']
    submission = json.loads(Path('submission.json').read_text())
    assert submission['task_id'] == 'modular-addition'
    assert submission['execution_status'] in ['complete', 'partial', 'blocked']
    for key in ['manuscript', 'review', 'artifact_manifest', 'measurements']:
        assert not Path(submission[key]).is_absolute() and Path(submission[key]).is_file()
    for key in ['reproduce', 'recompute']:
        assert isinstance(submission[key]['argv'], list) and all(isinstance(v, str) for v in submission[key]['argv'])
        assert not Path(submission[key]['cwd']).is_absolute()
        assert Path(submission[key]['cwd']).is_dir()
    measurements = json.loads(Path(submission['measurements']).read_text())
    assert measurements['format'] == 'research-measurements-v1'
    assert Path(measurements['protocol']).is_file()
    expected = {(seed, wd) for seed in [1001, 1002, 1003, 1004] for wd in [0, 1]}
    observed = {(r['seed'], r['weight_decay']) for r in measurements['runs']}
    if submission['execution_status'] == 'complete':
        assert observed == expected and len(measurements['runs']) == 8
        assert all(r['updates'] == 100000 and r['phase'] == 'confirmation' for r in measurements['runs'])
    for run in measurements['runs']:
        for key in ['arrays', 'weights', 'curve', 'checkpoint', 'initial_weights', 'partition', 'config']:
            assert not Path(run[key]).is_absolute() and Path(run[key]).is_file()
        for aid in run['attempt_ids']:
            assert (Path('.compute/requests') / (aid + '.json')).is_file()
    analysis = json.loads(Path('analysis/results.json').read_text())
    assert analysis['execution_status'] == submission['execution_status']
    assert json.loads(Path('analysis/verification.json').read_text())['passed']
    assert json.loads(Path('analysis/analysis-tests.json').read_text())['passed']
    link_count = 0
    for document in ['REPORT.md', 'REPRODUCE.md']:
        for target in re.findall(r'\]\(([^)]+)\)', Path(document).read_text()):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            assert Path(target).exists(), (document, target)
            link_count += 1
    result = {'passed': True, 'verified_artifact_count': len(manifest['artifacts']),
              'verified_internal_document_links': link_count, 'measurement_runs': len(measurements['runs']),
              'submission_status': submission['execution_status'],
              'coverage': ['SHA256 and sizes of manifest entries', 'submission paths and argv schema',
                           'complete eight-cell grid', 'measurement evidence paths', 'broker attempt IDs',
                           'analysis verification result', 'scientific analysis known-answer result', 'local document links'],
              'not_executed': ['fresh full-study reproduction command (would need a second scientific budget)']}
    s.write_json('package-verification.json', result)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.check_only:
        manifest = json.loads(Path('artifact-manifest.json').read_text())
    else:
        info = ledger()
        print(json.dumps({'ledger_charges': info['charged_seconds'], 'requests': len(info['requests'])}))
        manifest = inventory()
    verify_package(manifest)


if __name__ == '__main__':
    main()
