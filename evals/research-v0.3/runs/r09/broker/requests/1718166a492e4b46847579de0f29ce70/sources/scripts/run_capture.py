"""Execute an unchanged scientific script while retaining its actual call outputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=["iris", "zoo", "wine"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    events = (out / "events.jsonl").open("x", buffering=1)

    def event(kind, **kwargs):
        events.write(json.dumps({"event": kind, "utc": datetime.now(timezone.utc).isoformat(), **kwargs}) + "\n")
        events.flush()
        os.fsync(events.fileno())

    code = ROOT / "source/adapted/code"
    script = code / (args.dataset + "_sample.py")
    revision = json.loads((ROOT / "evidence/source-revision.json").read_text())
    metadata = {"dataset": args.dataset, "script": str(script.relative_to(ROOT)),
                "script_sha256": digest(script), "source_revision": revision["adapted_tree_sha256"],
                "protocol_sha256": digest(ROOT / "PROTOCOL.md"), "argv": sys.argv,
                "execution": "runpy.run_path with return-preserving capture wrappers", "status": "started",
                "calls": []}
    (out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
    event("started", dataset=args.dataset, source_revision=metadata["source_revision"])

    class Tee:
        def __init__(self, terminal, file):
            self.terminal, self.file = terminal, file

        def write(self, data):
            self.terminal.write(data)
            self.file.write(data)
            self.flush()
            return len(data)

        def flush(self):
            self.terminal.flush()
            self.file.flush()

    original_stdout, original_stderr = sys.stdout, sys.stderr
    stdout_file = (out / "stdout.txt").open("x", buffering=1)
    stderr_file = (out / "stderr.txt").open("x", buffering=1)
    sys.stdout, sys.stderr = Tee(sys.stdout, stdout_file), Tee(sys.stderr, stderr_file)
    try:
        # Imports deliberately follow durable markers so an import-time interruption is visible.
        import numpy as np
        sys.path.insert(0, str(code))
        from culp import classifier, leg
        original_culp, original_leg = classifier.culp, leg.create_leg
        graphs = []

        def capture_leg(*positional, **keywords):
            graph = original_leg(*positional, **keywords)
            graphs.append(graph)
            return graph

        def capture_culp(train, labels, test, link_predictor, similarity, k, n_jobs=1):
            caller = inspect.currentframe().f_back.f_globals
            display = caller["lp"]
            number = len(metadata["calls"]) + 1
            event("call_started", call=number, display_predictor=display, actual_predictor=link_predictor)
            before = len(graphs)
            prediction = original_culp(train, labels, test, link_predictor, similarity, k, n_jobs)
            if len(graphs) != before + 1:
                raise RuntimeError("Expected one captured graph per classifier call")
            graph = graphs[-1]
            arrays_name = f"call-{number:02d}.npz"
            arrays_path = out / arrays_name
            np.savez_compressed(arrays_path,
                train=np.asarray(train, dtype=float), test=np.asarray(test, dtype=float),
                train_labels=np.asarray(labels, dtype=np.int64),
                test_labels=np.asarray(caller["y_test"], dtype=np.int64),
                prediction=np.asarray(prediction, dtype=np.int64),
                graph_edges=np.asarray(list(graph.edges()), dtype=np.int64),
                raw_data=np.asarray(caller["data"], dtype=float),
                raw_labels=np.asarray(caller["labels"], dtype=np.int64))
            record = {"call": number, "display_predictor": display, "actual_predictor": link_predictor,
                      "similarity": similarity, "k": k, "n_jobs": n_jobs,
                      "arrays": str(arrays_path.relative_to(ROOT)), "arrays_sha256": digest(arrays_path),
                      "train_shape": list(train.shape), "test_shape": list(test.shape),
                      "original_train_labels_dtype": str(labels.dtype),
                      "original_test_labels_dtype": str(caller["y_test"].dtype),
                      "graph_nodes": graph.number_of_nodes(), "graph_edges": graph.number_of_edges()}
            metadata["calls"].append(record)
            (out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
            event("call_saved", call=number, arrays=record["arrays"], arrays_sha256=record["arrays_sha256"])
            return prediction

        leg.create_leg, classifier.culp = capture_leg, capture_culp
        event("imports_complete")
        runpy.run_path(str(script), run_name="__main__")
        if len(metadata["calls"]) != 4:
            raise RuntimeError("Expected all four original predictor iterations")
        metadata["status"] = "completed"
        event("completed", calls=len(metadata["calls"]))
    except BaseException as error:
        metadata["status"] = "failed"
        metadata["error"] = repr(error)
        traceback.print_exc()
        event("failed", error=repr(error))
        raise
    finally:
        (out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
        sys.stdout, sys.stderr = original_stdout, original_stderr
        stdout_file.close()
        stderr_file.close()
        events.close()


if __name__ == "__main__":
    main()
