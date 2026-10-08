"""Freeze qualified protocol and source hashes before confirmation."""
from datetime import datetime, timezone
from pathlib import Path
import json
import study as s

assert not list(Path('artifacts/confirmation').glob('*/checkpoint.pt')), 'Confirmation already started'
q=json.loads(Path('artifacts/qualification.json').read_text())
n=json.loads(Path('artifacts/numerical-qualification.json').read_text())
assert n['status']=='passed'
speed=next(r['seconds_per_update'] for r in q['benchmark'] if r['device']=='cpu' and r['implementation']=='dense')
files=['protocol.json','PROTOCOL.md','study.py','study_pilot_v1.py','qualify_numerics.py','qualify_numerics_v1.py']
value=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
    confirmation_started=False,source_sha256={p:s.sha(p) for p in files},
    pilot_seconds_per_update=speed,projected_core_training_seconds_800000=speed*800000,
    budget_compute_seconds=1800,budget_setup_seconds=300,
    decision='Proceed with full prescribed horizon on CPU; retain at least 120 seconds for analysis and verification.',
    qualification_paths=['artifacts/qualification.json','artifacts/numerical-qualification.json'])
s.dump('artifacts/protocol-freeze.json',value)
print(json.dumps(value,indent=2))
