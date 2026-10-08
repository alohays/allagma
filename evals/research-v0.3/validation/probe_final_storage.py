"""Force a legal sample/exit interleaving with an actual short-lived worker.

This is a supervisor regression, not native-host or scientific qualification.
The sampling hook takes a real storage reading, then waits for the actual worker
to finish before returning that earlier reading, making the exit race repeatable.
"""
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from allagma import resources

base = Path(sys.argv[1]).resolve()
base.mkdir(parents=True, exist_ok=False)
work = base / 'workspace'
work.mkdir()
ledger = base / 'ledger'
profile = {'format': resources.FORMAT, 'budgets_seconds': {'compute': 30, 'setup': 30},
           'command_timeout_seconds': {'compute': 5, 'setup': 5}, 'attempt_limit': 2,
           'rss_limit_bytes': 200000000, 'storage_limit_bytes': 1000, 'file_limit_bytes': 5000,
           'poll_seconds': .03, 'terminate_grace_seconds': .03}
resources.initialize(ledger, profile, work)
original_popen, original_storage = subprocess.Popen, resources.storage_bytes
state = {'process': None, 'gated': False}


def capture_process(*args, **kwargs):
    process = original_popen(*args, **kwargs)
    if kwargs.get('preexec_fn') is not None:
        state['process'] = process
    return process


def sample_storage(path):
    value = original_storage(path)
    if state['process'] is not None and not state['gated']:
        state['gated'] = True
        (work / 'go').write_text('go')
        state['process'].wait(timeout=3)
    return value


program = "from pathlib import Path; import time\nwhile not Path('go').exists(): time.sleep(.005)\nPath('payload').write_bytes(b'x'*2000)\n"
with patch.object(subprocess, 'Popen', capture_process), patch.object(resources, 'storage_bytes', sample_storage):
    result = resources.execute(ledger, [sys.executable, '-c', program],
                               label='fast-final-write', category='compute', timeout=4, attempt=True)
final_size = original_storage(work)
receipt = {'result': result, 'actual_final_storage_bytes': final_size,
           'limit_bytes': profile['storage_limit_bytes'],
           'violation_detected': result['status'] == 'storage_exceeded',
           'scope': 'Actual worker and file-size growth under a controlled storage-sampling/exit interleaving. Hook models a permissible scheduling race; not a native-host qualification or a claim of a violation in the research cohort.'}
(base / 'probe.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
