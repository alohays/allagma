"""Create an empty study with the same bundle, source and explicit new budget.

This copies no attempts, checkpoints, compute receipts or confirmation decision.
It does not install dependencies or launch scientific computation.
"""
import argparse
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent


def create(destination, authorized_seconds):
    if authorized_seconds!=1800:
        raise ValueError("This protocol requires explicit authorization for its 1800-second ceiling")
    destination=destination.resolve()
    if destination.exists():
        raise ValueError("Destination already exists; preserve earlier studies")
    destination.mkdir(parents=True)
    for name in (".agents",".allagma","profiles","overrides","modules-local","reference"):
        shutil.copytree(ROOT/name,destination/name,ignore=shutil.ignore_patterns("__pycache__","mutation.lock","*.pyc"))
    for name in ("AGENTS.md","ALLAGMA.md","CLAUDE.md","allagma.yaml","brief.json",
                 "compute.py","manage.py","native_session.py","verify_results.py","test_compute.py","reproduce_study.py","create_replication.py",
                 "publication.py","revise_publication.py","verify_supporting.py","DISCLOSURE.md",".gitignore"):
        shutil.copy2(ROOT/name,destination/name)
    campaign=ROOT/"campaigns/ema-v1"
    protocol=json.loads((campaign/"protocol.json").read_text())
    shutil.copy2(campaign/"protocol.json",destination/"protocol.json")
    for name in protocol["code"]:
        target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(campaign/"materials"/name,target)
    (destination/"NEW-RUN.md").write_text(
        "# New independent execution\n\nThis directory contains no original scientific results. "
        "A new 1800-second compute ceiling was explicitly authorized when it was created. "
        "Set up the environment, run known-answer checks, start the campaign, run the deliberate interruption, execute four "
        "pilots, freeze confirmation, execute ten confirmation trajectories, then analyze "
        "and audit. The source-study manuscript and host evidence are not evidence for this run.\n")
    (destination/"README.md").write_text('''# Independent EMA diffusion replication

This is an empty replication of the pinned ema-2d-v1 protocol and bundle.
No results, manuscript, host qualification or previous compute ledger were
copied. Interpret results only after this run produces its own evidence.
Read DESIGN.md, REFERENCE.md, DISCLOSURE.md and NEW-RUN.md.

Use Python 3.11 on a compatible MPS Mac. The new 1800-second ceiling was
explicitly authorized when this directory was created. Stop on any failure.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
python3 manage.py check
python3 manage.py start
python3 manage.py interrupt
python3 - <<'PY'
import subprocess
for _ in range(4):
    subprocess.run(['python3', 'manage.py', 'pilot'], check=True)
PY
python3 manage.py freeze
python3 - <<'PY'
import subprocess
for _ in range(10):
    subprocess.run(['python3', 'manage.py', 'confirm'], check=True)
PY
python3 manage.py analyze
python3 manage.py audit
python3 manage.py verify
python3 publication.py
python3 verify_supporting.py
```

The source study's reporting revision encoded its observed checkpoint pattern.
Inspect this replication's own findings before reusing revise_publication.py;
different findings require a new reporting revision, not changed raw evidence.
For native-host qualification, conduct the workflow through actual native
sessions and retain fresh activation, routing and continuation evidence.
''')
    return destination


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--destination",type=Path,required=True)
    parser.add_argument("--authorize-study-seconds",type=int,required=True)
    args=parser.parse_args()
    print(create(args.destination,args.authorize_study_seconds))
