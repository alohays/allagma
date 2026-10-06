"""Explicit three-way scaffold migrations, separate from method updates."""
from __future__ import annotations

from pathlib import Path
import uuid

from .files import AllagmaError, confined, digest, read_json, study_mutex, utcnow, write_json, write_text


def _user_path(study, name):
    if name.startswith((".allagma/", "campaigns/", ".agents/", ".claude/")) or name == "allagma.yaml":
        raise AllagmaError("Scaffold migrations cannot rewrite bundles, campaigns or active selection")
    return confined(study, name)


def plan_migration(study, migration):
    study = Path(study)
    with study_mutex(study):
        baseline = read_json(study / ".allagma/scaffold-baseline.json")
        if migration["from"] != baseline["version"] or migration["from"] == migration["to"]:
            raise AllagmaError("Migration source/target scaffold versions do not match")
        if migration["answers"] != baseline["answers"]:
            raise AllagmaError("Migration generation answers disagree with the baseline")
        paths, conflicts = {}, []
        for name, target in migration["files"].items():
            path = _user_path(study, name)
            local = path.read_text() if path.exists() else None
            base = baseline["files"].get(name)
            if local == base or local == target:
                result = target
            elif target == base:
                result = local
            else:
                result = local
                conflicts.append(name)
            paths[name] = {"base": base, "local": local, "target": target, "result": result}
        plan = {"id": "m-" + uuid.uuid4().hex[:12], "created_at": utcnow(), "from": migration["from"],
                "to": migration["to"], "answers": migration["answers"], "reason": migration["reason"],
                "baseline_digest": digest(baseline), "paths": paths, "conflicts": conflicts,
                "operation": "scaffold migration; bundle lock is unchanged"}
        write_json(study / ".allagma/migrations" / plan["id"] / "plan.json", plan, immutable=True)
        return plan


def apply_migration(study, migration_id):
    study = Path(study)
    with study_mutex(study):
        directory = confined(study, f".allagma/migrations/{migration_id}")
        plan = read_json(directory / "plan.json")
        if (directory / "applied.json").exists():
            raise AllagmaError("Migration already applied")
        if plan["conflicts"]:
            raise AllagmaError(f"Unresolved three-way conflicts: {plan['conflicts']}; preserve local edits and create a reconciled plan")
        baseline = read_json(study / ".allagma/scaffold-baseline.json")
        if digest(baseline) != plan["baseline_digest"]:
            raise AllagmaError("Scaffold baseline changed; replan migration")
        for name, item in plan["paths"].items():
            path = _user_path(study, name)
            if (path.read_text() if path.exists() else None) != item["local"]:
                raise AllagmaError(f"User file changed after migration planning: {name}")
        write_json(directory / "preimage.json", baseline, immutable=True)
        # All conflict and stale-plan checks precede any user-file mutation.
        for name, item in plan["paths"].items():
            path = _user_path(study, name)
            if item["result"] is None:
                path.unlink(missing_ok=True)
            else:
                write_text(path, item["result"])
            if item["target"] is None:
                baseline["files"].pop(name, None)
            else:
                baseline["files"][name] = item["target"]
        baseline["version"] = plan["to"]
        write_json(study / ".allagma/scaffold-baseline.json", baseline)
        receipt = {"id": migration_id, "applied_at": utcnow(), "baseline_digest": digest(baseline), "bundle_unchanged": True}
        write_json(directory / "applied.json", receipt, immutable=True)
        return receipt


def rollback_migration(study, migration_id):
    study = Path(study)
    with study_mutex(study):
        directory = confined(study, f".allagma/migrations/{migration_id}")
        if (directory / "rolled-back.json").exists():
            raise AllagmaError("Migration already rolled back")
        plan = read_json(directory / "plan.json")
        receipt = read_json(directory / "applied.json")
        if digest(read_json(study / ".allagma/scaffold-baseline.json")) != receipt["baseline_digest"]:
            raise AllagmaError("A later migration changed the scaffold; undo it first")
        for name, item in plan["paths"].items():
            path = _user_path(study, name)
            if (path.read_text() if path.exists() else None) != item["result"]:
                raise AllagmaError(f"Refusing to erase post-migration edits: {name}")
        for name, item in plan["paths"].items():
            path = _user_path(study, name)
            if item["local"] is None:
                path.unlink(missing_ok=True)
            else:
                write_text(path, item["local"])
        write_json(study / ".allagma/scaffold-baseline.json", read_json(directory / "preimage.json"))
        result = {"id": migration_id, "rolled_back_at": utcnow(), "user_preimages_restored": True}
        write_json(directory / "rolled-back.json", result, immutable=True)
        return result
