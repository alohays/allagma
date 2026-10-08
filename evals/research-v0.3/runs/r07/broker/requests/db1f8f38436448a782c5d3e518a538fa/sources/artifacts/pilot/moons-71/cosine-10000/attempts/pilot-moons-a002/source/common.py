"""Artifact conventions for this AI-generated/adapted study."""
import hashlib
import json
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT/'campaigns/ema-schedule-v1'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
    temporary.replace(path)

def ref(path, media=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT/path
    media = media or {'.json':'application/json', '.py':'text/x-python', '.md':'text/markdown',
                       '.npz':'application/x-npz'}.get(path.suffix, 'application/octet-stream')
    return {'path':str(path.relative_to(ROOT)), 'sha256':sha(path), 'media_type':media, 'retention':'retained'}

def array_hash(array):
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()

def named_hash(arrays):
    """Canonical name, dtype, shape and C-order bytes, sorted by name."""
    import numpy as np
    h = hashlib.sha256()
    for key in sorted(arrays):
        a = np.ascontiguousarray(arrays[key])
        h.update(json.dumps([key, str(a.dtype), list(a.shape)], separators=(',', ':')).encode()+b'\n')
        h.update(a.tobytes())
    return h.hexdigest()

def sources():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'study').glob('*.py'))}
