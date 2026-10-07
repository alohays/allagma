# Independent replication and reporting boundaries

The [source-study README](README.md) contains the original study's findings
and commands. `create_replication.py` creates a new README for an empty replication
and copies no prior observations, manuscript, qualification or budget ledger.
Follow the new directory's README for that replication.

The original second-publication script encodes this study's observed checkpoint
pattern. Inspect a replication's own findings before reusing
`revise_publication.py`; differing findings require a new reporting revision,
not altered raw data. The first publication and numerical analysis can still
report different, negative or inconclusive findings. No identical cross-platform
training result is promised.

The [accepted copier check](evidence/setup/reproduction-layout-delivery.json)
verified the new empty layout, pinned bundle and system-Python launcher import.
It did not execute another training study. The completed source study's raw-data
recomputation and saved-weight sampling checks are separate evidence.

Create the empty copy with an explicit new budget:

```sh
python3 create_replication.py --destination /absolute/path/to/new-ema-study \
  --authorize-study-seconds 1800
```

The original `reproduce_study.py` remains at its natively reviewed revision.
The newer entrypoint adds a neutral replication README and retains that
original copier for provenance. Neither entrypoint starts training.
