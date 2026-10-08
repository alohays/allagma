"""Actual interpreter probes for a suspected r05 reproduction-path defect."""
import json
from pathlib import Path
import subprocess
import sys

root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new defect receipt')
script = (root / 'study/reproduce.py').read_text()
assert "py=str((Path(args.output)/'.venv/bin/python').resolve())" in script
environment = root / 'reproduction-smoke/.venv'
lexical = environment / 'bin/python'
resolved = lexical.resolve(strict=True)
probe = 'import sys,json,importlib.util;print(json.dumps({"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"numpy_available":importlib.util.find_spec("numpy") is not None,"torch_available":importlib.util.find_spec("torch") is not None}))'
results = {}
for label, executable in [('fresh_environment_interpreter', lexical), ('delivered_driver_resolved_interpreter', resolved)]:
    process = subprocess.run([str(executable), '-c', probe], check=True, text=True, capture_output=True)
    results[label] = json.loads(process.stdout)
assert Path(results['fresh_environment_interpreter']['prefix']).resolve() == environment.resolve()
defect = Path(results['delivered_driver_resolved_interpreter']['prefix']).resolve() != environment.resolve()
result = {'status': 'defect_reproduced' if defect else 'pass', 'source': 'study/reproduce.py',
          'expression': "str((Path(args.output)/'.venv/bin/python').resolve())",
          'probe_environment': str(environment), 'probes': results, 'interpreter_is_symlink': lexical.is_symlink(),
          'impact': 'The resolved path bypasses the fresh environment.' if defect else 'The tested staging path uses a copied interpreter. Resolving that path retains the fresh environment and its packages; the suspected defect is not reproduced.',
          'scope': 'Actual interpreter executions with sys.prefix and module-availability observations. No confirmation retraining, candidate edit or mocked-host claim.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
