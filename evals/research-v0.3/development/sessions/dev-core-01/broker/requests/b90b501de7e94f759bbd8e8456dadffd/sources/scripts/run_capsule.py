"""Execute frozen sample scripts and retain predictions without altering inference."""
import contextlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import runpy
import sys

MATERIALS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MATERIALS / "source/adapted/code"))


def clean(value):
    if hasattr(value, "tolist"):
        return clean(value.tolist())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(x) for x in value]
    return value


class Tee(io.StringIO):
    def write(self, value):
        sys.__stdout__.write(value)
        sys.__stdout__.flush()
        return super().write(value)


def main():
    parameters = json.loads(Path(sys.argv[1]).read_text())
    target = Path(sys.argv[2])
    import numpy as np
    import culp.classifier as classifier
    import culp.leg as leg
    import sklearn.model_selection as selection
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "packages": {p: importlib.metadata.version(p) for p in
                                ["numpy", "scipy", "scikit-learn", "networkx", "pandas"]},
                   "threads": {k: os.environ.get(k) for k in
                               ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]}}
    if parameters["mode"] == "pilot":
        predictions = {}
        for predictor in ["CN", "AA", "RA", "CS"]:
            predictions[predictor] = classifier.culp(np.array([[0.0], [10.0]]), np.array([0, 1]),
                np.array([[0.1], [9.9]]), predictor, "manhattan", 1).tolist()
        raw = {"mode": "pilot", "seed": parameters["seed"], "environment": environment,
               "expected": [0, 1], "predictions": predictions,
               "derivation": "Each test node is adjacent only to its nearby training node, which connects to its own class node. Each predictor has one positive same-class score and zero other-class score."}
    else:
        original_culp = classifier.culp
        original_split = selection.train_test_split
        raw = {"mode": "confirmation", "seed": parameters["seed"], "environment": environment, "datasets": {}}
        for dataset in ["iris", "zoo", "wine"]:
            item = {"calls": []}

            def traced_culp(*args, **kwargs):
                original_leg = leg.create_leg
                graphs = []
                def traced_leg(*leg_args, **leg_kwargs):
                    graph = original_leg(*leg_args, **leg_kwargs)
                    graphs.append({"nodes": list(graph.nodes), "edges": list(graph.edges)})
                    return graph
                leg.create_leg = traced_leg
                try:
                    prediction = original_culp(*args, **kwargs)
                finally:
                    leg.create_leg = original_leg
                call = {"actual_predictor": kwargs["link_predictor"], "similarity": kwargs["similarity"],
                        "k": kwargs["k"], "X_train": clean(args[0]), "y_train": clean(args[1]),
                        "X_test": clean(args[2]), "prediction": clean(prediction), "graph": clean(graphs[0])}
                item["calls"].append(call)
                with (target.parent / "prediction-events.jsonl").open("a") as stream:
                    stream.write(json.dumps({"dataset": dataset, **call}) + "\n")
                return prediction

            def traced_split(*args, **kwargs):
                values = original_split(*args, **kwargs)
                train_ids, test_ids = original_split(np.arange(len(args[0])), **kwargs)
                item.update({"data": clean(args[0]), "labels": clean(args[1]),
                             "train_indices": clean(train_ids), "test_indices": clean(test_ids),
                             "split_kwargs": kwargs, "split_X_train": clean(values[0]),
                             "split_X_test": clean(values[1]), "y_train": clean(values[2]), "y_test": clean(values[3])})
                return values

            classifier.culp = traced_culp
            selection.train_test_split = traced_split
            stdout = Tee()
            try:
                with contextlib.redirect_stdout(stdout):
                    runpy.run_path(str(MATERIALS / "source/adapted/code" / f"{dataset}_sample.py"), run_name="__main__")
            finally:
                classifier.culp = original_culp
                selection.train_test_split = original_split
                (target.parent / f"{dataset}-stdout.txt").write_text(stdout.getvalue())
            item["stdout"] = stdout.getvalue()
            raw["datasets"][dataset] = item
            (target.parent / f"{dataset}-raw.json").write_text(json.dumps(item, indent=2) + "\n")
    target.write_text(json.dumps(raw, indent=2) + "\n")


if __name__ == "__main__":
    main()
