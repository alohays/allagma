import copy
import math
from pathlib import Path

from allagma.composition import select_context
from allagma.configuration import DEFAULT_BUDGET, resolve_configuration
from allagma.contracts import validate, validate_record
from allagma.files import (AllagmaError, confined, read_json, reference, verify_reference,
                          write_json, write_text)
from conformance.support import ROOT, WorkspaceTest


class Contracts(WorkspaceTest):
    def test_records_are_closed_and_versioned(self):
        fixture = read_json(ROOT / "methods/allagma-context-active-brief/example.json")
        valid = select_context(fixture, "context/active-brief")
        validate_record(valid)
        for change in ({"schema_version": "1.0"}, {"unreviewed_extra": 1}, {"required": "question"}):
            with self.subTest(change=change), self.assertRaises(AllagmaError):
                validate_record({**valid, **change})
        del valid["selected"]
        with self.assertRaises(AllagmaError):
            validate_record(valid)

    def test_schema_rejects_unknown_validation_keywords(self):
        with self.assertRaises(AllagmaError):
            validate({}, {"type": "object", "unsupportedConstraint": True})

    def test_numbers_are_finite_and_booleans_are_not_integers(self):
        for value in (True, math.nan, math.inf):
            with self.subTest(value=value), self.assertRaises(AllagmaError):
                validate(value, {"type": "number"})
        validate(1.0, {"type": "integer"})
        validate(10 ** 500, {"type": "integer"})
        validate([0, False], {"type": "array", "uniqueItems": True})
        with self.assertRaises(AllagmaError):
            validate(False, {"const": 0})

    def test_json_reader_rejects_duplicate_and_nonfinite_values(self):
        path = self.work / "bad.json"
        for text in ('{"x":1,"x":2}', '{"x":NaN}'):
            write_text(path, text)
            with self.assertRaises(AllagmaError):
                read_json(path)

    def test_references_detect_changes_and_confine_paths(self):
        path = self.work / "raw.json"
        write_json(path, {"value": 1})
        ref = reference(self.work, path)
        self.assertEqual(verify_reference(self.work, ref), path.resolve())
        write_json(path, {"value": 2})
        with self.assertRaises(AllagmaError):
            verify_reference(self.work, ref)
        for name in ("../escape", "/tmp/escape", "x/../../escape", "x\\escape"):
            with self.subTest(name=name), self.assertRaises(AllagmaError):
                confined(self.work, name)

    def test_symlinks_cannot_be_bundled_or_used_as_evidence(self):
        (self.work / "link").symlink_to(self.work / "missing")
        with self.assertRaises(AllagmaError):
            confined(self.work, "link/child")

    def test_immutable_artifact_cannot_be_replaced(self):
        path = self.work / "raw.json"
        write_json(path, {"n": 1}, immutable=True)
        write_json(path, {"n": 1}, immutable=True)
        with self.assertRaises(AllagmaError):
            write_json(path, {"n": 2}, immutable=True)

    def test_configuration_precedence_and_origins(self):
        layers = [("module", {"budget": DEFAULT_BUDGET, "nested": {"x": 0, "y": 1}}),
                  ("recipe", {"nested": {"x": 1}}), ("profile", {"nested": {"x": 2}}),
                  ("override", {"nested": {"x": 3}}), ("request", {"nested": {"x": 4}})]
        config, origins = resolve_configuration(layers, ["artifact.read"])
        self.assertEqual(config["nested"], {"x": 4, "y": 1})
        self.assertEqual(origins["nested.x"], "request")
        self.assertEqual(config["budget"]["money_usd"], "unset")

    def test_configuration_cannot_expand_authorization_or_store_secrets(self):
        for patch in ({"capabilities": ["paid.api"]}, {"model": "pinned"}, {"api_key": "example-not-real"}, {"budget": {"max_attempts": True}}):
            with self.subTest(patch=patch), self.assertRaises(AllagmaError):
                resolve_configuration([("defaults", {"budget": DEFAULT_BUDGET}), ("request", patch)], ["artifact.read"])

    def test_required_context_survives_small_budget_and_missing_fields_fail(self):
        case = read_json(ROOT / "methods/allagma-context-active-brief/example.json")
        case["max_chars"] = 1
        selected = select_context(case, "context/active-brief")
        self.assertTrue(set(case["required"]) <= selected["content"].keys())
        self.assertTrue(selected["limitations"])
        del case["records"]["constraints"]
        with self.assertRaises(AllagmaError):
            select_context(case, "context/active-brief")
