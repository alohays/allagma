"""Compile the study-owned CPU implementation inside a broker setup request."""
from pathlib import Path
import subprocess,json,os
Path('build').mkdir(exist_ok=True)
Path('.tmp/compiler').mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(Path('.tmp/compiler').resolve()),CLANG_MODULE_CACHE_PATH=str(Path('.tmp/compiler/modules').resolve()))
cmd=['/usr/bin/clang','-O3','-shared','-fPIC','-framework','Accelerate','study/engine.c','-o','build/engine.dylib']
subprocess.run(cmd,env=env,check=True)
Path('build/build.json').write_text(json.dumps({'argv':cmd,'compiler':subprocess.check_output(['/usr/bin/clang','--version'],env=env,text=True)},indent=2))
