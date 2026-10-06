"""Readable module registry, capability closure, and scoped conformance."""
from __future__ import annotations

from pathlib import Path
import re

from .files import AllagmaError, confined, read_json

FIELDS = {"id", "kind", "entry", "contract", "inputs", "outputs", "requires",
          "optional", "settings", "dependencies", "resources", "sources", "adaptation",
          "lifecycle", "maintainer", "evaluation", "examples", "compatibility", "replacement"}
STATES = {"proposed", "experimental", "stable", "deprecated", "retired"}
KINDS = {"method", "recipe", "adapter", "evaluation", "policy", "profile"}


class Catalog:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.registry = read_json(self.root / "registry.json")
        self.release = read_json(self.root / "release.json")

    def module(self, module_id):
        try:
            directory = self.registry["modules"][module_id]
        except KeyError as exc:
            raise AllagmaError(f"Unknown module: {module_id}") from exc
        return read_json(confined(self.root, directory + "/module.yaml"))

    def directory(self, module_id):
        self.module(module_id)
        return confined(self.root, self.registry["modules"][module_id])

    def check(self, module_id=None):
        checked = []
        for key in ([module_id] if module_id else self.registry["modules"]):
            module = self.module(key)
            missing = FIELDS - module.keys()
            if missing:
                raise AllagmaError(f"{key}: missing module fields {sorted(missing)}")
            if module["id"] != key or module["kind"] not in KINDS or module["lifecycle"] not in STATES:
                raise AllagmaError(f"{key}: invalid identity, kind or lifecycle")
            if module["contract"] != "0.2" or module["compatibility"]["contracts"] != ["0.2"]:
                raise AllagmaError(f"{key}: unsupported contract version; explicit migration required")
            if not module["maintainer"] or not module["adaptation"]:
                raise AllagmaError(f"{key}: missing ownership or adaptation")
            directory = self.directory(key)
            for relative in [module["entry"], *module["resources"], *module["evaluation"], *module["examples"]]:
                if not confined(directory, relative).is_file():
                    raise AllagmaError(f"{key}: missing resource {relative}")
            for name in [*module["inputs"], *module["outputs"]]:
                if not (self.root / "contracts" / f"{name}.schema.json").is_file():
                    raise AllagmaError(f"{key}: unknown artifact contract {name}")
            for dependency in module["dependencies"]:
                self.module(dependency)
            if module["kind"] in ("method", "recipe"):
                self._check_skill(directory, module)
            if module["lifecycle"] == "deprecated":
                replacement = module["replacement"]
                if not isinstance(replacement, dict) or not all(k in replacement for k in ("id", "migration", "earliest_retirement")):
                    raise AllagmaError(f"{key}: incomplete deprecation commitment")
                self.module(replacement["id"])
            if module["kind"] == "recipe":
                self._check_recipe(module)
            checked.append(key)
        return checked

    @staticmethod
    def _check_skill(directory, module):
        body = (directory / module["entry"]).read_text()
        parts = body.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            raise AllagmaError(f"{module['id']}: missing skill frontmatter")
        frontmatter = {}
        for line in parts[1].strip().splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                raise AllagmaError("Shared skill frontmatter uses single-line name and description")
            frontmatter[key.strip()] = value.strip()
        if set(frontmatter) != {"name", "description"}:
            raise AllagmaError("Shared skills only contain name and description; host settings belong in adapters")
        name = frontmatter["name"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64 or name != directory.name:
            raise AllagmaError(f"Invalid skill directory/name: {name}")
        if not 1 <= len(frontmatter["description"]) <= 1024:
            raise AllagmaError(f"Invalid description: {name}")
        if any(word in parts[2] for word in ("mcp__", "functions.exec", "allowed-tools:", "model:")):
            raise AllagmaError(f"{name}: provider syntax in shared method")

    def _check_recipe(self, module):
        recipe = read_json(self.directory(module["id"]) / "recipe.json")
        phases = recipe["steps"]
        available = {"StudySpec"}
        if not recipe["stop_rules"] or not phases:
            raise AllagmaError("Recipes need steps and stopping rules")
        for step in phases:
            method_id = recipe["roles"].get(step["method"].removeprefix("$"), step["method"])
            method = self.module(method_id)
            if method_id not in {*module["dependencies"], *recipe["roles"].values()}:
                raise AllagmaError(f"{module['id']}: undeclared method dependency {method_id}")
            if set(step["consumes"]) != set(method["inputs"]):
                raise AllagmaError(f"{module['id']}: input contract disagrees with {method_id}")
            missing = set(step["consumes"]) - available
            if missing:
                raise AllagmaError(f"{module['id']}: missing handoffs {sorted(missing)}")
            if not set(step["produces"]) <= set(method["outputs"]):
                raise AllagmaError(f"{module['id']}: step outputs disagree with {method_id}")
            available.update(step["produces"])
        if module["lifecycle"] == "stable":
            for selected in [*recipe["roles"].values(), *module["dependencies"]]:
                if self.module(selected)["lifecycle"] != "stable":
                    raise AllagmaError(f"Stable recipe selects non-stable module: {selected}")

    def resolve(self, intent):
        recipe_id = intent["recipe"]
        self.check(recipe_id)
        recipe = read_json(self.directory(recipe_id) / "recipe.json")
        roles = {**recipe["roles"], **intent.get("roles", {})}
        unknown_roles = set(roles) - recipe["roles"].keys()
        if unknown_roles:
            raise AllagmaError(f"Unknown recipe roles: {sorted(unknown_roles)}")
        for role, chosen in roles.items():
            default = self.module(recipe["roles"][role])
            replacement = self.module(chosen)
            if (default["kind"], default["inputs"], default["outputs"]) != (replacement["kind"], replacement["inputs"], replacement["outputs"]):
                raise AllagmaError(f"{chosen}: incompatible replacement for {role}")
        selected, visiting = set(), set()

        def visit(key):
            if key in visiting:
                raise AllagmaError(f"Dependency cycle at {key}")
            if key in selected:
                return
            module = self.module(key)
            self.check(key)
            if module["lifecycle"] in ("retired", "proposed"):
                raise AllagmaError(f"Cannot newly select {module['lifecycle']} module {key}")
            if module["lifecycle"] == "experimental" and not intent.get("allow_experimental", False):
                raise AllagmaError(f"Explicit experimental selection required for {key}")
            visiting.add(key)
            for dependency in module["dependencies"]:
                visit(dependency)
            visiting.remove(key)
            selected.add(key)

        for key in [recipe_id, "profile/default", "policy/local", *recipe["roles"].values(), *roles.values(), *(f"host/{host}" for host in intent["hosts"])]:
            visit(key)
        required = sorted({cap for key in selected for cap in self.module(key)["requires"]})
        missing = set(required) - set(intent["capabilities"])
        if missing:
            raise AllagmaError(f"Missing required capabilities: {sorted(missing)}; no scientific checks may be omitted")
        return {"recipe": recipe_id, "roles": roles, "modules": sorted(selected),
                "requires": required, "recipe_definition": recipe}
