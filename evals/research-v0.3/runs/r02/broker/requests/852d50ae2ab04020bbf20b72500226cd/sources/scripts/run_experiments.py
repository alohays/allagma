"""Execute all supplied sample scripts; transparently retain call-level evidence."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import runpy
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    provenance = json.loads((ROOT / "source/provenance.json").read_text())
    meta = {"format": "culp-execution-v1", "state": "started",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "output": args.output, "python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "device": "cpu",
            "source_revision": provenance["source_revision"],
            "runner_sha256": sha(Path(__file__)), "protocol_sha256": sha(ROOT / "PROTOCOL.md"),
            "thread_environment": {k: os.environ.get(k) for k in (
                "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")},
            "datasets_completed": []}
    write_json(output / "execution.json", meta)
    print("BEGIN CULP execution " + args.output, flush=True)
    start = time.monotonic()
    try:
        import numpy as np
        from sklearn.model_selection import train_test_split
        from threadpoolctl import threadpool_info
        meta["versions"] = {p: importlib.metadata.version(p) for p in (
            "numpy", "scipy", "scikit-learn", "pandas", "networkx", "joblib",
            "threadpoolctl", "python-dateutil", "pytz", "tzdata", "six")}
        meta["threadpools"] = threadpool_info()
        write_json(output / "execution.json", meta)
        code = ROOT / "source/adapted/code"
        sys.path.insert(0, str(code))
        import culp.classifier as classifier
        original_culp = classifier.culp

        for dataset in ("iris", "zoo", "wine"):
            destination = output / dataset
            destination.mkdir()
            calls = []
            print("SCRIPT " + dataset + "_sample.py", flush=True)

            def recorded_culp(train, labels, test, link_predictor, similarity, k, n_jobs=1):
                index = len(calls)
                event = {"call_index": index, "actual_predictor": link_predictor,
                         "similarity": similarity, "k": k, "n_jobs": n_jobs,
                         "state": "started"}
                calls.append(event)
                write_json(destination / "calls.json", calls)
                prediction = original_culp(train, labels, test, link_predictor, similarity, k, n_jobs)
                filename = "call_%02d.npz" % index
                temporary = destination / (filename + ".tmp")
                with temporary.open("wb") as handle:
                    np.savez_compressed(handle, train=np.asarray(train, dtype=float),
                                        train_labels=np.asarray(labels, dtype=np.int64),
                                        test=np.asarray(test, dtype=float),
                                        predictions=np.asarray(prediction, dtype=np.int64))
                temporary.replace(destination / filename)
                event.update(state="completed", arrays=filename,
                             arrays_sha256=sha(destination / filename))
                write_json(destination / "calls.json", calls)
                return prediction

            classifier.culp = recorded_culp
            with (destination / "stdout.txt").open("w") as out, (destination / "stderr.txt").open("w") as err:
                with contextlib.redirect_stdout(Tee(sys.stdout, out)), contextlib.redirect_stderr(Tee(sys.stderr, err)):
                    namespace = runpy.run_path(str(code / (dataset + "_sample.py")), run_name="__main__")
            data = np.asarray(namespace["data"], dtype=float)
            labels = np.asarray(namespace["labels"], dtype=np.int64)
            train_indices, test_indices = train_test_split(np.arange(len(data)), test_size=0.2, random_state=42)
            np.savez_compressed(destination / "dataset.npz", data=data, labels=labels,
                                train_indices=train_indices, test_indices=test_indices,
                                train=np.asarray(namespace["X_train"], dtype=float),
                                test=np.asarray(namespace["X_test"], dtype=float),
                                train_labels=np.asarray(namespace["y_train"], dtype=np.int64),
                                test_labels=np.asarray(namespace["y_test"], dtype=np.int64))
            for index, label in enumerate(("CN", "AA", "RA", "CS")):
                calls[index]["printed_label"] = label
            write_json(destination / "calls.json", calls)
            meta["datasets_completed"].append(dataset)
            write_json(output / "execution.json", meta)
        classifier.culp = original_culp
        meta["state"] = "completed"
        meta["elapsed_seconds"] = time.monotonic() - start
        write_json(output / "execution.json", meta)
        print("END CULP execution " + args.output, flush=True)
    except BaseException:
        meta["state"] = "failed"
        meta["elapsed_seconds"] = time.monotonic() - start
        write_json(output / "execution.json", meta)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
