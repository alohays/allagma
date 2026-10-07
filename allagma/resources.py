"""Finite local process budgets, independent of any study's scientific logic.

Reservations and outcomes are separate immutable files. An absent outcome costs
the entire reservation. POSIX process/RSS and storage watchdogs are operational
limits, not a security boundary or an exact GPU-memory accounting mechanism.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time

from .files import AllagmaError, digest, read_json, utcnow, write_json

FORMAT = "allagma-resource-profile-v1"
FIELDS = {"format", "budgets_seconds", "command_timeout_seconds", "attempt_limit",
          "rss_limit_bytes", "storage_limit_bytes", "file_limit_bytes",
          "poll_seconds", "terminate_grace_seconds"}


def validate_profile(profile):
    if set(profile) != FIELDS or profile["format"] != FORMAT:
        raise AllagmaError("Resource profile has missing, extra or unsupported fields")
    for name in ("budgets_seconds", "command_timeout_seconds"):
        mapping = profile[name]
        if not isinstance(mapping, dict) or not mapping:
            raise AllagmaError(f"{name} must be a nonempty category-to-seconds mapping")
        for key, value in mapping.items():
            if not re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", key):
                raise AllagmaError("Invalid resource category")
            _positive(value, name)
    if profile["budgets_seconds"].keys() != profile["command_timeout_seconds"].keys():
        raise AllagmaError("Budget and timeout categories must match")
    for name in ("attempt_limit", "rss_limit_bytes", "storage_limit_bytes", "file_limit_bytes"):
        if type(profile[name]) is not int or profile[name] <= 0:
            raise AllagmaError(f"{name} must be a positive integer")
    for name in ("poll_seconds", "terminate_grace_seconds"):
        _positive(profile[name], name)
    if not .02 <= profile["poll_seconds"] <= 1:
        raise AllagmaError("Watchdog interval must be between 0.02 and 1 second")
    if profile["terminate_grace_seconds"] > 5:
        raise AllagmaError("Termination grace must not exceed five seconds")
    return profile


def _positive(value, name):
    if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
        raise AllagmaError(f"{name} must contain finite positive numbers")


def initialize(directory, profile, workdir):
    directory, workdir = Path(directory).resolve(), Path(workdir).resolve()
    validate_profile(profile)
    if not workdir.is_dir():
        raise AllagmaError("Resource work directory does not exist")
    directory.mkdir(parents=True, exist_ok=True)
    with _mutex(directory):
        write_json(directory / "policy.json", {"profile": profile,
            "profile_sha256": digest(profile), "workdir": str(workdir),
            "created_at": utcnow()}, immutable=True)
    return summary(directory)


@contextmanager
def _mutex(directory):
    with (directory / ".mutex").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AllagmaError("Another resource operation is live; observe it instead of restarting") from exc
        yield


def _policy(directory):
    value = read_json(directory / "policy.json")
    validate_profile(value["profile"])
    if digest(value["profile"]) != value["profile_sha256"]:
        raise AllagmaError("Resource policy digest mismatch")
    return value


def summary(directory):
    directory = Path(directory).resolve()
    policy = _policy(directory)
    charged = {key: 0. for key in policy["profile"]["budgets_seconds"]}
    entries, attempts = [], 0
    for path in sorted(directory.glob("jobs/*/reservation.json")):
        reservation = read_json(path)
        if reservation["profile_sha256"] != policy["profile_sha256"]:
            raise AllagmaError("Reservation belongs to a different resource policy")
        result_path = path.parent / "result.json"
        result = read_json(result_path) if result_path.exists() else None
        cost = result["charged_seconds"] if result else reservation["reserved_seconds"]
        _positive(cost, "charged_seconds")
        charged[reservation["category"]] += cost
        attempts += reservation["attempt"]
        entries.append({"job": path.parent.name, "reservation": reservation, "result": result,
                        "charged_seconds": cost})
    return {"profile_sha256": policy["profile_sha256"], "workdir": policy["workdir"],
            "charged_seconds": charged,
            "remaining_seconds": {key: max(0., limit-charged[key])
                for key, limit in policy["profile"]["budgets_seconds"].items()},
            "attempts": attempts, "attempt_limit": policy["profile"]["attempt_limit"],
            "entries": entries}


def storage_bytes(directory):
    """Logical regular-file bytes; do not follow links outside the study."""
    total = 0
    for root, dirs, files in os.walk(directory, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(root) / name).is_symlink()]
        for name in files:
            path = Path(root) / name
            try:
                if not path.is_symlink() and path.is_file():
                    total += path.stat().st_size
            except FileNotFoundError:
                pass  # Atomic replacement between the directory scan and stat.
    return total


def process_table():
    result = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,rss=,lstart="],
                            capture_output=True, text=True, timeout=3, check=True)
    processes = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 4)
        if len(fields) == 5:
            pid, parent, group, rss = map(int, fields[:4])
            processes[pid] = {"parent": parent, "group": group, "rss": rss*1024,
                              "started": fields[4]}
    return processes


def _family(table, pid, known):
    found = {key for key, start in known.items()
             if key in table and table[key]["started"] == start}
    if pid in table and (pid not in known or table[pid]["started"] == known[pid]):
        found.add(pid)
    while True:
        extra = {key for key, item in table.items() if item["parent"] in found}
        if extra <= found:
            return {key: table[key]["started"] for key in found}
        found |= extra


def _stop(process, known, grace):
    # A child may have created another session. Kill observed descendants too.
    table = process_table()
    known = _family(table, process.pid, known)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except (ProcessLookupError, PermissionError):
            # Some macOS hosts deny group signaling but allow signaling owned
            # child PIDs. The observed identity-checked family is still stopped.
            pass
        table = process_table()
        for pid, started in known.items():
            if pid in table and table[pid]["started"] == started:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
        if sig == signal.SIGTERM:
            time.sleep(grace)
    process.wait(timeout=3)


def recover(directory):
    """Mark abandoned reservations without crediting unmeasured computation."""
    directory = Path(directory).resolve()
    with _mutex(directory):
        table = process_table()
        recovered = []
        for entry in summary(directory)["entries"]:
            if entry["result"] is not None:
                continue
            job = directory / "jobs" / entry["job"]
            child_path = job / "process.json"
            if child_path.exists():
                child = read_json(child_path)
                if any(item["group"] == child["pid"] for item in table.values()):
                    raise AllagmaError("An abandoned job still has live processes; inspect and terminate them before recovery")
            write_json(job / "result.json", {"status": "abandoned", "exit_code": None,
                "ended_at": utcnow(), "charged_seconds": entry["reservation"]["reserved_seconds"],
                "charge_basis": "full reservation: missing outcome", "peak_rss_bytes": None,
                "peak_storage_bytes": None}, immutable=True)
            recovered.append(entry["job"])
    return {"recovered": recovered, "summary": summary(directory)}


def execute(directory, command, *, label, category, timeout, attempt=False):
    directory = Path(directory).resolve()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", label):
        raise AllagmaError("Invalid resource job label")
    if not command or not all(isinstance(x, str) and x and "\0" not in x for x in command):
        raise AllagmaError("Resource command must be a nonempty argv array")
    _positive(timeout, "timeout")
    with _mutex(directory):
        policy = _policy(directory)
        profile, workdir = policy["profile"], Path(policy["workdir"])
        current = summary(directory)
        if any(entry["result"] is None for entry in current["entries"]):
            raise AllagmaError("An unresolved reservation exists; observe or recover it first")
        if category not in profile["command_timeout_seconds"] or timeout > profile["command_timeout_seconds"][category]:
            raise AllagmaError("Command category or timeout exceeds the frozen resource policy")
        reserve = timeout + profile["terminate_grace_seconds"] + profile["poll_seconds"] + 4
        if current["remaining_seconds"][category] < reserve:
            raise AllagmaError("Insufficient remaining budget for the full timeout reservation")
        if attempt and current["attempts"] >= profile["attempt_limit"]:
            raise AllagmaError("Attempt ceiling reached")
        initial_storage = storage_bytes(workdir)
        if initial_storage >= profile["storage_limit_bytes"]:
            raise AllagmaError("Study already reaches its storage ceiling")
        job = directory / "jobs" / f"{len(current['entries'])+1:04d}-{label}"
        job.mkdir(parents=True, exist_ok=False)
        reservation = {"label": label, "command": command, "category": category,
            "attempt": bool(attempt), "timeout_seconds": timeout, "reserved_seconds": reserve,
            "workdir": str(workdir), "profile_sha256": policy["profile_sha256"],
            "started_at": utcnow(), "supervisor_pid": os.getpid()}
        write_json(job / "reservation.json", reservation, immutable=True)
        environment = {**os.environ, "ALLAGMA_RESOURCE_RECEIPT": str(job / "reservation.json")}
        interrupted = []
        previous_handlers = {}
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.signal(sig, lambda signum, frame: interrupted.append(signum))
        process, known, status = None, {}, "failed"
        started, peak_rss, peak_storage = time.monotonic(), 0, initial_storage

        def file_limit():
            resource.setrlimit(resource.RLIMIT_FSIZE,
                               (profile["file_limit_bytes"], profile["file_limit_bytes"]))

        try:
            with (job / "stdout.txt").open("wb") as out, (job / "stderr.txt").open("wb") as err:
                process = subprocess.Popen(command, cwd=workdir, env=environment,
                    stdout=out, stderr=err, start_new_session=True, preexec_fn=file_limit)
                write_json(job / "process.json", {"pid": process.pid, "started_at": utcnow()}, immutable=True)
                while True:
                    table = process_table()
                    known = _family(table, process.pid, known)
                    peak_rss = max(peak_rss, sum(table[pid]["rss"] for pid in known))
                    peak_storage = max(peak_storage, storage_bytes(workdir))
                    if interrupted:
                        status = "interrupted"
                    elif time.monotonic()-started >= timeout:
                        status = "timed_out"
                    elif peak_rss > profile["rss_limit_bytes"]:
                        status = "memory_exceeded"
                    elif peak_storage > profile["storage_limit_bytes"]:
                        status = "storage_exceeded"
                    elif process.poll() is not None:
                        status = "completed" if process.returncode == 0 else "failed"
                        if any(pid != process.pid for pid in known):
                            status = "orphaned_children"
                            _stop(process, known, profile["terminate_grace_seconds"])
                        break
                    else:
                        time.sleep(profile["poll_seconds"])
                        continue
                    _stop(process, known, profile["terminate_grace_seconds"])
                    break
            outcome = {"status": status, "exit_code": process.returncode,
                "ended_at": utcnow(), "charged_seconds": time.monotonic()-started,
                "charge_basis": "measured supervisor wall time", "peak_rss_bytes": peak_rss,
                "peak_storage_bytes": peak_storage,
                "monitor_scope": "Polled process-tree RSS and workdir logical file bytes; RSS excludes some GPU allocations; not adversarial containment"}
        except BaseException:
            if process is not None:
                _stop(process, known, profile["terminate_grace_seconds"])
            # Leave the reservation unresolved and fully charged on uncertainty.
            raise
        finally:
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
        write_json(job / "result.json", outcome, immutable=True)
        return {"job": str(job), **outcome}
