"""Canonical JSON, content references, confined paths, and atomic writes."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import tempfile


class AllagmaError(Exception):
    """An actionable contract, configuration or integrity error."""


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return digest_bytes(canonical(value))


def file_hash(path):
    try:
        result = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                result.update(block)
        return result.hexdigest()
    except OSError as exc:
        raise AllagmaError(f"Cannot hash artifact {path}: {exc}") from exc


def read_json(path):
    def reject_constant(value):
        raise AllagmaError(f"Non-finite JSON value: {value}")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AllagmaError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise AllagmaError(f"Non-finite JSON number: {value}")
        return result

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          parse_constant=reject_constant, parse_float=finite_float,
                          object_pairs_hook=unique)
    except (OSError, ValueError) as exc:
        raise AllagmaError(f"Cannot read {path}: {exc}. Use JSON-compatible YAML.") from exc


def confined(root, relative):
    """Reject traversal and symlinks, including dangling symlinks."""
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise AllagmaError(f"Invalid relative path: {relative!r}")
    part = PurePosixPath(relative)
    if part.is_absolute() or any(p in ("..", ".") for p in relative.split("/")):
        raise AllagmaError(f"Path must stay within its root: {relative}")
    target = root
    for name in part.parts:
        target = target / name
        if target.is_symlink():
            raise AllagmaError(f"Symlinks are not bundle or evidence files: {relative}")
    if not target.resolve().is_relative_to(root):
        raise AllagmaError(f"Escaping path: {relative}")
    return target


def write_bytes(path, data, *, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise AllagmaError(f"Refusing symlink write: {path}")
    if immutable:
        try:
            with path.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            if path.read_bytes() != data:
                raise AllagmaError(f"Immutable artifact already exists: {path}") from exc
        return
    fd, temp = tempfile.mkstemp(prefix=".allagma-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def write_json(path, value, *, immutable=False):
    write_bytes(path, canonical(value), immutable=immutable)


def write_text(path, value, *, immutable=False):
    write_bytes(path, value.encode(), immutable=immutable)


def inventory(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            raise AllagmaError(f"Symlink in inventory: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = file_hash(path)
    return result


def verify_inventory(root, expected):
    actual = inventory(root)
    changes = sorted(p for p in actual.keys() | expected.keys()
                     if actual.get(p) != expected.get(p))
    if changes:
        raise AllagmaError("Inventory mismatch: " + ", ".join(changes))


def reference(root, path, media_type=None):
    root, path = Path(root).absolute(), Path(path).absolute()
    # Inspect the supplied path before resolving it; resolution would hide an
    # alias symlink and silently change the identity of the referenced file.
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        try:
            relative = path.relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise AllagmaError(f"Evidence path is outside its root: {path}") from exc
    path = confined(root, relative)
    media_type = media_type or {".json": "application/json", ".yaml": "application/json", ".py": "text/x-python",
                                ".md": "text/markdown", ".csv": "text/csv", ".svg": "image/svg+xml", ".txt": "text/plain"}.get(path.suffix, "application/octet-stream")
    return {"path": relative, "sha256": file_hash(path), "media_type": media_type,
            "retention": "retain-with-study"}


def verify_reference(root, ref):
    path = confined(root, ref["path"])
    if not path.is_file() or file_hash(path) != ref["sha256"]:
        raise AllagmaError(f"Missing or changed evidence: {ref['path']}")
    return path


def publication_reference(root, path, staging, target, media_type=None):
    """Hash prepared bytes while recording their eventual immutable location."""
    result = reference(root, path, media_type)
    published = Path(target) / Path(path).relative_to(staging)
    result["path"] = published.relative_to(Path(root)).as_posix()
    confined(root, result["path"])
    return result


@contextmanager
def staged_directory(study, target):
    """Publish a complete initial directory with one same-filesystem rename.

    A killed preparer may leave a staging directory, but no executable job has
    been launched and no incomplete campaign or attempt has been published.
    """
    parent = confined(study, ".allagma/staging")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prepare-", dir=parent) as temp:
        staging = Path(temp)
        yield staging
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise AllagmaError(f"Prepared artifact already exists: {target}")
        staging.rename(target)


@contextmanager
def study_mutex(study):
    """Serialize local mutating operations; kernel releases locks on process death."""
    path = confined(study, ".allagma/mutation.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AllagmaError("Another Allagma operation holds this study's lock") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)
