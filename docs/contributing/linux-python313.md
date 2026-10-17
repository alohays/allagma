# Linux and Python 3.13 onboarding qualification

This receipt addresses [issue #7](https://github.com/alohays/allagma/issues/7):
run the literal [first-study tutorial](../guides/first-study.md) and full offline
conformance suite on Linux with a distinct Python 3.13 interpreter. It measures
one local container environment. It does not qualify native agent execution,
model quality, independent scientific review, every Linux distribution or other
Python builds.

The issue was selected on 18 October 2026 (Asia/Seoul) because it was the remaining
unclaimed engineering task without an implementing PR. Issues #19, #22 and #23
already had PRs #25, #26 and #27; #6 had a confirmed contributor; #8 required an
owner rights decision. This work uses public main directly and has no dependency
on those open PRs. It is maintainer-requested, agent-assisted qualification.

## Measured environment

| Item | Recorded value |
| --- | --- |
| Source | [`174e200`](https://github.com/alohays/allagma/tree/174e200b508b07f022ba36233db54ca0b60e48e1), current main at execution |
| Userland | Debian GNU/Linux 12 (bookworm), aarch64 |
| Kernel | Linux `6.10.14-linuxkit` in a local Docker Desktop Linux VM on an Apple Silicon Mac |
| Interpreter | CPython 3.13.16; `/usr/local/bin/python3` resolves to `/usr/local/bin/python3.13` |
| System tools | Git 2.39.5 and procps `ps`; exact versions are in the environment receipt |
| Container limits | Four CPUs, 4 GiB RAM, 256 PIDs; no host workspace, credentials or sockets mounted |
| Checkout | `/qualification/clean path with spaces/allagma` |
| Study | `work/my-first-study` under that checkout; its absolute path contains spaces |
| Acquisition | Anonymous HTTPS shallow, blob-filtered, sparse Git clone; no Allagma or third-party Python package installation |

The base image was `python:3.13-slim-bookworm`, resolved to
`sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641`.
Image acquisition, system-package installation and Git acquisition used network
access. The container was disconnected from its bridge network before the
catalog, toy, audit and conformance commands. These commands then ran offline.
The image included pip, but no third-party Python packages.

The [environment receipt](evidence/linux-python313/environment.json) records
the interpreter binary digest, OS, Git, sparse paths and exact source revision.
The [command receipt](evidence/linux-python313/commands.json) records each
command's working directory, UTC start, exit code, elapsed time and output
digests. Durations are observations, not performance guarantees.

## Commands and observed results

The three shell blocks were checked against the guide at the tested commit.
The collection script recorded individual commands and directory transitions;
it did not replace them with internal API calls. The first block was:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/alohays/allagma.git
cd allagma
git sparse-checkout set allagma adapters contracts methods recipes policies profiles \
  templates tools conformance examples/toy-study examples/first-research evals/context-retention
python3 -m allagma check
```

The remaining tutorial commands, followed by the full conformance command, were:

```sh
python3 -m allagma toy --destination work/my-first-study
python3 -m allagma campaign audit --study work/my-first-study --campaign toy-v1
python3 -m unittest discover -s conformance -v
```

All Python commands used the same recorded Python 3.13 executable, including
the child processes launched by the toy and tests. The
[results receipt](evidence/linux-python313/results.json) binds the catalog,
complete toy, repeated audit, conformance log and evidence inspection. No
expected scientific hash or test assertion was changed to obtain the result.

| Check | Exit | Observed result with `procps` present |
| --- | ---: | --- |
| Catalog | 0 | All 23 modules pass |
| Complete default toy | 0 | 26 successful attempts, one deliberate failure, one interruption |
| Explicit repeat audit | 0 | Pass; 521 references, no findings or stale claims; new `review-002` |
| Full conformance | 0 | 192 tests pass in 49.037 seconds; zero skips |
| Separate raw-data recomputation | 0 | 24 confirmation replicates and all manuscript values/claim directions agree |

The [full passing conformance log](evidence/linux-python313/conformance.log)
is retained. The [manifest](evidence/linux-python313/manifest.json) binds the
compact receipts, including the read-only inspection script. That script is
evidence-collection support, not a new Allagma runtime command.

## Missing system prerequisite and retained attempts

The first slim-image run had Git and Python but no `ps`. The catalog, complete
toy and 521-reference audit passed; full conformance ran 192 tests and failed
with two failures and 15 errors in resource-supervision and related cases.
The retained [failure receipt](evidence/linux-python313/attempts.json) and
[failure excerpt](evidence/linux-python313/conformance-without-ps.log) identify
the affected tests and missing executable. This is a missing system
prerequisite, not evidence of Python 3.13 incompatibility.

The existing [resource-supervision contract](../resource-supervision.md) already
requires `ps`, but the contributor and conformance entry points did not name it.
Those entry points now document the requirement. On minimal Debian/Ubuntu,
install `procps` before running the full suite; the needed interface is:

```sh
ps -axo pid=,ppid=,pgid=,rss=,stat=,lstart=
```

A second container used the same pinned base image plus Git, CA certificates
and `procps`, with a new anonymous sparse checkout and a new study. The first
container was stopped to terminate the failed run's remaining child processes;
its filesystem and study were preserved. This changes the environment to meet
the existing prerequisite, not the tested Allagma source. Neither study's
28-attempt/60-second ceiling was increased.

An earlier collection-script self-check also caught an extra `+` in the sparse
path list before any Allagma execution. That setup attempt and its correction
are recorded separately; the measured runs use the exact guide path list.

## Manuscript and evidence inspection

The generated manuscript was read alongside `summary.json`, `claims.json`, the
raw manifest and the seed-104 raw measurement. Its three Markdown links resolve
to the figure, claim ledger and analysis record inside the study. The claim
ledger's direct references were checked against their digests, and the campaign
audit followed the complete 521-reference chain and regenerated the report.

The report gives sample-mean MSE 0.01529948, biased-estimator MSE 0.08040365 and
paired difference 0.06510417, with approximate interval [0.03985104, 0.09035729].
It keeps the 24 independent confirmation seeds distinct from retries and the
two pilots. The average-effect claim is supported; the universal claim is
contradicted by seeds 104, 108, 118 and 121. Seed 104's mean is −0.34375, so
adding 0.25 reduces its squared error, consistent with that counterexample.
The report calls the interval a normal approximation and limits the result to
this synthetic known-answer example.

As an additional check, the existing `tools/audit_toy.py` recomputed the raw
sample arithmetic, CSVs, figure points, claim directions and report numbers
without importing the Allagma or study helpers. Its
[rational-arithmetic receipt](evidence/linux-python313/rational-audit.json)
is deterministic verification of this example, not scientific or model-quality
qualification.

The repeat audit appended `review-002` and an event, updated the two documented
mutable state/audit pointers, and preserved the other 753 retained files by
SHA-256 and nanosecond mtime. This inventory excludes interpreter bytecode
caches, as shown in the retained inspection script. Original attempts, bundles, analysis and
`review-001` remain intact. The study finished at phase `audit`, execution
status `completed`, assurance `deterministic`. Only compact sanitized receipts
are committed; the complete studies remain in the local stopped containers.

## Main advanced during qualification

PRs #26 and #27 merged while this work was running. The initial receipts above
remain bound to `174e200` and are unchanged. A fresh sparse checkout then tested
[`da9ea458`](https://github.com/alohays/allagma/tree/da9ea45844c59d14ece28789f2707627e8af724f),
the new main containing both fixes, in the same Linux/Python 3.13 environment.

All tutorial commands passed again: 23 catalog modules, the complete 26/1/1 toy,
and the 521-reference audit. **All 206 conformance tests passed**, without skips,
in 51.861 seconds. The new study's manuscript values, links, rational
recomputation and preservation checks also pass. Its study and receipt are
separate from the original run. The
[integration receipt](evidence/linux-python313-current-main.json) records the
source-selection guard, exact commands and outputs; the
[full conformance log](evidence/linux-python313-current-main.log) is retained.

PR #25 then merged. A further fresh sparse checkout at
[`f7e32a7`](https://github.com/alohays/allagma/tree/f7e32a70b43675444e9f88c07d227a8b762b9e56)
also passes all tutorial commands and **217 conformance tests**, with zero skips,
in 55.100 seconds. This includes the merged toy-paper and audit-binding
regressions. The [follow-up receipt](evidence/linux-python313-toy-paper-main.json)
and [full log](evidence/linux-python313-toy-paper-main.log) preserve that run
separately. The toy again retains 26/1/1 attempts, a passing 521-reference audit,
unchanged original evidence and the same reported values.

The documentation adds a discoverable evidence page and links from the tutorial
and host-support guide. The production build, internal links and all 18
existing desktop/mobile browser checks pass. The new page was also inspected in
light and dark themes at 1440- and 390-pixel widths; its links work and the page
does not overflow the viewport. These are documentation checks on the PR, not
additional platform or native-host qualification.
