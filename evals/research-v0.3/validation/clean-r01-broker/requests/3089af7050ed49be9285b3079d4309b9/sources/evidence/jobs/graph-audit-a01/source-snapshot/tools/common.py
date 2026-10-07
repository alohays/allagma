"""Artifact bookkeeping, shared by study-owned programs."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")

def ref(path):
    p = Path(path).resolve()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p),
            "media_type": "application/json" if p.suffix == ".json" else "application/octet-stream",
            "retention": "retained in study"}

def check_ref(item):
    p = ROOT / item["path"]
    assert p.is_file() and not p.is_symlink(), item["path"]
    assert sha(p) == item["sha256"], "Digest mismatch: " + item["path"]
    return p
