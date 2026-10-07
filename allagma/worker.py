"""A bounded POSIX worker that outlives an interrupted controller.

The worker owns the timeout and child process group, so controller termination
does not turn a bounded local job into an unbounded orphan.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main(path):
    job = json.loads(Path(path).read_text())
    child = None
    started = time.monotonic()
    result = {"exit_code": None, "stop": None}

    def signal_group(signum):
        try:
            os.killpg(child.pid, signum)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # On macOS an already-disappeared group can report EPERM after its
            # leader is reaped. Do not mistake that race for a live job, and do
            # not assume that every permission error means the group is gone.
            groups = subprocess.run(["ps", "-e", "-o", "pgid=,stat="],
                                    capture_output=True, text=True, timeout=0.5)
            if groups.returncode:
                raise
            if any(fields[0] == str(child.pid) and not fields[1].startswith("Z")
                   for line in groups.stdout.splitlines() if len(fields := line.split()) == 2):
                raise
            return False

    def terminate():
        if child is None:
            return
        # The process-group leader can exit before its descendants. Checking
        # only child.poll() would then abandon a live group and late writes.
        if not signal_group(signal.SIGTERM):
            child.wait(timeout=1)
            return
        deadline = time.monotonic() + 0.2
        while time.monotonic() < deadline:
            child.poll()  # Reap the leader so it does not keep the group alive.
            if not signal_group(0):
                break
            time.sleep(0.01)
        else:
            signal_group(signal.SIGKILL)
        child.wait(timeout=1)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        with Path(job["stdout"]).open("xb") as out, Path(job["stderr"]).open("xb") as err:
            child = subprocess.Popen(job["command"], cwd=job["cwd"], stdout=out, stderr=err,
                                     start_new_session=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            if job["interrupt"]:
                deadline = time.monotonic() + min(job["timeout"], 5)
                ready = Path(job["cwd"]) / "interrupt-ready"
                while child.poll() is None and not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                result["stop"] = "interrupted" if ready.exists() else "checkpoint_missing"
            else:
                try:
                    child.wait(timeout=job["timeout"])
                except subprocess.TimeoutExpired:
                    result["stop"] = "timeout"
    except KeyboardInterrupt:
        result["stop"] = "interrupted"
    except Exception as exc:
        result["stop"] = "worker_error"
        result["error"] = str(exc)
    finally:
        try:
            terminate()
        except Exception as exc:
            result["stop"] = "worker_error"
            result["error"] = f"Process-group cleanup could not be verified: {exc}"
        result["exit_code"] = child.poll() if child else None
        result["wall_seconds"] = time.monotonic() - started
        target = Path(job["result"])
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        os.replace(temporary, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
