#!/usr/bin/env python3
"""Build a deterministic, small source distribution; never publish it."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from allagma.bundles import source_inventory  # noqa: E402


def build(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / "release.json").read_text())["release"]
    name = f"allagma-{version}-source"
    target = output / (name + ".tar.gz")
    receipt = output / (name + ".json")
    if target.exists() or receipt.exists():
        raise SystemExit("Use a new output directory; existing release assets are retained")
    paths = set(source_inventory(ROOT))
    for directory in ("examples/toy-study", "examples/first-research", "conformance", "tools", ".github"):
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/module-authoring.md",
                     "CODE_OF_CONDUCT.md", "GOVERNANCE.md", "SECURITY.md", "SUPPORT.md", "CITATION.cff", "pyproject.toml"):
        if (ROOT / filename).is_file():
            paths.add(filename)
    manifest = {}
    with target.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            for path in sorted(paths):
                file = ROOT / path
                if file.is_symlink():
                    raise ValueError(f"Resolve source symlinks explicitly: {path}")
                data = file.read_bytes()
                info = tarfile.TarInfo(name + "/" + path)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                archive.addfile(info, io.BytesIO(data))
                manifest[path] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    result = {"format": "allagma-source-distribution-v1", "release": version, "git_head": head,
              "archive": target.name, "bytes": target.stat().st_size,
              "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "files": manifest,
              "scope": "Core, all catalog modules, offline example, small native-study inputs, and conformance. No retained scientific archives, site toolchain, third-party study adaptations or wheels. Documentation links target the repository; use the site/full source for all guides.",
              "publication": "prepared-locally-not-published"}
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "SHA256SUMS").write_text(f"{result['sha256']}  {target.name}\n")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
