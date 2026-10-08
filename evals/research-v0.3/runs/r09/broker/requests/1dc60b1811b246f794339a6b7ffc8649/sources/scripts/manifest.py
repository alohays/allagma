"""Create/verify the package's SHA-256 file inventory, excluding caches and queues."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRUNED = {".venv", "__pycache__", ".compute", ".tmp", ".git"}
EXCLUDED = {"artifact-manifest.json"}
FINAL_TRACE = "evidence/manifest-verification"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory():
    result = []
    for current, directories, files in os.walk(ROOT):
        directories[:] = sorted(d for d in directories if d not in PRUNED and
                                  str((Path(current) / d).relative_to(ROOT)) != FINAL_TRACE)
        for name in sorted(files):
            path = Path(current) / name
            relative = str(path.relative_to(ROOT))
            if relative in EXCLUDED or name == ".DS_Store" or name.endswith(".pyc") or path.is_symlink():
                continue
            result.append({"path": relative, "sha256": sha(path), "bytes": path.stat().st_size})
    return sorted(result, key=lambda row: row["path"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Also require no unlisted nonexcluded files")
    args = parser.parse_args()
    assert args.create != args.verify, "Choose --create or --verify"
    target = ROOT / "artifact-manifest.json"
    if args.create:
        value = {"format": "research-artifact-manifest-v1", "hash_algorithm": "SHA-256",
                 "exclusions": ["artifact-manifest.json (self-reference)",
                     "Any .venv, __pycache__, .compute, .tmp, or .git directory; .pyc and .DS_Store files; symlinks",
                     "evidence/manifest-verification (final verification trace created after this inventory; avoids a self-reference cycle)"],
                 "files": inventory()}
        target.write_text(json.dumps(value, indent=2) + "\n")
        print(json.dumps({"created": "artifact-manifest.json", "files": len(value["files"]), "sha256": sha(target)}, indent=2))
        return
    value = json.loads(target.read_text())
    paths = []
    for row in value["files"]:
        path = ROOT / row["path"]
        assert not Path(row["path"]).is_absolute() and path.resolve().is_relative_to(ROOT)
        assert path.is_file() and not path.is_symlink(), row["path"]
        assert path.stat().st_size == row["bytes"], row["path"]
        assert sha(path) == row["sha256"], row["path"]
        paths.append(row["path"])
    assert len(set(paths)) == len(paths)
    unlisted = sorted({row["path"] for row in inventory()} - set(paths))
    if args.strict:
        assert not unlisted, unlisted
    print(json.dumps({"status": "passed", "files_verified": len(paths), "manifest_sha256": sha(target),
                      "unlisted_nonexcluded_files": unlisted,
                      "establishes": "Exact byte/size integrity of inventoried files; strict mode additionally checks current inventory coverage.",
                      "does_not_establish": "Scientific validity or independently authenticated provenance."}, indent=2))


if __name__ == "__main__":
    main()
