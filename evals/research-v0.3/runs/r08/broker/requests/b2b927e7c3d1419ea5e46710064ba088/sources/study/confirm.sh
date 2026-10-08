#!/bin/sh
# Only orchestrates the common broker; no scientific computation in this shell.
set -eu
PYTHON_ENV=${1:-.venv/bin/python}
DESTINATION=${2:-evidence/confirmation}
SHARED_INPUTS=${3:-evidence/inputs}
for DATASET in moons gmm8; do
  if [ "$DATASET" = moons ]; then SEEDS="4001 4002 4003 4004"; else SEEDS="5001 5002 5003 5004"; fi
  for SEED in $SEEDS; do
    for CONDITION in constant10000 cosine5000 cosine10000; do
      case "$CONDITION" in
        constant10000) POLICY=constant; DURATION=10000 ;;
        cosine5000) POLICY=cosine; DURATION=5000 ;;
        cosine10000) POLICY=cosine; DURATION=10000 ;;
      esac
      python3 inputs/compute.py --category compute --label "confirm-$DATASET-$SEED-$CONDITION" --timeout 45 -- "$PYTHON_ENV" study/run.py --dataset "$DATASET" --seed "$SEED" --policy "$POLICY" --duration "$DURATION" --phase confirmation --output "$DESTINATION/$DATASET-$SEED-$CONDITION" --shared "$SHARED_INPUTS"
    done
  done
done
