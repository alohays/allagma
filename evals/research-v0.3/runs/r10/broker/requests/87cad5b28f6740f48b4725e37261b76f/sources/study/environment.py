"""Run through setup broker to record the installed, offline environment."""
import importlib.metadata
import platform
import sys
from common import ROOT, digest, write

packages = sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())
write(ROOT / "provenance/environment.json", {
    "python": sys.version, "executable": sys.executable,
    "platform": platform.platform(), "machine": platform.machine(),
    "packages": dict(packages), "device": "cpu", "network": False,
    "wheels": [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)}
               for p in sorted((ROOT / "inputs/materials/wheels").glob("*.whl"))]})
(ROOT / "requirements-lock.txt").write_text("".join(f"{name}=={version}\n" for name, version in packages
    if name.lower() not in ("pip", "setuptools")))
print("Recorded Python, platform, installed versions and offline wheel hashes.")
