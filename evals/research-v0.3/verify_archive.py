"""Verify retained freeze and input identities independently of current source.

The original evaluate.py verify command guards launches against changes in the
current checkout/model/CLI. After a separately versioned release repair, this
read-only check verifies historical stored bytes without relabeling the repair
as the source evaluated by the frozen cohort.
"""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(*, allow_missing_packages=False):
    frozen = json.loads((BASE / 'frozen/freeze.json').read_text())
    errors = []
    for name, expected in frozen['controller_files'].items():
        path = BASE / 'frozen/source' / name
        if not path.is_file() or sha(path) != expected:
            errors.append({'kind': 'frozen-source', 'path': name})
    groups = {}
    packages = []
    missing = []
    for run in frozen['run_order']:
        root = BASE / 'runs' / run['run_id']
        prepared = json.loads((root / 'prepared.json').read_text())
        inputs = prepared['common_inputs']
        task = run['task']
        if task in groups and groups[task] != inputs:
            errors.append({'kind': 'common-input-pairing', 'run': run['run_id']})
        groups[task] = inputs
        for name, expected in frozen['materials'][task].items():
            if inputs.get('materials/' + name) != expected:
                errors.append({'kind': 'frozen-material', 'run': run['run_id'], 'path': name})
        originals = {'BRIEF.md': 'evals/research-v0.3/briefs/' + task + '.md',
                     'COMPUTE.md': 'adapters/local-process/COMPUTE.md',
                     'compute.py': 'adapters/local-process/compute_client.py'}
        for name, original in originals.items():
            if inputs.get(name) != frozen['controller_files'][original]:
                errors.append({'kind': 'frozen-common-interface', 'run': run['run_id'], 'path': name})
        policy = json.loads((root / 'resources/policy.json').read_text())
        if policy['profile'] != frozen['profiles']['profiles'][task]:
            errors.append({'kind': 'resource-profile', 'run': run['run_id']})
        index_path = root / 'package/package-index.json'
        if not index_path.exists():
            missing.append(run['run_id'])
            continue
        index = json.loads(index_path.read_text())
        files = {**index['files'], **index['external_wheels']}
        for name, expected in inputs.items():
            if files.get('inputs/' + name, {}).get('sha256') != expected:
                errors.append({'kind': 'retained-input', 'run': run['run_id'], 'path': name})
        for part in index['parts']:
            path = index_path.parent / part['path']
            if not path.is_file() or sha(path) != part['sha256']:
                errors.append({'kind': 'retained-part', 'run': run['run_id'], 'path': part['path']})
        supplement = index_path.parent / 'terminal-queue-index.json'
        if supplement.exists():
            addition = json.loads(supplement.read_text())
            if addition['package_index_sha256'] != sha(index_path):
                errors.append({'kind': 'supplement-binding', 'run': run['run_id']})
            for name, entry in addition['files'].items():
                path = index_path.parent / 'terminal-queue' / name
                if not path.is_file() or sha(path) != entry['sha256']:
                    errors.append({'kind': 'supplement-file', 'run': run['run_id'], 'path': name})
        packages.append(run['run_id'])
    if missing and not allow_missing_packages:
        errors.append({'kind': 'missing-packages', 'runs': missing})
    return {'status': 'fail' if errors else 'partial' if missing else 'pass',
            'frozen_source_commit': frozen['source_commit'],
            'frozen_files_checked': len(frozen['controller_files']), 'prepared_runs_checked': 12,
            'retained_packages_checked': packages, 'missing_packages': missing, 'errors': errors,
            'scope': 'Stored frozen source, paired prepared inputs, original materials/interfaces, resource profiles, archive parts and supplements. Does not rerun scientific execution, infer task completion or require the current release to equal the historical freeze.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-missing-packages', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Use a new archive-verification receipt')
    result = verify(allow_missing_packages=args.allow_missing_packages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(1 if result['errors'] else 0)
