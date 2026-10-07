"""Study-owned factorial EMA feasibility pilot; see ../REFERENCE.md."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import torch
from science import Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage


def digest(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["moons", "gmm8"], default="gmm8")
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--updates", type=int, choices=[5000, 10000], required=True)
    parser.add_argument("--schedule", choices=["constant", "cosine"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = Path(os.environ["ALLAGMA_RESOURCE_RECEIPT"])
    if not receipt.is_file() or args.output.exists():
        raise RuntimeError("Require live reservation and a new output file")
    torch.set_num_threads(1)
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable")
    torch.mps.set_per_process_memory_fraction(.20)
    torch.manual_seed(args.seed)
    started = time.monotonic()
    model = Denoiser().to("mps")
    emas = {key: copy.deepcopy(model).requires_grad_(False) for key in ("ema099", "ema0999")}
    initial = digest(torch.nn.utils.parameters_to_vector(model.parameters()).detach().cpu().numpy())
    coefficients_np = schedule()
    coefficients = {key: torch.tensor(value, device="mps", dtype=torch.float32) for key, value in coefficients_np.items()}
    train = dataset(args.dataset, 100000, args.seed+1_000_000)
    heldout = dataset(args.dataset, 2048, args.seed+2_000_000)
    rng = np.random.default_rng(args.seed+100_000)
    # Always draw the same maximum-length stream before selecting a prefix.
    indices = rng.integers(0, len(train), (10000, 256))
    noise_np = rng.normal(size=(10000, 256, 2)).astype(np.float32)
    timesteps_np = rng.integers(0, 100, (10000, 256))
    noisy_np = (coefficients_np["sqrt_abar"][timesteps_np, None]*train[indices]
                +coefficients_np["sqrt_one_minus"][timesteps_np, None]*noise_np).astype(np.float32)
    noisy = torch.tensor(noisy_np, device="mps")
    noise = torch.tensor(noise_np, device="mps")
    timesteps = torch.tensor(timesteps_np, dtype=torch.float32, device="mps")
    sample_noise = np.random.default_rng(args.seed+3_000_000).normal(size=(100, 2048, 2)).astype(np.float32)
    sample_t = torch.tensor(sample_noise, device="mps")
    parameters = list(model.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=3e-4, weight_decay=.01, foreach=True)
    losses = []
    for step in range(1, args.updates+1):
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(model(noisy[step-1], timesteps[step-1]), noise[step-1])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, .5, foreach=False)
        lr = 3e-4 if args.schedule=="constant" else 3e-4*.5*(1+np.cos(np.pi*(step-1)/args.updates))
        optimizer.param_groups[0]["lr"] = lr
        optimizer.step()
        with torch.no_grad():
            for key, decay in (("ema099", .99), ("ema0999", .999)):
                torch._foreach_lerp_(list(emas[key].parameters()), parameters, 1-decay)
        if step == 1 or step % 1000 == 0:
            row = {"step": step, "loss": float(loss.detach().cpu()), "lr": float(lr)}
            if not np.isfinite(row["loss"]):
                raise RuntimeError("Nonfinite training loss")
            losses.append(row)
            print(json.dumps(row), flush=True)
    torch.mps.synchronize()
    training_elapsed = time.monotonic()-started
    results, weights = {}, {}
    for name, candidate in {"raw": model, **emas}.items():
        samples = draw(candidate, sample_t, coefficients)
        results[name] = {"sw1": sliced_wasserstein(samples, heldout), "samples": samples.tolist()}
        if args.dataset == "gmm8":
            results[name]["mode_coverage"] = mode_coverage(samples)
        for key, value in candidate.state_dict().items():
            weights[name+"__"+key] = value.detach().cpu().numpy().copy()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    weights_path = args.output.with_suffix(".npz")
    np.savez_compressed(weights_path, **weights)
    outcome = {"kind": "development-only", "dataset": args.dataset, "seed": args.seed,
        "updates": args.updates, "schedule": args.schedule, "initial_weights_sha256": initial,
        "training_noise_prefix_sha256": digest(noise_np[:args.updates]),
        "first5000_noise_sha256": digest(noise_np[:5000]), "heldout_sha256": digest(heldout),
        "sampling_noise_sha256": digest(sample_noise), "heldout": heldout.tolist(),
        "variants": results, "loss_trace": losses,
        "training_seconds": training_elapsed, "total_seconds": time.monotonic()-started,
        "weights_file": weights_path.name, "weights_sha256": hashlib.sha256(weights_path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "science_sha256": hashlib.sha256(Path(__file__).with_name("science.py").read_bytes()).hexdigest(),
        "torch": torch.__version__, "numpy": np.__version__, "device": "mps",
        "mps_driver_bytes": torch.mps.driver_allocated_memory(), "resource_receipt": str(receipt)}
    args.output.write_text(json.dumps(outcome, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({"output": str(args.output), "total_seconds": outcome["total_seconds"],
                      "sw1": {key: value["sw1"] for key, value in results.items()}}), flush=True)


if __name__ == "__main__":
    main()
