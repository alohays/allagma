"""Execute the actual capsule scripts, observing inputs/graphs without changing results."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import inspect
from pathlib import Path
import runpy
import sys
import traceback
from common import ROOT, digest, read, ref, verify_refs, write


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
    parser.add_argument("--dataset", required=True, choices=["iris", "zoo", "wine"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / "work/capsule/code" / f"{args.dataset}_sample.py"
    source_manifest = read(ROOT / "provenance/source-manifest.json")
    verify_refs(source_manifest["original"] + source_manifest["adapted"])
    write(out / "started.json", {"dataset": args.dataset, "started_at": datetime.now(timezone.utc).isoformat(),
          "argv": sys.argv, "source": ref(source), "source_revision": digest(ROOT / "provenance/source-manifest.json"),
          "protocol": ref(ROOT / "campaigns/culp-v1/protocol.json"), "status": "running"})
    # Persist identity before the potentially slow scientific imports.
    import numpy as np
    sys.path.insert(0, str(source.parent))
    import culp.classifier as classifier
    import culp.leg as leg
    original_culp = classifier.culp
    original_leg = leg.create_leg
    calls = []
    last_graph = None

    def observed_leg(*a, **kw):
        nonlocal last_graph
        last_graph = original_leg(*a, **kw)
        return last_graph

    def observed_culp(train, labels, test, link_predictor, similarity, k, n_jobs=1):
        caller = inspect.currentframe().f_back.f_globals
        displayed = caller["lp"]
        prediction = original_culp(train, labels, test, link_predictor, similarity, k, n_jobs)
        index = len(calls)
        arrays_path = out / f"call-{index:02d}.npz"
        n = len(train)
        m = len(test)
        c = len(np.unique(labels))
        np.savez_compressed(arrays_path,
            X_train=np.asarray(train, dtype=float), X_test=np.asarray(test, dtype=float),
            y_train=np.asarray(labels, dtype=np.int64), y_test=np.asarray(caller["y_test"], dtype=np.int64),
            prediction=np.asarray(prediction, dtype=np.int64),
            full_data=np.asarray(caller["data"], dtype=float),
            full_labels=np.asarray(caller["labels"], dtype=np.int64),
            graph_edges=np.asarray(sorted((min(int(a), int(b)), max(int(a), int(b)))
                for a, b in last_graph.edges()), dtype=np.int64),
            node_counts=np.asarray([n, m, c], dtype=np.int64))
        calls.append({"call_index": index, "dataset": args.dataset,
            "printed_label": displayed, "executed_predictor": link_predictor,
            "similarity": similarity, "k": k, "n_jobs": n_jobs,
            "arrays": ref(arrays_path), "source": ref(source)})
        write(out / "calls.json", calls)
        return prediction

    classifier.culp = observed_culp
    leg.create_leg = observed_leg
    with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
        try:
            with redirect_stdout(Tee(sys.stdout, stdout)), redirect_stderr(Tee(sys.stderr, stderr)):
                runpy.run_path(str(source), run_name="__main__")
        except BaseException:
            traceback.print_exc(file=stderr)
            raise
    assert len(calls) == 4
    write(out / "completion.json", {"status": "completed", "dataset": args.dataset,
          "ended_at": datetime.now(timezone.utc).isoformat(), "calls": 4,
          "stdout": ref(out / "stdout.txt"), "stderr": ref(out / "stderr.txt"),
          "call_manifest": ref(out / "calls.json")})


if __name__ == "__main__":
    main()
