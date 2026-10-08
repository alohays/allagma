"""Resolve settings with leaf-level provenance; permissions can only narrow."""
from __future__ import annotations

from copy import deepcopy
import math
from .files import AllagmaError, digest

DEFAULT_BUDGET = {"max_attempts": "unset", "max_seconds": "unset", "money_usd": "unset",
                  "per_attempt_seconds": 30.0}


def resolve_configuration(layers, host_capabilities):
    effective, origins = {}, {}

    def merge(target, patch, source, prefix=""):
        for key, value in patch.items():
            if key.lower() in ("api_key", "token", "password", "secret", "credentials"):
                raise AllagmaError("Keep credentials in host-managed storage, outside frozen configuration")
            if key in ("model", "review_model"):
                raise AllagmaError("Project model pins are not supported; record experimental controls in the campaign")
            name = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                if not isinstance(target.get(key), dict):
                    target[key] = {}
                    origins.pop(name, None)
                merge(target[key], value, source, name)
            else:
                target[key] = deepcopy(value)
                for old in list(origins):
                    if old.startswith(name + "."):
                        del origins[old]
                origins[name] = source

    for name, values in layers:
        merge(effective, values, name)
    requested = effective.get("capabilities", host_capabilities)
    if not isinstance(requested, list) or not set(requested) <= set(host_capabilities):
        raise AllagmaError("Configuration cannot expand host authorization")
    effective["capabilities"] = sorted(requested)
    origins.setdefault("capabilities", "host authorization")
    budget = effective.get("budget", {})
    if set(budget) != set(DEFAULT_BUDGET):
        raise AllagmaError("Budget must define max_attempts, max_seconds, money_usd and per_attempt_seconds")
    for key, value in budget.items():
        if value == "unset" and key != "per_attempt_seconds":
            continue
        minimum = {"money_usd": 0, "max_attempts": 1, "max_seconds": 0.001, "per_attempt_seconds": 0.01}[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or (isinstance(value, float) and not math.isfinite(value)) or value < minimum):
            raise AllagmaError(f"Invalid budget {key}: {value!r}")
        if key == "max_attempts" and not isinstance(value, int):
            raise AllagmaError("max_attempts must be an integer")
    return effective, origins
