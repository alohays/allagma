"""Broker-only entry point to verify and analyze retained evidence without training."""
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
    parser.add_argument('--root', default='artifacts')
    parser.add_argument('--output', default='analysis')
    parser.add_argument('--environment', default='.venv')
    args = parser.parse_args()
    env = Path(args.environment)
    python = env / 'bin/python'
    if not python.exists():
        broker('setup', 'recompute-isolated-environment', 45, ['python3', '-m', 'venv', env])
        broker('setup', 'recompute-offline-locked-packages', 120,
               [python, '-m', 'pip', 'install', '--no-index', '--find-links', 'inputs/materials/wheels',
                '-r', 'artifacts/frozen/requirements-lock.txt'])
    broker('compute', 'recompute-analysis-known-answers', 15, [python, 'src/test_analysis.py'])
    broker('compute', 'recompute-retained-evidence', 60,
           [python, 'src/analyze.py', '--root', args.root, '--output', args.output])


if __name__ == '__main__':
    main()
