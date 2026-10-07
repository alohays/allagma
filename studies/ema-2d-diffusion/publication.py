"""Publish a disclosed manuscript with exact, recomputable draft provenance.

The frozen study writer remains the source of all scientific content. This
separate reporting step adds the required AI disclosure and relocates links.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from compute import ROOT, execute

DISCLOSURE=("**Disclosure.** This study's code, analysis, figures and manuscript were "
    "machine-generated with OpenAI Codex, using an adaptation of SakanaAI/AI-Scientist's "
    "pinned 2D diffusion template. Measurements come from retained local MPS executions. "
    "No independent scientific peer review is claimed.\n\n")


def reference(path, media="application/json"):
    return {"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "media_type":media,"retention":"retain-with-study"}


def content(source,destination):
    original=source.read_text()
    def relocate(match):
        target=match.group(2)
        if "://" in target or target.startswith("#"):
            return match.group(0)
        actual=(source.parent/target).resolve()
        if not actual.is_relative_to(ROOT) or not actual.is_file():
            raise ValueError("Broken or external local manuscript link: "+target)
        return f"[{match.group(1)}]({os.path.relpath(actual,destination.parent)})"
    relocated=re.sub(r"\[([^\]]*)\]\(([^)]+)\)",relocate,original)
    heading,body=relocated.split("\n\n",1)
    return heading+"\n\n"+DISCLOSURE+body


def publish():
    source=ROOT/"campaigns/ema-v1/analyses/a001/paper/manuscript.md"
    directory=ROOT/"publication"
    directory.mkdir(exist_ok=False)
    destination=directory/"manuscript.md"
    destination.write_text(content(source,destination))
    # Independently repeat the deterministic text transformation before receipt.
    assert destination.read_text()==content(source,destination)
    report={"status":"pass","transformation":"Prepend machine-generation disclosure after title; rebase local Markdown links; preserve all remaining scientific wording and numbers",
            "source":reference(source,"text/markdown"),"output":reference(destination,"text/markdown"),
            "script":reference(Path(__file__).resolve(),"text/x-python"),
            "disclosure":reference(ROOT/"DISCLOSURE.md","text/markdown"),
            "analysis":reference(ROOT/"campaigns/ema-v1/analyses/a001/record.json"),
            "claims":reference(ROOT/"campaigns/ema-v1/analyses/a001/paper/claims.json"),
            "scope":"Publication text transformation and local link verification; scientific recomputation is separately established by campaign audit and independent verification"}
    (directory/"record.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    if sys.argv[1:]==["--worker"]:
        publish()
    elif not sys.argv[1:]:
        raise SystemExit(execute("publication",[str(ROOT/".venv/bin/python"),str(Path(__file__).resolve()),"--worker"],15))
    else:
        raise SystemExit("Use publication.py without arguments for the budgeted publication step")
