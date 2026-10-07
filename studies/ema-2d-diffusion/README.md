# When Does Weight EMA Help Tiny 2D Diffusion?

A separate study for real native Codex qualification of Allagma. It compares
raw weights with constant EMA 0.99 and 0.999 on paired training trajectories,
using two moons and eight Gaussians on an Apple M4 Pro with 48 GB. The default
framework conformance kit remains dependency-free.

Read [DESIGN.md](DESIGN.md), [protocol.json](protocol.json), and
[reference provenance](REFERENCE.md). Run `python3 manage.py status` to inspect
the current campaign and global compute ledger. The accepted manuscript and
host report will be linked here after verification.

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
