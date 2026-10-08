"""Exercise recomputation and assert deterministic retained analysis/figures."""
import json
from pathlib import Path
import subprocess
import sys
from run import dump,sha

files=["measurements.json","analysis/summary.json","analysis/seed-metrics.csv","analysis/seed-contrasts.csv","analysis/tables.md","analysis/main-figure.png","analysis/main-figure.pdf","analysis/main-figure.svg","analysis/analysis-provenance.json"]
before={p:sha(p) for p in files}
subprocess.run([sys.executable,"study/analyze.py"],check=True)
after={p:sha(p) for p in files}
assert before==after,[(p,before[p],after[p]) for p in files if before[p]!=after[p]]
subprocess.run([sys.executable,"study/verify.py"],check=True)
subprocess.run([sys.executable,"study/claims.py"],check=True)
dump("analysis/recompute-audit.json",{"all_passed":True,"checks":"rerun analysis from retained samples, then independent numerical verifier and central claim checks","byte_identical_derived_files":after,"count":len(files),"script_sha256":sha(__file__)})
print(json.dumps({"byte_identical_outputs":len(files),"all_passed":True}))
