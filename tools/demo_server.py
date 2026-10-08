#!/usr/bin/env python3
"""A loopback-only recording workbench for the actual offline Allagma example.

This demonstration utility exposes exactly two bounded commands, never an
arbitrary shell. It creates new study evidence and serves only selected files.
It is not the native agent runner or a hosted research service.
"""
from __future__ import annotations

import argparse
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Workbench:
    def __init__(self, output):
        if output.exists():
            raise SystemExit("Choose a new output directory; previous captures are retained")
        output.mkdir(parents=True)
        self.output, self.study = output, output / "study"
        self.lock, self.events = threading.Lock(), []
        self.running, self.started, self.complete, self.audit = False, False, False, None

    def start(self, operation):
        with self.lock:
            if self.running or (operation == "run" and self.started) or (operation == "audit" and not self.complete):
                return False
            self.running = True
            if operation == "run":
                self.started = True
        threading.Thread(target=self.execute, args=(operation,), daemon=True).start()
        return True

    def execute(self, operation):
        stamp = time.time()
        command = [sys.executable, "-m", "allagma"]
        if operation == "run":
            command += ["toy", "--destination", str(self.study)]
        else:
            command += ["campaign", "audit", "--study", str(self.study), "--campaign", "toy-v1"]
        number = len(self.events) + 1
        record = {"operation": operation, "command": command, "started_at_unix": stamp, "status": "running"}
        self.events.append(record)
        log = self.output / f"command-{number:02d}"
        try:
            with log.with_suffix('.stdout').open('wb') as out, log.with_suffix('.stderr').open('wb') as err:
                process = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=120)
            record.update(exit_code=process.returncode, status="completed" if process.returncode == 0 else "failed")
            if process.returncode == 0:
                result = json.loads(log.with_suffix('.stdout').read_text())
                if operation == "run":
                    self.complete = True
                    self.audit = result["audit"]
                else:
                    self.audit = result
        except subprocess.TimeoutExpired:
            record.update(status="timeout", exit_code=None)
        except Exception as error:
            record.update(status="failed", error=str(error))
        finally:
            record["wall_seconds"] = time.time() - stamp
            log.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n')
            with self.lock:
                self.running = False

    def state(self):
        attempts = []
        for p in sorted((self.study / "campaigns/toy-v1/runs").glob("*/attempts/*/record.json")):
            try:
                j = json.loads(p.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                continue
            attempts.append({"run": j["run_id"], "attempt": j["attempt_id"], "status": j["status"], "split": j["split"]})
        summary, claims = None, []
        analysis = self.study / "campaigns/toy-v1/analyses/a001"
        if self.complete:
            summary = json.loads((analysis / "outputs/summary.json").read_text())
            claims = json.loads((analysis / "paper/claims.json").read_text())
        return {"capture_root": str(self.output), "running": self.running, "started": self.started, "complete": self.complete,
                "attempts": attempts, "counts": dict(Counter(a["status"] for a in attempts)),
                "summary": summary, "claims": claims, "audit": self.audit,
                "events": [{k:v for k,v in e.items() if k != 'command'} for e in self.events]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--port", type=int, default=4330)
    args = parser.parse_args()
    workbench = Workbench(args.output.resolve())
    files = {
        "/": (ROOT/"media/source/workbench.html", "text/html; charset=utf-8"),
        "/figure.svg": (workbench.study/"campaigns/toy-v1/analyses/a001/outputs/paired-differences.svg", "image/svg+xml"),
        "/report.md": (workbench.study/"campaigns/toy-v1/analyses/a001/paper/manuscript.md", "text/plain; charset=utf-8"),
        "/native-figure.png": (ROOT/"studies/ema-schedule/figures/r07-main-figure.png", "image/png"),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, code, data, kind="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            request_path = urlparse(self.path).path
            if request_path == "/state":
                self.respond(200, json.dumps(workbench.state()).encode())
            elif request_path in files:
                path, kind = files[request_path]
                if path.exists():
                    self.respond(200, path.read_bytes(), kind)
                else:
                    self.respond(404, b'{"error":"artifact not yet created"}')
            else:
                self.respond(404, b'{"error":"not found"}')

        def do_POST(self):
            # Reject cross-origin form/script requests; there is no CORS or
            # arbitrary path/command input. The workbench binds loopback only.
            origin = self.headers.get("Origin")
            if origin != f"http://127.0.0.1:{args.port}" or self.headers.get("X-Allagma-Demo") != "1":
                self.respond(403, b'{"error":"same-origin workbench requests only"}')
                return
            operation = {"/run":"run", "/audit":"audit"}.get(self.path)
            if not operation or not workbench.start(operation):
                self.respond(409, b'{"error":"operation unavailable"}')
                return
            self.respond(202, b'{"status":"started"}')

    print(f"Allagma recording workbench: http://127.0.0.1:{args.port}", flush=True)
    print(f"Fresh evidence directory: {workbench.output}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
