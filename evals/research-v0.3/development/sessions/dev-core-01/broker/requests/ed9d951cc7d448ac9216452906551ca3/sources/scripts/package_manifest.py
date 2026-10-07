"""File-inventory bookkeeping, excluding caches, queues and the self-referential seal."""
import hashlib
import json
from pathlib import Path

root = Path.cwd().resolve()
excluded_directories = {".compute", ".tmp", ".git", "__pycache__", ".pytest_cache"}
excluded_names = {"artifact-manifest.json", ".DS_Store", "mutation.lock"}
files = []
def walk(directory):
    for path in sorted(directory.iterdir()):
        if path.name in excluded_directories or path.name.startswith(".venv"):
            continue
        if path.is_symlink():
            continue
        if path.is_dir():
            walk(path)
        elif path.name not in excluded_names and path.suffix != ".pyc":
            h = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024*1024), b""):
                    h.update(block)
            files.append({"path": path.relative_to(root).as_posix(), "sha256": h.hexdigest(), "size_bytes": path.stat().st_size})
walk(root)
value = {"format": "sha256-artifact-manifest-v1", "root": ".", "files": files,
         "exclusions": ["artifact-manifest.json (self-reference)", ".compute (transient queue; completed receipts copied to evidence/broker)", ".tmp", ".venv*", "__pycache__ and *.pyc", ".git", ".pytest_cache", "mutation.lock", ".DS_Store"],
         "scope": "Final delivery inventory. Verification before final receipt archival is recorded separately; subsequent sealing adds the completed receipts and inventory metadata only."}
(root / "artifact-manifest.json").write_text(json.dumps(value, indent=2) + "\n")
print("Manifest contains", len(files), "files")
