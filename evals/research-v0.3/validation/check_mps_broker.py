"""Controller for the post-cohort full-broker MPS regression.

Creates a fresh isolated environment from supplied local wheels. All setup and
worker computation is charged to an existing finite controller validation ledger.
Run after repairing the release source; never modify a frozen cohort workspace.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from allagma import resources


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--wheels', type=Path, required=True)
    args = parser.parse_args()
    workspace, record = args.workspace.resolve(), args.record.resolve()
    if workspace.exists() or record.exists():
        raise RuntimeError('Use new MPS validation workspace and record directories')
    policy = resources._policy(args.ledger)
    allowed = Path(policy['workdir']).resolve()
    if workspace != allowed and allowed not in workspace.parents:
        raise RuntimeError('Canary workspace must be within the existing ledger workdir')
    workspace.mkdir(parents=True)
    inputs = workspace / 'inputs'
    inputs.mkdir()
    source = Path(__file__).with_name('mps_broker_canary.py')
    shutil.copyfile(source, inputs / source.name)
    wheels = inputs / 'wheels'
    shutil.copytree(args.wheels, wheels)
    readonly = inputs / 'readonly.txt'
    readonly.write_text('allagma readonly canary\n')
    record.mkdir(parents=True)
    protected = record / 'synthetic-protected'
    protected.mkdir()
    (protected / 'answer.txt').write_text('synthetic canary; no external credentials\n')
    broker_path = ROOT / 'adapters/local-process/broker.py'
    spec = importlib.util.spec_from_file_location('mps_validation_broker', broker_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    broker = module.Broker(workspace, args.ledger, record / 'broker', readonly=[inputs], protected=[record])
    requests = []
    def submit(category, label, timeout, argv):
        request_id = uuid.uuid4().hex
        value = {'request_id': request_id, 'argv': list(map(str, argv)), 'cwd': '.',
                 'category': category, 'label': label, 'timeout_seconds': timeout,
                 'attempt': category == 'compute'}
        (workspace / '.compute/requests' / (request_id + '.json')).write_text(json.dumps(value) + '\n')
        response = broker.poll()
        requests.append({'request_id': request_id, 'label': label, 'response': response})
        if response is None or response['result']['status'] != 'completed':
            raise RuntimeError('Broker validation request did not complete: ' + label)
        return response
    result = {'scope': 'Actual local scientific broker and MPS regression, not native-agent qualification.',
              'broker_sha256': digest(broker_path), 'canary_sha256': digest(source),
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'profile_sha256': resources.summary(args.ledger)['profile_sha256'], 'requests': requests}
    try:
        submit('setup', 'mps-canary-venv', 60, [sys.executable, '-m', 'venv', '.venv'])
        submit('setup', 'mps-canary-offline-packages', 120,
               ['.venv/bin/python', '-m', 'pip', 'install', '--no-index', '--no-cache-dir',
                '--find-links', 'inputs/wheels', 'torch==2.14.1', 'numpy==2.4.6'])
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                accepted, _ = listener.accept()
                accepted.close()
            result['controller_loopback_positive_control'] = True
            submit('compute', 'mps-full-broker-regression', 90,
                   ['.venv/bin/python', 'inputs/mps_broker_canary.py', '--output', 'evidence',
                    '--readonly', readonly, '--protected', protected, '--port', port])
        worker = json.loads((workspace / 'evidence/result.json').read_text())
        assert worker['status'] == 'pass'
        result.update(status='pass', worker=worker)
    except Exception as error:
        result.update(status='failed', error=str(error))
        raise
    finally:
        (record / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'record': str(record / 'validation.json')}))


if __name__ == '__main__':
    main()
