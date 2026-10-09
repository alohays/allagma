"""Explicit, bounded reference acquisition. Never run inside scientific workers.

Only this optional adapter opens network connections. The default core and
reference-map checker remain offline and use the Python standard library.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import gzip
import hashlib
from http.client import HTTPException
import io
import os
from pathlib import Path
import re
import signal
import shutil
import ssl
import stat
import subprocess
import sys
import tarfile
import time
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid
import zipfile

from allagma.files import AllagmaError, confined, digest, read_json, utcnow, write_json
from allagma.references import ID, SHA, nonempty, public_url, require

MIB = 1024 ** 2
GIB = 1024 ** 3
CHUNK = 256 * 1024
DEFAULTS = {"format": "allagma-acquisition-policy-v1", "asset_bytes": 256 * MIB,
            "expanded_bytes": 512 * MIB, "study_bytes": GIB, "cache_bytes": 4 * GIB,
            "minimum_free_bytes": 20 * GIB, "study_transfer_bytes": 2 * GIB,
            "attempts_per_asset": 2, "extraction_files": 10000,
            "request_timeout_seconds": 30, "asset_timeout_seconds": 600}
KINDS = {"paper-pdf", "paper-source", "code", "model", "dataset"}


def tls_context():
    context = ssl.create_default_context()
    defaults = ssl.get_default_verify_paths()
    # python.org macOS installations can have an uninstalled optional certifi
    # link. Use the OS's existing CA bundle when no configured trust path exists;
    # certificate and hostname verification remain required.
    if not defaults.cafile and not defaults.capath and sys.platform == "darwin" and Path("/etc/ssl/cert.pem").is_file():
        context.load_verify_locations(cafile="/etc/ssl/cert.pem")
    return context


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            result.update(block)
    return result.hexdigest()


def disk_bytes(root):
    total = 0
    for path in Path(root).rglob("*"):
        require(not path.is_symlink(), "Reference caches cannot contain symlinks")
        if path.is_file():
            total += path.stat().st_size
    return total


def validate_policy(policy):
    require(set(policy) == set(DEFAULTS) and policy["format"] == DEFAULTS["format"], "Invalid acquisition policy fields")
    for name in DEFAULTS.keys() - {"format"}:
        require(type(policy[name]) is int and policy[name] > 0, f"Invalid acquisition limit: {name}")
    require(policy["asset_bytes"] <= policy["study_bytes"] <= policy["cache_bytes"], "Acquisition storage limits are inconsistent")
    require(policy["request_timeout_seconds"] <= policy["asset_timeout_seconds"], "Request timeout exceeds asset timeout")
    return policy


def git_output(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    require(result.returncode == 0, "Acquisition caches require a Git working tree")
    return result.stdout.strip()


def exclude_cache(cache):
    """Resolve Git's actual exclude file, including linked-worktree indirection."""
    cache = Path(cache).absolute()
    parent = cache
    while not parent.exists():
        parent = parent.parent
    root = Path(git_output(parent, "rev-parse", "--show-toplevel")).resolve()
    require(cache != root and cache.is_relative_to(root), "Cache must be inside its Git working tree")
    relative = cache.relative_to(root).as_posix()
    confined(root, relative)
    require(not any(part in (".allagma", ".agents", ".claude", "campaigns") for part in Path(relative).parts),
            "Keep raw caches outside locked bundles, generated skills and campaign evidence")
    require(not relative.startswith(".git/") and relative != ".git", "Choose a cache outside Git's internal directory")
    tracked = git_output(root, "ls-files", "--", relative)
    require(not tracked, "Raw cache path contains tracked files; choose a new excluded path")
    exclude = Path(git_output(root, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"))
    exclude.parent.mkdir(parents=True, exist_ok=True)
    escaped = "".join("\\" + c if c in "\\*?[]!# " else c for c in relative)
    pattern = "/" + escaped + "/"
    with exclude.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        previous = stream.read()
        if pattern not in previous.splitlines():
            stream.write(("\n" if previous and not previous.endswith("\n") else "") +
                         "# Allagma local reference assets (not publication content)\n" + pattern + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        fcntl.flock(stream, fcntl.LOCK_UN)
    return {"repository": str(root), "exclude_file": str(exclude), "pattern": pattern}


@contextmanager
def mutex(cache):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / "acquisition.lock").open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AllagmaError("Another acquisition holds this cache's lock") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def initialize(cache, *, policy=None):
    cache = Path(cache).absolute()
    exclusion = exclude_cache(cache)
    with mutex(cache):
        write_json(cache / ".allagma-reference-cache.json", {"format": "allagma-raw-reference-cache-v1"}, immutable=True)
        path = cache / "policy.json"
        if path.exists():
            adopted = validate_policy(read_json(path))
            require(policy is None or policy == adopted, "Cache already has an adopted policy; use explicit policy adoption")
        else:
            adopted = validate_policy(policy or dict(DEFAULTS))
            # Initial custom limits are an explicit researcher configuration.
            # Record the observed machine state, not an inferred hardware cap.
            write_json(path, adopted, immutable=True)
            write_json(cache / "initialization.json", {"created_at": utcnow(), "exclusion": exclusion,
                "disk_free_bytes": shutil.disk_usage(cache).free, "policy_sha256": digest(adopted)}, immutable=True)
    return {"policy": adopted, "exclusion": exclusion, "cache": str(cache)}


def adopt_policy(cache, policy, *, approval=None):
    cache = Path(cache)
    validate_policy(policy)
    with mutex(cache):
        old = read_json(cache / "policy.json")
        expanded = [key for key in DEFAULTS.keys() - {"format"}
                    if (policy[key] < old[key] if key == "minimum_free_bytes" else policy[key] > old[key])]
        if expanded:
            require(isinstance(approval, dict) and approval.get("decision") == "expand-acquisition-limits"
                    and approval.get("previous_policy_sha256") == digest(old)
                    and approval.get("policy_sha256") == digest(policy)
                    and all(nonempty(approval.get(k)) for k in ("approved_by", "approved_at", "reason")),
                    "Ask the researcher before expanding adopted limits; supply a decision bound to both policy digests")
        record = {"time": utcnow(), "previous": old, "adopted": policy, "expanded_fields": expanded,
                  "approval": approval}
        write_json(cache / "policy-history" / f"{uuid.uuid4().hex}.json", record, immutable=True)
        write_json(cache / "policy.json", policy)
    return record


def validate_manifest(manifest):
    require(manifest.get("format") == "allagma-reference-assets-v1", "Unsupported reference asset manifest")
    require(isinstance(manifest.get("study_id"), str) and ID.fullmatch(manifest["study_id"]), "Invalid acquisition study ID")
    require(isinstance(manifest.get("assets"), list), "Asset manifest requires a list")
    ids = set()
    for asset in manifest["assets"]:
        key = asset.get("id", "")
        require(isinstance(key, str) and ID.fullmatch(key) and key not in ids, "Asset IDs must be unique")
        ids.add(key)
        require(asset.get("kind") in KINDS, f"{key}: unsupported asset kind")
        public_url(asset.get("url"))
        require(nonempty(asset.get("purpose")) and asset.get("use") in ("reading", "execution"),
                f"{key}: explain why this asset is needed")
        require(asset.get("access") in ("public", "gated", "unavailable"), f"{key}: declare asset access")
        require(asset.get("acquisition", "http") in ("http", "provided"), f"{key}: invalid acquisition route")
        license_record = asset.get("license", {})
        require(nonempty(license_record.get("name")) and nonempty(license_record.get("note")),
                f"{key}: retain a license and permitted-use note, including unknown restrictions")
        public_url(license_record.get("url"))
        require(asset.get("extract", "none") in ("none", "tar", "zip"), f"{key}: unsupported extraction format")
        if asset.get("sha256"):
            require(isinstance(asset["sha256"], str) and SHA.fullmatch(asset["sha256"]), f"{key}: invalid expected digest")
        if asset.get("size_bytes") is not None:
            require(type(asset["size_bytes"]) is int and asset["size_bytes"] > 0, f"{key}: invalid expected size")
        if asset["kind"] in ("code", "model", "dataset"):
            require(isinstance(asset.get("revision"), str) and re.fullmatch(r"[a-f0-9]{40,64}", asset["revision"]),
                    f"{key}: code, weights and data must be pinned to an immutable commit/revision")
            require(asset.get("sha256") or asset["revision"] in asset["url"],
                    f"{key}: bind the revision through its retrieval URL or expected content digest")
        else:
            require(nonempty(asset.get("revision")), f"{key}: pin the paper version or supplied source revision")
        if asset["kind"] == "dataset":
            require(nonempty(asset.get("split")), f"{key}: declare the selected dataset file/split")
        if asset["access"] != "public":
            require(nonempty(asset.get("access_reason")), f"{key}: explain unavailable or gated access")
    return manifest


def identity(asset):
    return digest({key: asset.get(key) for key in ("kind", "url", "revision", "sha256", "extract")})


class BudgetError(AllagmaError):
    pass


@contextmanager
def asset_deadline(seconds):
    """An elapsed deadline also interrupts a peer that keeps a read alive."""
    require(threading.current_thread() is threading.main_thread(), "Run acquisition in a dedicated main process, not a background thread")
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    require(old_timer[0] == 0, "Acquisition cannot replace another active process deadline")

    def expired(signum, frame):
        raise BudgetError("asset_timeout_seconds")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


class Cache:
    def __init__(self, path, study_id):
        self.path = Path(path).resolve()
        self.policy = validate_policy(read_json(self.path / "policy.json"))
        require(isinstance(study_id, str) and ID.fullmatch(study_id), "Invalid acquisition study ID")
        self.study = self.path / "studies" / study_id
        self.ledger_path = self.study / "ledger.json"
        self.ledger = read_json(self.ledger_path) if self.ledger_path.exists() else {
            "format": "allagma-acquisition-ledger-v1", "study_id": study_id, "transfer_bytes": 0,
            "assets": {}, "attempts": [], "materializations": []}
        self.index_path = self.path / "source-index.json"
        self.index = read_json(self.index_path) if self.index_path.exists() else {}

    def save(self):
        write_json(self.ledger_path, self.ledger)

    def recover(self):
        # Call only while holding the cache's kernel lock. A former owner
        # cannot still be transferring or materializing through this adapter.
        for attempt in self.ledger["attempts"]:
            if attempt["status"] == "running":
                attempt.update(status="interrupted", ended_at=utcnow())
        for materialization in self.ledger.get("materializations", []):
            if materialization["status"] == "preparing":
                materialization.update(status="interrupted", ended_at=utcnow())
        self.save()

    def study_bytes(self):
        roots = {str(self.study / "partial"), str(self.study / "quarantine")}
        for record in self.ledger["assets"].values():
            if record.get("cache_path"):
                roots.add(str(confined(self.path, record["cache_path"])))
            if record.get("tree"):
                roots.add(str(confined(self.path, record["tree"]["cache_path"])))
        return (sum(Path(p).stat().st_size if Path(p).is_file() else disk_bytes(p) for p in roots if Path(p).exists())
                + sum(item["reserved_bytes"] for item in self.ledger.get("materializations", [])))

    def reserve_storage(self, amount):
        if self.study_bytes() + amount > self.policy["study_bytes"]:
            raise BudgetError("study_bytes")
        # Metadata has real disk cost too; leave a small transaction allowance.
        if disk_bytes(self.path) + amount + 4096 > self.policy["cache_bytes"]:
            raise BudgetError("cache_bytes")
        if shutil.disk_usage(self.path).free - amount - 4096 < self.policy["minimum_free_bytes"]:
            raise BudgetError("minimum_free_bytes")

    def admit_existing(self, record):
        if record["size_bytes"] > self.policy["asset_bytes"]:
            raise BudgetError("asset_bytes")
        if record.get("tree", {}).get("size_bytes", 0) > self.policy["expanded_bytes"]:
            raise BudgetError("expanded_bytes")
        paths = {r.get("cache_path") for r in self.ledger["assets"].values()}
        trees = {r.get("tree", {}).get("cache_path") for r in self.ledger["assets"].values()}
        added = 0 if record["cache_path"] in paths else record["size_bytes"]
        if record.get("tree", {}).get("cache_path") not in trees:
            added += record.get("tree", {}).get("size_bytes", 0)
        if self.study_bytes() + added > self.policy["study_bytes"]:
            raise BudgetError("study_bytes")
        # Reuse adds only metadata to physical cache usage.
        self.reserve_storage(0)

    def check(self, record):
        path = confined(self.path, record["cache_path"])
        require(path.is_file() and path.stat().st_size == record["size_bytes"] and
                sha256(path) == record["sha256"], "Cached asset is missing or corrupt")
        if record.get("tree"):
            tree = record["tree"]
            root = confined(self.path, tree["cache_path"])
            require(root.is_dir(), "Extracted source tree is missing")
            actual = {p.relative_to(root).as_posix(): {"sha256": sha256(p), "size_bytes": p.stat().st_size}
                      for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
            require(not any(p.is_symlink() for p in root.rglob("*")) and actual == tree["files"],
                    "Extracted source tree is missing or corrupt")
        return path

    def _charge_read(self, stream, amount, attempt):
        remaining = self.policy["study_transfer_bytes"] - self.ledger["transfer_bytes"]
        if amount > remaining:
            raise BudgetError("study_transfer_bytes")
        # Reserve before reading. A killed process retains the full reservation;
        # it cannot erase the cost of an interrupted or repeated transfer.
        self.ledger["transfer_bytes"] += amount
        attempt["charged_bytes"] += amount
        self.save()
        block = getattr(stream, "read1", stream.read)(amount)
        unused = amount - len(block)
        self.ledger["transfer_bytes"] -= unused
        attempt["charged_bytes"] -= unused
        self.save()
        return block

    def _download(self, asset, key, attempt, *, online, provided):
        directory = self.study / "partial" / key
        directory.mkdir(parents=True, exist_ok=True)
        part, state_path = directory / "data.part", directory / "state.json"
        state = read_json(state_path) if state_path.exists() else {}
        offset = part.stat().st_size if part.exists() else 0
        limit = self.policy["asset_bytes"]
        if asset.get("size_bytes", 0) > limit:
            raise BudgetError("asset_bytes")
        started = time.monotonic()
        expected_total = None
        stream = None
        try:
            if provided is not None:
                source = Path(provided)
                require(source.is_file() and not source.is_symlink(), "Provided assets must be regular files")
                expected_total = source.stat().st_size
                require(expected_total > 0, "Empty reference asset")
                if expected_total > limit:
                    raise BudgetError("asset_bytes")
                require(not source.resolve().is_relative_to(directory), "Cannot import an asset from its own partial download")
                # Local resumes verify the source identity before using a prefix.
                source_hash = sha256(source)
                if state.get("provided_sha256") != source_hash:
                    offset = 0
                stream = source.open("rb")
                stream.seek(offset)
                state = {"provided_sha256": source_hash}
            else:
                require(online, "Online acquisition requires an explicit --online request")
                headers = {"User-Agent": "Allagma-reference-acquisition/1.0", "Accept-Encoding": "identity"}
                validator = state.get("etag")
                if offset and (asset.get("sha256") or validator):
                    headers["Range"] = f"bytes={offset}-"
                    if validator:
                        headers["If-Range"] = validator
                else:
                    offset = 0
                stream = urlopen(Request(asset["url"], headers=headers), timeout=self.policy["request_timeout_seconds"], context=tls_context())
                require(stream.status in (200, 206), "Unexpected acquisition HTTP status")
                require(stream.headers.get("Content-Encoding", "identity") == "identity", "Encoded HTTP transfer is unsupported")
                if stream.status == 206:
                    content_range = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", stream.headers.get("Content-Range", ""))
                    require(content_range and int(content_range[1]) == offset and int(content_range[2]) + 1 == int(content_range[3]),
                            "Invalid resume Content-Range")
                    expected_total = int(content_range[3])
                    require(not validator or stream.headers.get("ETag") == validator, "Asset validator changed during resume")
                else:
                    offset = 0
                    if stream.headers.get("Content-Length"):
                        expected_total = int(stream.headers["Content-Length"])
                etag = stream.headers.get("ETag")
                state = {"etag": etag if etag and not etag.startswith("W/") else None}
            if expected_total is not None and expected_total > limit:
                raise BudgetError("asset_bytes")
            require(expected_total is None or offset <= expected_total, "Partial file exceeds declared source length")
            write_json(state_path, state)
            with part.open("ab" if offset else "wb") as output:
                while expected_total is None or offset < expected_total:
                    if time.monotonic() - started > self.policy["asset_timeout_seconds"]:
                        raise BudgetError("asset_timeout_seconds")
                    remaining = limit - offset
                    if remaining <= 0:
                        raise BudgetError("asset_bytes (length unknown at ceiling)")
                    amount = min(CHUNK, remaining, self.policy["study_transfer_bytes"] - self.ledger["transfer_bytes"])
                    if expected_total is not None:
                        amount = min(amount, expected_total - offset)
                    if amount <= 0:
                        raise BudgetError("study_transfer_bytes")
                    self.reserve_storage(amount)
                    block = self._charge_read(stream, amount, attempt)
                    if not block:
                        break
                    output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
                    offset += len(block)
            require(offset > 0 and (expected_total is None or offset == expected_total), "Interrupted or truncated asset transfer")
            require(asset.get("size_bytes") is None or offset == asset["size_bytes"], "Asset size differs from the pinned size")
            observed = sha256(part)
            require(not asset.get("sha256") or observed == asset["sha256"], "Asset digest differs from the pinned digest")
            if asset["kind"] == "paper-pdf":
                with part.open("rb") as check:
                    require(check.read(5) == b"%PDF-", "Paper PDF endpoint returned a different file format")
            destination = self.path / "objects" / observed / "data"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                require(sha256(destination) == observed, "Content-addressed object is corrupt; verify and quarantine it first")
                part.unlink()
            else:
                part.rename(destination)
                destination.chmod(0o444)
            state_path.unlink(missing_ok=True)
            directory.rmdir()
            return {"sha256": observed, "size_bytes": offset,
                    "cache_path": destination.relative_to(self.path).as_posix()}
        finally:
            if stream is not None:
                stream.close()

    def _extract(self, asset, record):
        kind = asset.get("extract", "none")
        if kind == "none":
            return
        blob = self.check(record)
        tree_root = self.path / "trees" / record["sha256"]
        receipt_path = self.path / "tree-manifests" / (record["sha256"] + ".json")
        if receipt_path.exists():
            record["tree"] = read_json(receipt_path)
            self.check(record)
            if len(record["tree"]["files"]) > self.policy["extraction_files"]:
                raise BudgetError("extraction_files")
            self.admit_existing(record)
            return
        staging = self.study / "partial" / (identity(asset) + "-extract")
        if staging.exists():
            # Interrupted extraction has no reusable authenticated output. Keep
            # it in the accounted quarantine instead of deleting evidence.
            target = self.study / "quarantine" / uuid.uuid4().hex
            target.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(target)
        staging.mkdir(parents=True)
        written, count, names = 0, 0, set()
        started = time.monotonic()

        def unpack(name, size, source, is_dir=False):
            nonlocal written, count
            count += 1
            if count > self.policy["extraction_files"]:
                raise BudgetError("extraction_files")
            name = name.rstrip("/")
            if name in ("", ".") and is_dir:
                return
            while name.startswith("./"):
                name = name[2:]
            require(name not in names, "Duplicate archive member")
            names.add(name)
            destination = confined(staging, name)
            if is_dir:
                destination.mkdir(parents=True, exist_ok=True)
                return
            if written + size > self.policy["expanded_bytes"]:
                raise BudgetError("expanded_bytes")
            self.reserve_storage(size)
            destination.parent.mkdir(parents=True, exist_ok=True)
            copied = 0
            with destination.open("xb") as output:
                while copied < size:
                    if time.monotonic() - started > self.policy["asset_timeout_seconds"]:
                        raise BudgetError("asset_timeout_seconds")
                    amount = min(CHUNK, size - copied)
                    self.reserve_storage(amount)
                    block = source.read(amount)
                    require(bool(block), "Truncated archive member")
                    output.write(block)
                    output.flush()
                    copied += len(block)
                    written += len(block)

        if kind == "zip":
            with zipfile.ZipFile(blob) as archive:
                require(len(archive.infolist()) <= self.policy["extraction_files"], "Archive file count exceeds its ceiling")
                for item in archive.infolist():
                    mode = item.external_attr >> 16
                    require(not stat.S_ISLNK(mode) and not item.flag_bits & 1 and
                            (stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR)), "Archive links, devices or encrypted files are unsupported")
                    with archive.open(item) as source:
                        unpack(item.filename, item.file_size, source, item.is_dir())
        else:
            with blob.open("rb") as raw:
                compressed = raw.read(2) == b"\x1f\x8b"
                raw.seek(0)
                expanded = gzip.GzipFile(fileobj=raw) if compressed else raw
                # Bound *all* decompressed bytes, including PAX headers and tar
                # padding, before the tar parser allocates member metadata.
                bounded = ExpandedReader(expanded, self.policy["expanded_bytes"])
                try:
                    with tarfile.open(fileobj=bounded, mode="r|") as archive:
                        for item in archive:
                            require(item.isfile() or item.isdir(), "Archive links and special files are unsupported")
                            source = archive.extractfile(item) if item.isfile() else io.BytesIO()
                            with source:
                                unpack(item.name, item.size, source, item.isdir())
                finally:
                    if compressed:
                        expanded.close()
        files = {p.relative_to(staging).as_posix(): {"sha256": sha256(p), "size_bytes": p.stat().st_size}
                 for p in sorted(staging.rglob("*")) if p.is_file()}
        require(files, "Source archive contains no files")
        tree_root.parent.mkdir(parents=True, exist_ok=True)
        require(not tree_root.exists(), "Unindexed extracted tree exists; inspect it before retrying")
        staging.rename(tree_root)
        for path in tree_root.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
        record["tree"] = {"cache_path": tree_root.relative_to(self.path).as_posix(),
                          "size_bytes": written, "files": files}
        write_json(receipt_path, record["tree"], immutable=True)

    def fetch(self, asset, *, online=False, provided=None, approval=None):
        key = identity(asset)
        if asset["access"] == "gated":
            allowed = (isinstance(approval, dict) and approval.get("decision") == "accept-asset-terms"
                       and approval.get("asset_identity") == key and approval.get("license_url") == asset["license"]["url"]
                       and all(nonempty(approval.get(k)) for k in ("approved_by", "approved_at", "reason")))
            retained = self.study / "approvals" / (key + ".json")
            if not allowed and retained.exists():
                old = read_json(retained)
                allowed = old.get("asset_identity") == key and old.get("license_url") == asset["license"]["url"]
            if not allowed:
                return {"status": "gated", "reason": "Researcher acceptance of these terms is required", "asset_identity": key}
            if approval:
                write_json(retained, approval, immutable=True)
        existing = self.ledger["assets"].get(key) or self.index.get(key)
        if existing and existing.get("status") == "available":
            self.check(existing)
            require(asset.get("size_bytes") is None or existing["size_bytes"] == asset["size_bytes"],
                    "Cached asset size disagrees with the supplied pin")
            self.admit_existing(existing)
            self.ledger["assets"][key] = existing
            self.save()
            return {**existing, "reused": True}
        if asset["access"] == "unavailable":
            result = {"status": "unavailable", "reason": asset["access_reason"]}
            self.ledger["assets"][key] = result
            self.save()
            return result
        cached_sha = asset.get("sha256") or (existing or {}).get("sha256")
        cached_blob = self.path / "objects" / (cached_sha or "unknown") / "data"
        have_blob = bool(cached_sha and cached_blob.is_file() and sha256(cached_blob) == cached_sha)
        attempts = [a for a in self.ledger["attempts"] if a["asset_identity"] == key]
        if len(attempts) >= self.policy["attempts_per_asset"]:
            return {"status": "budget-exceeded", "reason": "attempts_per_asset", "attempts": len(attempts)}
        if provided is None and not online and not have_blob:
            return {"status": "unavailable", "reason": "Asset is not cached or provided; online retrieval was not enabled"}
        if provided is None and asset.get("acquisition") == "provided" and not have_blob:
            return {"status": "unavailable", "reason": "Import the pinned file from the source package through --provided; its URL records provenance"}
        attempt = {"id": uuid.uuid4().hex, "asset_identity": key, "started_at": utcnow(),
                   "status": "running", "charged_bytes": 0, "policy_sha256": digest(self.policy)}
        self.ledger["attempts"].append(attempt)
        self.save()
        result = {}
        try:
            with asset_deadline(self.policy["asset_timeout_seconds"]):
                # Shared content can be reused by digest even across source URLs.
                if have_blob:
                    result = {"sha256": cached_sha, "size_bytes": cached_blob.stat().st_size,
                              "cache_path": cached_blob.relative_to(self.path).as_posix()}
                    require(asset.get("size_bytes") is None or result["size_bytes"] == asset["size_bytes"],
                            "Cached asset size disagrees with the supplied pin")
                    self.admit_existing(result)
                else:
                    result = self._download(asset, key, attempt, online=online, provided=provided)
                # Account for the object before extraction and preserve its verified
                # identity even if extraction stops at a ceiling.
                self.ledger["assets"][key] = result
                self.save()
                self._extract(asset, result)
            result.update(status="available", acquired_at=utcnow(), asset_identity=key)
            self.index[key] = result
            write_json(self.index_path, self.index)
        except BudgetError as exc:
            result.update(status="budget-exceeded", reason=str(exc))
        except HTTPError as exc:
            result.update(status="unavailable" if exc.code in (401, 403, 404, 410) else "partial", reason=f"HTTP {exc.code}")
        except (URLError, TimeoutError, OSError, HTTPException) as exc:
            reason = "TLS verification failed; configure a trusted SSL_CERT_FILE" if isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError) else type(exc).__name__
            result.update(status="partial", reason=reason)
        except (AllagmaError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
            # Our validation messages contain no authenticated transport URL.
            result.update(status="failed", reason=str(exc))
        finally:
            attempt.update(status=result.get("status", "interrupted"), ended_at=utcnow())
            self.ledger["assets"][key] = result or {"status": "interrupted"}
            self.save()
        return result


class ExpandedReader:
    def __init__(self, stream, limit):
        self.stream, self.remaining = stream, limit

    def read(self, size):
        if size < 0 or size > self.remaining:
            raise BudgetError("expanded_bytes (archive stream)")
        result = self.stream.read(size)
        self.remaining -= len(result)
        return result


def acquire(cache, manifest, directory, *, online=False, provided=None, approvals=None):
    validate_manifest(manifest)
    initialize(cache)
    provided, approvals = provided or {}, approvals or {}
    assets = []
    with mutex(cache):
        controller = Cache(cache, manifest["study_id"])
        # A process that held this lock cannot still be acquiring. Keep the
        # reservation charged and use a new attempt for any continuation.
        controller.recover()
        for asset in manifest["assets"]:
            try:
                result = controller.fetch(asset, online=online, provided=provided.get(asset["id"]), approval=approvals.get(asset["id"]))
            except BudgetError as exc:
                result = {"status": "budget-exceeded", "reason": str(exc)}
            except (AllagmaError, OSError) as exc:
                previous = controller.ledger["assets"].get(identity(asset)) or controller.index.get(identity(asset)) or {}
                result = {key: val for key, val in previous.items() if key in ("sha256", "size_bytes", "cache_path", "tree", "asset_identity")}
                result.update(status="corrupt", reason=str(exc) if isinstance(exc, AllagmaError) else type(exc).__name__)
            assets.append({**asset, **result})
        output = {"format": "allagma-reference-retrieval-v1", "study_id": manifest["study_id"],
                  "created_at": utcnow(), "policy": controller.policy, "assets": assets,
                  "transfer_bytes": controller.ledger["transfer_bytes"],
                  "scope": "Available means byte integrity verified, not license clearance or scientific correctness"}
        write_json(Path(directory) / "retrieval.json", output)
    return output


def verify(cache, retrieval):
    with mutex(cache):
        controller = Cache(cache, retrieval["study_id"])
        checked = []
        for record in retrieval["assets"]:
            if record["status"] == "available":
                controller.check(record)
                checked.append(record["id"])
    return {"status": "pass", "checked": checked}


def quarantine(cache, retrieval, asset_id):
    """Preserve corrupt bytes; a later fetch is a separately charged attempt."""
    with mutex(cache):
        controller = Cache(cache, retrieval["study_id"])
        records = [r for r in retrieval["assets"] if r["id"] == asset_id]
        require(len(records) == 1 and records[0].get("cache_path"), "No cached identity for that asset")
        record = records[0]
        try:
            controller.check(record)
        except (AllagmaError, OSError):
            pass
        else:
            raise AllagmaError("The asset is intact; quarantine is only for corruption or missing bytes")
        moved = []
        paths = [record["cache_path"]]
        if record.get("tree"):
            paths.append(record["tree"]["cache_path"])
        for relative in paths:
            path = confined(controller.path, relative)
            if path.exists():
                target = controller.study / "quarantine" / uuid.uuid4().hex
                target.parent.mkdir(parents=True, exist_ok=True)
                path.rename(target)
                moved.append(target.relative_to(controller.path).as_posix())
        receipt = controller.path / "tree-manifests" / (record["sha256"] + ".json")
        if receipt.exists():
            target = controller.study / "quarantine" / (uuid.uuid4().hex + ".json")
            receipt.rename(target)
        for key, value in list(controller.index.items()):
            if value.get("sha256") == record["sha256"]:
                del controller.index[key]
        for value in controller.ledger["assets"].values():
            if value.get("sha256") == record["sha256"]:
                value["status"] = "corrupt"
                value.pop("cache_path", None)
                value.pop("tree", None)
        controller.save()
        write_json(controller.index_path, controller.index)
    return {"status": "quarantined", "preserved_paths": moved}


def input_plan(cache, retrieval):
    controller = Cache(cache, retrieval["study_id"])
    files = {}
    for record in retrieval["assets"]:
        if record["use"] != "execution":
            continue
        require(record["status"] == "available", f"Execution asset is unavailable: {record['id']}")
        source = controller.check(record)
        if record.get("tree"):
            for name, metadata in record["tree"]["files"].items():
                relative = record["id"] + "/" + name
                files[relative] = {**metadata, "source": str(confined(controller.path,
                    record["tree"]["cache_path"] + "/" + name)), "asset_id": record["id"]}
        else:
            name = record.get("filename", record["id"] + ".bin")
            require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name), "Invalid execution asset filename")
            files[record["id"] + "/" + name] = {"source": str(source), "sha256": record["sha256"],
                                                "size_bytes": record["size_bytes"], "asset_id": record["id"]}
    return files


