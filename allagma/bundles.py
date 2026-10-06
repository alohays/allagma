"""Coherent local releases, exact locks, and transactional study updates."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import uuid

from . import __version__
from .catalog import Catalog
from .configuration import DEFAULT_BUDGET, resolve_configuration
from .files import (AllagmaError, canonical, confined, digest, file_hash, inventory,
                    read_json, study_mutex, utcnow, verify_inventory, write_bytes,
                    write_json, write_text)

HOSTS = ["generic", "codex", "claude-code"]
CAPABILITIES = ["artifact.read", "artifact.write", "execution.local"]


def source_inventory(source):
    catalog = Catalog(source)
    paths = {"registry.json", "release.json", "LICENSE", "tools/allagma.py"}
    for directory in ["allagma", "contracts", "templates/study", *catalog.registry["modules"].values()]:
        for name in inventory(confined(source, directory)):
            paths.add(f"{directory}/{name}")
    return {name: file_hash(confined(source, name)) for name in sorted(paths)}


def source_revision(source):
    return "sha256:" + digest(source_inventory(source))


def default_intent(study_id):
    return {"schema_version": "0.2", "study_id": study_id, "recipe": "recipe/research",
            "roles": {}, "hosts": HOSTS, "capabilities": CAPABILITIES,
            "profile": "profiles/study.json", "overrides": ["overrides/settings.json"],
            "settings": {}, "request": {}, "allow_experimental": False}


def resolve_study(source, study, intent):
    catalog = Catalog(source)
    if intent.get("schema_version") != "0.2" or not intent["hosts"] or not set(intent["hosts"]) <= set(HOSTS):
        raise AllagmaError("Unsupported intent schema or host selection")
    composition = catalog.resolve(intent)
    layers = [("module defaults", {"budget": DEFAULT_BUDGET})]
    for key in composition["modules"]:
        if catalog.module(key)["kind"] != "recipe":
            layers.append((f"module:{key}", catalog.module(key)["settings"]))
    layers.append((f"recipe:{intent['recipe']}", catalog.module(intent["recipe"])["settings"]))
    profile = read_json(confined(study, intent["profile"]))
    layers.append((f"profile:{profile['id']}", profile["settings"]))
    inputs = {intent["profile"]: file_hash(confined(study, intent["profile"]))}
    layers.append(("study settings", intent["settings"]))
    for relative in intent["overrides"]:
        path = confined(study, relative)
        layers.append((f"override:{relative}", read_json(path)))
        inputs[relative] = file_hash(path)
    layers.append(("current request", intent["request"]))
    effective, origins = resolve_configuration(layers, intent["capabilities"])
    if set(composition["requires"]) - set(effective["capabilities"]):
        raise AllagmaError("Effective capability settings cannot satisfy the selected composition")
    return composition, effective, origins, inputs, [{"id": profile["id"], "sha256": inputs[intent["profile"]]}]


def seal_lock(lock):
    lock = deepcopy(lock)
    lock.pop("lock_id", None)
    lock["lock_id"] = digest(lock)
    return lock


def build_bundle(source, study, intent, destination, *, _local_prepared=False):
    """Export closure and helpers; no symlinks or dependency on the source checkout."""
    source, destination = Path(source).resolve(), Path(destination)
    if intent.get("local_modules") and not _local_prepared:
        # An explicit local variant enters the same catalog/contract checks. The
        # virtual source is temporary; every required byte travels in the bundle.
        with tempfile.TemporaryDirectory(prefix="allagma-local-source-") as temp:
            virtual = Path(temp)
            for name in source_inventory(source):
                write_bytes(confined(virtual, name), confined(source, name).read_bytes())
            registry = read_json(virtual / "registry.json")
            local_inputs, lineage = {}, []
            for variant in intent["local_modules"]:
                if not variant["path"].startswith("modules-local/") or variant["scope"] != "method":
                    raise AllagmaError("Local variants must declare method scope under modules-local/")
                directory = confined(study, variant["path"])
                meta = read_json(directory / "module.yaml")
                base = Catalog(source).module(variant["base"])
                if meta["id"] != variant["id"] or meta["kind"] != "method" or meta["id"] in registry["modules"]:
                    raise AllagmaError("Local variants require a new stable ID and method kind")
                if (meta["inputs"], meta["outputs"]) != (base["inputs"], base["outputs"]):
                    raise AllagmaError("Local replacement has incompatible contracts")
                paths = ["module.yaml", meta["entry"], *meta["resources"], *meta["examples"], *meta["evaluation"]]
                for name in set(paths):
                    data = confined(directory, name).read_bytes()
                    write_bytes(confined(virtual, f"{variant['path']}/{name}"), data)
                    local_inputs[f"{variant['path']}/{name}"] = file_hash(confined(directory, name))
                registry["modules"][meta["id"]] = variant["path"]
                lineage.append({**variant, "base_source_revision": source_revision(source)})
            write_json(virtual / "registry.json", registry)
            lock = build_bundle(virtual, study, intent, destination, _local_prepared=True)
            lock["local_modules"] = lineage
            lock["upstream_source_revision"] = source_revision(source)
            lock["configuration_inputs"].update(local_inputs)
            return seal_lock(lock)
    catalog = Catalog(source)
    composition, config, origins, inputs, provenance = resolve_study(source, study, intent)
    paths = {"release.json", "LICENSE", "tools/allagma.py"}
    for directory in ["allagma", "contracts", *[catalog.registry["modules"][key] for key in composition["modules"]]]:
        for name in inventory(confined(source, directory)):
            paths.add(f"{directory}/{name}")
    destination.mkdir(parents=True, exist_ok=False)
    for name in sorted(paths):
        write_bytes(confined(destination, name), confined(source, name).read_bytes(), immutable=True)
    registry = {"schema_version": "0.2", "modules": {key: catalog.registry["modules"][key] for key in composition["modules"]}}
    write_json(destination / "registry.json", registry, immutable=True)
    write_text(destination / "CATALOG.md", "# Locked Allagma catalog\n\n" + "\n".join(
        f"- `{key}`: [{catalog.module(key)['entry']}]({registry['modules'][key]}/{catalog.module(key)['entry']})"
        for key in composition["modules"]) + "\n", immutable=True)
    files = inventory(destination)
    revision = source_revision(source)
    bundle_id = "b-" + digest({"files": files, "source": revision})[:24]
    lock = {"schema_version": "0.2", "release": catalog.release["release"],
            "release_tag": catalog.release["release_tag"], "publication": catalog.release["publication"],
            "source_revision": revision, "bundle_id": bundle_id, "files": files,
            "recipe": composition["recipe"], "roles": composition["roles"],
            "modules": {key: {"path": registry["modules"][key],
                              "revision": "sha256:" + digest(inventory(catalog.directory(key))),
                              "dependencies": catalog.module(key)["dependencies"]}
                        for key in composition["modules"]},
            "contracts": catalog.release["contracts"], "hosts": intent["hosts"],
            "capabilities": config["capabilities"], "generator_version": __version__,
            "scaffold": {"version": catalog.release["scaffold_version"], "answers": {"study_id": intent["study_id"]}},
            "effective_configuration": config, "configuration_origins": origins,
            "profile_provenance": provenance, "configuration_inputs": inputs,
            "intent_digest": digest(intent), "created_at": utcnow()}
    return seal_lock(lock)


def _save_resolution(study, lock, intent):
    """Retain old configuration preimages for a complete, explicit rollback."""
    value = {"lock": lock, "intent": intent,
             "inputs": {name: confined(study, name).read_text() for name in lock["configuration_inputs"]}}
    write_json(Path(study) / ".allagma/resolutions" / f"{lock['lock_id']}.json", value, immutable=True)


def bundle_path(study, lock):
    return confined(study, f".allagma/bundles/{lock['bundle_id']}")


def verify_lock(study, lock, *, directory=None):
    required = {"lock_id", "files", "bundle_id", "source_revision", "contracts", "modules",
                "recipe", "roles", "effective_configuration", "intent_digest", "configuration_inputs"}
    if not required <= lock.keys() or lock.get("schema_version") != "0.2" or lock["contracts"] != ["0.2"]:
        raise AllagmaError("Unsupported or incomplete lock; migration required")
    if seal_lock(lock)["lock_id"] != lock["lock_id"]:
        raise AllagmaError("Lock digest mismatch")
    if not lock["source_revision"].startswith("sha256:") or len(lock["source_revision"]) != 71:
        raise AllagmaError("Lock must identify immutable source content")
    expected_id = "b-" + digest({"files": lock["files"], "source": lock["source_revision"]})[:24]
    if expected_id != lock["bundle_id"]:
        raise AllagmaError("Bundle identity mismatch")
    verify_inventory(directory or bundle_path(study, lock), lock["files"])
    return lock


def verify_study(study, *, freshness=True):
    study = Path(study)
    if (study / ".allagma/transaction.json").exists():
        raise AllagmaError("Unfinished update transaction; run update recover before using the active lock")
    lock = verify_lock(study, read_json(study / ".allagma/lock.yaml"))
    if freshness:
        if digest(read_json(study / "allagma.yaml")) != lock["intent_digest"]:
            raise AllagmaError("Selection intent differs from the lock; plan a settings update before a new campaign")
        for name, expected in lock["configuration_inputs"].items():
            if file_hash(confined(study, name)) != expected:
                raise AllagmaError(f"Configuration changed: {name}; plan an update, or resume a frozen campaign")
    return lock


def resolve_entry(study, module_id=None, campaign=None):
    study = Path(study)
    if campaign:
        lock = verify_lock(study, read_json(confined(study, f"campaigns/{campaign}/lock.yaml")))
    else:
        lock = verify_study(study)
    if module_id in lock["roles"]:
        module_id = lock["roles"][module_id]
    module_id = module_id or lock["recipe"]
    if module_id not in lock["modules"]:
        raise AllagmaError(f"{module_id} is absent from this campaign's bundle")
    root = bundle_path(study, lock)
    catalog = Catalog(root)
    path = catalog.directory(module_id) / catalog.module(module_id)["entry"]
    return {"bundle_id": lock["bundle_id"], "lock_id": lock["lock_id"], "module_id": module_id,
            "path": str(path), "sha256": file_hash(path), "contract": "0.2",
            "capabilities": lock["capabilities"]}


def generated_entries(study, lock, previous=None):
    previous = previous or {"files": {}, "mapping": {}}
    files, mapping = {}, {}
    root = bundle_path(study, lock)
    generic = ("# Allagma study entrypoint\n\nSelect or recover a campaign first. Its "
               "`campaigns/<campaign>/lock.yaml` is authoritative for resume; otherwise use "
               "`.allagma/lock.yaml` and compare selection intent. Read `bundle_id` and open "
               "`.allagma/bundles/<bundle_id>/CATALOG.md`. Use only that bundle's methods and "
               "helpers. A newer global skill or study lock cannot replace a campaign snapshot.\n\n"
               "For a machine-checked path, run `python3 .allagma/bundles/<bundle_id>/tools/allagma.py "
               "entry --study . --campaign <campaign> --module <method-id-or-role>`. Omit "
               "`--campaign` only for a new study phase. Required capabilities must be available; "
               "sequential artifact handoffs are the default. Shared contracts are in the bundle's "
               "`contracts/` directory.\n")

    def choose(key, preferred):
        if key in previous["mapping"]:
            return previous["mapping"][key]
        path = confined(study, preferred)
        if path.exists() and preferred not in previous["files"]:
            if preferred == "ALLAGMA.md":
                preferred = ".allagma/entrypoints/ALLAGMA.md"
            else:
                parent = Path(preferred).parent
                stem = parent.name[:47]
                preferred = (parent.parent / f"{stem}-{digest(key)[:8]}" / "SKILL.md").as_posix()
            if confined(study, preferred).exists():
                raise AllagmaError(f"Allagma namespace conflict: {preferred}")
        return preferred

    generic_path = choose("generic", "ALLAGMA.md")
    files[generic_path] = generic
    mapping["generic"] = generic_path
    for host, prefix in [("codex", ".agents/skills"), ("claude-code", ".claude/skills")]:
        if host not in lock["hosts"]:
            continue
        for key, item in lock["modules"].items():
            meta = read_json(root / item["path"] / "module.yaml")
            if meta["kind"] not in ("method", "recipe"):
                continue
            original = (root / item["path"] / meta["entry"]).read_text()
            description = original.split("description:", 1)[1].splitlines()[0].strip()
            name = Path(item["path"]).name
            path = choose(f"{host}:{key}", f"{prefix}/{name}/SKILL.md")
            name = Path(path).parent.name
            files[path] = (f"---\nname: {name}\ndescription: {description}\n---\n\n"
                           f"Read the study's `{generic_path}` and select or recover the campaign first. "
                           f"Resolve `{key}` through that campaign's lock and read its canonical SKILL.md "
                           "and adjacent module.yaml from the bundle. The module's declared inputs, outputs "
                           "and resources are authoritative. Do not use a global or newer copy.\n")
            mapping[f"{host}:{key}"] = path
    return files, {"schema_version": "0.2", "files": {key: digest_text(value) for key, value in files.items()},
                   "mapping": mapping}


def digest_text(value):
    from .files import digest_bytes
    return digest_bytes(value.encode())


def check_ownership(study):
    ownership = read_json(Path(study) / ".allagma/ownership.json")
    for name, expected in ownership["files"].items():
        path = confined(study, name)
        if not path.is_file() or file_hash(path) != expected:
            raise AllagmaError(f"Locally edited generated file: {name}; reconcile into overrides or a local module")
    return ownership


def initialize(source, study, *, study_id="study", intent=None):
    source, study = Path(source).resolve(), Path(study).resolve()
    study.mkdir(parents=True, exist_ok=True)
    with study_mutex(study):
        if (study / ".allagma/lock.yaml").exists():
            raise AllagmaError("Study already initialized")
        intent = deepcopy(intent or default_intent(study_id))
        defaults = {"allagma.yaml": intent,
                    intent["profile"]: read_json(source / "profiles/default/profile.json"),
                    "overrides/settings.json": {}}
        for relative, data in defaults.items():
            path = confined(study, relative)
            if not path.exists():
                write_json(path, data, immutable=True)
        intent = read_json(study / "allagma.yaml")
        baseline = {}
        for name in inventory(source / "templates/study"):
            data = (source / "templates/study" / name).read_bytes().replace(b"{{study_id}}", intent["study_id"].encode())
            baseline[name] = data.decode()
            if not confined(study, name).exists():
                write_bytes(confined(study, name), data, immutable=True)
        write_json(study / ".allagma/scaffold-baseline.json", {"version": "1", "answers": {"study_id": intent["study_id"]}, "files": baseline}, immutable=True)
        with tempfile.TemporaryDirectory(prefix="allagma-export-") as temp:
            candidate = Path(temp) / "bundle"
            lock = build_bundle(source, study, intent, candidate)
            target = bundle_path(study, lock)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                verify_lock(study, lock)
            else:
                shutil.copytree(candidate, target)
        files, owner = generated_entries(study, lock)
        for relative, content in files.items():
            write_text(confined(study, relative), content, immutable=True)
        write_json(study / ".allagma/ownership.json", owner)
        _save_resolution(study, lock, intent)
        write_json(study / ".allagma/lock.yaml", lock)
        return lock


def check_update(source, study):
    lock = verify_study(study, freshness=False)
    catalog = Catalog(source)
    return {"current_release": lock["release"], "target_release": catalog.release["release"],
            "current_source": lock["source_revision"], "target_source": source_revision(source),
            "available": lock["source_revision"] != source_revision(source),
            "compatibility": catalog.release["contracts"] == lock["contracts"],
            "active_files_changed": False}


def _event(directory, operation, **details):
    sequence = len(list((directory / "events").glob("*.json"))) + 1
    event = {"operation": operation, "time": utcnow(), **details}
    write_json(directory / "events" / f"{sequence:03d}-{operation}.json", event, immutable=True)
    return event


def plan_update(source, study):
    study = Path(study)
    with study_mutex(study):
        old = verify_study(study, freshness=False)
        check_ownership(study)
        intent = read_json(study / "allagma.yaml")
        update_id = "u-" + uuid.uuid4().hex[:12]
        directory = study / ".allagma/updates" / update_id
        directory.mkdir(parents=True)
        _event(directory, "check", result=check_update(source, study))
        try:
            lock = build_bundle(source, study, intent, directory / "bundle")
            write_json(directory / "lock.yaml", lock, immutable=True)
            write_json(directory / "intent.json", intent, immutable=True)
            _save_resolution(study, lock, intent)
            changed = sorted(key for key in old["files"].keys() | lock["files"].keys() if old["files"].get(key) != lock["files"].get(key))
            plan = {"id": update_id, "base_lock_id": old["lock_id"], "target_lock_id": lock["lock_id"],
                    "added_modules": sorted(lock["modules"].keys() - old["modules"].keys()),
                    "removed_modules": sorted(old["modules"].keys() - lock["modules"].keys()),
                    "changed_paths": changed, "configuration_changed": old["effective_configuration"] != lock["effective_configuration"],
                    "scaffold_migration": "separate operation; no study-owned files are replaced",
                    "contracts_compatible": lock["contracts"] == old["contracts"]}
            write_json(directory / "plan.json", plan, immutable=True)
            _event(directory, "plan", target=lock["source_revision"])
            return plan
        except Exception as exc:
            _event(directory, "failed", last_completed="check", reason=str(exc))
            raise


def _update(study, update_id):
    directory = confined(study, f".allagma/updates/{update_id}")
    plan = read_json(directory / "plan.json")
    lock = read_json(directory / "lock.yaml")
    if lock["lock_id"] != plan["target_lock_id"]:
        raise AllagmaError("Update target changed since planning")
    active = verify_study(study, freshness=False)
    if active["lock_id"] != plan["base_lock_id"]:
        raise AllagmaError("Active lock changed since planning; create a new plan")
    if not plan["contracts_compatible"]:
        raise AllagmaError("Contract migration required before adoption")
    verify_lock(study, lock, directory=directory / "bundle")
    if digest(read_json(Path(study) / "allagma.yaml")) != lock["intent_digest"]:
        raise AllagmaError("Intent changed after planning; plan again")
    for name, expected in lock["configuration_inputs"].items():
        if file_hash(confined(study, name)) != expected:
            raise AllagmaError(f"Configuration changed after planning: {name}")
    check_ownership(study)
    return directory, plan, lock


def reconcile_update(study, update_id):
    with study_mutex(study):
        directory, plan, lock = _update(study, update_id)
        return _event(directory, "reconcile", conflicts=[], user_owned_paths="preserved", target=lock["lock_id"])


def validate_update(study, update_id):
    with study_mutex(study):
        directory, plan, lock = _update(study, update_id)
        if not list((directory / "events").glob("*-reconcile.json")):
            raise AllagmaError("Reconcile the update before validation")
        catalog = Catalog(directory / "bundle")
        modules = catalog.check()
        from .qualification import qualify_examples
        output = directory / f"validation-{len(list(directory.glob('validation-*'))) + 1:03d}"
        examples = qualify_examples(directory / "bundle", lock["roles"], output)
        return _event(directory, "validate", target=lock["lock_id"], modules=modules, examples=examples,
                      coverage="Bundle integrity, contracts, capability closure, ownership and executable context/reviewer examples")


def _boundary(study):
    for path in (Path(study) / "campaigns").glob("*/state.json"):
        if read_json(path)["execution_status"] == "running":
            raise AllagmaError("Adopt at a campaign boundary: an execution is still marked running")


def _commit_active(study, lock, intent, record_id, *, fault=None, restored_inputs=None):
    """Journal preimages; commit lock last. Recovery restores the exact preimage."""
    study = Path(study)
    owner = check_ownership(study)
    entries, new_owner = generated_entries(study, lock, owner)
    updates = {**{name: text.encode() for name, text in entries.items()},
               ".allagma/ownership.json": canonical(new_owner), "allagma.yaml": canonical(intent),
               ".allagma/lock.yaml": canonical(lock)}
    updates.update({name: value.encode() for name, value in (restored_inputs or {}).items()})
    for name in owner["files"].keys() - new_owner["files"].keys():
        updates[name] = None
    preimages = {name: confined(study, name).read_text() if confined(study, name).exists() else None for name in updates}
    journal = {"id": record_id, "preimages": preimages, "target": lock["lock_id"]}
    write_json(study / ".allagma/transaction.json", journal, immutable=True)
    for i, (name, value) in enumerate(updates.items()):
        if name == ".allagma/lock.yaml":
            continue
        if value is None:
            confined(study, name).unlink(missing_ok=True)
        else:
            write_bytes(confined(study, name), value)
        if fault == "after-first-write" and i == 0:
            raise AllagmaError("Injected transaction interruption; run update recover")
    write_json(study / ".allagma/lock.yaml", lock)
    write_json(study / ".allagma/history" / f"{record_id}.json", journal, immutable=True)
    (study / ".allagma/transaction.json").unlink()


def adopt_update(study, update_id, *, fault=None):
    study = Path(study)
    with study_mutex(study):
        directory, plan, lock = _update(study, update_id)
        if not list((directory / "events").glob("*-validate.json")):
            raise AllagmaError("Validate the reconciled update before adoption")
        _boundary(study)
        target = bundle_path(study, lock)
        if not target.exists():
            staging = target.with_name(target.name + ".installing")
            if staging.exists():
                shutil.rmtree(staging)
            shutil.copytree(directory / "bundle", staging)
            verify_lock(study, lock, directory=staging)
            staging.rename(target)
        verify_lock(study, lock)
        _commit_active(study, lock, read_json(directory / "intent.json"), update_id, fault=fault)
        return _event(directory, "adopt", target=lock["lock_id"], campaign_boundary=True)


def recover_update(study):
    study = Path(study)
    with study_mutex(study):
        path = study / ".allagma/transaction.json"
        if not path.exists():
            return {"recovered": False}
        transaction = read_json(path)
        for name, content in transaction["preimages"].items():
            if content is None:
                confined(study, name).unlink(missing_ok=True)
            else:
                write_text(confined(study, name), content)
        path.unlink()
        write_json(study / ".allagma/recoveries" / f"{uuid.uuid4().hex}.json",
                   {"transaction": transaction["id"], "recovered_at": utcnow(), "action": "restored preimage"}, immutable=True)
        return {"recovered": True, "transaction": transaction["id"]}


def rollback(study, update_id):
    study = Path(study)
    with study_mutex(study):
        active = verify_study(study, freshness=False)
        _boundary(study)
        history = read_json(confined(study, f".allagma/history/{update_id}.json"))
        import json
        lock = json.loads(history["preimages"][".allagma/lock.yaml"])
        resolution = read_json(study / ".allagma/resolutions" / f"{lock['lock_id']}.json")
        intent = resolution["intent"]
        verify_lock(study, lock)
        # Refuse to erase edits made after the adopted resolution. Explicit
        # rollback restores pre-update overrides and profile projections too.
        for name, expected in active["configuration_inputs"].items():
            if file_hash(confined(study, name)) != expected:
                raise AllagmaError(f"Post-update local edit blocks rollback: {name}")
        record_id = "rollback-" + uuid.uuid4().hex[:12]
        _commit_active(study, lock, intent, record_id, restored_inputs=resolution["inputs"])
        return {"id": record_id, "operation": "rollback", "bundle_id": lock["bundle_id"],
                "scaffold": "unchanged; inverse migration is separate"}
