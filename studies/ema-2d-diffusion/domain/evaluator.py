"""Independent structural/metric checks; no claimed independent peer review."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import wasserstein_distance
from science import dataset, mode_coverage, projections


def main():
    inputs, raw_path, destination = map(Path, sys.argv[1:])
    cfg, raw = json.loads(inputs.read_text()), json.loads(raw_path.read_text())
    checks = {}
    checks["exact_input"] = cfg == raw["input"]
    checks["native_mps"] = raw["environment"]["device"] == "mps" and raw["environment"]["fallback"] is False
    checks["trajectory_complete"] = (raw["updates"], raw["batch_size"], raw["diffusion_steps"], raw["parameter_count"], raw["ema_update_count"]) == (10000, 256, 100, 296450, 10000)
    checks["checkpoints"] = [c["step"] for c in raw["checkpoints"]] == [5000, 10000]
    expected = dataset(cfg["dataset"], cfg["eval_size"], cfg["seed"]+2_000_000)
    heldout = np.asarray(raw["heldout"], dtype=np.float32)
    checks["heldout_reseeded"] = np.array_equal(expected, heldout)
    checks["heldout_hash"] = hashlib.sha256(heldout.tobytes()).hexdigest() == raw["heldout_sha256"]
    checks["checkpoint_digest"] = hashlib.sha256((raw_path.parent/raw["checkpoint_file"]["name"]).read_bytes()).hexdigest() == raw["checkpoint_file"]["sha256"]
    directions = projections()
    for checkpoint in raw["checkpoints"]:
        checks[f"variants_{checkpoint['step']}"] = set(checkpoint["variants"]) == {"raw", "ema099", "ema0999"}
        for name, value in checkpoint["variants"].items():
            sample = np.asarray(value["samples"], dtype=np.float64)
            sw = np.mean([wasserstein_distance(sample@d, heldout.astype(np.float64)@d) for d in directions])
            prefix = f"{checkpoint['step']}_{name}"
            checks[prefix+"_finite_shape"] = sample.shape == (cfg["eval_size"], 2) and bool(np.isfinite(sample).all())
            checks[prefix+"_scipy_w1"] = bool(np.isclose(sw, value["sw1"], rtol=1e-12, atol=1e-12))
            if cfg["dataset"] == "gmm8":
                checks[prefix+"_coverage"] = mode_coverage(sample) == value["mode_coverage"]
    destination.write_text(json.dumps({"valid": all(checks.values()), "checks": checks,
        "scope": "Seeded holdout reconstruction, complete paired trajectories, finite output, checkpoint hash and SciPy projected W1 cross-check; no retraining or scientific peer review"}, sort_keys=True, indent=2)+"\n")
    if not all(checks.values()):
        raise RuntimeError(str({k:v for k,v in checks.items() if not v}))


if __name__ == "__main__":
    main()
