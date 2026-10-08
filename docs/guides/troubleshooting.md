# Troubleshooting

Start with the exact command, Python/host version, exit code and sanitized
error. Retain the attempt directory. A failed command is evidence to diagnose,
not a reason to delete the study.

| Symptom | What to check or do |
| --- | --- |
| `No module named allagma` | Run from the source checkout root, with Python 3.11+. A partial Python wheel is not the supported distribution. |
| A catalog resource is missing | Complete the sparse-checkout directory list in the [first-study tutorial](first-study.md). It includes `evals/context-retention`. |
| Destination already exists | Choose a new destination, or resume the existing campaign. Never erase evidence just to rerun a tutorial. |
| Toy command prints nothing for a while | It prints its JSON handoff after the bounded workflow. Check its process before retrying. |
| A failure or interruption appears in the toy | The default example deliberately exercises both and retains separate retries. Check the final audit verdict. |
| Intent differs from the lock | Settings changed after resolution. Follow the [update workflow](../versioning.md); historical campaigns still use their own locks. |
| A digest or claim is stale | Inspect which upstream file changed. Restore its exact bytes or start a new campaign/analysis; do not rewrite the expected hash. |
| The model is unavailable in the CLI | Verify the actual executable version and your account's available models. Use a compatible CLI; do not add a project model pin to hide a mismatch. |
| Research runner fails on Linux | The offline core supports POSIX; the supervised native runner currently targets macOS. See [support boundaries](../host-support.md). |
| Scientific imports are unavailable | Supply compatible wheels before preparation, then create the study-owned environment through setup. Default offline commands need no packages. |
| MPS allocation fails in an old bundle | rc2 corrects the broker's high/low watermark pair. Historical campaigns keep their frozen helper. Prepare a new workspace or document a prospective study repair. |
| A resource budget is exhausted | Inspect charged reservations and actual outcomes. Retries also consume budget. Any expansion changes the declared scope and must be explicit. |
| Docs search has no results in development | Search indexes are generated during production build. Run `npm run build` then `npm run preview` in `site/`. |
| A preview gives 404 at `/` | The Pages project lives at `/allagma/`. Open the printed host followed by `/allagma/`. |

For a bug report, include a minimal reproducible example and the release,
module and campaign identities. Redact credentials, account IDs and private
research data. See [support](../../SUPPORT.md) and [security](../../SECURITY.md).
