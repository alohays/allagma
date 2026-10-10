# Resume, audit and reproduce

A study keeps its own methods and scientific programs. New central code does
not silently change an old campaign. That makes recovery and reproduction
inspectable, but it also means a new release's fixes do not retroactively repair
an old bundle.

## Resume the same campaign

Read its state and run the remaining work through its exact helper:

```sh
python3 -m allagma campaign status --study work/my-first-study --campaign toy-v1
python3 -m allagma campaign run --study work/my-first-study --campaign toy-v1
```

Completed runs are retained. Failed or interrupted attempts remain separate
from retries. A process still running under a controller must be reconciled,
not duplicated. The [resource guide](../resource-supervision.md) explains
reservation recovery and what the local supervisor actually bounds.

## Recompute the report

First, inspect a delivered record without executing any of its programs:

```sh
python3 -B -m allagma verify-evidence --study work/my-first-study \
  --record campaigns/toy-v1/analyses/a001/paper/claims.json
```

This reads declared references and reports all independent missing/changed
artifacts it reaches. It writes no study files or reviews. Use a quiescent copy
and review the coverage and findings; a pass does not establish package
completeness or scientific correctness. See [limits and exit codes](../cli.md#read-only-evidence-inspection).

To rerun the study-owned analyzer and writer and append a new review:

```sh
python3 -m allagma campaign audit --study work/my-first-study --campaign toy-v1
```

An audit verifies references and regenerates analysis/writing under the pinned
helper. It does **not** retrain a scientific model unless the study's reproduction
command explicitly does so. A saved-weight replay, raw-data reanalysis and fresh
full training are three different kinds of evidence. Name the one you performed.

## Restore a delivered real study

Each [showcase study](../showcase/index.md) links to a package index and exact
reproduction instructions. Archives may be multipart. The retention helper
streams restoration and verifies every hash; do not concatenate a large archive
into a filesystem with a small per-file cap.

```sh
python3 evals/research-v0.3/retention.py restore \
  --source evals/research-v0.3/runs/r01/package \
  --destination work/restored-culp --download-wheels
```

This optional path requires the retained evaluation files from a full or
expanded sparse checkout and may download pinned dependency wheels. Review
[artifact sizes and distribution](../launch/artifact-distribution.md) first.
Read the restored `REPRODUCE.md` before execution. Run science through a new
finite resource ledger using the [standalone broker](../research-workspaces.md#run-a-delivered-reproduction-command-without-another-model-session).

## Change the plan deliberately

An amended hypothesis, dataset, metric or sampling plan starts a new campaign
with an explanation of the change. Do not edit a frozen protocol or lock to make
old results appear to follow the new plan. To change Allagma composition, use
[Check → Plan → Reconcile → Validate → Adopt](../versioning.md) at a campaign
boundary. Rollback preserves both the prior and later bundles.
