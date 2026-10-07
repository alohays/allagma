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
import subprocess
import sys
import time
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from allagma.resources import _family, _stop, process_table, storage_bytes

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
        # Permit ancestor metadata lookup needed by realpath()/CLI startup.
        # Contents and directory enumeration remain unavailable outside roots.
        lines.append(f"(deny file-read-data file-write* {predicate})")
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


def permission_config(workspace, runtime, blocked, readonly):
    filesystem = {":root": "deny", ":minimal": "read", ":tmpdir": "write", ":slash_tmp": "deny",
        "/Library/Frameworks/Python.framework": "read", "/usr/local/bin": "read",
        "/Applications/ChatGPT.app": "read"}
    filesystem.update({str(Path(path).resolve()): "deny" for path in blocked})
    filesystem[str(runtime)] = "deny"
    filesystem[str(workspace)] = "write"
    filesystem.update({str(Path(path).resolve()): "read" for path in readonly})
    return {"allagma-eval": {"extends": ":workspace", "filesystem": filesystem,
                            "network": {"enabled": False}}}


def config_text(controlled, disabled_skills):
    lines = [f"{key} = {json.dumps(value)}" for key, value in controlled.items() if key not in ("permissions","features")]
    if "features" in controlled:
        lines += ["\n[features]"]+[f"{key} = {str(value).lower()}" for key,value in controlled["features"].items()]
    for name, value in controlled["permissions"].items():
        lines += [f"\n[permissions.{name}]", f"extends = {json.dumps(value['extends'])}",
                  f"\n[permissions.{name}.filesystem]"]
        lines += [f"{json.dumps(key)} = {json.dumps(access)}" for key, access in value["filesystem"].items()]
        lines += [f"\n[permissions.{name}.network]", "enabled = false"]
    for path in disabled_skills:
        lines += ["\n[[skills.config]]", f"path = {json.dumps(str(path))}", "enabled = false"]
    return "\n".join(lines)+"\n"


