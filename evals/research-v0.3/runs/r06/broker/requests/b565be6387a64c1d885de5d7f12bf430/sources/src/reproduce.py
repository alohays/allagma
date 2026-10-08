"""Broker-only orchestration. Fresh offline environment, all eight full trajectories."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def broker(category, label, timeout, argv):
    command = [sys.executable, 'inputs/compute.py', '--category', category, '--label', label,
               '--timeout', str(timeout), '--', *map(str, argv)]
    print('BROKER', json.dumps(command), flush=True)
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='reproduction')
    args = parser.parse_args()
    root = Path(args.output)
    if root.is_absolute() or '..' in root.parts:
        raise SystemExit('Output must be a workspace-relative directory.')
    if root.exists():
        raise SystemExit('Choose a new output directory: fresh reproduction never overwrites evidence.')
    # Directory and environment creation are delegated to the broker as setup.
    env = root / '.venv'
    broker('setup', 'reproduce-fresh-environment', 45, ['python3', '-m', 'venv', env])
    python = env / 'bin/python'
    broker('setup', 'reproduce-offline-locked-packages', 120,
           [python, '-m', 'pip', 'install', '--no-index', '--find-links', 'inputs/materials/wheels',
            '-r', 'artifacts/frozen/requirements-lock.txt'])
    evidence = root / 'artifacts'
    broker('compute', 'reproduce-freeze-identical-protocol', 10,
           [python, 'src/train.py', 'freeze', '--root', evidence])
    for segment in range(1, 33):
        completed = []
        for seed in [1001, 1002, 1003, 1004]:
            for wd in [0, 1]:
                status = evidence / 'runs' / ('seed-%d-wd-%d' % (seed, wd)) / 'state.json'
                completed.append(status.exists() and json.loads(status.read_text())['complete'])
        if all(completed):
            break
        label = root.name + '-segment-%02d' % segment
        broker('compute', label, 170,
               [python, 'src/train.py', 'train', '--root', evidence, '--segment', label, '--seconds', '155'])
    else:
        raise SystemExit('Training did not finish in 32 segments; retained partial state, no shorter horizon substituted.')
    broker('compute', 'reproduce-analysis-and-verification', 60,
           [python, 'src/analyze.py', '--root', evidence, '--output', root / 'analysis'])
    print('Fresh study completed at ' + str(root), flush=True)


if __name__ == '__main__':
    main()
