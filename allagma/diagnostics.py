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


def diagnose(source, *, study=None, scope="offline", codex=None):
    source = Path(source).resolve()
    study = Path(study).resolve() if study is not None else None
    checks = []

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

    inspect("catalog", catalog, "Restore the source checkout's declared modules and resources; see the first-study sparse-checkout list.")

    def toy():
        root = confined(source, "examples/toy-study")
        protocol = read_json(confined(root, "protocol.json"))
        for name in {"brief.json", "evidence-map.json", *protocol["code"],
                     protocol["runner"], protocol["evaluator"], protocol["analyzer"], protocol["writer"]}:
            if not confined(root, name).is_file():
                raise AllagmaError(f"Missing toy resource: examples/toy-study/{name}")
        return "Toy protocol and declared local resources are present; no experiment executed."

    inspect("toy-resources", toy, "Restore examples/toy-study from the same checkout before running the toy.")

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

    return {"diagnostic_version": 1, "scope": scope,
            "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
            "checks": checks,
            "limitations": ["Read-only prerequisite inspection, not execution or host qualification.",
                            "No authentication, model availability, scientific dependencies, network or resource-capacity checks.",
                            "A passing study lock does not verify campaign evidence or scientific conclusions."]}
