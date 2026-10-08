#!/bin/sh
# Recompute from retained evidence without training. All calculations use broker.
set -eu
python3 inputs/compute.py --category compute --label recompute-retained-evidence --timeout 45 -- .venv/bin/python study/analyze.py
python3 inputs/compute.py --category compute --label verify-retained-evidence --timeout 45 -- .venv/bin/python study/verify.py
