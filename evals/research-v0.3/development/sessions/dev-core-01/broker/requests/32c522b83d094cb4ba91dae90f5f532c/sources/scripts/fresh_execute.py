"""Run each frozen sample as a plain script in the fresh broker environment."""
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

root = Path.cwd().resolve()
output = root / sys.argv[1]
output.mkdir(parents=True, exist_ok=False)
code = root / "campaigns/core-culp/materials/source/adapted/code"
results = {}
for dataset in ["iris", "zoo", "wine"]:
    command = [sys.executable, str(code / f"{dataset}_sample.py")]
    start = time.monotonic()
    result = subprocess.run(command, cwd=code, capture_output=True, text=True, timeout=35)
    (output / f"{dataset}-stdout.txt").write_text(result.stdout)
    (output / f"{dataset}-stderr.txt").write_text(result.stderr)
    results[dataset] = {"argv": command, "cwd": str(code.relative_to(root)),
                        "exit_code": result.returncode, "seconds": time.monotonic()-start,
                        "stdout": result.stdout,
                        "scores": dict((label, float(value)) for label, value in
                                       re.findall(r"\(λ=(\w+)\) = ([0-9.]+)%", result.stdout))}
    assert result.returncode == 0, result.stderr
    assert set(results[dataset]["scores"]) == {"CN", "AA", "RA", "CS"}
manifest = json.loads((root / "analysis/raw-manifest.json").read_text())
raw = json.loads((root / manifest["raw"][0]["path"]).read_text())
for dataset in results:
    assert results[dataset]["stdout"] == raw["datasets"][dataset]["stdout"]
value = {"passed": True, "coverage": "All three scripts execute directly with no observation wrappers in a newly installed isolated environment; all 12 labelled stdout scores exactly equal the primary run.",
         "python": platform.python_version(), "packages": {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "scikit-learn", "pandas", "networkx"]}, "scripts": results}
(output / "results.json").write_text(json.dumps(value, indent=2) + "\n")
print(json.dumps(value, indent=2))
