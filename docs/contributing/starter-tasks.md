# Small contributions with a clear finish line

These are concrete proposed tasks, not claims that a community has already
requested them. Open a short issue before starting one so work is not duplicated.
The maintainer can then create an issue with `good first issue` and `help wanted`
labels. No account usage or scientific training is needed for the tasks below.

| Task | Where to work | Done when |
| --- | --- | --- |
| Explain one validator error with a recovery example | `docs/guides/troubleshooting.md` | A real failing command is reproduced, the corrected command passes, and no historical evidence is edited |
| Add an accessible description of the EMA figure | `studies/ema-schedule/RESULTS.md` | The prose states axes, independent seeds, interval assumptions and inconclusive findings without changing numerical claims |
| Add a source-lineage example for a local method | `docs/module-authoring.md` | A minimal local variant passes its module check and names which text/code was adapted and under what license |
| Document a distinct Python executable on Linux | `docs/guides/first-study.md` | The existing commands pass on the stated environment and the note avoids implying native macOS runner support there |
| Improve an empty-state or error message in docs search | `site/` | Keyboard and mobile behavior pass the site tests and the production base path remains correct |

For code changes, first reproduce the behavior and agree on the intended
contract. A documentation-only fix usually needs the link check and a rendered
review, not a new test that merely repeats its text. See the complete
[contribution guide](../../CONTRIBUTING.md) for targeted checks.
