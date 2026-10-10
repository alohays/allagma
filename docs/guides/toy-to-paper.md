# From toy results to a reviewed paper

Turn the [offline toy](first-study.md) into an additional paper revision using
its actual results. The base walkthrough needs Python 3.11+, Git and macOS or
Linux. It runs offline after checkout with the standard library. TeX is a
separate, optional last step; the original Markdown report remains the default.

This is a known-answer tutorial, with provided-only reference coverage and
self-review. It establishes neither scientific novelty nor agent research quality.
The [validation receipt](../contributing/toy-paper-walkthrough.md) records the
tested environment, literal commands, review judgments and limits.

## Prepare the small checkout and study

Start at the root of the [small source checkout](first-study.md#get-the-small-source-checkout).
Its `examples/toy-study` directory already includes all the additional inputs:
`paper/prepare.py`, `paper/record_review.py`, `paper/paper.example.json`,
`paper/authors.anonymous.json`, `paper/reference-map.json`, `paper/OUTLINE.md`
and the seven files in `paper/sections/`. No EMA archive, test fixture, cache,
provider account or Python dependency is needed. To read this guide locally,
add `docs` with `git sparse-checkout add docs`.

All commands below run from that checkout in the same shell. The paths
deliberately contain spaces. Use a fresh destination:

```sh
export TOY_PAPER_STUDY='work/toy paper study'
export TOY_PAPER_PUBLICATION="$TOY_PAPER_STUDY/publications/toy-paper-r1"
python3 -B -m allagma check
python3 -B -m allagma toy --destination "$TOY_PAPER_STUDY"
```

If you already completed the default first-study example, set `TOY_PAPER_STUDY`
to that study and set `TOY_PAPER_PUBLICATION` accordingly; omit the `toy` command.
Use the current source checkout's helper. An older locked bundle does not gain
new commands implicitly. The example accepts the complete default `toy-v1`
campaign and `a001` analysis, not an adapted or partial experiment.

The toy keeps its 60-second execution budget and 28-attempt ceiling: 26
successful attempts, one deliberate failure and one interruption. Its final
audit reports `pass` and 521 checked references. Publication work does not
rerun experiments, change those limits, or edit the campaign, root `paper.json`,
reference dossier, locks or bundles.

## Choose attribution and create a publication revision

The following command explicitly selects an **anonymous draft**. Read the
attribution file first. For a named paper, supply your own attribution JSON as
described in the [paper guide](../arxiv-papers.md); no name, affiliation or email
is inferred from Git. The anonymous file records its example choice and date,
not an assertion about the repository owner's authorship.

```sh
cat examples/toy-study/paper/authors.anonymous.json
python3 -B examples/toy-study/paper/prepare.py \
  --study "$TOY_PAPER_STUDY" --revision toy-paper-r1 \
  --authors examples/toy-study/paper/authors.anonymous.json
python3 -B -m allagma reference check \
  --directory "$TOY_PAPER_PUBLICATION/references" --require-review
```

Preparation returns `prepared-unreviewed`. The copied `paper.json` and seven
TeX sections are editable study-owned inputs. Every selected evidence file has
a study-relative path and digest. Values use RFC 6901 pointers: for example,
`difference` selects `/difference` in the retained summary. The average claim
uses the original claim's text and links to both its ledger entry and result
locators. Numerical macros resolve at checking/building time; the template does
not contain replacement measurements.

The reference check passes with zero external records. Read the map's category
assessments: only the supplied protocol, derivation, analysis and claim ledger
were inspected. No category claims external coverage. The empty bibliography
is intentional; the compiled paper explains it in its References section.

This next command **must fail**, with exit code 2 and a request for a scoped
scientific review. A successful reference or integrity check is not approval:

```sh
python3 -B -m allagma paper check --study "$TOY_PAPER_STUDY" \
  --config "$TOY_PAPER_PUBLICATION/paper.json"
```

## Perform the scientific and wording reviews

Read the outline, every copied section, the frozen derivation, original report
and claims. Check the study question, pilot exclusions, seed unit, pairing,
uncertainty method and counterexamples. Review the wording separately for clear
claims, preserved uncertainty and unsupported generalization.

```sh
cat examples/toy-study/paper/OUTLINE.md
cat "$TOY_PAPER_PUBLICATION"/sections/*.tex
cat "$TOY_PAPER_STUDY/campaigns/toy-v1/materials/domain/derivation.md"
cat "$TOY_PAPER_STUDY/campaigns/toy-v1/analyses/a001/paper/manuscript.md"
python3 -B - <<'PY'
import math, os, statistics
from pathlib import Path
from allagma.files import read_json, verify_reference
from allagma.papers import json_pointer, review_fingerprint
study = Path(os.environ['TOY_PAPER_STUDY'])
publication = Path(os.environ['TOY_PAPER_PUBLICATION'])
config = read_json(publication / 'paper.json')
summary = read_json(study / config['evidence']['summary']['path'])
manifest = read_json(study / config['evidence']['raw-manifest']['path'])
differences = []
counterexamples = []
for ref in manifest['raw']:
    raw = read_json(verify_reference(study, ref))
    # Independent algebraic route to (mean+b)^2 - mean^2, target zero.
    delta = 2 * raw['bias'] * statistics.mean(raw['samples']) + raw['bias'] ** 2
    differences.append(delta)
    if delta <= 0:
        counterexamples.append(raw['seed'])
mean = statistics.mean(differences)
se = statistics.stdev(differences) / math.sqrt(len(differences))
assert len(differences) == summary['replicates'] == 24
assert math.isclose(mean, summary['difference'])
assert all(math.isclose(a, b) for a, b in zip(
    [mean - 1.96 * se, mean + 1.96 * se], summary['ci95_normal']))
assert sorted(counterexamples) == summary['counterexample_seeds']
for key, value in config['values'].items():
    data = read_json(study / config['evidence'][value['evidence']]['path'])
    print(key, json_pointer(data, value['pointer']))
print('Exclusions:', manifest['exclusions'])
print('Claims:', read_json(study / config['evidence']['toy-claims']['path']))
print('Review fingerprint:', review_fingerprint(study, config))
PY
```

For the default toy, the mean difference is 0.06510417 and the approximate
95% interval is [0.03985104, 0.09035729]. Seeds 104, 108, 118 and 121 refute an
ordering on every seed. Verify these against your output. The uncertainty is
across 24 independent confirmation seeds, not 1,536 independent paired effects.
The normal interval is approximate; leave-one-seed-out sensitivity does not
establish robustness to other distributions. The two pilots, failure and
interruption are excluded from confirmation; retries do not enlarge the sample.

If your reading supports these observations, the next command records that
self-review. Change the reviewer description and observations to reflect who
actually reviewed the files and what they found. If a finding remains unresolved,
keep the verdict pending and revise the manuscript. The helper only records
supplied judgments; it cannot assess their truth. The fingerprint comes from
preparation, so editing the manuscript requires a new review input.

```sh
python3 -B - <<'PY'
import os
from pathlib import Path
from allagma.files import read_json, write_json
p = Path(os.environ['TOY_PAPER_PUBLICATION'])
notes = read_json(p / 'review-input.json')
notes['reviewer'] = 'Walkthrough executor (self-review; no independent reviewer)'
notes['scientific'] = {
    'verdict': 'accept',
    'scope': 'Default toy derivation, retained raw/summary/claim links and all seven sections; no external literature or model-quality assessment.',
    'observations': [
        'Read the frozen derivation and recomputed the paired mean and normal interval from the raw samples using 2*b*mean+b*b.',
        'Checked 24 confirmation seeds, pilot and unsuccessful-attempt exclusions, and counterexamples 104, 108, 118 and 121.',
        'The text limits the positive average result to this synthetic problem and retains the approximate-interval and self-review limits.']}
notes['humanizer'] = {
    'verdict': 'accept',
    'scope': 'Clarity and claim-preserving wording review of all seven sections; no independent scientific endorsement.',
    'observations': [
        'Read every section for clear subjects, concrete comparisons and unsupported novelty or agent-quality language.',
        'Checked that numerical macros, the counterexample and uncertainty qualifications retain the scientific meaning.']}
write_json(p / 'review-input-r1.json', notes, immutable=True)
PY
python3 -B examples/toy-study/paper/record_review.py \
  --study "$TOY_PAPER_STUDY" --publication toy-paper-r1 --revision r1 \
  --input "$TOY_PAPER_PUBLICATION/review-input-r1.json"
python3 -B -m allagma paper check --study "$TOY_PAPER_STUDY" \
  --config "$TOY_PAPER_PUBLICATION/reviews/r1/paper.json"
```

The check now passes. `reviews/r1/` retains the supplied judgments, separate
scientific and wording records, and a configuration referencing their hashes.
The original unreviewed configuration and pending input remain. The checker
verifies integrity and declared links; the observations remain the reviewer's
responsibility.

## Change prose, observe a stale review, and recover

Keep the accepted first revision intact. Copy the discussion into a new file,
add one sentence and point a new configuration at it. This changes the section
being reviewed while leaving every earlier section, configuration and review
unchanged:

```sh
python3 -B - <<'PY'
import os
from pathlib import Path
from allagma.files import read_json, write_json, write_text
study = Path(os.environ['TOY_PAPER_STUDY'])
p = Path(os.environ['TOY_PAPER_PUBLICATION'])
config = read_json(p / 'reviews/r1/paper.json')
new = p / 'sections/discussion-r2.tex'
text = (study / config['sections']['discussion']).read_text()
write_text(new, text + '\nThis publication revision reuses the completed experiment.\n', immutable=True)
config['sections']['discussion'] = new.relative_to(study).as_posix()
write_json(p / 'paper-r2.json', config, immutable=True)
PY
python3 -B -m allagma paper check --study "$TOY_PAPER_STUDY" \
  --config "$TOY_PAPER_PUBLICATION/paper-r2.json"
```

The last command must fail with exit code 2: `scientific review is stale`.
Reusing `review-input-r1.json` with `record_review.py --config paper-r2.json`
also fails; copying an old fingerprint cannot approve changed content.

Read the new discussion and compare its meaning with the first revision. It
adds no scientific result. Recheck the unchanged configuration, evidence and
remaining sections before recording the following scoped continuation:

```sh
cat "$TOY_PAPER_PUBLICATION/sections/discussion-r2.tex"
python3 -B - <<'PY'
import os
from pathlib import Path
from allagma.files import read_json, write_json
from allagma.papers import review_fingerprint
study = Path(os.environ['TOY_PAPER_STUDY'])
p = Path(os.environ['TOY_PAPER_PUBLICATION'])
notes = read_json(p / 'review-input-r1.json')
notes['reviewed_content_sha256'] = review_fingerprint(study, read_json(p / 'paper-r2.json'))
notes['scientific']['observations'].append(
    'Read discussion-r2 and compared the new configuration: the added sentence describes reuse, no new experiment or empirical conclusion; original evidence and other sections are unchanged.')
notes['humanizer']['observations'].append(
    'Reread the added sentence in context; it preserves the distinction between publication revision and experiment.')
write_json(p / 'review-input-r2.json', notes, immutable=True)
PY
python3 -B examples/toy-study/paper/record_review.py \
  --study "$TOY_PAPER_STUDY" --publication toy-paper-r1 --config paper-r2.json \
  --revision r2 --input "$TOY_PAPER_PUBLICATION/review-input-r2.json"
python3 -B -m allagma paper check --study "$TOY_PAPER_STUDY" \
  --config "$TOY_PAPER_PUBLICATION/reviews/r2/paper.json"
```

This new check passes. Both review revisions remain, and the new records point
to the superseded records by path and digest. If any preparation, review or
build stops partway, preserve its directory and use a new revision ID/output
path; do not delete a failed revision to make the same command pass.

## Optional: compile, unpack, rebuild and inspect

Stop here for the ordinary offline/report route. Compilation additionally needs
an installed TeX distribution with `pdflatex`, BibTeX, `geometry`, `fontenc`,
`inputenc`, `lmodern`, `amsmath`, `amssymb`, `graphicx`, `booktabs`, `longtable`,
`natbib`, `url` and `hyperref`; check the [adapter prerequisites](../../adapters/arxiv/README.md).
The sandbox requires macOS `sandbox-exec`, or functional Linux `bubblewrap`.
There is no unsandboxed fallback or automatic installation. PDF inspection below
uses Poppler's `pdfinfo` and `pdftoppm`; archive extraction uses `tar`.

```sh
pdflatex --version
python3 -B -m allagma paper build --study "$TOY_PAPER_STUDY" \
  --config "$TOY_PAPER_PUBLICATION/reviews/r2/paper.json" \
  --destination "$TOY_PAPER_PUBLICATION/build-r2"
mkdir "$TOY_PAPER_PUBLICATION/unpacked-r2"
tar -xzf "$TOY_PAPER_PUBLICATION/build-r2/paper-source.tar.gz" \
  -C "$TOY_PAPER_PUBLICATION/unpacked-r2"
python3 -B "$TOY_PAPER_PUBLICATION/unpacked-r2/anc/build.py" \
  --output "$TOY_PAPER_PUBLICATION/rebuilt-r2"
pdfinfo "$TOY_PAPER_PUBLICATION/build-r2/paper.pdf"
mkdir "$TOY_PAPER_PUBLICATION/rendered-r2"
pdftoppm -scale-to 1200 -png "$TOY_PAPER_PUBLICATION/build-r2/paper.pdf" \
  "$TOY_PAPER_PUBLICATION/rendered-r2/page"
```

The build itself also unpacks and invokes the packaged `anc/build.py`; the
explicit invocation above shows how a recipient rebuilds from the delivered
archive. Inspect **every** rendered page for clipping, overlap, legible numbers,
section flow and the anonymous author line. Compare the displayed values with
the inspected JSON and verify that the References section explains the empty
bibliography. Keep a visual-review note separate from the compiler receipt.

`build-r2/` contains the PDF, source archive, delivery receipt and compiler logs.
`rebuilt-r2/` is a separate clean rebuild; byte-identical PDFs are not promised.
Neither compilation nor self-review establishes arXiv acceptance. No submission
occurs. The [paper guide](../arxiv-papers.md) explains the wider configuration
contract; the [reference guide](../reference-research.md) explains coverage.
