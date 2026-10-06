#!/usr/bin/env python3
"""Optional independent JSON Schema and skill/YAML validation."""
import argparse
import importlib.metadata
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from allagma.files import read_json, utcnow, write_json


def records(value):
    if isinstance(value, dict):
        if isinstance(value.get("record_type"), str):
            yield value
        for item in value.values():
            yield from records(item)
    elif isinstance(value, list):
        for item in value:
            yield from records(item)


def main():
    import jsonschema
    import yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skill-validator", type=Path)
    args = parser.parse_args()
    checker = jsonschema.FormatChecker()
    validators = {}
    for path in (ROOT / "contracts").glob("*.schema.json"):
        schema = read_json(path)
        jsonschema.Draft202012Validator.check_schema(schema)
        validators[schema["title"]] = jsonschema.Draft202012Validator(schema, format_checker=checker)
    count = 0
    for path in args.evidence.rglob("*.json"):
        for value in records(read_json(path)):
            validators[value["record_type"]].validate(value)
            count += 1
    skills = [*ROOT.glob("methods/*/SKILL.md"), *ROOT.glob("recipes/*/SKILL.md"), *args.evidence.rglob("SKILL.md")]
    for path in skills:
        match = re.match(r"^---\n(.*?)\n---", path.read_text(), flags=re.S)
        if not match:
            raise ValueError(f"Missing skill frontmatter: {path}")
        value = yaml.safe_load(match.group(1))
        if value["name"] != path.parent.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value["name"]):
            raise ValueError(f"Invalid skill name: {path}")
        if len(value["name"]) > 64 or not 1 <= len(value["description"]) <= 1024:
            raise ValueError(f"Invalid skill metadata lengths: {path}")
        if args.skill_validator:
            result = subprocess.run([sys.executable, str(args.skill_validator), str(path.parent)], capture_output=True, text=True, timeout=10)
            if result.returncode:
                raise ValueError(f"Skill Creator validator rejected {path}: {result.stdout} {result.stderr}")
    result = {"status": "pass", "checked_at": utcnow(), "jsonschema_version": importlib.metadata.version("jsonschema"),
              "pyyaml_version": yaml.__version__, "schemas_checked": len(validators), "record_occurrences_checked": count,
              "skills_checked": len(skills), "format_checks_available": sorted(checker.checkers),
              "skill_creator_validator_used": args.skill_validator is not None,
              "coverage": "Independent structural schema validation and YAML/skill packaging; no model-quality inference"}
    write_json(args.output, result, immutable=True)
    print(result)


if __name__ == "__main__":
    main()
