import shutil
import subprocess
import sys

from allagma.bundles import default_intent
from allagma.catalog import Catalog
from allagma.contracts import validate_record
from allagma.files import AllagmaError, read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class Modules(WorkspaceTest):
    def test_all_module_contracts_and_portable_frontmatter(self):
        self.assertGreaterEqual(len(Catalog(ROOT).check()), 21)

    def test_alternative_requires_explicit_selection(self):
        intent = default_intent("test")
        intent["roles"]["context"] = "context/full-record"
        with self.assertRaises(AllagmaError):
            Catalog(ROOT).resolve(intent)
        intent["allow_experimental"] = True
        self.assertIn("context/full-record", Catalog(ROOT).resolve(intent)["modules"])

    def test_missing_capability_does_not_drop_a_check(self):
        intent = default_intent("test")
        intent["capabilities"] = ["artifact.read", "artifact.write"]
        with self.assertRaisesRegex(AllagmaError, "Missing required capabilities"):
            Catalog(ROOT).resolve(intent)

    def test_incompatible_role_replacement_fails(self):
        intent = default_intent("test")
        intent["roles"]["reviewer"] = "runner/local-process"
        with self.assertRaisesRegex(AllagmaError, "incompatible replacement"):
            Catalog(ROOT).resolve(intent)

    def test_retired_modules_cannot_enter_new_selection(self):
        source = self.source_copy()
        path = source / "methods/allagma-context-active-brief/module.yaml"
        value = read_json(path); value["lifecycle"] = "retired"; write_json(path, value)
        with self.assertRaises(AllagmaError):
            Catalog(source).resolve(default_intent("test"))

    def test_dependency_cycle_and_missing_resources_fail(self):
        source = self.source_copy()
        path = source / "methods/allagma-scope/module.yaml"
        value = read_json(path); value["dependencies"] = ["research/scope"]; write_json(path, value)
        with self.assertRaisesRegex(AllagmaError, "cycle"):
            Catalog(source).resolve(default_intent("test"))
        value["dependencies"] = []; value["resources"] = ["not-present.json"]; write_json(path, value)
        with self.assertRaisesRegex(AllagmaError, "missing resource"):
            Catalog(source).check("research/scope")

    def test_a_contributor_can_add_and_check_one_module(self):
        source = self.source_copy()
        base = source / "methods/allagma-context-active-brief"
        example = source / "methods/allagma-context-example"
        shutil.copytree(base, example)
        skill = example / "SKILL.md"
        skill.write_text(skill.read_text().replace("name: allagma-context-active-brief", "name: allagma-context-example"))
        metadata = read_json(example / "module.yaml")
        metadata["id"] = "context/example"
        metadata["lifecycle"] = "experimental"
        write_json(example / "module.yaml", metadata)
        registry = read_json(source / "registry.json")
        registry["modules"]["context/example"] = "methods/allagma-context-example"
        write_json(source / "registry.json", registry)
        self.assertEqual(Catalog(source).check("context/example"), ["context/example"])
        output = self.work / "context.json"
        subprocess.run([sys.executable, str(example / "select.py"), str(example / "example.json"), str(output)], check=True)
        result = validate_record(read_json(output))
        self.assertEqual(result["record_type"], "ContextRecord")
        self.assertEqual(result["method_id"], "context/example")
