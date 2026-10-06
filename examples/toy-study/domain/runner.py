"""Study-owned synthetic observations, with explicit fault fixtures."""
import json
from pathlib import Path
import random
import sys
import time


def run(config):
    n = config["n"]
    if not isinstance(n, int) or n < 2 or n > 10000:
        raise ValueError("n must be an integer between 2 and 10000")
    if config.get("fault") == "failure":
        raise RuntimeError("Deliberate runner failure for retry evidence")
    if config.get("fault") == "interrupt":
        Path("interrupt-ready").write_text("Checkpoint reached before observations\n")
        time.sleep(60)
    control = config.get("control", "random")
    rng = random.Random(config["seed"])
    if control == "zero":
        samples = [0.0] * n
    elif control == "balanced":
        if n % 2:
            raise ValueError("Balanced control needs even n")
        samples = [-1.0, 1.0] * (n // 2)
    elif control == "random":
        samples = [float(2 * rng.randrange(2) - 1) for _ in range(n)]
    else:
        raise ValueError("Unknown control")
    mean = sum(samples) / n
    return {"schema_version": "0.2", "seed": config["seed"], "n": n,
            "control": control, "samples": samples, "target": 0.0,
            "bias": config["bias"], "mean_estimate": mean,
            "biased_estimate": mean + config["bias"]}


if __name__ == "__main__":
    config = json.loads(Path(sys.argv[1]).read_text())
    value = run(config)
    with Path(sys.argv[2]).open("x") as output:
        json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)
        output.write("\n")
