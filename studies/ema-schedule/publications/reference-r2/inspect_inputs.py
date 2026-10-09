#!/usr/bin/env python3
"""Inspect selected non-pickle artifacts inside the unchanged scientific broker."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import socket
import struct
import zipfile


def inspect_npz(path):
    arrays = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            if not member.filename.endswith(".npy"):
                raise ValueError("Unexpected non-array file in the retained NPZ")
            with archive.open(member) as stream:
                if stream.read(6) != b"\x93NUMPY":
                    raise ValueError("Missing NumPy array header")
                major, minor = stream.read(2)
                length = struct.unpack("<H" if major == 1 else "<I", stream.read(2 if major == 1 else 4))[0]
                if length > 65536:
                    raise ValueError("Unreasonably large array header")
                header = ast.literal_eval(stream.read(length).decode("latin1"))
                if "O" in str(header["descr"]):
                    raise ValueError("Object/pickle arrays are not accepted")
                arrays.append({"name": member.filename, "shape": list(header["shape"]), "dtype": header["descr"]})
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size,
            "arrays": arrays}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-canary", type=Path, required=True)
    args = parser.parse_args()
    selected = json.loads(Path("inputs/REFERENCE-INPUTS.json").read_text())
    inspected = {}
    for relative, metadata in selected["files"].items():
        path = Path("inputs/reference-assets") / relative
        inspected[relative] = inspect_npz(path)
        if inspected[relative]["sha256"] != metadata["sha256"]:
            raise ValueError("Protected asset differs from the acquisition manifest")
    checks = {"network_denied": False, "input_write_denied": False, "cache_read_denied": False}
    try:
        with socket.socket() as connection:
            connection.settimeout(.5)
            connection.connect(("127.0.0.1", 9))
    except PermissionError:
        checks["network_denied"] = True
    except OSError:
        pass  # A refused connection is not evidence of network isolation.
    try:
        with Path("inputs/BRIEF.md").open("r+b"):
            pass  # Open only: never modify protected content during the probe.
    except PermissionError:
        checks["input_write_denied"] = True
    try:
        with args.cache_canary.open("rb"):
            pass
    except PermissionError:
        checks["cache_read_denied"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    record = {"format": "allagma-reference-input-inspection-v1", "status": "pass" if all(checks.values()) else "fail",
              "checks": checks, "assets": inspected,
              "scope": "Real pinned NPZ headers and hashes; actual broker restrictions; no training or model inference"}
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": record["status"], "checks": checks, "assets": len(inspected)}))
    raise SystemExit(0 if record["status"] == "pass" else 1)
