#!/usr/bin/env python3
"""Select proportional no-account checks for a Git diff."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from allagma.catalog import Catalog
from check_docs import check_docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD~1")
    args = parser.parse_args()
    diff = subprocess.run(["git", "diff", "--name-only", args.base or "HEAD~1", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if diff.returncode:
        changed = ["allagma/"]
    else:
        changed = diff.stdout.splitlines()
    catalog = Catalog(ROOT)
    modules = [key for key, path in catalog.registry["modules"].items() if any(name.startswith(path + "/") for name in changed)]
    for module in modules:
        catalog.check(module)
    suites = set()
    if any(name.startswith(("allagma/", "contracts/", "tools/", "conformance/", ".github/")) or name in ("registry.json", "release.json") for name in changed):
        suites.update("conformance." + path.stem for path in (ROOT / "conformance").glob("test_*.py"))
    elif any(name.startswith(("adapters/", "recipes/", "examples/", "templates/")) for name in changed):
        suites.update(["conformance.test_modules", "conformance.test_versions", "conformance.test_research"])
    elif modules:
        suites.update(["conformance.test_modules"])
        if any(module.startswith("context/") for module in modules):
            suites.add("conformance.test_improvement")
    result = check_docs()
    if result["errors"]:
        print(result)
        return 1
    print(f"Changed-module checks: {modules}; suites: {sorted(suites)}; documentation links: {result['checked_links']}", flush=True)
    if any(name.startswith(("tools/", ".github/")) for name in changed):
        release_checks = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tools/tests", "-v"], cwd=ROOT)
        if release_checks.returncode:
            return release_checks.returncode
    if suites:
        return subprocess.run([sys.executable, "-m", "unittest", *sorted(suites), "-v"], cwd=ROOT).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
