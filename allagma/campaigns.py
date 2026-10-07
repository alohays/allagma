"""Frozen campaigns and append-only local experiment attempts.

Scientific runner, evaluator, analyzer and writer programs belong to the study.
This module only enforces their file handoffs, identity and resource policy.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from .bundles import bundle_path, resolve_entry, verify_lock, verify_study
from .contracts import validate_record
from .files import (AllagmaError, canonical, confined, digest, file_hash, read_json,
                    reference, publication_reference, staged_directory, study_mutex, utcnow, verify_reference, write_bytes,
                    write_json, write_text)


def record(path, data):
    validate_record(data)
    write_json(path, data, immutable=True)
    return data


def campaign_path(study, campaign):
    if not campaign or "/" in campaign or "\\" in campaign:
        raise AllagmaError("Campaign ID must be a single path component")
    return confined(study, f"campaigns/{campaign}")


def _state(directory, *, phase=None, status=None, assurance=None, reason=None):
    path = directory / "state.json"
    state = read_json(path) if path.exists() else {"phase": "protocol", "execution_status": "ready", "assurance": "unreviewed", "stop_reason": None}
    if phase is not None:
        state["phase"] = phase
    if status is not None:
        state["execution_status"] = status
    if assurance is not None:
        state["assurance"] = assurance
    state["stop_reason"] = reason
    write_json(directory / "events" / f"{time.time_ns()}-{uuid.uuid4().hex[:6]}.json",
               {"at": utcnow(), **state}, immutable=True)
    write_json(path, state)
    return state


def _load(study, campaign):
    directory = campaign_path(study, campaign)
    lock = verify_lock(study, read_json(directory / "lock.yaml"))
    spec = read_json(directory / "study.json")
    validate_record(spec)
    for name in ("lock", "protocol"):
        path = directory / ("lock.yaml" if name == "lock" else "protocol.json")
        if verify_reference(study, spec[name]) != path:
            raise AllagmaError(f"StudySpec {name} does not reference its own campaign")
    protocol = read_json(directory / "protocol.json")
    brief = read_json(directory / "brief.json")
    for key in ("release", "bundle_id", "capabilities", "effective_configuration", "configuration_origins", "profile_provenance"):
        if spec[key] != lock[key]:
            raise AllagmaError(f"StudySpec disagrees with the frozen lock: {key}")
    for key in ("study_id", "question", "motivation", "success_criteria", "constraints", "output", "stop_rules"):
        if spec[key] != brief[key]:
            raise AllagmaError(f"StudySpec disagrees with the frozen brief: {key}")
    if spec["resources"] != lock["effective_configuration"]["budget"] or spec["protocol_revision"] != protocol["revision"]:
        raise AllagmaError("StudySpec resource policy or protocol revision differs")
    if "amendment" in protocol:
        amendment = read_json(directory / "amendment.json")
        verify_reference(study, amendment["prior_protocol"])
        if any(amendment[key] != value for key, value in protocol["amendment"].items()):
            raise AllagmaError("Amendment receipt disagrees with the frozen protocol")
    return directory, lock, protocol


def _amendment(study, campaign, protocol):
    previous = {path.parent.name: path for path in (study / "campaigns").glob("*/protocol.json")}
    prior = {name: read_json(path) for name, path in previous.items()}
    if any(value["revision"] == protocol["revision"] and value != protocol for value in prior.values()):
        raise AllagmaError("Changed protocol content requires a new protocol revision")
    change = protocol.get("amendment")
    if change is None:
        if prior and protocol not in prior.values():
            raise AllagmaError("Changed protocol requires amendment: from_campaign, reason and affected_runs")
        return None
    if not isinstance(change, dict) or set(change) != {"from_campaign", "reason", "affected_runs"}:
        raise AllagmaError("Amendment requires from_campaign, reason and affected_runs")
    parent = change["from_campaign"]
    affected = change["affected_runs"]
    if parent not in prior or parent == campaign or not isinstance(change["reason"], str) or not change["reason"].strip():
        raise AllagmaError("Amendment requires an existing parent campaign and a nonempty reason")
    known = {run["id"] for run in prior[parent]["runs"]}
    if not isinstance(affected, list) or any(not isinstance(run, str) for run in affected) or len(set(affected)) != len(affected) or not set(affected) <= known:
        raise AllagmaError("Amendment affected_runs must identify unique runs from the parent campaign")
    if protocol["revision"] == prior[parent]["revision"]:
        raise AllagmaError("Amendment requires a new protocol revision")
    return {**change, "from_revision": prior[parent]["revision"], "to_revision": protocol["revision"],
            "prior_protocol": reference(study, previous[parent])}


def start_campaign(study, campaign):
    study = Path(study).resolve()
    with study_mutex(study):
        lock = verify_study(study)
        directory = campaign_path(study, campaign)
        if directory.exists():
            raise AllagmaError("Campaign already exists; resume it instead")
        protocol = read_json(study / "protocol.json")
        brief = read_json(study / "brief.json")
        minimum = protocol.get("minimum_confirmation_runs", 1)
        if type(minimum) is not int or minimum < 1:
            raise AllagmaError("minimum_confirmation_runs must be a positive integer chosen by the study")
        if type(protocol.get("paired_seeds", False)) is not bool:
            raise AllagmaError("paired_seeds must be boolean")
        plan = protocol["runs"]
        if not plan or len({run["id"] for run in plan}) != len(plan):
            raise AllagmaError("Protocol needs a finite plan with unique run IDs")
        seeds = {split: {run["input"]["seed"] for run in plan if run["split"] == split}
                 for split in ("pilot", "confirmation", "discovery")}
        if seeds["confirmation"] & (seeds["pilot"] | seeds["discovery"]):
            raise AllagmaError("Pilot/discovery seeds cannot be reused as untouched confirmation")
        if not any(run["split"] == "pilot" for run in plan):
            raise AllagmaError("The local computational recipe requires known-answer pilot qualification")
        for run in plan:
            if "/" in run["id"] or not run["id"] or run["split"] not in seeds:
                raise AllagmaError("Invalid run ID or data split")
            if not isinstance(run["input"]["seed"], int) or isinstance(run["input"]["seed"], bool):
                raise AllagmaError("The local adapter requires explicit integer seeds")
            confined(study, f"campaigns/{campaign}/runs/{run['id']}")
        for split in seeds:
            if sum(run["split"] == split for run in plan) != len(seeds[split]):
                if not protocol.get("paired_seeds", False):
                    raise AllagmaError(f"Duplicate seeds in {split}; declare paired_seeds and distinct condition_id values for paired conditions")
                for seed in seeds[split]:
                    group = [run for run in plan if run["split"] == split and run["input"]["seed"] == seed]
                    if len(group) > 1:
                        conditions = [run.get("condition_id") for run in group]
                        if any(not isinstance(value,str) or not value.strip() for value in conditions) or len(set(conditions)) != len(conditions):
                            raise AllagmaError("Paired runs sharing a seed need distinct nonempty condition_id values")
        if "execution.local" not in lock["capabilities"]:
            raise AllagmaError("Local execution capability is missing")
        for role in ("runner", "evaluator", "analyzer", "writer"):
            if protocol[role] not in protocol["code"]:
                raise AllagmaError(f"{role} must be included in the frozen code manifest")
        amendment = _amendment(study, campaign, protocol)
        with staged_directory(study, directory) as staging:
            return _prepare_campaign(study, lock, protocol, brief, staging, directory, amendment)


def _prepare_campaign(study, lock, protocol, brief, directory, target, amendment):
    plan = protocol["runs"]

    def ref(path, media_type=None):
        return publication_reference(study, path, directory, target, media_type)

    write_json(directory / "lock.yaml", lock, immutable=True)
    write_json(directory / "protocol.json", protocol, immutable=True)
    write_json(directory / "brief.json", brief, immutable=True)
    if amendment is not None:
        write_json(directory / "amendment.json", amendment, immutable=True)
    for path in protocol["code"]:
        write_bytes(confined(directory, f"materials/{path}"), confined(study, path).read_bytes(), immutable=True)
    effective = lock["effective_configuration"]
    spec = {"schema_version": "0.2", "record_type": "StudySpec", "study_id": brief["study_id"],
            **{key: brief[key] for key in ("question", "motivation", "success_criteria", "constraints", "output", "stop_rules")},
            "resources": effective["budget"], "capabilities": lock["capabilities"],
            "release": lock["release"], "bundle_id": lock["bundle_id"],
            "lock": ref(directory / "lock.yaml"),
            "profile_provenance": lock["profile_provenance"],
            "effective_configuration": effective, "configuration_origins": lock["configuration_origins"],
            "protocol_revision": protocol["revision"], "protocol": ref(directory / "protocol.json")}
    record(directory / "study.json", spec)
    code_refs = {key: ref(directory / "materials" / protocol[key], "text/x-python")
                 for key in ("runner", "evaluator", "analyzer", "writer")}
    write_json(directory / "code-manifest.json", {path: ref(directory / "materials" / path) for path in protocol["code"]}, immutable=True)
    for run in plan:
        rdir = directory / "runs" / run["id"]
        write_json(rdir / "parameters.json", run["input"], immutable=True)
        experiment = {"schema_version": "0.2", "record_type": "ExperimentSpec", "experiment_id": run["id"],
                      "hypothesis": protocol["hypothesis"], "inputs": [ref(rdir / "parameters.json")],
                      "runner": code_refs["runner"], "evaluator": code_refs["evaluator"],
                      "seed_policy": {"seed": run["input"]["seed"], "split": run["split"], "disjoint_confirmation": True},
                      "budget": effective["budget"], "expected_artifacts": ["raw.json", "evaluation.json"],
                      "editable": ["fault injection for conformance, excluded from successful science"],
                      "fixed": ["runner", "evaluator", "seed", "parameters", "protocol", "analysis"],
                      "protocol_revision": protocol["revision"], "split": run["split"], "parameters": run["input"]}
        record(rdir / "spec.json", experiment)
    write_json(directory / "experiment-manifest.json",
               {run["id"]: ref(directory / "runs" / run["id"] / "spec.json") for run in plan}, immutable=True)
    _state(directory)
    return spec


def _attempts(directory):
    return [validate_record(read_json(path)) for path in sorted(directory.glob("runs/*/attempts/*/record.json"))]


def _check_materials(study, directory):
    protocol = read_json(directory / "protocol.json")
    code = read_json(directory / "code-manifest.json")
    if set(code) != set(protocol["code"]):
        raise AllagmaError("Frozen code manifest does not cover the protocol's complete material inventory")
    for name, item in code.items():
        if item["path"] != (directory / "materials" / name).relative_to(study).as_posix():
            raise AllagmaError("Frozen code manifest points outside its declared material path")
        verify_reference(study, item)
    experiments = read_json(directory / "experiment-manifest.json")
    if set(experiments) != {run["id"] for run in protocol["runs"]}:
        raise AllagmaError("Experiment manifest does not cover the frozen run plan")
    for name, item in experiments.items():
        if item["path"] != (directory / "runs" / name / "spec.json").relative_to(study).as_posix():
            raise AllagmaError("Experiment manifest points outside its declared run")
        verify_reference(study, item)


def _attempt_outputs(study, directory):
    outputs = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name in ("started.json", "record.json", "input.json"):
            continue
        media_type = None
        if path.suffix == ".json":
            try:
                read_json(path)
            except AllagmaError:
                media_type = "application/octet-stream"
        outputs.append(reference(study, path, media_type))
    return outputs


def _recover_attempts(study, directory):
    for path in sorted(directory.glob("runs/*/attempts/*/started.json")):
        if (path.parent / "record.json").exists():
            continue
        started = read_json(path)
        validate_record(started)
        charged_seconds = 0.0
        for job_path in path.parent.glob("*.job.json"):
            job = read_json(job_path)
            result_path = path.parent / Path(job["result"]).name
            if result_path.exists():
                charged_seconds += read_json(result_path)["wall_seconds"]
            elif time.time() < job["deadline_epoch"]:
                raise AllagmaError("An interrupted controller still has a bounded worker in flight; resume after its recorded deadline")
            else:
                # The worker deadline is an upper-bound charge, not a fabricated
                # observation of CPU time. Never use uncertain output as success.
                charged_seconds += job["timeout"] + 2
        # Never infer success from a leftover output after a controller crash.
        terminal = {**started, "ended_at": utcnow(), "status": "interrupted",
                    "error": {"kind": "controller_interruption", "message": "No terminal record was committed; preserved for inspection"},
                    "usage": {"wall_seconds": charged_seconds, "money_usd": 0.0, "tokens": 0},
                    "environment": {**started["environment"], "recovered_usage_basis": "worker measurement when available; deadline upper bound otherwise; zero before launch"},
                    "outputs": _attempt_outputs(study, path.parent)}
        record(path.parent / "record.json", terminal)


def _stop(directory, status, reason):
    state = _state(directory, status=status, reason=reason)
    write_text(directory / "reports" / f"partial-{time.time_ns()}.md",
               f"# Partial research package\n\nExecution status: {status}.\n\n{reason}\n\n"
               "All earlier attempts remain available. A partial package does not establish the research hypothesis.\n", immutable=True)
    return state


def _terminate(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)


def _execute(command, cwd, stdout, stderr, timeout, *, interrupt=False):
    job_path = stdout.with_suffix(".job.json")
    result_path = stdout.with_suffix(".job-result.json")
    job = {"command": command, "cwd": str(cwd), "stdout": str(stdout), "stderr": str(stderr),
           "timeout": timeout, "interrupt": interrupt, "result": str(result_path),
           "deadline_epoch": time.time() + timeout + 3}
    write_json(job_path, job, immutable=True)
    with stdout.with_suffix(".worker-stdout.txt").open("xb") as worker_out, stdout.with_suffix(".worker-stderr.txt").open("xb") as worker_err:
        process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("worker.py")), str(job_path)],
                                   cwd=cwd, stdout=worker_out, stderr=worker_err, start_new_session=True)
    try:
        process.wait(timeout=timeout + 3)
    except subprocess.TimeoutExpired:
        _terminate(process)
    finally:
        _terminate(process)
    if not result_path.exists():
        raise AllagmaError("Bounded worker did not commit a result; preserve this attempt for recovery")
    result = read_json(result_path)
    if result.get("stop") in ("checkpoint_missing", "worker_error"):
        raise AllagmaError(f"Worker failed: {result}")
    return result["exit_code"], result["stop"]


def run_campaign(study, campaign, *, fault=None, stop_after=None, crash_after_start=False):
    study = Path(study).resolve()
    with study_mutex(study):
        directory, lock, protocol = _load(study, campaign)
        _check_materials(study, directory)
        _recover_attempts(study, directory)
        previous_state = read_json(directory / "state.json")
        budget = lock["effective_configuration"]["budget"]
        unset = [key for key in ("max_attempts", "max_seconds", "money_usd") if budget[key] == "unset"]
        if unset:
            return _stop(directory, "blocked", "Execution requires explicit resource ceilings: " + ", ".join(unset) + ". Set the study budget and start a new frozen campaign.")
        completed_this_call = 0
        for run in protocol["runs"]:
            rdir = directory / "runs" / run["id"]
            spec = read_json(rdir / "spec.json")
            validate_record(spec)
            if spec["parameters"] != run["input"] or spec["protocol_revision"] != protocol["revision"]:
                raise AllagmaError("Experiment parameters disagree with the frozen protocol")
            for item in [*spec["inputs"], spec["runner"], spec["evaluator"]]:
                verify_reference(study, item)
            prior = [read_json(path) for path in sorted(rdir.glob("attempts/*/record.json"))]
            successes = [item for item in prior if item["status"] == "succeeded"]
            if successes:
                for item in successes:
                    validate_record(item)
                    for ref in [*item["inputs"], *item["outputs"]]:
                        verify_reference(study, ref)
                continue
            attempts = _attempts(directory)
            elapsed = sum(item["usage"]["wall_seconds"] for item in attempts)
            if budget["max_attempts"] != "unset" and len(attempts) >= budget["max_attempts"]:
                return _stop(directory, "budget_exhausted", "Campaign attempt ceiling reached before the next launch.")
            if budget["max_seconds"] != "unset" and elapsed >= budget["max_seconds"]:
                return _stop(directory, "budget_exhausted", "Campaign execution-time ceiling reached before the next launch.")
            if sum(item["status"] == "failed" for item in prior) >= protocol.get("max_failures_per_run", 2):
                return _stop(directory, "failed", f"Repeated failure stop for {run['id']}.")
            if stop_after is not None and completed_this_call >= stop_after:
                return _stop(directory, "paused", "Requested checkpoint reached; resume uses the same lock.")
            if run["split"] == "confirmation":
                pilots = [item for item in attempts if item["split"] == "pilot" and item["status"] == "succeeded"]
                expected_pilots = sum(item["split"] == "pilot" for item in protocol["runs"])
                if len(pilots) != expected_pilots:
                    return _stop(directory, "failed", "Known-answer pilot qualification is incomplete.")
            phase = "pilot" if run["split"] == "pilot" else "campaign"
            _state(directory, phase=phase, status="running", assurance="unreviewed")
            number = len(prior) + 1
            attempt_id = f"{run['id']}-a{number:03d}"
            adir = rdir / "attempts" / f"{number:03d}"
            inputs = deepcopy(run["input"])
            mode = fault["mode"] if fault and fault["run_id"] == run["id"] else None
            if mode:
                inputs["fault"] = mode
            runner = verify_reference(study, spec["runner"])
            evaluator = verify_reference(study, spec["evaluator"])
            command = [sys.executable, str(runner), str(adir / "input.json"), str(adir / "raw.json")]
            started = {"schema_version": "0.2", "record_type": "RunRecord", "run_id": run["id"],
                       "attempt_id": attempt_id, "attempt_number": number, "campaign_id": campaign,
                       "experiment_id": run["id"], "started_at": utcnow(), "ended_at": None,
                       "inputs": [reference(study, rdir / "spec.json"), spec["runner"], spec["evaluator"]],
                       "outputs": [], "environment": {"python": platform.python_version(), "platform": platform.platform(), "executable": sys.executable,
                                                         "isolation": "local process; not an OS security sandbox"},
                       "model_revision": None, "data_revision": digest(run["input"]),
                       "usage": {"wall_seconds": 0.0, "money_usd": 0.0, "tokens": 0},
                       "status": "running", "error": None, "protocol_revision": protocol["revision"],
                       "bundle_id": lock["bundle_id"], "split": run["split"], "command": command, "exit_code": None}
            with staged_directory(study, adir) as staging:
                write_json(staging / "input.json", inputs, immutable=True)
                started["inputs"].insert(0, publication_reference(study, staging / "input.json", staging, adir))
                record(staging / "started.json", started)
            if crash_after_start:
                # Test-only deterministic controller crash before a child is launched.
                os._exit(86)
            begin = time.monotonic()
            timeout = budget["per_attempt_seconds"]
            if budget["max_seconds"] != "unset":
                timeout = min(timeout, max(0.001, budget["max_seconds"] - elapsed))
            error, outputs, status, exit_code = None, [], "failed", None
            try:
                exit_code, interrupted = _execute(command, adir, adir / "stdout.txt", adir / "stderr.txt", timeout, interrupt=mode == "interrupt")
                if interrupted:
                    status = "interrupted" if interrupted == "interrupted" else "failed"
                    error = {"kind": interrupted, "message": "Process terminated; this attempt is not scientific evidence"}
                elif exit_code != 0:
                    error = {"kind": "runner_exit", "message": f"Runner exited {exit_code}; see stderr.txt"}
                elif not (adir / "raw.json").is_file():
                    error = {"kind": "missing_artifact", "message": "Runner did not produce raw.json"}
                else:
                    remaining = max(0.001, timeout - (time.monotonic() - begin))
                    eval_command = [sys.executable, str(evaluator), str(adir / "input.json"), str(adir / "raw.json"), str(adir / "evaluation.json")]
                    write_json(adir / "evaluator-command.json", eval_command, immutable=True)
                    evaluation_exit, eval_stop = _execute(eval_command, adir, adir / "evaluator-stdout.txt", adir / "evaluator-stderr.txt", remaining)
                    if evaluation_exit != 0 or eval_stop:
                        error = {"kind": "evaluator_failure", "message": "Evaluator failed or exceeded the attempt time ceiling"}
                    else:
                        evaluation = read_json(adir / "evaluation.json")
                        if evaluation.get("valid") is not True:
                            error = {"kind": "qualification_failure", "message": "Study evaluator rejected the output"}
                        else:
                            status = "succeeded"
                            outputs = [reference(study, adir / name) for name in ("raw.json", "evaluation.json")]
            except KeyboardInterrupt:
                status, error = "interrupted", {"kind": "user_interruption", "message": "Interrupted by the user"}
            except (AllagmaError, OSError, ValueError) as exc:
                error = {"kind": "adapter_error", "message": str(exc)}
            terminal = {**started, "ended_at": utcnow(), "status": status, "error": error,
                        "outputs": outputs, "exit_code": exit_code,
                        "usage": {"wall_seconds": time.monotonic() - begin, "money_usd": 0.0, "tokens": 0}}
            # Logs are evidence for both successes and failures, and are never overwritten.
            terminal["outputs"] = _attempt_outputs(study, adir)
            record(adir / "record.json", terminal)
            completed_this_call += 1
            if status != "succeeded":
                return _stop(directory, "paused" if status == "interrupted" else "failed", f"{attempt_id}: {error['message']}")
        if completed_this_call == 0 and previous_state["execution_status"] == "completed":
            return previous_state
        return _state(directory, phase="analysis", status="ready", reason="Declared run plan complete")


def _run_helper(command, cwd, timeout=30, *, check=True):
    with tempfile.TemporaryDirectory(prefix="allagma-helper-") as temp:
        output = Path(temp)
        code, stop = _execute(command, cwd, output / "stdout.txt", output / "stderr.txt", timeout)
        stdout = (output / "stdout.txt").read_text()
        stderr = (output / "stderr.txt").read_text()
        if check and stop:
            raise AllagmaError(f"Study helper exceeded {timeout}s or was interrupted: {stop}")
        if check and code:
            raise AllagmaError(f"Study helper failed ({code}): {stderr[-2000:]}")
        return {"command": command, "exit_code": code, "stdout": stdout, "stderr": stderr, "stop": stop}


def analyze_campaign(study, campaign, *, analysis_id="a001", allow_partial=False):
    study = Path(study).resolve()
    with study_mutex(study):
        directory, lock, protocol = _load(study, campaign)
        _check_materials(study, directory)
        _recover_attempts(study, directory)
        attempts = _attempts(directory)
        successes = {item["run_id"]: item for item in attempts if item["status"] == "succeeded"}
        if len(successes) != len(protocol["runs"]) and not allow_partial:
            raise AllagmaError("Run plan is incomplete; explicitly request partial analysis")
        adir = confined(directory, f"analyses/{analysis_id}")
        if adir.exists():
            raise AllagmaError("Analysis ID exists; choose a new ID to preserve the prior analysis")
        manifest = {"schema_version": "0.2", "campaign_id": campaign, "protocol_revision": protocol["revision"], "raw": [], "runs": [], "exclusions": []}
        for item in attempts:
            validate_record(item)
            for ref in [*item["inputs"], *item["outputs"]]:
                verify_reference(study, ref)
            path = directory / "runs" / item["run_id"] / "attempts" / f"{item['attempt_number']:03d}" / "record.json"
            manifest["runs"].append(reference(study, path))
            if item["status"] == "succeeded" and item["split"] == "confirmation":
                manifest["raw"].append(next(ref for ref in item["outputs"] if ref["path"].endswith("/raw.json")))
            else:
                manifest["exclusions"].append({"attempt_id": item["attempt_id"], "reason": item["status"] if item["status"] != "succeeded" else "pilot data excluded from confirmation"})
        minimum = protocol.get("minimum_confirmation_runs", 1)
        if type(minimum) is not int or minimum < 1:
            raise AllagmaError("Invalid frozen minimum_confirmation_runs")
        if len(manifest["raw"]) < minimum:
            raise AllagmaError(f"Study protocol requires at least {minimum} eligible confirmation runs")
        adir.mkdir(parents=True)
        write_json(adir / "raw-manifest.json", manifest, immutable=True)
        analyzer = directory / "materials" / protocol["analyzer"]
        outputs = adir / "outputs"
        trace = _run_helper([sys.executable, str(analyzer), str(study), str(adir / "raw-manifest.json"), str(outputs)], study)
        write_json(adir / "execution.json", trace, immutable=True)
        output_refs = [reference(study, path) for path in sorted(outputs.iterdir()) if path.is_file()]
        if not output_refs:
            raise AllagmaError("Analyzer produced no outputs")
        analysis = {"schema_version": "0.2", "record_type": "AnalysisRecord", "analysis_id": analysis_id,
                    "raw_manifest": reference(study, adir / "raw-manifest.json"),
                    "analysis_revision": file_hash(analyzer), "code": reference(study, analyzer, "text/x-python"),
                    "configuration": {"protocol_revision": protocol["revision"], "partial": len(successes) != len(protocol["runs"]),
                                      "minimum_confirmation_runs": minimum},
                    "outputs": output_refs, "exclusions": manifest["exclusions"], "uncertainty": protocol["uncertainty"],
                    "dependencies": [reference(study, directory / "protocol.json"), *manifest["runs"], *manifest["raw"]]}
        if (directory / "amendment.json").exists():
            analysis["dependencies"].append(reference(study, directory / "amendment.json"))
        record(adir / "record.json", analysis)
        # The writer is study-owned: framework code does not invent scientific claims.
        writer = directory / "materials" / protocol["writer"]
        paper = adir / "paper"
        trace = _run_helper([sys.executable, str(writer), str(study), str(adir / "record.json"), str(paper)], study)
        write_json(adir / "writing-execution.json", trace, immutable=True)
        claims = read_json(paper / "claims.json")
        if not isinstance(claims, list) or not claims or not (paper / "manuscript.md").is_file():
            raise AllagmaError("Writer must produce claims.json and manuscript.md")
        for claim in claims:
            validate_record(claim)
        write_json(directory / "latest-analysis.json", {"id": analysis_id})
        _state(directory, phase="audit", status="ready", assurance="unreviewed")
        return analysis


def _references(value):
    if isinstance(value, dict):
        if {"path", "sha256", "media_type", "retention"} <= value.keys():
            yield value
        else:
            for item in value.values():
                yield from _references(item)
    elif isinstance(value, list):
        for item in value:
            yield from _references(item)


def audit_evidence(study, value, seen=None):
    seen = set() if seen is None else seen
    for ref in _references(value):
        path = verify_reference(study, ref)
        identity = (ref["path"], ref["sha256"])
        if identity in seen:
            continue
        seen.add(identity)
        if ref["media_type"] == "application/json":
            child = read_json(path)
            if isinstance(child, dict) and "record_type" in child:
                validate_record(child)
            audit_evidence(study, child, seen)
    return seen


def audit_campaign(study, campaign, *, analysis_id=None):
    study = Path(study).resolve()
    with study_mutex(study):
        directory, lock, protocol = _load(study, campaign)
        _recover_attempts(study, directory)
        analysis_id = analysis_id or read_json(directory / "latest-analysis.json")["id"]
        adir = confined(directory, f"analyses/{analysis_id}")
        analysis = read_json(adir / "record.json")
        claims = read_json(adir / "paper/claims.json")
        findings, stale, checked = [], [], set()
        for claim in claims:
            try:
                validate_record(claim)
                checked.update(audit_evidence(study, claim))
            except AllagmaError as exc:
                stale.append(claim["claim_id"])
                findings.append(str(exc))
        try:
            validate_record(analysis)
            checked.update(audit_evidence(study, analysis))
            _check_materials(study, directory)
            recipe = read_json(bundle_path(study, lock) / lock["modules"][lock["recipe"]]["path"] / "recipe.json")
            with tempfile.TemporaryDirectory(prefix="allagma-reproduce-") as temp:
                for repetition in range(recipe["analysis_repetitions"]):
                    output = Path(temp) / f"reanalysis-{repetition}"
                    _run_helper([sys.executable, str(directory / "materials" / protocol["analyzer"]), str(study), str(adir / "raw-manifest.json"), str(output)], study)
                    if {p.name for p in output.iterdir()} != {Path(ref["path"]).name for ref in analysis["outputs"]}:
                        raise AllagmaError("Reanalysis output inventory differs")
                    for ref in analysis["outputs"]:
                        if file_hash(output / Path(ref["path"]).name) != ref["sha256"]:
                            raise AllagmaError(f"Reanalysis differs: {ref['path']}")
                paper = Path(temp) / "paper"
                _run_helper([sys.executable, str(directory / "materials" / protocol["writer"]), str(study), str(adir / "record.json"), str(paper)], study)
                for name in ("claims.json", "manuscript.md"):
                    if (paper / name).read_bytes() != (adir / "paper" / name).read_bytes():
                        raise AllagmaError(f"Manuscript/claim reproduction differs: {name}")
        except AllagmaError as exc:
            findings.append(str(exc))
        number = 1
        while (adir / "reviews" / f"review-{number:03d}").exists():
            number += 1
        review_id = f"review-{number:03d}"
        rdir = adir / "reviews" / review_id
        material = reference(study, adir / "paper/manuscript.md", "text/markdown")
        payload = {"study": str(study), "material": material, "claims": claims}
        write_json(rdir / "input.json", payload, immutable=True)
        reviewer = lock["roles"]["reviewer"]
        adapter = bundle_path(study, lock) / lock["modules"][reviewer]["path"] / "review.py"
        trace = _run_helper([sys.executable, str(adapter), str(rdir / "input.json"), str(rdir / "adapter-result.json")], study)
        write_json(rdir / "execution.json", trace, immutable=True)
        adapter_result = read_json(rdir / "adapter-result.json")
        if adapter_result.get("verdict") not in ("pass", "revise", "blocked"):
            raise AllagmaError("Reviewer returned an invalid verdict")
        findings.extend(adapter_result["findings"])
        if adapter_result["verdict"] != "pass" and not adapter_result["findings"]:
            findings.append(f"Reviewer returned {adapter_result['verdict']} without supporting findings")
        verdict = "revise" if findings else "pass"
        review = {"schema_version": "0.2", "record_type": "ReviewRecord", "review_id": review_id,
                  "reviewer": reviewer, "backend": "local deterministic Python", "backend_version": platform.python_version(),
                  "material": material, "criteria": ["transitive evidence integrity", "raw-data recomputation", "manuscript and claim regeneration"],
                  "verdict": verdict, "findings": findings, "trace": [reference(study, rdir / name) for name in ("input.json", "adapter-result.json", "execution.json")],
                  "assurance": "deterministic", "coverage": adapter_result["coverage"] + " Plus raw-data recomputation and deterministic report regeneration."}
        record(rdir / "record.json", review)
        result = {"verdict": verdict, "stale_claims": stale, "checked_references": len(checked), "findings": findings,
                  "review": reference(study, rdir / "record.json"), "analysis_repetitions": recipe["analysis_repetitions"] if not findings else 0,
                  "limitations": ["No independent scientific peer review or real-model quality evaluation."]}
        write_json(rdir / "audit.json", result, immutable=True)
        write_json(directory / "latest-audit.json", result)
        partial = analysis["configuration"]["partial"]
        _state(directory, phase="audit", status="completed" if verdict == "pass" and not partial else "partial" if verdict == "pass" else "needs_revision",
               assurance="deterministic", reason="Partial analysis" if partial else None)
        return result
