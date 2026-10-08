#!/bin/sh
# Full fresh-environment reproduction. Requires the supplied common broker.
# Run in a fresh authorized workspace/budget containing this package and inputs.
set -eu
if [ -e .venv-reproduction ] || [ -e evidence/reproduction ]; then
  echo 'Fresh reproduction paths already exist; preserve them and use a fresh workspace.' >&2
  exit 1
fi
python3 inputs/compute.py --category setup --label reproduce-fresh-environment --timeout 60 -- python3 -m venv .venv-reproduction
python3 inputs/compute.py --category setup --label reproduce-pinned-packages --timeout 120 -- .venv-reproduction/bin/python -m pip install --no-index --find-links inputs/materials/wheels -r requirements-lock.txt
sh study/confirm.sh .venv-reproduction/bin/python evidence/reproduction evidence/reproduction-inputs
python3 inputs/compute.py --category compute --label reproduce-analysis --timeout 45 -- .venv-reproduction/bin/python study/analyze.py --evidence evidence/reproduction --output reproduction-analysis --measurements reproduction-measurements.json
python3 inputs/compute.py --category compute --label reproduce-regenerate-moons --timeout 40 -- .venv-reproduction/bin/python study/regenerate.py --measurements reproduction-measurements.json --dataset moons --output reproduction-analysis/regenerate-moons.json
python3 inputs/compute.py --category compute --label reproduce-regenerate-gmm8 --timeout 40 -- .venv-reproduction/bin/python study/regenerate.py --measurements reproduction-measurements.json --dataset gmm8 --output reproduction-analysis/regenerate-gmm8.json
