# rc2 source qualification evidence

The [acceptance receipt](acceptance/acceptance.json) identifies release
`0.3.0rc2` and distributable source
`sha256:a7a67e09548e40442f2ff72ba63898f66e02368046132a183588ebebdbc1a196`.
All I1–I5 scenarios and 113 tests pass with no skips. The complete toy retains
26 successful, one failed and one interrupted attempt, and its deterministic
audit verifies 521 evidence references. Host fixtures in this acceptance run
establish packaging/contracts, not native model qualification.

The 5,944-file [archive inventory](acceptance/archive-manifest.json) binds the
entire fresh acceptance tree. Every restored hash was checked before the
[relocated pinned-helper replay](archive-reproduction.json), which also passes.
The [independent toy calculation](independent-toy.json) uses rational arithmetic
without importing Allagma or the study's science, checking primary/sensitivity
tables, figure data, claims and manuscript numbers.

The standalone conformance log and catalog receipt in this directory supplement
the source-bound logs inside `acceptance/`. Six retention and four comparison
regressions pass. Five optional scientific-scorer tests, including real MPS
checkpoint sampling, pass in validation job 0057. Job 0056's failed controller
invocation is preserved and charged at the full reservation after explicit
recovery; see the [validation note](../../../../evals/research-v0.3/validation/README.md).

Actual MPS training/checkpoint and access-denial evidence is at
[mps-broker-rc2](../../../../evals/research-v0.3/validation/mps-broker-rc2/validation.json).
The separate real native cohort, frozen integrity checks, task packages,
clean-checkout CULP execution and descriptive comparison are linked by the
[requirement ledger](../../requirements.md). Those evidence types retain their
own revisions and must not be inferred from offline tests.

Recreate acceptance with a fresh destination:

```sh
python3 -m allagma check
python3 -m unittest discover -s conformance -v
python3 -m allagma acceptance --output build/new-acceptance
python3 tools/retain_evidence.py --from build/new-acceptance --destination /path/to/new-evidence
```

Existing evidence destinations are not overwritten. The release/migration notes
explain how to adopt the source without changing an old bundle or campaign.
