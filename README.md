# Allagma

Allagma is a portable, file-based research harness: reusable methods, recipes
that compose them, adapters that connect them to a host, and evidence records
that link a scientific question to a manuscript. A study pins an exact local
bundle. Central edits and later releases cannot change an existing campaign.

**v0.3 release candidate:** [research workspaces](docs/research-workspaces.md)
prepare a brief, source materials and finite resource profile for a fresh native
Codex session. The [qualification ledger](docs/v0.3/requirements.md) tracks the
three studies, controlled comparison and reproduction gates. Evaluation is in
progress; the version label does not claim those gates are complete.

The v0.2 implementation includes an offline toy study, generic/Codex/Claude
Code packaging, replaceable context and reviewer examples, update and rollback
tools, and a contributor conformance kit. The core and offline toy study use **Python 3.11+ on POSIX**
(macOS or Linux), with **no third-party runtime dependencies, paid APIs or GPU**.
Distribution is a source checkout or a generated study-local bundle; a Python
wheel, remote scheduler and autonomous model optimizer are outside this release.

## Run the complete example

From this checkout:

```sh
python3 -m allagma check
python3 -m allagma toy --destination work/my-toy-study
python3 -m allagma campaign audit --study work/my-toy-study --campaign toy-v1
```

The destination must be empty; existing evidence is never erased. The example
runs two known-answer pilots and 24 confirmation seeds, deliberately fails and
interrupts two attempts, resumes them with new attempt IDs, computes paired
uncertainty, writes supported and contradicted claims, and generates a short
manuscript. The audit reruns analysis and writing and verifies transitive
evidence digests. This demonstrates the workflow, not scientific novelty or
improved language-model research quality.

Open the study's
`campaigns/toy-v1/analyses/a001/paper/manuscript.md`, `walkthrough.json`, and
`campaigns/toy-v1/latest-audit.json`. See [the toy guide](examples/toy-study/README.md)
for the study question and artifact layout.

## Check the implementation

```sh
python3 -m unittest discover -s conformance -v
python3 -m allagma acceptance --output build/acceptance
```

The acceptance command creates fresh I1–I5 evidence, including independent
context/reviewer/recipe substitutions, three host packaging walkthroughs,
historical resume, a scaffold migration and rollback. It exits unsuccessfully
if any criterion fails. Use a new output directory for a later run.
See [acceptance evidence](docs/acceptance.md) and the generated report for
the exact tested scope. Native-host packaging and contract tests are separate
from real-host activation and model-quality qualification.

The [post-delivery self-audit](docs/audit/README.md) records the defects found,
their corrections, independent checks and a requirement-by-requirement map.

The separate [weight EMA diffusion study](studies/ema-2d-diffusion/README.md)
retains real native Codex sessions, MPS training, held-out comparisons and
fresh-session recovery. Its PyTorch environment and scientific code belong to
the study. See the [host qualification report](studies/ema-2d-diffusion/HOST-QUALIFICATION.md)
for the exact tested scope and evidence.

## Start your own study

```sh
python3 -m allagma init --study work/new-study --id new-study
python3 -m allagma entry --study work/new-study
```

Read the generated `ALLAGMA.md` and catalog. Existing `AGENTS.md`, `CLAUDE.md`
and user skills are preserved; naming conflicts are resolved inside the
Allagma namespace. The native paths are `.agents/skills/allagma-*/SKILL.md`
and `.claude/skills/allagma-*/SKILL.md`. They route to the same canonical sources
through the selected campaign's lock. No hooks, subagents or model pins are
installed. A generic agent can read or receive the same files as text.

Develop the brief, evidence map and protocol with the shared methods. Supply
study-owned runner, evaluator, analyzer and writer programs for computational
work. The [runner contract](docs/study-adapters.md) describes their interfaces.
Then start a campaign and run its bundled helper:

```sh
python3 -m allagma campaign start --study work/new-study --campaign pilot-1
python3 -m allagma campaign run --study work/new-study --campaign pilot-1
python3 -m allagma campaign analyze --study work/new-study --campaign pilot-1
python3 -m allagma campaign audit --study work/new-study --campaign pilot-1
```

The CLI dispatches execution to the helper in the campaign's own bundle.
Scientific inputs and code are frozen at campaign creation. A protocol
amendment starts a new campaign and records its reason and affected earlier
runs. Instruction-only research can use the portable methods without a helper
runtime; it must state which experimental phases are inapplicable.

## Change composition without rewriting methods

```sh
python3 -m allagma toy --destination work/alternative \
  --context context/full-record --reviewer reviewer/trace \
  --recipe recipe/replication
python3 -m allagma compare --output work/context-comparison
```

The alternative context and replication recipe are explicit experimental
selections. The comparison measures required-field retention and serialized
character cost, with a candidate, fixed fixtures and an ImprovementRecord.
It does not claim a model-quality improvement or change defaults automatically.

For an existing study, edit its `allagma.yaml` and/or overrides, then follow
[Check → Plan → Reconcile → Validate → Adopt](docs/versioning.md). Resume does
not resolve new versions. Old bundles remain available after retirement and
rollback.

## Repository map

| Location | Responsibility |
| --- | --- |
| `methods/` | Portable canonical `SKILL.md` and module metadata |
| `recipes/` | Roles, handoffs, branches and stopping rules |
| `adapters/` | Host registration, local execution and reviewer boundaries |
| `contracts/` | Versioned evidence schemas and compatibility |
| `allagma/`, `tools/` | Small validators, exporter, campaign and update helpers |
| `profiles/`, `policies/` | Public examples; personal credentials stay outside |
| `evals/`, `conformance/` | Framework evaluation and offline behavioral checks |
| `examples/toy-study/` | Study-owned science and a complete reference workflow |
| `studies/ema-2d-diffusion/` | Native Codex/MPS study, pinned science and retained results |
| `templates/study/` | Initial scaffold, owned by the study after generation |

Read [architecture](docs/architecture.md), [module authoring](docs/module-authoring.md),
[host support](docs/host-support.md), [contributing](CONTRIBUTING.md),
[governance](GOVERNANCE.md), and [release notes](docs/releases/0.2.0.md).
The [adopted specifications](docs/specification/README.md) and
[design lineage](docs/design-lineage.md) explain the design's origins.

Allagma core is MIT licensed. Study-specific source reuse and licensing are
documented in [third-party notices](THIRD_PARTY_NOTICES.md).