def materialize(cache, retrieval, destination, *, storage_limit):
    """Copy only required execution inputs; keep raw copies out of Git too."""
    destination = Path(destination).resolve()
    require(not destination.exists(), "Reference input destination already exists")
    with mutex(cache):
        controller = Cache(cache, retrieval["study_id"])
        controller.recover()
        plan = input_plan(cache, retrieval)
        size = sum(item["size_bytes"] for item in plan.values())
        require(size < storage_limit, "Reference execution inputs exceed the prepared workspace storage ceiling")
        if controller.study_bytes() + size > controller.policy["study_bytes"]:
            raise BudgetError("study_bytes (including protected input copies)")
        if not plan:
            return {"files": {}, "bytes": 0}
        # A stand-alone prepared workspace gets its own Git repository only
        # when raw execution assets need a local exclusion. Existing enclosing
        # repositories, including linked worktrees, retain their configuration.
        probe = destination.parent
        while not probe.exists():
            probe = probe.parent
        check = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"], capture_output=True)
        if check.returncode:
            workspace = destination.parent.parent
            subprocess.run(["git", "init", "-q", str(workspace)], check=True, capture_output=True)
        exclusion = exclude_cache(destination)
        transaction = {"destination": str(destination), "reserved_bytes": size,
                       "started_at": utcnow(), "status": "preparing"}
        controller.ledger.setdefault("materializations", []).append(transaction)
        controller.save()
        try:
            destination.mkdir(parents=True)
            write_json(destination / ".allagma-reference-cache.json", {"format": "allagma-raw-reference-cache-v1"}, immutable=True)
            public = {}
            for name, item in plan.items():
                target = confined(destination, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                if shutil.disk_usage(target.parent).free - item["size_bytes"] < controller.policy["minimum_free_bytes"]:
                    raise BudgetError("minimum_free_bytes (protected input copy)")
                # shutil uses the platform's efficient copying primitive when
                # available. Never hardlink mutable study inputs to shared cache.
                shutil.copyfile(item["source"], target)
                require(sha256(target) == item["sha256"], "Reference asset changed while preparing immutable inputs")
                target.chmod(0o444)
                public[name] = {k: v for k, v in item.items() if k != "source"}
            transaction.update(status="completed", completed_at=utcnow())
            return {"files": public, "bytes": size, "git_exclusion": exclusion["pattern"]}
        except BaseException as exc:
            transaction.update(status="interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed",
                               ended_at=utcnow(), reason=type(exc).__name__)
            raise
        finally:
            controller.save()
