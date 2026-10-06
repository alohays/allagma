#!/usr/bin/env python3
"""Check local Markdown links in maintained repository documentation."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


def check_docs():
    errors, checked = [], 0
    directories = [ROOT / "docs", ROOT / "examples/toy-study", ROOT / "conformance"]
    files = set(ROOT.glob("*.md"))
    for directory in directories:
        files.update(directory.rglob("*.md"))
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        if "evidence" in relative.parts or (relative.parts[:2] == ("docs", "specification") and path.name != "README.md"):
            continue
        body = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", body):
            target = target.split("#", 1)[0]
            if not target or urlparse(target).scheme:
                continue
            checked += 1
            if not (path.parent / unquote(target)).exists():
                errors.append(f"{relative}: missing {target}")
    return {"checked_links": checked, "errors": errors}


if __name__ == "__main__":
    result = check_docs()
    print(result)
    raise SystemExit(bool(result["errors"]))
