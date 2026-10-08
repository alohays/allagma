#!/usr/bin/env python3
"""Generate reproducible local narration with the separately licensed Kokoro model.

Optional media-only dependencies live outside the Python core. Download the
declared model/voices explicitly; this tool verifies hashes before loading them.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import time
import wave

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(model, voices, output):
    import numpy as np
    import onnxruntime as rt
    from kokoro_onnx import Kokoro
    config = json.loads((ROOT / "media/source/narration-model.json").read_text())
    if sha(model) != config["model_sha256"] or sha(voices) != config["voices_sha256"]:
        raise ValueError("Narration model or voice digest differs from the reviewed source")
    if importlib.metadata.version("kokoro-onnx") != config["engine_version"]:
        raise ValueError("Use the pinned narration environment")
    output.mkdir(parents=True, exist_ok=False)
    script_file = ROOT / "media/source/scenes.json"
    script = json.loads(script_file.read_text())
    options = rt.SessionOptions()
    options.intra_op_num_threads, options.inter_op_num_threads = 2, 1
    session = rt.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
    synth = Kokoro.from_session(session, str(voices))
    clips = []
    started = time.monotonic()
    for scene in script["scenes"]:
        for number, sentence in enumerate(re.split(r'(?<=[.!?])\s+', scene["narration"])):
            audio, rate = synth.create(sentence, voice=config["voice"], speed=config["speed"], lang=config["language"])
            if not len(audio) or not np.isfinite(audio).all() or float(np.max(np.abs(audio))) >= 1:
                raise ValueError("Invalid or clipped synthesized audio")
            target = output / f"{scene['id']}-{number:02d}.wav"
            with wave.open(str(target), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(rate)
                stream.writeframes((audio * 32767).astype("<i2").tobytes())
            clips.append({"scene": scene["id"], "text": sentence, "path": target.name,
                          "seconds": len(audio) / rate, "sample_rate": rate, "sha256": sha(target)})
        print(f"Generated {scene['id']}", flush=True)
    receipt = {"format": "allagma-narration-v1", "source": config, "script_sha256": sha(script_file),
               "wall_seconds": time.monotonic() - started, "clips": clips,
               "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}}
    (output / "narration.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.model, args.voices, args.output)
