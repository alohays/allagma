"""Optional native Codex session capture with explicit local isolation.

This adapter does not plan a study, choose a model, authenticate a new account,
or judge science. Callers supply a workspace, prompt, deadline and protection
roots. It snapshots selected existing user settings into a fresh runtime home.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import tomllib

SETTING_KEYS = ("model", "model_reasoning_effort", "model_context_window",
                "model_auto_compact_token_limit", "model_provider")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")
    temporary.replace(path)


def seatbelt_profile(*, blocked, allowed, readonly):
    """Read/write exclusions are absolute paths; no shell interpolation."""
    q = lambda path: json.dumps(str(Path(path).resolve()))
    exceptions = "(require-any " + " ".join(f"(subpath {q(path)})" for path in allowed) + ")"
    lines = ["(version 1)", "(allow default)"]
    for path in blocked:
        predicate = f"(subpath {q(path)})"
        if allowed:
            predicate = f"(require-all {predicate} (require-not {exceptions}))"
        lines.append(f"(deny file-read* file-write* {predicate})")
    for path in readonly:
        lines.append(f"(deny file-write* (subpath {q(path)}))")
    return "\n".join(lines)+"\n"


def selected_settings(path):
    source = tomllib.loads(Path(path).read_text())
    settings = {key: source[key] for key in SETTING_KEYS if key in source}
    if not isinstance(settings.get("model"), str) or not settings["model"]:
        raise ValueError("An explicit existing user model is required to preserve selection in an isolated session")
    if "model_provider" in settings and settings["model_provider"] != "openai":
        raise ValueError("Custom provider authentication/configuration needs separate qualification")
    return settings


def stop(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        if process.poll() is None:
            process.send_signal(sig)
        try:
            process.wait(timeout=2)
            return
        except subprocess.TimeoutExpired:
            pass
    process.wait(timeout=3)


def observations(runtime):
    result = []
    for path in sorted((runtime/"sessions").rglob("*.jsonl")):
        for line in path.open():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "turn_context":
                payload = event["payload"]
                result.append({key: payload[key] for key in
                    ("model", "effort", "cwd", "approval_policy", "sandbox_policy") if key in payload})
    return result


def capture(*, codex, workspace, record, runtime, prompt, timeout,
            config, auth, blocked=(), readonly=(), on_tick=None):
    if os.uname().sysname != "Darwin":
        raise ValueError("This isolation adapter currently qualifies macOS only")
    if not 0 < timeout <= 7200:
        raise ValueError("Native session deadline must be finite and at most two hours")
    workspace, record, runtime = (Path(p).resolve() for p in (workspace, record, runtime))
    if not workspace.is_dir() or record.exists() or runtime.exists():
        raise ValueError("Require existing workspace and new record/runtime directories")
    config, auth = Path(config).resolve(), Path(auth).resolve()
    settings = selected_settings(config)
    if not auth.is_file():
        raise ValueError("Existing Codex auth file unavailable; do not provision a new account")
    record.mkdir(parents=True)
    runtime.mkdir(parents=True, mode=0o700)
    (runtime/"auth.json").symlink_to(auth)
    # The temporary runtime is a CODEX_HOME, not a project .codex configuration.
    # Personal tools, global instructions and saved chat histories are excluded.
    controlled = {**settings, "web_search": "disabled", "project_doc_max_bytes": 0}
    (runtime/"config.toml").write_text("".join(f"{key} = {json.dumps(value)}\n" for key, value in controlled.items()))
    profile = seatbelt_profile(blocked=blocked, allowed=[workspace, runtime, auth], readonly=readonly)
    (record/"isolation.sb").write_text(profile)
    (record/"prompt.txt").write_text(prompt)
    command = ["/usr/bin/sandbox-exec", "-p", profile, str(codex), "--strict-config", "-a", "never",
               "exec", "--sandbox", "workspace-write", "--ignore-rules", "--skip-git-repo-check",
               "--json", "-C", str(workspace), "-o", str(runtime/"final.txt"), "-"]
    environment = {key: value for key, value in os.environ.items() if key in
                   ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "SHELL", "TERM", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")}
    environment["CODEX_HOME"] = str(runtime)
    receipt = {"started_at": now(), "workspace": str(workspace), "runtime": str(runtime),
        "fresh_session": True, "resume": False, "prompt_sha256": sha(record/"prompt.txt"),
        "settings": settings, "controlled_settings": controlled,
        "settings_source": str(config), "project_model_config_written": False,
        "runtime_config_sha256": sha(runtime/"config.toml"),
        "authentication": "Existing Codex auth file referenced locally; no credentials in evidence",
        "cli_version": subprocess.check_output([str(codex), "--version"], text=True).strip(),
        "cli_sha256": sha(codex), "adapter_sha256": sha(__file__), "command": command,
        "timeout_seconds": timeout, "status": "running"}
    write(record/"session.json", receipt)
    started = time.monotonic()
    process = None
    try:
        with (runtime/"stdout.jsonl").open("w") as out, (runtime/"stderr.txt").open("w") as err:
            process = subprocess.Popen(command, env=environment, cwd=workspace, stdin=subprocess.PIPE,
                stdout=out, stderr=err, text=True, start_new_session=True)
            receipt["pid"] = process.pid
            write(record/"session.json", receipt)
            process.stdin.write(prompt)
            process.stdin.close()
            while process.poll() is None:
                if time.monotonic()-started >= timeout:
                    receipt["status"] = "timed_out"
                    stop(process)
                    break
                if on_tick is not None:
                    on_tick(process, timeout-(time.monotonic()-started))
                time.sleep(.2)
            process.wait()
            if receipt["status"] == "running":
                receipt["status"] = "completed" if process.returncode == 0 else "failed"
    except BaseException:
        receipt["status"] = "interrupted"
        if process is not None:
            stop(process)
        raise
    finally:
        receipt.update(ended_at=now(), wall_seconds=time.monotonic()-started,
                       exit_code=process.returncode if process else None)
        events, malformed = [], 0
        raw = runtime/"stdout.jsonl"
        if raw.exists():
            for line in raw.read_text().splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue
                # Keep actions, outputs and public messages, never private reasoning.
                if event.get("item", {}).get("type") != "reasoning":
                    events.append(event)
        (record/"events.jsonl").write_text("".join(json.dumps(event)+"\n" for event in events))
        receipt["malformed_event_lines"] = malformed
        receipt["thread_ids"] = [event["thread_id"] for event in events if event.get("type")=="thread.started"]
        receipt["usage"] = [event["usage"] for event in events if "usage" in event]
        receipt["model_observations"] = observations(runtime)
        receipt["settings_unchanged"] = sha(runtime/"config.toml") == receipt["runtime_config_sha256"]
        receipt["events_sha256"] = sha(record/"events.jsonl")
        if (runtime/"final.txt").exists():
            (record/"final.txt").write_bytes((runtime/"final.txt").read_bytes())
        write(record/"session.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    for name in ("workspace", "record", "runtime", "prompt", "config", "auth", "codex"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--blocked", type=Path, action="append", default=[])
    parser.add_argument("--readonly", type=Path, action="append", default=[])
    args = vars(parser.parse_args())
    args["prompt"] = args["prompt"].read_text()
    result = capture(**args)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
