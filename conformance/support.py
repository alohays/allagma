from pathlib import Path
import shutil
import tempfile
import unittest

from allagma.bundles import source_inventory
from allagma.files import write_bytes

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="allagma-conformance-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def source_copy(self, name="source"):
        source = self.work / name
        for path in source_inventory(ROOT):
            write_bytes(source / path, (ROOT / path).read_bytes())
        shutil.copytree(ROOT / "examples/toy-study", source / "examples/toy-study",
                        ignore=shutil.ignore_patterns("__pycache__", "evidence"))
        return source
