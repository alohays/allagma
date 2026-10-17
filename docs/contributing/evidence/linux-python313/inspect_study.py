"""Read the actual isolated study; do not import Allagma or change its files."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

study = Path('work/my-first-study').resolve()
campaign = study / 'campaigns/toy-v1'
analysis = campaign / 'analyses/a001'
evidence = Path('/qualification/evidence')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def inventory():
    return {str(p.relative_to(study)): {'sha256': digest(p), 'mtime_ns': p.stat().st_mtime_ns}
            for p in sorted(study.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


if sys.argv[1] == 'snapshot':
    snapshot = inventory()
    (evidence / 'before-audit.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    print(json.dumps({'files': len(snapshot), 'snapshot_sha256': digest(evidence / 'before-audit.json')}))
else:
    before, after = load(evidence / 'before-audit.json'), inventory()
    mutable = {'campaigns/toy-v1/latest-audit.json', 'campaigns/toy-v1/state.json'}
    changed = [p for p in before if before[p] != after.get(p)]
    assert set(changed) <= mutable, changed
    new = sorted(after.keys() - before.keys())
    attempts = [load(p) for p in sorted(campaign.glob('runs/*/attempts/*/record.json'))]
    counts = Counter(record['status'] for record in attempts)
    assert counts == {'succeeded': 26, 'failed': 1, 'interrupted': 1}, counts
    audit = load(campaign / 'latest-audit.json')
    assert audit['verdict'] == 'pass' and audit['checked_references'] == 521
    assert not audit['findings'] and not audit['stale_claims']
    claims = load(analysis / 'paper/claims.json')
    assert [c['status'] for c in claims] == ['supported', 'contradicted', 'supported']
    paper = analysis / 'paper/manuscript.md'
    links = []
    for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', paper.read_text()):
        path = (paper.parent / target.split('#')[0]).resolve()
        assert path.is_relative_to(study) and path.is_file(), target
        links.append({'label': label, 'target': target, 'study_path': str(path.relative_to(study)), 'sha256': digest(path)})
    assert links, 'No manuscript links'
    direct = {}
    def refs(value):
        if isinstance(value, dict):
            if {'path', 'sha256'} <= value.keys():
                path = (study / value['path']).resolve()
                assert path.is_relative_to(study) and path.is_file()
                assert digest(path) == value['sha256'], value['path']
                direct[value['path']] = value['sha256']
            for item in value.values(): refs(item)
        elif isinstance(value, list):
            for item in value: refs(item)
    refs(claims)
    lock = load(campaign / 'lock.yaml')
    result = {
        'status': 'pass', 'attempts': dict(counts), 'audit': audit,
        'state': load(campaign / 'state.json'),
        'effective_configuration': lock['effective_configuration'],
        'summary': load(analysis / 'outputs/summary.json'),
        'manuscript_sha256': digest(paper), 'claims_sha256': digest(analysis / 'paper/claims.json'),
        'summary_sha256': digest(analysis / 'outputs/summary.json'),
        'manuscript_links': links, 'direct_claim_references': direct,
        'claim_statuses': {c['claim_id']: c['status'] for c in claims},
        'preservation': {
            'original_files': len(before), 'immutable_original_files_unchanged': len(before) - len(mutable),
            'comparison': 'SHA-256 and nanosecond mtime for every original file except the two mutable state/audit pointers',
            'changed_mutable_pointers': changed, 'added_files': new,
            'before_inventory_sha256': digest(evidence / 'before-audit.json')
        },
        'scope': 'Offline deterministic example on the recorded Linux container/Python interpreter. No scientific or model-quality qualification, independent peer review, or native-host qualification.'
    }
    (evidence / 'study-inspection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
