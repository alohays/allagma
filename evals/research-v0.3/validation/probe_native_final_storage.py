"""Offline native-adapter storage regression with a fake CLI, not a model run.

The actual fixture process writes after the workspace sample and exits before
the next sample. No account, model call or native-host qualification is involved.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('storage_native_fixture', ROOT / 'adapters/codex/session.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
base = Path(sys.argv[1]).resolve()
base.mkdir(parents=True, exist_ok=False)
workspace = base / 'workspace'
workspace.mkdir()
cli = base / 'fixture-cli'
cli.write_text('#!/usr/bin/env python3\nimport sys,time\nfrom pathlib import Path\n'
               'if "--version" in sys.argv: print("offline-fixture-no-model"); raise SystemExit(0)\n'
               'sys.stdin.read()\n'
               'while not Path("go").exists(): time.sleep(.005)\n'
               'Path("payload").write_bytes(b"x"*200000)\n')
cli.chmod(0o755)
config, auth = base / 'fixture-config.toml', base / 'fixture-auth.json'
config.write_text('model = "offline-fixture-no-model"\n')
auth.write_text('{}\n')
original_popen, original_storage = subprocess.Popen, native.storage_bytes
state = {'process': None, 'gated': False}


def capture_process(*args, **kwargs):
    process = original_popen(*args, **kwargs)
    if kwargs.get('stdin') == subprocess.PIPE and kwargs.get('start_new_session'):
        state['process'] = process
    return process


def sample_storage(path):
    value = original_storage(path)
    if Path(path).resolve() == workspace and state['process'] is not None and not state['gated']:
        state['gated'] = True
        (workspace / 'go').write_text('go')
        state['process'].wait(timeout=3)
    return value


limit = 100000
with patch.object(subprocess, 'Popen', capture_process), patch.object(native, 'storage_bytes', sample_storage):
    result = native.capture(codex=cli, workspace=workspace, record=base / 'record',
                            runtime=base / 'runtime', prompt='Offline storage fixture; no model.',
                            timeout=10, config=config, auth=auth, rss_limit_bytes=200000000,
                            storage_limit_bytes=limit)
final_size = original_storage(workspace) + original_storage(base / 'runtime')
receipt = {'adapter_status': result['status'], 'sampled_peak_storage_bytes': result['peak_storage_bytes'],
           'actual_final_storage_bytes': final_size, 'limit_bytes': limit,
           'violation_detected': result['status'] == 'storage_exceeded',
           'scope': 'Offline native-adapter fixture with an actual local process and controlled sampling/exit interleaving. Fake CLI, no hosted model, no native-host qualification.'}
(base / 'probe.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
