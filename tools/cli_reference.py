#!/usr/bin/env python3
"""Print Markdown command help directly from the public parser."""
from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from allagma.cli import parser

root = parser()
print("Generated from the current CLI parser during the site build. See the [CLI overview](/allagma/reference/cli/) for behavior and costs.\n")
print("## Allagma\n\n```text\n" + root.format_help().strip() + "\n```\n")
for action in root._actions:
    if isinstance(action, argparse._SubParsersAction):
        for name, subparser in action.choices.items():
            print(f"## {name}\n\n```text\n{subparser.format_help().strip()}\n```\n")
