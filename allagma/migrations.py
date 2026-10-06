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


def apply_migration(study, migration_id, *, fault=None):
    study = Path(study)
    with study_mutex(study):
        directory = confined(study, f".allagma/migrations/{migration_id}")
        if list((study / ".allagma/migrations").glob("*/transaction.json")):
            raise AllagmaError("An interrupted scaffold migration requires migrate recover first")
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
        write_json(directory / "transaction.json", {"id": migration_id, "started_at": utcnow()}, immutable=True)
        # All conflict and stale-plan checks precede any user-file mutation.
        for index, (name, item) in enumerate(plan["paths"].items()):
            path = _user_path(study, name)
            if item["result"] is None:
                path.unlink(missing_ok=True)
            else:
                write_text(path, item["result"])
            if fault == "after-first-write" and index == 0:
                raise AllagmaError("Injected migration interruption; run migrate recover")
            if item["target"] is None:
                baseline["files"].pop(name, None)
            else:
                baseline["files"][name] = item["target"]
        baseline["version"] = plan["to"]
        write_json(study / ".allagma/scaffold-baseline.json", baseline)
        receipt = {"id": migration_id, "applied_at": utcnow(), "baseline_digest": digest(baseline), "bundle_unchanged": True}
        write_json(directory / "applied.json", receipt, immutable=True)
        (directory / "transaction.json").unlink()
        return receipt


def recover_migration(study, migration_id):
    study = Path(study)
    with study_mutex(study):
        directory = confined(study, f".allagma/migrations/{migration_id}")
        if not (directory / "transaction.json").exists():
            return {"id": migration_id, "recovered": False}
        transaction = read_json(directory / "transaction.json")
        plan = read_json(directory / "plan.json")
        for name, item in plan["paths"].items():
            path = _user_path(study, name)
            current = path.read_text() if path.exists() else None
            if current not in (item["local"], item["result"]):
                raise AllagmaError(f"Post-interruption edit requires reconciliation: {name}")
        if transaction.get("direction") == "rollback":
            if (directory / "rolled-back.json").exists():
                receipt = read_json(directory / "rolled-back.json")
                if digest(read_json(study / ".allagma/scaffold-baseline.json")) != receipt["baseline_digest"]:
                    raise AllagmaError("Committed inverse baseline changed; reconcile before recovery")
                for name, item in plan["paths"].items():
                    path = _user_path(study, name)
                    if (path.read_text() if path.exists() else None) != item["local"]:
                        raise AllagmaError("Committed inverse files changed; reconcile before recovery")
                action = "finished committed inverse migration"
            else:
                for name, content in transaction["files"].items():
                    path = _user_path(study, name)
                    if content is None:
                        path.unlink(missing_ok=True)
                    elif not path.exists() or path.read_text() != content:
                        write_text(path, content)
                write_json(study / ".allagma/scaffold-baseline.json", transaction["baseline"])
                action = "restored pre-rollback state"
        elif (directory / "applied.json").exists():
            receipt = read_json(directory / "applied.json")
            if digest(read_json(study / ".allagma/scaffold-baseline.json")) != receipt["baseline_digest"]:
                raise AllagmaError("Committed migration baseline changed; reconcile before recovery")
            for name, item in plan["paths"].items():
                path = _user_path(study, name)
                if (path.read_text() if path.exists() else None) != item["result"]:
                    raise AllagmaError("Committed migration files changed; reconcile before recovery")
            action = "finished committed migration"
        else:
            for name, item in plan["paths"].items():
                path = _user_path(study, name)
                current = path.read_text() if path.exists() else None
                if current == item["local"]:
                    continue
                if item["local"] is None:
                    path.unlink(missing_ok=True)
                else:
                    write_text(path, item["local"])
            write_json(study / ".allagma/scaffold-baseline.json", read_json(directory / "preimage.json"))
            action = "restored pre-migration state"
        result = {"id": migration_id, "recovered": True, "action": action, "at": utcnow()}
        write_json(directory / f"recovery-{uuid.uuid4().hex[:8]}.json", result, immutable=True)
        (directory / "transaction.json").unlink()
        return result


def rollback_migration(study, migration_id, *, fault=None):
    study = Path(study)
    with study_mutex(study):
        directory = confined(study, f".allagma/migrations/{migration_id}")
        if list((study / ".allagma/migrations").glob("*/transaction.json")):
            raise AllagmaError("An interrupted scaffold migration requires migrate recover first")
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
        write_json(directory / "transaction.json", {"direction": "rollback", "id": migration_id,
                   "baseline": read_json(study / ".allagma/scaffold-baseline.json"),
                   "files": {name: item["result"] for name, item in plan["paths"].items()}}, immutable=True)
        for index, (name, item) in enumerate(plan["paths"].items()):
            path = _user_path(study, name)
            if item["local"] is None:
                path.unlink(missing_ok=True)
            else:
                write_text(path, item["local"])
            if fault == "after-first-write" and index == 0:
                raise AllagmaError("Injected inverse interruption; run migrate recover")
        baseline = read_json(directory / "preimage.json")
        write_json(study / ".allagma/scaffold-baseline.json", baseline)
        result = {"id": migration_id, "rolled_back_at": utcnow(), "user_preimages_restored": True, "baseline_digest": digest(baseline)}
        write_json(directory / "rolled-back.json", result, immutable=True)
        (directory / "transaction.json").unlink()
        return result
