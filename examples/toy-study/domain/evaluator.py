"""Independently check generator identity, arithmetic and known-answer controls."""
import json
import math
from pathlib import Path
import random
import sys


def evaluate(config, raw):
    samples = raw["samples"]
    n = config["n"]
    control = config.get("control", "random")
    if control == "random":
        rng = random.Random(config["seed"])
        expected = [2 * rng.randrange(2) - 1 for _ in range(n)]
    elif control == "balanced":
        expected = [-1, 1] * (n // 2)
    else:
        expected = [0] * n
    mean = math.fsum(samples) / n
    valid = (len(samples) == n and samples == expected and raw["seed"] == config["seed"]
             and raw["target"] == 0.0 and raw["bias"] == config["bias"]
             and raw["n"] == n and raw["control"] == control
             and raw["mean_estimate"] == mean and raw["biased_estimate"] == mean + config["bias"]
             and all(isinstance(x, (int, float)) and math.isfinite(x) for x in samples))
    if control in ("zero", "balanced"):
        valid = valid and mean == 0.0 and raw["biased_estimate"] ** 2 == config["bias"] ** 2
    return {"valid": valid, "coverage": "Seeded samples, estimator arithmetic, known-answer controls",
            "mean_squared_error": mean ** 2, "biased_squared_error": (mean + config["bias"]) ** 2,
            "unit": "squared synthetic outcome", "scientific_hypothesis_validated": False}


if __name__ == "__main__":
    config, raw = [json.loads(Path(path).read_text()) for path in sys.argv[1:3]]
    with Path(sys.argv[3]).open("x") as output:
        json.dump(evaluate(config, raw), output, sort_keys=True, indent=2, allow_nan=False)
        output.write("\n")
