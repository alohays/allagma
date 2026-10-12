"""Read-only prerequisites; never execute a discovered host or inspect credentials."""
from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import sys

from . import bundles
from .catalog import Catalog
from .files import AllagmaError, confined, read_json


def distribution_kind(source):
    """Recognize selected catalogs without using absent toy files as a signal."""
    # The location still identifies a study bundle if its registry is damaged.
    # A relocated bundle retains the composition marker written by build_bundle.
    if source.parent.name == "bundles" and source.parent.parent.name == ".allagma":
        return "standalone-bundle"
    try:
        registry = read_json(source / "registry.json")
    except (AllagmaError, OSError, ValueError, RecursionError):
        return "source-checkout"
    return ("standalone-bundle" if isinstance(registry, dict) and "composition" in registry
            else "source-checkout")


def diagnose(source, *, study=None, scope="offline", codex=None):
    source = Path(source).resolve()
    study = Path(study).resolve() if study is not None else None
    distribution = distribution_kind(source)
    checks, excluded = [], []

    def add(identity, passed, message, remedy=None):
        # Reports are suitable for issue triage without exposing home paths.
        for path, replacement in ((study, "<study>"), (source, "<source>"), (Path.home(), "<home>")):
            if path is not None:
                message = message.replace(str(path), replacement)
        checks.append({"id": identity, "status": "pass" if passed else "fail",
                       "message": message, "remedy": None if passed else remedy})

    def inspect(identity, action, remedy):
        try:
            message = action()
        # Existing verifiers also use mapping methods on decoded documents.
        # Wrong JSON shapes and excessive nesting are failed prerequisites,
        # not reasons to lose the remaining independent diagnostics.
        except (AllagmaError, OSError, ValueError, KeyError, TypeError,
                AttributeError, RecursionError) as exc:
            add(identity, False, str(exc), remedy)
        else:
            add(identity, True, message)

    add("python", sys.version_info >= (3, 11), platform.python_version(),
        "Use a Python 3.11+ interpreter to run Allagma.")
    add("platform", os.name == "posix", platform.system(),
        "Run the offline core on macOS or Linux; other platforms are not qualified.")

    def catalog():
        checked = Catalog(source).check()
        return f"{len(checked)} catalog modules checked."

    catalog_remedy = ("Recover an intact exported study from its retained copy or owner. "
                      "For an intentional change, use the update workflow from a source checkout; "
                      "never insert files into or rewrite a locked bundle."
                      if distribution == "standalone-bundle" else
                      "Restore the source checkout's declared modules and resources; see the first-study sparse-checkout list.")
    inspect("catalog", catalog, catalog_remedy)

    def toy():
        root = confined(source, "examples/toy-study")
        protocol = read_json(confined(root, "protocol.json"))
        for name in {"brief.json", "evidence-map.json", *protocol["code"],
                     protocol["runner"], protocol["evaluator"], protocol["analyzer"], protocol["writer"]}:
            if not confined(root, name).is_file():
                raise AllagmaError(f"Missing toy resource: examples/toy-study/{name}")
        return "Toy protocol and declared local resources are present; no experiment executed."

    if distribution == "source-checkout":
        inspect("toy-resources", toy, "Restore examples/toy-study from the same checkout before running the toy.")
    else:
        excluded.append({"id": "toy-resources", "reason":
            "Central examples/toy-study resources are outside standalone-bundle scope. "
            "Science files belong to the study; this report does not execute or validate its protocol."})

    if study is not None:
        def lock():
            value = bundles.verify_study(study)
            return f"Verified current lock {value['lock_id']} and selection freshness."

        inspect("study-lock", lock, "Inspect the failure; use update check/plan for changed intent or recover an unfinished transaction. Never edit a frozen lock.")
        inspect("generated-files", lambda: f"{len(bundles.check_ownership(study)['files'])} generated files match ownership.",
                "Reconcile edited generated files into overrides or a local module; preserve user edits.")

    if scope == "native":
        add("native-platform", platform.system() == "Darwin", platform.system(),
            "The supervised native runner is currently qualified on macOS only. Offline work remains available on Linux.")
        sandbox = shutil.which("sandbox-exec")
        add("native-sandbox", sandbox is not None, "sandbox-exec found" if sandbox else "sandbox-exec not found",
            "Use a supported macOS environment with sandbox-exec; do not disable the supervisor.")
        executable = Path(codex) if codex is not None else shutil.which("codex")
        found = executable is not None and Path(executable).is_file() and os.access(executable, os.X_OK)
        add("native-executable", found, "Codex executable found; not invoked" if found else "Codex executable not found or not executable",
            "Supply --codex /path/to/codex or install it separately; doctor does not install software.")

    return {"diagnostic_version": 1, "scope": scope, "distribution": distribution,
            "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
            "checks": checks, "excluded_checks": excluded,
            "limitations": ["Read-only prerequisite inspection, not execution or host qualification.",
                            "No authentication, model availability, scientific dependencies, network or resource-capacity checks.",
                            "A passing study lock does not verify campaign evidence or scientific conclusions."]}
