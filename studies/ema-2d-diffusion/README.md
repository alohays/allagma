# When Does Weight EMA Help Tiny 2D Diffusion?

A separate study for real native Codex qualification of Allagma. It compares
raw weights with constant EMA 0.99 and 0.999 on paired training trajectories,
using two moons and eight Gaussians on an Apple M4 Pro with 48 GB. The default
framework conformance kit remains dependency-free.

**Machine-generation disclosure:** this study's code, analyses, figures,
manuscripts and reports were produced with OpenAI Codex, using adaptations of
the pinned AI-Scientist template. See [disclosure](DISCLOSURE.md) and the
[reference license](reference/LICENSE).

Read [DESIGN.md](DESIGN.md), [protocol.json](protocol.json), and
[reference provenance](REFERENCE.md). Run `python3 manage.py status` to inspect
the current campaign and global compute ledger. The current manuscript is
[publication/v2/manuscript.md](publication/v2/manuscript.md), with
[13 evidence-linked claims](publication/v2/claims.json) and retained publication
history. See the [host qualification](HOST-QUALIFICATION.md) for tested native
behavior and limitations.

## Environment and execution

From this directory, create an isolated environment using Python 3.11:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
python3 manage.py status
```

The recorded environment uses PyTorch 2.14.1, NumPy 2.4.6, SciPy 1.17.1 and
Matplotlib 3.11.2. The lock pins transitive dependencies. MPS is required and
implicit CPU fallback is disabled. Use the supervisor for scientific work.
An existing study resumes its frozen campaign and must not be reinitialized.
Training reruns need a separate study and an explicitly authorized new budget
once this study's ceiling is spent.

Native sessions activate study-local skills, resolve the campaign bundle and
use `manage.py` for execution. Evidence lives in `evidence/native/`,
`evidence/compute/` and `campaigns/ema-v1/`. The parent `GOAL.md` records the
scope and commit/push instructions. No project model is pinned.

## Scientific result

The four comparisons at 5,000 updates all favored EMA in observed mean Sliced
W1 (mean EMA-minus-raw differences approximately -0.059 to -0.062). At 10,000
updates the differences were about -0.00091 to +0.00070 and every unadjusted
95% paired t interval included zero. All observed mixture mode counts were
eight. Five seeds per dataset, eight comparisons and one optimizer schedule
limit inference; these observations do not establish general EMA superiority.

The [paired figure](campaigns/ema-v1/analyses/a001/outputs/paired-quality.png)
uses a separate numerical y scale in each panel. The
[sample figure](campaigns/ema-v1/analyses/a001/outputs/samples.png) uses the
prespecified first confirmation seed for each dataset. Numerical source files
are [summary.json](campaigns/ema-v1/analyses/a001/outputs/summary.json),
[per-seed.csv](campaigns/ema-v1/analyses/a001/outputs/per-seed.csv) and
[paired-differences.csv](campaigns/ema-v1/analyses/a001/outputs/paired-differences.csv).

## Recompute retained results without training

Use the pinned environment above. This command reruns frozen analysis and
writing in temporary directories, compares the outputs, verifies evidence
digests and appends a new review. It is charged against the same remaining
study-computation budget and refuses to exceed the ceiling:

```sh
python3 manage.py audit
```

To retain a new copy of numerical results and figures, choose an unused output
directory and run the frozen analyzer through the supervisor:

```sh
python3 - <<'PY'
from compute import ROOT, execute
campaign = ROOT / 'campaigns/ema-v1'
command = [str(ROOT / '.venv/bin/python'),
           str(campaign / 'materials/domain/analyze.py'), str(ROOT),
           str(campaign / 'analyses/a001/raw-manifest.json'),
           str(ROOT / 'reproductions/check-001')]
raise SystemExit(execute('recompute-retained-data', command, 60))
PY
```

The original [primary verification](evidence/independent-verification.json)
checked 84 Sliced W1 results, 84 checkpoint-state digests, 42 mixture-coverage
results and eight primary paired intervals. Twelve sample sets regenerated
exactly from saved weights for seeds 1001/2001, every variant and checkpoint.
The separate [supporting verification](evidence/supporting-verification.json)
covers all confirmation CSV rows, paired mode/inlier intervals, finite-sample
holdout controls and leave-one-seed-out ranges. The first verifier alone does
not establish that supporting-diagnostic coverage. Training itself was not
independently repeated; PyTorch does not guarantee identical training across
platforms or versions.

## Run an independent training replication

Creating the empty copy launches no computation. The explicit budget argument
authorizes a **new** study ceiling; it does not enlarge this study's ledger.
The copier retains the exact bundle and frozen scientific source, excluding
all attempts, results, ledgers, environments and the confirmation decision:

```sh
python3 reproduce_study.py --destination /absolute/path/to/new-ema-study \
  --authorize-study-seconds 1800
cd /absolute/path/to/new-ema-study
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
python3 manage.py check
python3 manage.py start
python3 manage.py interrupt
python3 - <<'PY'
import subprocess
for _ in range(4):
    subprocess.run(['python3', 'manage.py', 'pilot'], check=True)
PY
python3 manage.py freeze
python3 - <<'PY'
import subprocess
for _ in range(10):
    subprocess.run(['python3', 'manage.py', 'confirm'], check=True)
PY
python3 manage.py analyze
python3 manage.py audit
python3 manage.py verify
python3 publication.py
python3 verify_supporting.py
python3 revise_publication.py
```

Stop on a failure or budget refusal. A scientific rerun does not inherit the
original native-host qualification. To qualify another host/model, invoke the
local skills in real fresh sessions and retain its own traces and recovery
evidence. This host used Codex CLI 0.160.1 from the desktop application's
bundle. CLI 0.151.0 on the shell PATH rejected the inherited `gpt-6-astra`
model. `native_session.py --codex /path/to/compatible/codex LABEL PROMPT_FILE`
selects a compatible executable without setting a model. Original prompts and
session receipts are under `evidence/native/`; their historical state assertions
must be adapted to a new run's actual evidence.
