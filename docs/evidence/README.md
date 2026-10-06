# Retained v0.2 acceptance evidence

- [Acceptance report](acceptance.json): exact source, environment, I1–I5 checks
  and artifact paths within the archive.
- [Conformance receipt](conformance.json) and [log](conformance.log): 51 passing
  tests, no skips.
- [Independent validation](external-validation.json): eight schemas, 629 record
  occurrences and 293 skill files checked with separate validators.
- [Archive](acceptance.tar.gz) and [manifest](archive-manifest.json): the full
  acceptance tree, 5,169 files in a compressed package of about 1.5 MB.
- [Relocation/reproduction receipt](archive-reproduction.json): the archive was
  extracted to a new location and the pinned generic campaign audit passed.

Extract the archive, then open
`allagma-acceptance/generic/campaigns/toy-v1/analyses/a001/paper/manuscript.md`.
The adjacent claims, analysis record and raw manifest lead to every original
observation, failed/interrupted attempt, evaluator output and review trace.
The versioning directory retains synthetic lifecycle/update/migration examples;
these are not published future Allagma releases.

```sh
mkdir -p work/reproduction
tar -xzf docs/evidence/acceptance.tar.gz -C work/reproduction
python3 -m allagma campaign audit \
  --study work/reproduction/allagma-acceptance/generic --campaign toy-v1
```

The archive contains exact bundled helper code and study-owned scientific
materials. Historical absolute command paths are execution metadata;
study-relative content references support relocation. New audits append records.

The independent JSON Schema validator's available format checkers are listed
in its receipt. Timestamp checks are covered by Allagma's built-in validator;
the external installation did not include an optional date-time format checker.
None of these checks establishes native model activation or scientific quality.

The `reproduction/` directory retains the additional review and trace produced
by the relocation check. Overlay it onto the extracted generic study to inspect
the exact review referenced by the reproduction receipt.
