"""Independent pilot checks; scope explicitly excludes unavailable predictions."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import wasserstein_distance

ROOT = Path(__file__).resolve().parents[3]
outputs = []
directions = np.random.default_rng(7321).uniform(0, 2*np.pi, 128)
directions = np.column_stack((np.cos(directions), np.sin(directions)))
checks = []
for path in sorted((ROOT/"studies/ema-schedule/development/evidence").glob("*.json")):
    record = json.loads(path.read_text())
    assert record["kind"] == "development-only"
    assert hashlib.sha256(path.with_suffix(".npz").read_bytes()).hexdigest() == record["weights_sha256"]
    reference = np.asarray(record["heldout"], dtype=np.float64)
    assert reference.shape == (2048, 2)
    for name, item in record["variants"].items():
        samples = np.asarray(item["samples"], dtype=np.float64)
        sw1 = float(np.mean([wasserstein_distance(samples@v, reference@v) for v in directions]))
        assert abs(sw1-item["sw1"]) < 1e-12
        assert np.isfinite(samples).all()
        if record["dataset"] == "gmm8":
            theta = 2*np.pi*np.arange(8)/8
            centers = 2*np.column_stack((np.cos(theta), np.sin(theta)))
            distance = np.linalg.norm(samples[:, None]-centers[None], axis=2)
            nearest = distance.argmin(axis=1)
            counts = np.bincount(nearest[distance.min(axis=1)<=.45], minlength=8)
            assert counts.tolist() == item["mode_coverage"]["counts"]
            assert int((counts>=21).sum()) == item["mode_coverage"]["covered"]
        checks.append({"file": path.name, "variant": name, "sw1": sw1})
    for row in record["loss_trace"]:
        expected = .0003 if record["schedule"]=="constant" else .0003*.5*(1+np.cos(np.pi*(row["step"]-1)/record["updates"]))
        assert abs(row["lr"]-expected) < 1e-15
    outputs.append(record)
for dataset in ["gmm8", "moons"]:
    matching = [r for r in outputs if r["dataset"] == dataset]
    for field in ["initial_weights_sha256", "first5000_noise_sha256", "heldout_sha256", "sampling_noise_sha256"]:
        assert len({r[field] for r in matching}) == 1, (dataset, field)
grok = []
for path in sorted((ROOT/"studies/modular-addition/development").glob("*.json")):
    value = json.loads(path.read_text())
    assert value["kind"] == "development-only"
    a, b = set(value["train_indices"]), set(value["test_indices"])
    assert len(a) == 2822 and len(b) == 6587 and not a & b and a | b == set(range(97*97))
    assert value["history"][0]["step"] == 0 and value["history"][-1]["step"] == value["steps"]
    assert all(0 <= r["train_accuracy"] <= 1 and 0 <= r["test_accuracy"] <= 1 for r in value["history"])
    assert all(np.isfinite(r["train_loss"]) and np.isfinite(r["test_loss"]) for r in value["history"])
    grok.append({"file": path.name, "seed": value["seed"], "steps": value["steps"],
                 "weight_decay": value["weight_decay"], "last": value["history"][-1],
                 "train_indices_sha256": value["train_indices_sha256"], "test_indices_sha256": value["test_indices_sha256"]})
for seed in [17, 29]:
    matches = [v for v in grok if v["seed"] == seed and v["steps"] == 100000]
    assert len(matches) == 2 and {v["weight_decay"] for v in matches} == {0, 1}
    for key in ["train_indices_sha256", "test_indices_sha256"]:
        assert len({v[key] for v in matches}) == 1
report = {"status": "pass", "ema_variant_checks": checks, "grok_history_and_partition_checks": grok,
          "limitations": ["Grokking pilots retain aggregate curves, not endpoint predictions or checkpoints; accuracy is not independently recomputed here.", "No final confirmation or agent comparison run is included."]}
path = ROOT/"evals/research-v0.3/development/pilot-verification.json"
if path.exists():
    raise RuntimeError("Use a new receipt for a later verification")
path.write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps({"status": "pass", "ema_variant_checks": len(checks), "grok_pilots": len(grok)}))
