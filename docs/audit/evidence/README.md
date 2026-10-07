# Audited v0.2 acceptance evidence

This is the corrected source's qualification. The original evidence under
`docs/evidence/` is historical and is not overwritten.

- [Acceptance](acceptance.json): all I1–I5 scenarios, exact source and inventories.
- [Conformance](conformance.json) and [log](conformance.log): 75 tests, no skips.
- [Independent validation](external-validation.json): eight schemas, 643 record
  occurrences, 290 skills, including installed timestamp-format checking.
- [Differential schema check](contract-differential.json): 1,557 cases, no mismatches.
- [Independent science](independent-science.json): rational arithmetic, eligibility,
  primary/sensitivity tables, figure data, claim directions and manuscript values.
- [Archive](acceptance.tar.gz) and [inventory](archive-manifest.json): 5,839 files,
  1,708,053 compressed bytes, SHA-256
  `1a29828b20895dd5430ddf10bb0ffd18244c48bd0fa75b836cf9571e541ebf67`.
- [Reproduction](archive-reproduction.json): successful extraction elsewhere
  and pinned re-audit, with 521 verified evidence references.

```sh
mkdir -p work/reproduction-audited
tar -xzf docs/audit/evidence/acceptance.tar.gz -C work/reproduction-audited
python3 -m allagma campaign audit \
  --study work/reproduction-audited/allagma-acceptance/generic --campaign toy-v1
```

The manuscript is at
`generic/campaigns/toy-v1/analyses/a001/paper/manuscript.md` inside the extracted
tree. The `reproduction/` directory here is an overlay for the extracted generic
study, retaining the additional review referenced by the reproduction receipt.
The root archive includes the original review and every prior artifact.

These are deterministic local checks. Native-host activation, model research
quality and independent scientific review are not inferred from them.
