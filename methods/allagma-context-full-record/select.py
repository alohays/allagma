from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from allagma.composition import context_main

if __name__ == "__main__":
    context_main("context/full-record")
