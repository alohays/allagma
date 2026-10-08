#!/usr/bin/env python3
"""Build a compact distribution from committed Git blobs; never publish it.

Local edits, ignored files and untracked files never enter a release asset.
Documentation links to omitted files point at the exact source commit.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import tarfile
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXTRA_DIRECTORIES = ("examples/toy-study", "examples/first-research", "conformance", "tools", ".github")
DOCUMENTS = ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CONTRIBUTING.md", "CHANGELOG.md",
             "docs/module-authoring.md", "CODE_OF_CONDUCT.md", "GOVERNANCE.md", "SECURITY.md",
             "SUPPORT.md", "CITATION.cff", "pyproject.toml")


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args])


def documentation_links(data, name, paths, head):
    """Rewrite only omitted documentation targets, leaving core bundle bytes exact."""
    def target(url, raw=False):
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
            return url
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
        if resolved == ".." or resolved.startswith("../"):
            raise ValueError(f"Documentation link escapes the repository: {name}: {url}")
        if resolved in paths or any(p.startswith(resolved + "/") for p in paths):
            return url
        suffix = ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
        prefix = f"https://raw.githubusercontent.com/alohays/allagma/{head}/" if raw else f"https://github.com/alohays/allagma/blob/{head}/"
        return prefix + quote(resolved, safe='/') + suffix

    text = data.decode("utf-8")
    # The maintained documents use inline links and HTML picture sources.
    text = re.sub(r'(!\[[^\]]*\]\()([^\s)]+)', lambda m: m[1] + target(m[2], raw=True), text)
    text = re.sub(r'(\]\()([^\s)]+)', lambda m: m[1] + target(m[2]), text)
    text = re.sub(r'((?:src|srcset)=")([^"]+)(")', lambda m: m[1] + target(m[2], raw=True) + m[3], text)
    return text.encode("utf-8")


def build(output: Path, source: Path = ROOT):
    source, output = source.resolve(), output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new output directory; existing release assets are retained")
    if Path(git(source, "rev-parse", "--show-toplevel").decode().strip()).resolve() != source:
        raise ValueError("Build from the root of a committed Git checkout")
    head = git(source, "rev-parse", "HEAD").decode().strip()
    entries = {}
    for entry in git(source, "ls-tree", "-r", "-z", head).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            entries[path.decode()] = (mode, kind, oid)
    registry = json.loads(git(source, "show", head + ":registry.json"))
    directories = ["allagma", "contracts", "templates/study", *registry["modules"].values()]
    for directory in directories:
        if PurePosixPath(directory).is_absolute() or ".." in directory.split("/"):
            raise ValueError(f"Invalid source directory: {directory}")
    core = {p for p in entries if any(p.startswith(d + "/") for d in directories)}
    core.update(("registry.json", "release.json", "LICENSE", "tools/allagma.py"))
    paths = core | {p for p in entries if p in DOCUMENTS or any(p.startswith(d + "/") for d in EXTRA_DIRECTORIES)}
    for path in paths:
        if path not in entries or entries[path][0] not in ("100644", "100755") or entries[path][1] != "blob":
            raise ValueError(f"Release sources must be committed regular files: {path}")
    version = json.loads(git(source, "show", head + ":release.json"))["release"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("Invalid release version for an archive filename")
    name = f"allagma-{version}-source"
    manifest, contents, rewrites = {}, {}, {}
    process = subprocess.Popen(["git", "-C", str(source), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for path in sorted(paths):
            process.stdin.write((entries[path][2] + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().split()
            data = process.stdout.read(int(header[2]))
            if header[1] != b"blob" or process.stdout.read(1) != b"\n":
                raise ValueError("Invalid Git blob stream")
            original = hashlib.sha256(data).hexdigest()
            if path.endswith(".md") and path not in core:
                data = documentation_links(data, path, paths, head)
                if hashlib.sha256(data).hexdigest() != original:
                    rewrites[path] = {"source_sha256": original, "transformation": "Omitted relative documentation/media targets point to the exact Git commit."}
            contents[path] = data
            manifest[path] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    # Validate inputs before creating an output; only reviewed committed bytes
    # (plus the disclosed documentation link transformation) are ever written.
    output.mkdir(parents=True, exist_ok=True)
    target = output / (name + ".tar.gz")
    with target.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            for path, data in contents.items():
                info = tarfile.TarInfo(name + "/" + path)
                info.size, info.mode, info.mtime = len(data), int(entries[path][0], 8) & 0o777, 0
                archive.addfile(info, io.BytesIO(data))
    result = {"format": "allagma-source-distribution-v2", "release": version, "git_head": head,
              "source_policy": "Committed HEAD blobs only; all local edits, ignored files and untracked files excluded.",
              "tracked_worktree_changes": bool(git(source, "diff", "HEAD", "--name-only").strip()),
              "archive": target.name, "bytes": target.stat().st_size,
              "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "files": manifest,
              "documentation_rewrites": rewrites,
              "scope": "Core, all catalog modules, offline example, small native-study inputs, and conformance. No retained scientific archives, site toolchain, third-party study adaptations or wheels. Omitted documentation targets link to the source commit.",
              "publication": "prepared-locally-not-published"}
    (output / (name + ".json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "SHA256SUMS").write_text(f"{result['sha256']}  {target.name}\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("files", "documentation_rewrites")}, indent=2))
