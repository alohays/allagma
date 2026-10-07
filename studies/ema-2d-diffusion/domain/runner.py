"""One trajectory, two checkpoints and matched raw/EMA samples on MPS."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import torch
from science import Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage


def digest_array(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def main():
    inputs, destination = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(inputs.read_text())
    begin = time.monotonic()
    study = next(p for p in inputs.resolve().parents if (p/".allagma/lock.yaml").is_file())
    receipt_path = Path(os.environ["ALLAGMA_STUDY_COMPUTE_RECEIPT"])
    if receipt_path.parent != study/"evidence/compute" or json.loads(receipt_path.read_text())["status"] != "running":
        raise RuntimeError("A live study-compute reservation is required")
    if cfg["phase"] == "confirmation":
        freeze = json.loads((study/"confirmation-freeze.json").read_text())
        protocol_path = study/"campaigns/ema-v1/protocol.json"
        if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != freeze["protocol_sha256"]:
            raise RuntimeError("Confirmation freeze differs from the campaign protocol")
    torch.set_num_threads(1)
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS is required; silently falling back to CPU is forbidden")
    if os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1":
        raise RuntimeError("Disable implicit MPS fallback")
    seed = cfg["seed"]
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed+100_000)
    model = Denoiser().to("mps")
    emas = {"ema099": copy.deepcopy(model), "ema0999": copy.deepcopy(model)}
    for ema in emas.values():
        ema.requires_grad_(False)
    parameters = list(model.parameters())
    initial_hash = digest_array(torch.nn.utils.parameters_to_vector(parameters).detach().cpu().numpy())
    coefficients_np = schedule()
    coefficients = {key: torch.tensor(value, dtype=torch.float32, device="mps") for key, value in coefficients_np.items()}
    train = dataset(cfg["dataset"], cfg["train_size"], seed+1_000_000)
    heldout = dataset(cfg["dataset"], cfg["eval_size"], seed+2_000_000)
    indices = rng.integers(0, len(train), (10000, 256))
    noise_np = rng.normal(size=(10000, 256, 2)).astype(np.float32)
    timesteps_np = rng.integers(0, 100, (10000, 256))
    noisy_np = (coefficients_np["sqrt_abar"][timesteps_np, None]*train[indices]
                +coefficients_np["sqrt_one_minus"][timesteps_np, None]*noise_np).astype(np.float32)
    noisy = torch.tensor(noisy_np, device="mps")
    noise = torch.tensor(noise_np, device="mps")
    timesteps = torch.tensor(timesteps_np, dtype=torch.float32, device="mps")
    evaluation_noise_np = np.random.default_rng(seed+3_000_000).normal(size=(100, cfg["eval_size"], 2)).astype(np.float32)
    evaluation_noise = torch.tensor(evaluation_noise_np, device="mps")
    optimizer = torch.optim.AdamW(parameters, lr=3e-4, weight_decay=.01, foreach=True)
    checkpoints, loss_trace, weight_arrays = [], [], {}
    torch.mps.synchronize()
    train_started = time.monotonic()
    evaluation_seconds = 0.
    for step in range(1, 10001):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(model(noisy[step-1], timesteps[step-1]), noise[step-1])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, .5, foreach=False)
        # Same cosine decay as reference; never restart at the 5k checkpoint.
        optimizer.param_groups[0]["lr"] = 3e-4*.5*(1+np.cos(np.pi*(step-1)/10000))
        optimizer.step()
        with torch.no_grad():
            for name, decay in (("ema099", .99), ("ema0999", .999)):
                torch._foreach_lerp_(list(emas[name].parameters()), parameters, 1-decay)
        if step == 1 or step % 500 == 0:
            value = float(loss.detach().cpu())
            if not np.isfinite(value):
                raise RuntimeError("Nonfinite training loss")
            loss_trace.append({"step": step, "noise_mse": value})
            print(json.dumps({"step": step, "loss": value, "elapsed_seconds": time.monotonic()-begin}), flush=True)
        if cfg.get("fault") == "interrupt" and step == 100:
            (destination.parent/"partial-training.json").write_text(json.dumps({"updates": step, "seed": seed, "scientific_evidence": False}))
            (destination.parent/"interrupt-ready").write_text("Actual 100-update trajectory; qualification interruption only.\n")
            while True:
                time.sleep(.1)
        if step not in (5000, 10000):
            continue
        torch.mps.synchronize()
        evaluation_start = time.monotonic()
        variants = {}
        for name, candidate in {"raw": model, **emas}.items():
            candidate.eval()
            state = {key: value.detach().cpu().numpy().copy() for key, value in candidate.state_dict().items()}
            vector = np.concatenate([state[key].ravel() for key in sorted(state)])
            for key, value in state.items():
                weight_arrays[f"step{step}__{name}__{key}"] = value
            sample = draw(candidate, evaluation_noise, coefficients)
            if not np.isfinite(sample).all():
                raise RuntimeError("Nonfinite generated samples")
            variants[name] = {"samples": sample.tolist(), "weights_sha256": digest_array(vector),
                              "sw1": sliced_wasserstein(sample, heldout)}
            if cfg["dataset"] == "gmm8":
                variants[name]["mode_coverage"] = mode_coverage(sample)
        torch.mps.synchronize()
        evaluation_seconds += time.monotonic()-evaluation_start
        checkpoints.append({"step": step, "variants": variants})
    torch.mps.synchronize()
    train_seconds = time.monotonic()-train_started-evaluation_seconds
    weights_path = destination.parent/"weights.npz"
    np.savez_compressed(weights_path, **weight_arrays)
    raw = {"format": "ema-2d-v1", "input": cfg, "seed": seed, "dataset": cfg["dataset"],
           "parameter_count": sum(p.numel() for p in parameters), "updates": 10000,
           "batch_size": 256, "diffusion_steps": 100, "ema_update_count": 10000,
           "ema_initialization": "copy of initial raw weights; constant decay after every optimizer update",
           "initial_weights_sha256": initial_hash, "train_sha256": digest_array(train),
           "training_noise_sha256": digest_array(noise_np), "heldout_sha256": digest_array(heldout),
           "evaluation_noise_sha256": digest_array(evaluation_noise_np), "heldout": heldout.tolist(),
           "checkpoint_file": {"name": weights_path.name, "sha256": hashlib.sha256(weights_path.read_bytes()).hexdigest()},
           "checkpoints": checkpoints, "loss_trace": loss_trace,
           "timing": {"training_seconds": train_seconds, "evaluation_seconds": evaluation_seconds,
                      "total_seconds": time.monotonic()-begin},
           "environment": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__,
                           "device": "mps", "fallback": False, "platform": platform.platform(),
                           "mps_peak_allocated_bytes": torch.mps.driver_allocated_memory()}}
    destination.write_text(json.dumps(raw, sort_keys=True, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
