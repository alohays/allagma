from allagma.demo import compare_context
from allagma.files import read_json
from conformance.support import ROOT, WorkspaceTest


class Improvement(WorkspaceTest):
    def test_costlier_alternative_is_rejected_and_preserved(self):
        output = self.work / "rejected"
        result = compare_context(ROOT, output, baseline_id="context/active-brief", candidate_id="context/full-record")
        self.assertEqual(result["outcome"], "reject")
        self.assertTrue((output / "package/methods/allagma-context-full-record/SKILL.md").exists())
        self.assertTrue((output / "package/allagma/composition.py").exists())
        self.assertEqual(result["measurements"]["context/full-record"]["required_recall"], 1)

    def test_environment_failure_is_unevaluated_not_rejected(self):
        source = self.source_copy()
        path = source / "methods/allagma-context-active-brief/select.py"
        path.write_text('raise RuntimeError("Unavailable fixture backend")\n')
        output = self.work / "unevaluated"
        result = compare_context(source, output)
        self.assertEqual(result["outcome"], "not evaluated")
        self.assertNotIn("context/active-brief", result["measurements"])
        trace = read_json(output / "execution-trace.json")
        self.assertNotEqual(trace[-1]["exit_code"], 0)
        self.assertIn("Unavailable fixture backend", trace[-1]["stderr"])
