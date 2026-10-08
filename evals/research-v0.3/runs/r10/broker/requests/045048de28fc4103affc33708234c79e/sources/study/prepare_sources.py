"""Bookkeeping only: copy supplied capsule and apply two path-only changes."""
import difflib
import shutil
from common import ROOT, ref, tree_manifest, write


def main():
    original = ROOT / "inputs/materials/capsule-6460826"
    target = ROOT / "work/capsule"
    if target.exists():
        raise SystemExit("Refusing to overwrite an existing source copy")
    shutil.copytree(original, target)
    patches = []
    for dataset in ("wine", "zoo"):
        path = target / "code" / f"{dataset}_sample.py"
        before = path.read_text()
        after = "from pathlib import Path\n" + before.replace(
            f"'/data/{dataset}.txt'", f"Path(__file__).resolve().parents[1] / 'data/{dataset}.txt'")
        assert before != after
        path.write_text(after)
        patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile=f"original/code/{path.name}", tofile=f"adapted/code/{path.name}"))
    (ROOT / "provenance").mkdir(exist_ok=True)
    (ROOT / "provenance/platform.patch").write_text("".join(patches))
    write(ROOT / "provenance/source-manifest.json", {
        "source": "CORE-Bench capsule-6460826",
        "benchmark_commit": "e32a2980e72fe6eb04ee04eb749458f570625663",
        "doi": "https://doi.org/10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5",
        "original": tree_manifest(original.rglob("*")),
        "adapted": tree_manifest(target.rglob("*")),
        "patch": ref(ROOT / "provenance/platform.patch"),
        "changes": ["Only resolve /data/wine.txt and /data/zoo.txt relative to the copied capsule.",
                    "Iris and Zoo hard-coded CS calls intentionally preserved.",
                    "No algorithms, parameters, partitions, printed labels or rounding changed."]})


if __name__ == "__main__":
    main()
