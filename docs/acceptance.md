# I1–I5 acceptance evidence

The executable acceptance command builds fresh studies, runs conformance and
retains a machine-readable report. It marks a milestone passing only after the
associated scenarios execute successfully. This document maps the criteria to
the implementation; `docs/evidence/acceptance.json` records the qualified source
and actual results.

```sh
python3 -m allagma acceptance --output build/acceptance
```

| Criterion | Concrete passing evidence |
| --- | --- |
| I1 — portable foundation | Generic, Codex and Claude Code entrypoint fixtures resolve one identical bundle; three complete walkthroughs produce the same scientific summary without native hooks/subagents |
| I2 — replaceable composition | Independent context-only, reviewer-only and recipe-only replacements complete the workflow; shared module revisions are unchanged; controlled comparisons retain adoption and rejection decisions |
| I3 — contributor path | A fixture adds one module and runs its targeted example without an account; conformance, governance, ownership, issue/PR templates and authoring guidance are present |
| I4 — versioned studies | Central/profile isolation, update-stage receipts, generated-file conflicts, contract mismatch, coexistence, retirement, historical resume, complete rollback and separate scaffold migration/inverse |
| I5 — research walkthrough | 26 successful runs (2 pilots + 24 confirmation), 1 failed and 1 interrupted attempt; raw manifest, recomputed table, supported/contradicted claims, manuscript and exact-revision audit; a separate limited-budget partial manuscript |

The conformance receipt additionally includes controller crashes, worker
timeouts after controller death, stale evidence, duplicate/overlapping inputs,
late intent edits, local variants and recovery from interrupted adoption and
multi-file migration/inverse operations. No skipped test is counted as passing.

Source inventories include canonical module files and bundled helpers. The
acceptance runner checks that source and test files did not change during the
run. Optional independent validation uses the published JSON Schema documents,
a separate JSON Schema implementation and a YAML parser/skill validator.

## Retained and reproducible evidence

The repository retains a compressed acceptance tree plus plain JSON receipts
under `docs/evidence/`. The archive includes every toy raw observation and
attempt, exact bundles, protocols, comparison candidates, update histories,
migration examples, manuscripts and review traces. Its inventory and SHA-256
are recorded in `archive-manifest.json`.

```sh
mkdir -p work/reproduction
tar -xzf docs/evidence/acceptance.tar.gz -C work/reproduction
python3 -m allagma campaign audit \
  --study work/reproduction/allagma-acceptance/generic --campaign toy-v1
```

Reanalysis dispatches to the archived campaign's pinned helper. Historical
absolute command paths describe the original execution; scientific artifact
references are study-relative and survive relocation. Byte-level recomputation
is checked in the recorded Python environment; record any environment change
when interpreting a difference.

## Scope of the result

The generic local path is executed. Codex and Claude Code are format/contract
checked, with installed version probes when available. Native skill activation,
hosted-model tool use and research quality are not claimed. The toy result tests
a known analytical expectation, not Noemetric or a novel scientific hypothesis.
The review is deterministic with explicit coverage, not independent peer review.

The complete machine-readable receipts and retained evidence are the basis for
the milestone status. The presence of a manuscript alone is not acceptance.