def stop(process, known):
    _stop(process, known, .5)


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
            config, auth, blocked=(), readonly=(), on_tick=None,
            rss_limit_bytes=8589934592, storage_limit_bytes=6442450944):
    if not 0 < timeout <= 7200:
        raise ValueError("Native session deadline must be finite and at most two hours")
    if any(type(value) is not int or value <= 0 for value in (rss_limit_bytes, storage_limit_bytes)):
        raise ValueError("Native RSS and storage ceilings must be finite positive integers")
    workspace, record, runtime = (Path(p).resolve() for p in (workspace, record, runtime))
    if not workspace.is_dir() or record.exists() or runtime.exists():
        raise ValueError("Require existing workspace and new record/runtime directories")
    for left, right in ((workspace, record), (workspace, runtime), (record, runtime)):
        if left == right or left in right.parents or right in left.parents:
            raise ValueError("Workspace, runtime and evidence directories must be separate, non-overlapping roots")
    if os.uname().sysname != "Darwin":
        raise ValueError("This isolation adapter currently qualifies macOS only")
    config, auth = Path(config).resolve(), Path(auth).resolve()
    settings = selected_settings(config)
    if not auth.is_file():
        raise ValueError("Existing Codex auth file unavailable; do not provision a new account")
    record.mkdir(parents=True)
    (record/"adapter.py").write_bytes(Path(__file__).read_bytes())
    runtime.mkdir(parents=True, mode=0o700)
    (runtime/".gitignore").write_text("*\n")
    (workspace/".tmp").mkdir(exist_ok=True)
    (runtime/"auth.json").symlink_to(auth)
    # The temporary runtime is a CODEX_HOME, not a project .codex configuration.
    # Personal tools, global instructions and saved chat histories are excluded.
    controlled = {**settings, "web_search": "disabled", "project_doc_max_bytes": 0,
        "features": {"multi_agent": False, "multi_agent_v2": False},
        "default_permissions": "allagma-eval",
        "permissions": permission_config(workspace, runtime, blocked, readonly)}
    disabled = sorted({str(path) for root in (Path.home()/".agents/skills", config.parent/"skills")
                       for path in root.rglob("SKILL.md")})
    disabled += [str(runtime/"skills/.system"/name/"SKILL.md") for name in
                 ("skill-creator", "skill-installer", "openai-docs", "imagegen")]
    (runtime/"config.toml").write_text(config_text(controlled, disabled))
    (record/"runtime-config.toml").write_bytes((runtime/"config.toml").read_bytes())
    (record/"prompt.txt").write_text(prompt)
    command = [str(codex), "--strict-config", "--no-daemon", "-a", "never",
               "exec", "--ignore-rules", "--skip-git-repo-check",
               "--json", "-C", str(workspace), "-o", str(runtime/"final.txt"), "-"]
    environment = {key: value for key, value in os.environ.items() if key in
                   ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "SHELL", "TERM", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")}
    environment["CODEX_HOME"] = str(runtime)
    environment["TMPDIR"] = str(workspace/".tmp")
    receipt = {"started_at": now(), "workspace": str(workspace), "runtime": str(runtime),
        "fresh_session": True, "resume": False, "prompt_sha256": sha(record/"prompt.txt"),
        "settings": settings, "controlled_settings": controlled,
        "disabled_skill_count": len(disabled), "isolation": "Native allagma-eval permission profile; tool reads restricted, command network disabled",
        "settings_source": str(config), "project_model_config_written": False,
        "runtime_config_sha256": sha(runtime/"config.toml"),
        "authentication": "Existing Codex auth file referenced locally; no credentials in evidence",
        "cli_version": subprocess.check_output([str(codex), "--version"], text=True).strip(),
        "cli_sha256": sha(codex), "adapter_sha256": sha(__file__), "command": command,
        "timeout_seconds": timeout, "rss_limit_bytes": rss_limit_bytes,
        "storage_limit_bytes": storage_limit_bytes, "status": "running"}
    write(record/"session.json", receipt)
    started = time.monotonic()
    process = None
    known = {}
    peak_rss, peak_storage, next_storage_check = 0, 0, 0.
    try:
        with (runtime/"stdout.jsonl").open("w") as out, (runtime/"stderr.txt").open("w") as err:
            process = subprocess.Popen(command, env=environment, cwd=workspace, stdin=subprocess.PIPE,
                stdout=out, stderr=err, text=True, start_new_session=True)
            receipt["pid"] = process.pid
            write(record/"session.json", receipt)
            process.stdin.write(prompt)
            process.stdin.close()
            while process.poll() is None:
                table = process_table()
                known = _family(table, process.pid, known)
                peak_rss = max(peak_rss, sum(table[pid]["rss"] for pid in known))
                if time.monotonic() >= next_storage_check:
                    peak_storage = max(peak_storage, storage_bytes(workspace)+storage_bytes(runtime))
                    next_storage_check = time.monotonic()+1
                if peak_rss > rss_limit_bytes or peak_storage > storage_limit_bytes:
                    receipt["status"] = "memory_exceeded" if peak_rss > rss_limit_bytes else "storage_exceeded"
                    stop(process, known)
                    break
                if time.monotonic()-started >= timeout:
                    receipt["status"] = "timed_out"
                    stop(process, known)
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
            stop(process, known)
        raise
    finally:
        receipt.update(ended_at=now(), wall_seconds=time.monotonic()-started,
                       exit_code=process.returncode if process else None,
                       peak_rss_bytes=peak_rss, peak_storage_bytes=peak_storage)
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
        after = tomllib.loads((runtime/"config.toml").read_text())
        before = tomllib.loads((record/"runtime-config.toml").read_text())
        receipt["settings_unchanged"] = {k: v for k, v in after.items() if k != "projects"} == before
        receipt["runtime_config_after_sha256"] = sha(runtime/"config.toml")
        receipt["runtime_project_trust_entries"] = after.get("projects", {})
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
    print(json.dumps({key: result[key] for key in
        ("status", "wall_seconds", "exit_code", "thread_ids", "usage", "model_observations", "settings_unchanged")}, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
