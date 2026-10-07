"""Execute unchanged science via runpy; observe returns without replacing functions.

The profile hook retains classifier inputs/predictions and graph/score evidence.
It never writes into any source frame or alters the returned values.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import runpy
import sys
from common import ROOT, now, ref, write_json


class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, value):
        for s in self.streams:
            s.write(value)
            s.flush()
        return len(value)
    def flush(self):
        for s in self.streams:
            s.flush()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=["iris", "zoo", "wine"], required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--source", default="source/adapted")
    args = p.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    source = (ROOT / args.source).resolve()
    script = source / "code" / (args.dataset + "_sample.py")
    write_json(out / "started.json", {"at": now(), "argv": sys.argv, "pid": os.getpid(),
                                     "dataset": args.dataset, "script": ref(script)})
    import numpy as np
    from sklearn.model_selection import train_test_split
    calls = []
    latest = {}
    culpdir = source / "code" / "culp"
    filenames = {str(culpdir / x) for x in ["classifier.py", "leg.py", "link_predictors.py"]}

    def observe(frame, event, returned):
        if event != "return" or frame.f_code.co_filename not in filenames:
            return
        name, local = frame.f_code.co_name, frame.f_locals
        if name == "create_leg" and returned is not None:
            latest["edges"] = np.array(list(returned.edges()), dtype=np.int64)
            latest["nodes"] = np.array(list(returned.nodes()), dtype=np.int64)
        elif "similarities" in local and returned is not None:
            latest["scores"] = np.array(local["similarities"], copy=True)
        elif name == "culp" and returned is not None:
            caller = frame.f_back.f_locals
            index = len(calls)
            f = out / f"call-{index:02d}.npz"
            np.savez(f, prediction=np.asarray(returned, dtype=np.int64),
                     y_test=np.asarray(caller["y_test"], dtype=np.int64),
                     X_train=np.asarray(local["train"], dtype=float),
                     y_train=np.asarray(local["labels"], dtype=np.int64),
                     X_test=np.asarray(local["test"], dtype=float),
                     edges=latest["edges"], nodes=latest["nodes"], scores=latest["scores"])
            call = {"index": index, "printed_label": caller["lp"],
                    "actual_predictor": local["link_predictor"], "k": local["k"],
                    "similarity": local["similarity"], "n_jobs": local["n_jobs"],
                    "arrays": ref(f)}
            calls.append(call)
            with (out / "calls.jsonl").open("a") as handle:
                handle.write(json.dumps(call, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    sys.path.insert(0, str(source / "code"))
    with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
        with contextlib.redirect_stdout(Tee(sys.stdout, stdout)), contextlib.redirect_stderr(Tee(sys.stderr, stderr)):
            sys.setprofile(observe)
            try:
                namespace = runpy.run_path(str(script), run_name="__main__")
            finally:
                sys.setprofile(None)
    n = len(namespace["labels"])
    train_i, test_i = train_test_split(np.arange(n), test_size=0.2, random_state=42)
    np.savez(out / "dataset.npz", data=np.asarray(namespace["data"], dtype=float),
             labels=np.asarray(namespace["labels"], dtype=np.int64),
             train_indices=train_i, test_indices=test_i,
             X_train=np.asarray(namespace["X_train"], dtype=float),
             X_test=np.asarray(namespace["X_test"], dtype=float),
             y_train=np.asarray(namespace["y_train"], dtype=np.int64),
             y_test=np.asarray(namespace["y_test"], dtype=np.int64))
    write_json(out / "raw.json", {"dataset": args.dataset, "seed": 42, "test_size": 0.2,
        "script": ref(script), "calls": calls, "dataset_arrays": ref(out / "dataset.npz"),
        "stdout": ref(out / "stdout.txt"), "stderr": ref(out / "stderr.txt"),
        "finished_at": now(), "phase": "confirmation", "device": "cpu"})


if __name__ == "__main__":
    main()
