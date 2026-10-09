"""Brief/material/resource preparation and explicit native research invocation.

This module copies inputs and composes existing adapters. It contains no
scientific runner, metric, protocol hypothesis or task-specific coordinator.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import shutil

from . import bundles, papers, references, resources
from .files import AllagmaError, canonical, file_hash, inventory, read_json, utcnow, write_json


def _separate(study, control):
    if study == control or study in control.parents or control in study.parents:
        raise AllagmaError("Study and controller directories must be separate non-overlapping roots")


def _copy_materials(source, destination):
    source=Path(source).resolve()
    if not source.is_dir():raise AllagmaError("Materials must be a directory of explicitly supplied files")
    destination.mkdir(parents=True,exist_ok=True)
    for path in _material_files(source):
        if path.is_symlink():raise AllagmaError("Material symlinks must be resolved explicitly before preparation")
        if path.is_file():
            if path.name in ("auth.json", ".env"):
                raise AllagmaError("Keep authentication and environment secrets outside research materials")
            target=destination/path.relative_to(source)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)


def _material_files(source):
    """Prune local raw caches instead of silently copying them as materials."""
    import os
    if (Path(source) / ".allagma-reference-cache.json").exists():
        raise AllagmaError("Use a reference manifest to select inputs; do not copy an entire raw cache as materials")
    for directory, dirs, files in os.walk(source, followlinks=False):
        parent = Path(directory)
        dirs[:] = [name for name in dirs if name not in (".git", ".venv", "__pycache__")
                   and not (parent / name / ".allagma-reference-cache.json").exists()]
        for name in dirs:
            if (parent / name).is_symlink():
                raise AllagmaError("Resolve material links before preparation")
        for name in files:
            yield parent / name


def prepare(source, study, control, *, brief, materials, profile, study_id="study", install_workflow=True,
            reference_directory=None, reference_cache=None, paper_configuration=None):
    source,study,control=(Path(p).resolve() for p in (source,study,control))
    _separate(study,control)
    resources.validate_profile(profile)
    if paper_configuration is not None:
        if paper_configuration.get("format") != papers.FORMAT or paper_configuration.get("output") not in ("report", "arxiv"):
            raise AllagmaError("Invalid requested paper output")
        if paper_configuration["output"] == "arxiv":
            papers.author_tex(paper_configuration)
    if not {"compute","setup"} <= profile["budgets_seconds"].keys():
        raise AllagmaError("Research preparation requires separate compute and setup budgets")
    if study.exists() and any(study.iterdir()):raise AllagmaError("Use a new or empty study directory")
    if control.exists():raise AllagmaError("Use a new controller directory")
    brief=Path(brief).resolve()
    if not brief.is_file() or not brief.read_text().strip():raise AllagmaError("A nonempty research brief is required")
    materials=Path(materials).resolve()
    if not materials.is_dir():raise AllagmaError("Materials must be an existing directory")
    if materials==study or materials in study.parents or materials==control or materials in control.parents:
        raise AllagmaError("Output directories cannot be inside the materials tree")
    material_bytes=0
    for path in _material_files(materials):
        if path.is_symlink() or path.name in ("auth.json", ".env"):
            raise AllagmaError("Resolve material links and remove credentials before preparation")
        if path.is_file():material_bytes+=path.stat().st_size
    acquisition = None
    retrieval = None
    reference_bytes = 0
    dossier_plan = None
    dossier_bytes = working_dossier_bytes = 0
    if reference_directory is not None:
        reference_directory = Path(reference_directory).resolve()
        dossier_plan = references.plan_snapshot(reference_directory)
        working_dossier_bytes = sum(dossier_plan["sizes"].values()) if install_workflow else 0
        dossier_bytes = dossier_plan["size_bytes"] + working_dossier_bytes
        if (reference_directory / "retrieval.json").exists():
            retrieval = read_json(reference_directory / "retrieval.json")
            if any(item["use"] == "execution" for item in retrieval["assets"]):
                if reference_cache is None:
                    raise AllagmaError("Selected reference execution assets require --reference-cache")
                acquisition = _load("allagma_prepare_acquisition", source / "adapters/reference-assets/acquire.py")
                reference_bytes = sum(item["size_bytes"] for item in acquisition.input_plan(reference_cache, retrieval).values())
    material_bytes += (reference_bytes + dossier_bytes + brief.stat().st_size +
        (source / "adapters/local-process/COMPUTE.md").stat().st_size +
        (source / "adapters/local-process/compute_client.py").stat().st_size +
        (2 * len(canonical(paper_configuration)) if paper_configuration is not None else 0))
    workflow_reserve = 1_000_000
    if material_bytes+workflow_reserve >= profile["storage_limit_bytes"]:
        raise AllagmaError("Materials leave insufficient space for the workflow within the storage ceiling")
    if profile["command_timeout_seconds"]["compute"] < .01 or profile["budgets_seconds"]["compute"] < .001:
        raise AllagmaError("Resource timings are below the campaign contract minimum")
    study.mkdir(parents=True,exist_ok=True)
    inputs=study/"inputs";inputs.mkdir()
    _copy_materials(materials,inputs/"materials")
    shutil.copyfile(brief,inputs/"BRIEF.md")
    shutil.copyfile(source/"adapters/local-process/COMPUTE.md",inputs/"COMPUTE.md")
    shutil.copyfile(source/"adapters/local-process/compute_client.py",inputs/"compute.py")
    if paper_configuration is not None:
        write_json(inputs / "PAPER.json", paper_configuration, immutable=True)
    reference_snapshot = None
    if reference_directory is not None:
        reference_snapshot = references.snapshot(reference_directory, inputs / "references", plan=dossier_plan,
            storage_limit=profile["storage_limit_bytes"] - resources.storage_bytes(study) -
                          reference_bytes - working_dossier_bytes - workflow_reserve)
    if acquisition is not None:
        selected = acquisition.materialize(reference_cache, retrieval, inputs / "reference-assets",
            storage_limit=profile["storage_limit_bytes"] - material_bytes + reference_bytes - workflow_reserve)
        write_json(inputs / "REFERENCE-INPUTS.json", selected, immutable=True)
    write_json(inputs/"RESOURCES.json", {"profile":profile,"network":False,
        "scientific_execution":"CPU or MPS through the local resource broker; isolated environment inside this study",
        "model_usage":"Accounted separately by the native adapter; existing Codex authentication only"},immutable=True)
    intent=bundles.default_intent(study_id);intent["hosts"]=["codex"]
    intent["request"]={"budget":{"max_attempts":profile["attempt_limit"],
        "max_seconds":profile["budgets_seconds"]["compute"],"money_usd":0,
        "per_attempt_seconds":profile["command_timeout_seconds"]["compute"]}}
    lock=bundles.initialize(source,study,study_id=study_id,intent=intent) if install_workflow else None
    if paper_configuration is not None:
        write_json(study / "paper.json", paper_configuration)
    if install_workflow and reference_snapshot:
        references.copy_snapshot_files(inputs / "references", study / "references", dossier_plan,
            storage_limit=profile["storage_limit_bytes"] - resources.storage_bytes(study), replace=True)
    readonly=[inputs]+([study/".allagma/bundles",study/".agents"] if install_workflow else [])
    control.mkdir(parents=True)
    resources.initialize(control/"resources",profile,study)
    prepared={"format":"allagma-research-workspace-v1","created_at":utcnow(),
        "study":str(study),"control":str(control),"study_id":study_id,
        "workflow_enabled":bool(install_workflow),
        "preparation_storage":{"planned_input_bytes":material_bytes,"dossier_copy_bytes":dossier_bytes,
                               "workflow_reserve_bytes":workflow_reserve},
        "lock_id":lock["lock_id"] if lock else None,"bundle_id":lock["bundle_id"] if lock else None,
        "common_inputs":inventory(inputs),"readonly":[str(p) for p in readonly]}
    write_json(control/"prepared.json",prepared,immutable=True)
    write_json(study/"research-workspace.json",prepared,immutable=True)
    if install_workflow:(study/"RESEARCH.md").write_text(
        "# Prepared research workspace\n\nRead `inputs/BRIEF.md`, the supplied `inputs/materials/`, "
        "`inputs/RESOURCES.json` and `inputs/COMPUTE.md`. The controller stores authoritative "
        "resource receipts outside this workspace. Read `ALLAGMA.md` and use the locked "
        "methods to plan, execute, recover, analyze, write and critically review the study. "
        "The study owns its scientific code and protocol. Never edit the generated bundle.\n\n"
        "Begin reference research with `references/INDEX.md`. Record primary papers, implementations, baselines, "
        "competing findings and coverage gaps before choosing the protocol. Consult the relevant notes during "
        "implementation, analysis, writing and every resumed session. Supplied reference snapshots in "
        "`inputs/references/` and selected `inputs/reference-assets/` are immutable; later reading belongs in "
        "the working dossier and a new revision. Scientific workers cannot acquire network inputs.\n\n"
        "Prepare and execute commands through the common local client. Keep setup separate "
        "from scientific computation. Preserve unsuccessful attempts, record uncertainty, "
        "and provide full reproduction and retained-data recomputation commands. "
        "Do not report a complete package until its evidence supports that status.\n")
    if resources.storage_bytes(study) >= profile["storage_limit_bytes"]:
        raise AllagmaError("Prepared workspace reaches its storage ceiling; retain this partial workspace and use a new revision")
    return prepared


def status(study, control):
    study,control=Path(study).resolve(),Path(control).resolve();_separate(study,control)
    prepared=read_json(control/"prepared.json")
    if prepared["study"]!=str(study) or prepared["control"]!=str(control):
        raise AllagmaError("Controller does not belong to this study")
    return {"prepared":prepared,"resources":resources.summary(control/"resources"),
            "sessions":[read_json(p) for p in sorted((control/"sessions").glob("*/native/session.json"))]}


def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def run(study, control, *, codex, timeout, session_id, config, auth, interrupt_first_attempt=False, prompt=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}",session_id):raise AllagmaError("Invalid research session ID")
    study,control=Path(study).resolve(),Path(control).resolve()
    prepared=status(study,control)["prepared"]
    workflow=prepared.get("workflow_enabled",True)
    lock=bundles.verify_study(study) if workflow else None
    if lock and lock["lock_id"]!=prepared["lock_id"]:
        raise AllagmaError("Prepared workflow lock changed; reconcile at a campaign boundary before new execution")
    if inventory(study/"inputs")!=prepared["common_inputs"]:
        raise AllagmaError("Prepared inputs changed; preserve the old study and prepare a new revision")
    root=bundles.bundle_path(study,lock) if lock else Path(__file__).resolve().parents[1]
    if lock:
        for name in ("allagma/resources.py","allagma/files.py"):
            if file_hash(Path(__file__).resolve().parents[1]/name)!=file_hash(root/name):
                raise AllagmaError("Controller helpers differ from the pinned workflow; invoke its tools/allagma.py directly")
    native=_load("allagma_research_native",root/"adapters/codex/session.py")
    local=_load("allagma_research_broker",root/"adapters/local-process/broker.py")
    broker=local.Broker(study,control/"resources",control/"broker",readonly=prepared["readonly"],
                       protected=[control],interrupt_first_attempt=interrupt_first_attempt)
    broker.recover()
    profile=resources._policy(control/"resources")["profile"]
    if prompt is None:prompt=("Complete the research brief in inputs/BRIEF.md. "
        "Read inputs/RESOURCES.json, inputs/COMPUTE.md and the supplied inputs/materials. Work autonomously through "
        "planning, implementation, bounded execution, recovery, analysis, substantive critique and reporting. "
        "Preserve all attempts and scientific evidence. Use the common local broker for setup and all scientific "
        "computation. Produce an evidence-linked English research package with full reproduction and "
        "retained-data recomputation commands. Distinguish completed checks from unverified claims and label "
        "any partial outcome honestly. Do not expand the supplied ceilings or change protected inputs. "
        "If a consequential unresolved choice prevents progress, record it explicitly for the user.\n")
    if workflow:prompt+="Use the installed Allagma research workflow. Read RESEARCH.md and ALLAGMA.md and resolve canonical methods through the exact study or campaign lock.\n"
    prompt+=f"The native session wall-time ceiling is {timeout} seconds, including model work. Scientific computation and setup retain their separate ceilings.\n"
    if interrupt_first_attempt:prompt+="A controlled interruption is enabled for the first marked scientific attempt; preserve it and recover.\n"
    return native.capture(codex=Path(codex).resolve(),workspace=study,record=control/"sessions"/session_id/"native",
        runtime=control/"sessions"/session_id/"runtime",prompt=prompt,timeout=timeout,config=config,auth=auth,
        blocked=[control,Path.home()/".codex",Path.home()/".agents",Path.home()/"Documents/vault"],
        readonly=prepared["readonly"],on_tick=broker.poll,rss_limit_bytes=profile["rss_limit_bytes"],
        storage_limit_bytes=profile["storage_limit_bytes"])
