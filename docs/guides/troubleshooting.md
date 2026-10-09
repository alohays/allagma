# Troubleshooting

Start with the exact command, Python/host version, exit code and sanitized
error. Retain the attempt directory. A failed command is evidence to diagnose,
not a reason to delete the study.

| Symptom | What to check or do |
| --- | --- |
| `No module named allagma` | Run from the source checkout root, with Python 3.11+. A partial Python wheel is not the supported distribution. |
| A catalog resource is missing | Complete the sparse-checkout directory list in the [first-study tutorial](first-study.md). It includes `evals/context-retention`. |
| Destination already exists | Choose a new destination, or resume the existing campaign. Never erase evidence just to rerun a tutorial. |
| `Duplicate JSON key` | Follow the [disposable-copy recovery example](#duplicate-json-keys) below. Keep the rejected file for diagnosis; do not edit retained evidence to make validation pass. |
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

## Duplicate JSON keys

Allagma rejects repeated keys within a JSON object, even when their values are
identical. Otherwise a reader could silently choose one value and hide an
editing mistake. The error names the repeated key; it does not mean the record
contract should be relaxed.

From the repository root, run these commands in the same POSIX shell with
Python 3.11+. Create a new temporary directory and generate a valid context
record from the shipped example:

```sh
duplicate_demo=$(python3 -c \
  'import tempfile; print(tempfile.mkdtemp(prefix="allagma-json-"))')
python3 methods/allagma-context-active-brief/select.py \
  methods/allagma-context-active-brief/example.json "$duplicate_demo/context.json"
```

Introduce a second `context_id` only in a separate, disposable copy. The original
record and repository files stay unchanged:

```sh
python3 - "$duplicate_demo" <<'PY'
from pathlib import Path
import sys

directory = Path(sys.argv[1])
original = (directory / "context.json").read_text(encoding="utf-8")
with (directory / "duplicate.json").open("x", encoding="utf-8") as copy:
    copy.write(original.replace("{", '{"context_id": "edited-copy",', 1))
PY

if python3 -m allagma validate-record \
  "$duplicate_demo/duplicate.json"; then
  echo "Unexpected success: duplicate keys should fail."
else
  echo "Exit code: $?"
fi
```

The validation command exits **2**, with the error on standard error:

```text
allagma: Duplicate JSON key: context_id
Exit code: 2
```

Validate the freshly generated original instead of the damaged copy:

```sh
python3 -m allagma validate-record "$duplicate_demo/context.json"
```

This exits **0** and prints:

```json
{
  "record_type": "ContextRecord",
  "status": "pass"
}
```

Keep the rejected copy while diagnosing the mistake. For your own draft
input, resolve the intended value at its source and generate a new record at a
fresh path. For retained evidence, restore verified original bytes from a
trusted copy or create a new campaign/analysis revision as appropriate. Do not
rewrite historical records, locks or expected digests to make a check pass.

This example checks JSON parsing and record shape only. Its illustrative
evidence reference is a placeholder; a passing `validate-record` does not verify
that referenced file or establish a scientific result. See the
[command-line reference](../cli.md) for the command's scope.
