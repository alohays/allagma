"""AI-generated artifact utilities; no scientific computation on import."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CAMP = ROOT/'campaigns/ema-schedule-v1'
BUNDLE = ROOT/'.allagma/bundles/b-9a39b70665ba909edb8abc13'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path, value, immutable=True):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if immutable and path.exists():
        if path.read_text()!=data: raise FileExistsError(path)
        return
    path.write_text(data)
def ref(path):
    path=Path(path)
    return {'path':str(path.relative_to(ROOT)), 'sha256':sha(path), 'media_type':'application/octet-stream', 'retention':'retained'}
def source_revision():
    files=sorted((ROOT/'study').glob('*.py'))
    return hashlib.sha256(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in files},sort_keys=True).encode()).hexdigest()
def array_hash(x):
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def start_attempt(name, cfg):
    dest=CAMP/'attempts'/name
    dest.mkdir(parents=True,exist_ok=False)
    write(dest/'input.json', cfg)
    sources={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'study').glob('*.py'))}
    for p in sorted((ROOT/'study').glob('*.py')):
        out=dest/'source'/p.name; out.parent.mkdir(exist_ok=True); out.write_bytes(p.read_bytes())
    write(dest/'started.json', {'attempt_id':name,'started_at':now(),'argv':sys.argv,'input':ref(dest/'input.json'),
          'protocol':ref(CAMP/'protocol.json'),'lock':ref(CAMP/'lock.yaml'),'source_hashes':sources,'source_revision':source_revision()})
    return dest
