"""Run only through the broker's setup category."""
import importlib.metadata
import json
import platform
import sys
from common import write_json, now

value = {"recorded_at": now(), "python": sys.version, "executable": sys.executable,
         "platform": platform.platform(), "machine": platform.machine(),
         "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}}
write_json(sys.argv[1], value)
print(json.dumps(value, indent=2, sort_keys=True))
