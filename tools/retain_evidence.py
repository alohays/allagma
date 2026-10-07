#!/usr/bin/env python3
"""Retain a passing acceptance run in the repository without duplicating its tree."""
import argparse
import gzip
from pathlib import Path
import shutil
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from allagma.bundles import source_revision
from allagma.files import AllagmaError, file_hash, inventory, read_json, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=ROOT / "docs/evidence")
    args = parser.parse_args()
    report = read_json(args.source / "acceptance.json")
    if report["status"] != "pass" or report["source_revision"] != source_revision(ROOT):
        raise AllagmaError("Only a passing run of the current distributable source can be retained")
    if report["conformance_inventory"] != inventory(ROOT / "conformance"):
        raise AllagmaError("Conformance sources changed after the acceptance run")
    if report.get("example_inventory") != inventory(ROOT / "examples"):
        raise AllagmaError("Study examples changed after the acceptance run")
    args.destination.mkdir(parents=True, exist_ok=True)
    files = {name: sha for name, sha in inventory(args.source).items() if not name.endswith("/.allagma/mutation.lock")}
    archive = args.destination / "acceptance.tar.gz"
    with archive.open("xb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for name in sorted(files):
                    path = args.source / name
                    info = tar.gettarinfo(str(path), arcname="allagma-acceptance/" + name)
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    with path.open("rb") as contents:
                        tar.addfile(info, contents)
    for name in ("acceptance.json", "conformance.json", "conformance.log", "external-validation.json"):
        source = args.source / name
        if source.exists():
            target = args.destination / name
            with target.open("xb") as stream:
                stream.write(source.read_bytes())
    receipt = {"archive": archive.name, "sha256": file_hash(archive), "files": files,
               "source_revision": report["source_revision"], "scope": "Complete I1–I5 acceptance tree; cache files and idle mutation locks excluded"}
    write_json(args.destination / "archive-manifest.json", receipt, immutable=True)
    print({"archive": str(archive), "files": len(files), "bytes": archive.stat().st_size, "sha256": receipt["sha256"]})


if __name__ == "__main__":
    main()
