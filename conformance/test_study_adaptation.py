"""A changed scientific setting must reach raw data, analysis and claim scope."""
import importlib.util
import math
from pathlib import Path

from allagma import bundles, campaigns
from allagma.files import AllagmaError, inventory, read_json, reference, write_json
from conformance.support import ROOT, WorkspaceTest


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load("prepare_toy", "examples/toy-study/prepare.py").prepare
analyze = load("analyze_toy", "examples/toy-study/domain/analyze.py").analyze


class StudyAdaptation(WorkspaceTest):
    def test_prepare_then_full_campaign_reports_actual_bias(self):
        study = self.work / "new study"
        source_before = inventory(ROOT / "examples/toy-study")
        result = prepare(study, bias=0.5, study_id="half-bias")
        self.assertEqual(result["executed_attempts"], 0)
        self.assertFalse((study / "campaigns").exists())
        self.assertEqual(bundles.verify_study(study)["hosts"], ["generic"])
        self.assertEqual(read_json(study / "adaptation.json")["license"], "MIT")
        campaigns.start_campaign(study, "prospective")
        self.assertEqual(campaigns.run_campaign(study, "prospective")["execution_status"], "ready")
        campaigns.analyze_campaign(study, "prospective", analysis_id="a001")
        adir = study / "campaigns/prospective/analyses/a001"
        summary = read_json(adir / "outputs/summary.json")
        self.assertEqual(summary["bias"], 0.5)
        manifest = read_json(adir / "raw-manifest.json")
        differences = []
        for ref in manifest["raw"]:
            raw = read_json(study / ref["path"])
            self.assertEqual(raw["bias"], 0.5)
            mean = sum(raw["samples"]) / len(raw["samples"])
            differences.append((mean + 0.5) ** 2 - mean ** 2)
        self.assertAlmostEqual(summary["difference"], math.fsum(differences) / 24)
        self.assertTrue(all("additive bias 0.5" in claim["scope"] for claim in read_json(adir / "paper/claims.json")))
        self.assertIn("sample mean plus 0.5", (adir / "paper/manuscript.md").read_text())
        self.assertEqual(campaigns.audit_campaign(study, "prospective")["verdict"], "pass")
        self.assertEqual(inventory(ROOT / "examples/toy-study"), source_before)

    def test_invalid_inputs_and_existing_destination_are_preserved(self):
        for bias in (math.nan, math.inf, 1.01, True):
            with self.subTest(bias=bias), self.assertRaises(AllagmaError):
                prepare(self.work / "absent", bias=bias)
        with self.assertRaises(AllagmaError):
            prepare(self.work / "absent", study_id="../escape")
        self.assertFalse((self.work / "absent").exists())
        write_json(self.work / "existing/user.json", {"keep": True})
        before = inventory(self.work)
        with self.assertRaises(AllagmaError):
            prepare(self.work / "existing")
        self.assertEqual(inventory(self.work), before)
        (self.work / "alias").symlink_to(self.work / "missing")
        with self.assertRaises(AllagmaError):
            prepare(self.work / "alias")
        self.assertFalse((self.work / "missing").exists())

    def test_long_precision_bias_survives_the_full_reporting_path(self):
        bias = 0.123456789
        study = self.work / "precise"
        prepare(study, bias=bias)
        self.assertIn(str(bias), read_json(study / "brief.json")["question"])
        protocol = read_json(study / "protocol.json")
        self.assertIn(f"Adding {bias} ", protocol["hypothesis"])
        self.assertIn(str(bias ** 2), protocol["hypothesis"])
        campaigns.start_campaign(study, "precision")
        self.assertEqual(campaigns.run_campaign(study, "precision")["execution_status"], "ready")
        campaigns.analyze_campaign(study, "precision", analysis_id="a001")
        adir = study / "campaigns/precision/analyses/a001"
        self.assertEqual(read_json(adir / "outputs/summary.json")["bias"], bias)
        for claim in read_json(adir / "paper/claims.json"):
            reported = claim["scope"].split("additive bias ")[1]
            self.assertEqual(float(reported), bias)
        self.assertIn(f"sample mean plus {bias} ", (adir / "paper/manuscript.md").read_text())
        self.assertEqual(campaigns.audit_campaign(study, "precision")["verdict"], "pass")

    def test_boundary_biases_preserve_the_plan_without_execution(self):
        for bias in (-1.0, 0.0, 1.0):
            with self.subTest(bias=bias):
                study = self.work / str(bias)
                prepare(study, bias=bias)
                runs = read_json(study / "protocol.json")["runs"]
                self.assertEqual(len(runs), 26)
                self.assertEqual(sum(run["split"] == "pilot" for run in runs), 2)
                self.assertEqual({run["input"]["bias"] for run in runs}, {bias})
                self.assertEqual({run["input"]["n"] for run in runs}, {64})
                self.assertFalse((study / "campaigns").exists())
                budget = bundles.verify_study(study)["effective_configuration"]["budget"]
                self.assertEqual(budget["max_attempts"], 28)
                self.assertEqual(budget["max_seconds"], 60)

    def test_analysis_refuses_mixed_settings_instead_of_mislabeling(self):
        for mismatch in ("bias", "n"):
            with self.subTest(mismatch=mismatch):
                root = self.work / mismatch
                refs = []
                for seed in (100, 101):
                    raw = {"seed": seed, "n": 2, "bias": 0.5, "target": 0,
                           "samples": [-1, 1], "control": "random"}
                    if seed == 101:
                        raw[mismatch] = 0.25 if mismatch == "bias" else 4
                        if mismatch == "n":
                            raw["samples"] = [-1, 1, -1, 1]
                    write_json(root / f"{seed}.json", raw)
                    refs.append(reference(root, root / f"{seed}.json"))
                with self.assertRaisesRegex(ValueError, "one common bias and sample count"):
                    analyze(root, {"raw": refs}, root / "outputs")
                self.assertFalse((root / "outputs").exists())
