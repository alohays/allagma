#!/usr/bin/env python3
"""Run the exact helper shipped with a source tree or locked bundle."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from allagma.cli import main

raise SystemExit(main())
