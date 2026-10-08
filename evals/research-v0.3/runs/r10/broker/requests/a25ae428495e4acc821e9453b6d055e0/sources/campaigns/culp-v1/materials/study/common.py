"""Small study-owned artifact helpers; no scientific work on import."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def ref(path):
    path = Path(path).resolve()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
            "media_type": "application/json" if path.suffix == ".json" else "application/octet-stream",
            "retention": "retained"}


def tree_manifest(paths):
    return [ref(p) for p in sorted(set(paths)) if p.is_file() and "__pycache__" not in p.parts]


def verify_refs(items):
    for item in items:
        assert digest(ROOT / item["path"]) == item["sha256"], item["path"]
