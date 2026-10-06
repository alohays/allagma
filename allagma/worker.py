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

    def terminate():
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=1)
            except ProcessLookupError:
                pass

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
                terminate()
            else:
                try:
                    child.wait(timeout=job["timeout"])
                except subprocess.TimeoutExpired:
                    result["stop"] = "timeout"
                    terminate()
            result["exit_code"] = child.returncode
    except KeyboardInterrupt:
        result["stop"] = "interrupted"
        terminate()
        result["exit_code"] = child.returncode if child else None
    except Exception as exc:
        result["stop"] = "worker_error"
        result["error"] = str(exc)
        terminate()
    finally:
        terminate()
        result["wall_seconds"] = time.monotonic() - started
        target = Path(job["result"])
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        os.replace(temporary, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
