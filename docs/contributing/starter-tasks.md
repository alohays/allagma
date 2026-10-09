# Available first contributions

These are actual **maintainer-proposed, unassigned** tasks in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).
They do not imply external demand or prior contributors. The
[pinned overview](https://github.com/alohays/allagma/issues/9) is the current work
queue; read the [claim and review process](workflow.md) before starting.

| Available task | Starting files | Finish line and prerequisites |
| --- | --- | --- |
| [#5: Explain duplicate-key validation and recovery](https://github.com/alohays/allagma/issues/5) — good first issue, help wanted | `docs/guides/troubleshooting.md`, `methods/allagma-context-active-brief/` | Reproduce the error in a disposable copy, validate the fresh original, document recovery and check links. Python 3.11+, no package installation. |
| [#6: Describe the EMA figure accessibly](https://github.com/alohays/allagma/issues/6) — good first issue, help wanted | `studies/ema-schedule/RESULTS.md` and its figure | Describe axes, panels, paired seeds and uncertainty without changing numerical claims. No archive restoration or training; optional Node toolchain for site rendering. |
| [#7: Qualify Linux/Python 3.13 onboarding](https://github.com/alohays/allagma/issues/7) — help wanted | `docs/guides/first-study.md`, `conformance/` | Record a literal clean-checkout offline tutorial with a distinct interpreter and paths with spaces. Requires local Linux/Python 3.13, not a native model or GPU. |

Comment on the issue with your scope and environment. A maintainer confirms the
claim and assignment before overlapping implementation. No paid model access,
GPU, response-time guarantee or release deadline is involved. Submit concise
sanitized evidence with its exact tested commit. A documentation change needs a
rendered review and link check, not a test that merely repeats its prose.

## Proposed changes awaiting owner review

The deeper agent-assisted work is reserved in draft PRs:
[#10: adapted toy/report repair](https://github.com/alohays/allagma/pull/10),
[#11: prerequisite diagnostics](https://github.com/alohays/allagma/pull/11), and
[#12: read-only evidence inspection](https://github.com/alohays/allagma/pull/12).
These features are **proposed and unmerged**. Main's command guide and first-study
tutorial describe available behavior; checking a draft requires its explicit
branch. The three PRs have no dependency on one another.

The [historical-audio rights issue](https://github.com/alohays/allagma/issues/8)
is maintainer-owned and is not a newcomer task. See the complete
[contribution guide](../../CONTRIBUTING.md) for targeted checks.
