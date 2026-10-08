"""Record the installed environment; run through the setup broker."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys

record = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
          "machine": platform.machine(), "packages": dict(sorted((dist.metadata["Name"], dist.version)
          for dist in importlib.metadata.distributions())),
          "thread_environment": {k: v for k, v in os.environ.items() if k in ["OMP_NUM_THREADS",
          "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]}}
target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evidence/environment.json")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
