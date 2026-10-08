#!/usr/bin/env python3
"""Review reachable Git blobs and retained archives without exporting matched values.

This is a bounded pattern audit and inventory, not a proof of absence of secrets.
It scans all reachable historical blob versions, recursively opens ZIP/TAR files,
and reassembles every distinct multipart archive found in reachable commit trees.
It never extracts an archive or executes its contents.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "github_token": rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b",
    "provider_key": rb"\bsk-(?:proj-|ant-api\d{2}-)?[A-Za-z0-9_-]{32,}\b",
    "aws_access_key": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "slack_token": rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    "jwt": rb"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b",
    "credential_assignment": rb"[\"'](?:access_token|refresh_token|OPENAI_API_KEY|ANTHROPIC_API_KEY)[\"']\s*[:=]\s*[\"']([^\"'\r\n]{20,})[\"']",
    "home_path": rb"/(?:Users|home)/[^/\s\"'<>]+",
    "email": rb"[A-Za-z0-9_.+-]{1,64}@[A-Za-z0-9-]{1,63}\.[A-Za-z0-9.-]{1,190}",
    "account_identifier": rb"[\"'](?:account_id|chatgpt_account_id|organization_id)[\"']\s*:\s*[\"'][^\"']+[\"']",
}
PATTERNS = {k: re.compile(v) for k, v in PATTERNS.items()}
PREFIXES = {
    "private_key": (b"PRIVATE KEY-----",), "github_token": (b"ghp_", b"gho_", b"ghu_", b"ghs_", b"ghr_", b"github_pat_"),
    "provider_key": (b"sk-",), "aws_access_key": (b"AKIA", b"ASIA"), "slack_token": (b"xox",),
    "jwt": (b"eyJ",), "credential_assignment": (b"access_token", b"refresh_token", b"OPENAI_API_KEY", b"ANTHROPIC_API_KEY"),
    "home_path": (b"/Users/", b"/home/"), "email": (b"@",),
    "account_identifier": (b"account_id", b"organization_id"),
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


class Parts(io.RawIOBase):
    """One forward-only archive stream, loading at most one Git part at a time."""
    def __init__(self, objects):
        self.objects = iter(objects)
        self.current = io.BytesIO()

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            n = self.current.readinto(buffer)
            if n:
                return n
            try:
                self.current = io.BytesIO(git("cat-file", "blob", next(self.objects)))
            except StopIteration:
                return 0


def audit():
    start = time.monotonic()
    counts, categories, suffixes = Counter(), Counter(), Counter()
    findings, errors, opaque = [], [], []
    seen = set()

    def scan(data, location, depth=0):
        sha = hashlib.sha256(data).hexdigest()
        if sha in seen:
            counts["duplicate_contents"] += 1
            return
        seen.add(sha)
        counts["unique_contents"] += 1
        counts["unique_bytes"] += len(data)
        for kind, pattern in PATTERNS.items():
            if not any(prefix in data for prefix in PREFIXES[kind]):
                continue
            matches = list(pattern.finditer(data))
            if matches:
                categories[kind] += len(matches)
                findings.append({"kind": kind, "location": location, "content_sha256": sha,
                                 "count": len(matches),
                                 "lines": sorted({data.count(b"\n", 0, m.start()) + 1 for m in matches})[:20]})
        if depth > 4:
            errors.append({"location": location, "error": "archive nesting exceeds 4"})
            return
        if ".part-" in location:
            return  # Separately reassembled across the exact historical trees.
        try:
            if data.startswith(b"PK\x03\x04"):
                counts["zip_archives"] += 1
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        if member.file_size > 256 * 1024**2:
                            errors.append({"location": location + "!" + member.filename, "error": "member exceeds 256 MiB bound"})
                            continue
                        counts["archive_members"] += 1
                        scan(archive.read(member), location + "!" + member.filename, depth + 1)
            elif location.endswith((".tar.gz", ".tgz", ".tar")):
                archive_scan(io.BytesIO(data), location, depth + 1)
            elif data.startswith(b"\x1f\x8b"):
                counts["gzip_members"] += 1
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as compressed:
                    expanded = compressed.read(256 * 1024**2 + 1)
                if len(expanded) > 256 * 1024**2:
                    errors.append({"location": location, "error": "gzip content exceeds 256 MiB bound"})
                else:
                    scan(expanded, location + "!decompressed", depth + 1)
            elif b"\x00" in data[:8192]:
                counts["binary_contents_pattern_scanned"] += 1
                suffixes[Path(location).suffix or "(none)"] += 1
        except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError) as error:
            errors.append({"location": location, "error": type(error).__name__})

    def archive_scan(stream, location, depth):
        counts["tar_archives"] += 1
        with tarfile.open(fileobj=stream, mode="r|*") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                counts["archive_members"] += 1
                if member.size > 256 * 1024**2:
                    errors.append({"location": location + "!" + member.name, "error": "member exceeds 256 MiB bound"})
                    continue
                scan(archive.extractfile(member).read(), location + "!" + member.name, depth)

    objects = {}
    for line in git("rev-list", "--objects", "--all").decode().splitlines():
        oid, _, name = line.partition(" ")
        objects[oid] = name
    process = subprocess.Popen(["git", "-C", str(ROOT), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for oid, name in objects.items():
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().split()
            size = int(header[2])
            data = process.stdout.read(size)
            if process.stdout.read(1) != b"\n":
                raise RuntimeError("Git object stream framing error")
            counts["git_objects"] += 1
            if header[1] in (b"blob", b"commit", b"tag"):
                counts[header[1].decode() + "_versions"] += 1
                scan(data, oid + ":" + name)
    finally:
        process.stdin.close()
        process.wait()

    multipart = set()
    commits = git("rev-list", "--all").decode().splitlines()
    for commit in commits:
        groups = {}
        for item in git("ls-tree", "-r", "-z", commit).split(b"\x00"):
            if not item:
                continue
            metadata, name = item.split(b"\t", 1)
            match = re.match(rb"(.*\.tar\.gz)\.part-(\d+)$", name)
            if match:
                groups.setdefault(match[1].decode(), []).append((int(match[2]), metadata.split()[2].decode()))
        for name, parts in groups.items():
            parts.sort()
            identity = tuple(oid for _, oid in parts)
            if identity in multipart:
                continue
            multipart.add(identity)
            if [number for number, _ in parts] != list(range(1, len(parts) + 1)):
                errors.append({"location": name, "error": "non-contiguous archive parts"})
                continue
            try:
                archive_scan(io.BufferedReader(Parts(identity)), commit + ":" + name, 1)
            except (tarfile.TarError, EOFError, OSError) as error:
                errors.append({"location": commit + ":" + name, "error": type(error).__name__})
    return {"head": git("rev-parse", "HEAD").decode().strip(),
            "scope": "All objects reachable from all local refs, including historical commit metadata; all distinct multipart TAR combinations in their commit trees. Pattern matches never export matched values.",
            "limitations": "Pattern review cannot prove absence of secrets or certify legal rights. Binary files are pattern-scanned and ZIP/TAR members opened, but tensor/model/pickle contents are not executed. Review findings manually. Uncommitted files need a subsequent committed-tree scan.",
            "commits": len(commits), "multipart_archives": len(multipart), "counts": dict(counts),
            "category_counts": dict(categories), "binary_suffixes": dict(suffixes),
            "findings": findings, "errors": errors, "seconds": time.monotonic() - start}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; previous audit receipts are preserved")
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("findings", "binary_suffixes")}, indent=2))
    raise SystemExit(bool(result["errors"]))
