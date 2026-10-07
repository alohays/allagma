"""Bounded feasibility pilot, not confirmation or an original-paper replication.

Study-owned implementation of modular addition with a small two-layer MLP.
Inspired by the experimental question of Power et al., arXiv:2201.02177.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import torch


def hash_array(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--steps", type=int, default=10000)
    parser.add_argument("--weight-decay", type=float, required=True)
    parser.add_argument("--device", choices=["cpu", "mps"], default="mps")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = Path(os.environ["ALLAGMA_RESOURCE_RECEIPT"])
    if not receipt.is_file():
        raise RuntimeError("A resource reservation is required")
    if args.output.exists():
        raise RuntimeError("Pilot outputs are append-only")
    torch.set_num_threads(1)
    torch.manual_seed(args.seed)
    if args.device == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("Requested MPS unavailable")
        torch.mps.set_per_process_memory_fraction(.20)
    started = time.monotonic()
    p, width = 97, 128
    pairs = np.array([(a, b) for a in range(p) for b in range(p)], dtype=np.int64)
    labels = pairs.sum(axis=1) % p
    order = np.random.default_rng(args.seed).permutation(len(pairs))
    train_idx, test_idx = order[:int(.30*len(pairs))], order[int(.30*len(pairs)):]
    assert set(train_idx).isdisjoint(test_idx)
    features = torch.nn.functional.one_hot(torch.tensor(pairs), num_classes=p).reshape(-1, 2*p).float().to(args.device)
    y = torch.tensor(labels, device=args.device)
    train = torch.tensor(train_idx, device=args.device)
    test = torch.tensor(test_idx, device=args.device)
    x_train, y_train = features[train], y[train]
    model = torch.nn.Sequential(torch.nn.Linear(2*p, width, bias=False), torch.nn.ReLU(),
                                torch.nn.Linear(width, p, bias=False)).to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9, .98),
                                  weight_decay=args.weight_decay, foreach=args.device=="mps")
    history = []
    for step in range(args.steps+1):
        if step:
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(model(x_train), y_train)
            loss.backward()
            optimizer.step()
        if step % 100 == 0 or step == args.steps:
            with torch.no_grad():
                logits = model(features)
                row = {"step": step,
                    "train_accuracy": float((logits[train].argmax(1)==y[train]).float().mean().cpu()),
                    "test_accuracy": float((logits[test].argmax(1)==y[test]).float().mean().cpu()),
                    "train_loss": float(torch.nn.functional.cross_entropy(logits[train], y[train]).cpu()),
                    "test_loss": float(torch.nn.functional.cross_entropy(logits[test], y[test]).cpu())}
                history.append(row)
            if step % 1000 == 0:
                print(json.dumps({**row, "elapsed_seconds": time.monotonic()-started}), flush=True)
    if args.device == "mps":
        torch.mps.synchronize()
    outcome = {"kind": "development-only", "seed": args.seed, "steps": args.steps,
        "weight_decay": args.weight_decay, "device": args.device, "modulus": p,
        "architecture": "concatenated one-hot inputs -> bias-free Linear(194,128) -> ReLU -> bias-free Linear(128,97)",
        "parameter_count": sum(x.numel() for x in model.parameters()), "train_fraction": .30,
        "train_indices_sha256": hash_array(train_idx), "test_indices_sha256": hash_array(test_idx),
        "train_indices": train_idx.tolist(), "test_indices": test_idx.tolist(),
        "history": history, "elapsed_seconds": time.monotonic()-started,
        "python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__,
        "mps_driver_bytes": torch.mps.driver_allocated_memory() if args.device=="mps" else None,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "resource_receipt": str(receipt)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(args.output), "elapsed_seconds": outcome["elapsed_seconds"], "last": history[-1]}))


if __name__ == "__main__":
    main()
