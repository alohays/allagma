"""Controller-only deterministic scores; scientific dependencies are optional.

Run in the isolated evaluator environment, never inside a candidate workspace.
Numerical checks are separate from substantive protocol/report review.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Dict
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def confined(root, name):
    root=Path(root).resolve()
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("Evidence paths must be confined relative paths")
    path = root/name
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and root in p.parents):
        raise ValueError("Symlink evidence is not accepted")
    resolved = path.resolve()
    if root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"Missing or unconfined evidence: {name}")
    return resolved


def original_core_score(workspace, submission):
    import numpy as np
    from scipy.stats import t
    source = ROOT/"studies/core-culp/reference"
    original = read(source/"controller-task.json")
    reported = read(confined(workspace, submission["report"]))
    tree = ast.parse((source/"upstream-evaluations.py").read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name=="eval_result_json")
    namespace = {"np": np, "math": math, "t": t, "Dict": Dict}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "original-core-bench-scorer", "exec"), namespace)
    result = namespace["eval_result_json"](original["results"], copy.deepcopy(reported))
    return {"name": "original CORE-Bench score", "unchanged_upstream_function": True,
        "scorer_sha256": hashlib.sha256((source/"upstream-evaluations.py").read_bytes()).hexdigest(),
        "correct": result["correct_written_answers"]+result["correct_vision_answers"],
        "total": result["total_written_questions"]+result["total_vision_questions"], **result}


def npz(root, name):
    import numpy as np
    path = confined(root, name)
    if path.stat().st_size > 536870912:
        raise ValueError("Array archive exceeds the input-size limit")
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) > 10000 or sum(info.file_size for info in archive.infolist()) > 1073741824:
            raise ValueError("Expanded archive exceeds the control limit")
    with np.load(path, allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    if sum(value.nbytes for value in arrays.values()) > 1073741824:
        raise ValueError("Expanded arrays exceed 1 GiB")
    if any(value.dtype.hasobject or not np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("Arrays must be finite and contain no Python objects")
    return arrays


def sw1(x, y):
    import numpy as np
    from scipy.stats import wasserstein_distance
    angles = np.random.default_rng(7321).uniform(0, 2*np.pi, 128)
    return float(np.mean([wasserstein_distance(x[:,0]*np.cos(a)+x[:,1]*np.sin(a),
                                               y[:,0]*np.cos(a)+y[:,1]*np.sin(a)) for a in angles]))


def replay_checkpoint(weights, variant, noise, device):
    import torch
    trusted=ROOT/"studies/ema-2d-diffusion/domain/science.py"
    specification=importlib.util.spec_from_file_location("trusted_ema_reference",trusted)
    science=importlib.util.module_from_spec(specification);specification.loader.exec_module(science)
    torch.set_num_threads(1)
    if device not in ("cpu","mps"):raise ValueError("Unsupported saved-sample backend")
    if device=="mps":
        if not torch.backends.mps.is_available():raise ValueError("MPS replay unavailable")
        torch.mps.set_per_process_memory_fraction(.20)
    model=science.Denoiser().to(device)
    state={name[len(variant)+2:]:torch.tensor(value,device=device,dtype=torch.float32)
           for name,value in weights.items() if name.startswith(variant+"__")}
    model.load_state_dict(state,strict=True);model.eval()
    coefficients={name:torch.tensor(value,device=device,dtype=torch.float32)
                  for name,value in science.schedule().items()}
    return science.draw(model,torch.tensor(noise,device=device,dtype=torch.float32),coefficients)


def score_ema(workspace, measurements):
    import numpy as np
    expected = {(dataset, seed, updates, schedule) for dataset, seeds in
        [("moons", range(4001,4005)), ("gmm8", range(5001,5005))]
        for seed in seeds for updates in (5000,10000) for schedule in ("constant","cosine")}
    seen, checks, errors, groups = set(), [], [], {}
    for run in measurements["runs"]:
        key = (run["dataset"],run["seed"],run["updates"],run["schedule"])
        if key not in expected or key in seen or run["phase"]!="confirmation":
            errors.append(f"Unexpected, duplicated or non-confirmation cell: {key}")
            continue
        seen.add(key)
        arrays, weights = npz(workspace,run["arrays"]), npz(workspace,run["weights"])
        group=groups.setdefault((run["dataset"],run["seed"]),[])
        group.append((run,arrays))
        if arrays["heldout"].shape!=(2048,2) or arrays["generation_noise"].shape!=(100,2048,2):
            raise ValueError("EMA held-out/sample-noise shape mismatch")
        for variant in ("raw","ema099","ema0999"):
            samples = np.asarray(arrays[variant],dtype=np.float64)
            if samples.shape!=(2048,2): raise ValueError("EMA sample shape mismatch")
            value = sw1(samples, np.asarray(arrays["heldout"],dtype=np.float64))
            passed = abs(value-run["metrics"][variant]["sw1"]) <= 1e-8
            checks.append({"cell":key,"variant":variant,"metric":"sw1","value":value,"pass":bool(passed)})
            if not any(name.startswith(variant+"__") for name in weights):
                errors.append(f"Missing {variant} checkpoint in {key}")
            else:
                replay=replay_checkpoint(weights,variant,arrays["generation_noise"],run["device"])
                maximum=float(np.max(np.abs(replay-samples)))
                checks.append({"cell":key,"variant":variant,"metric":"checkpoint_sample_replay",
                    "pass":bool(np.allclose(replay,samples,rtol=1e-4,atol=1e-5)),"maximum_absolute_error":maximum})
            if run["dataset"]=="gmm8":
                theta = 2*np.pi*np.arange(8)/8
                centers = 2*np.column_stack([np.cos(theta),np.sin(theta)])
                distance = np.linalg.norm(samples[:,None]-centers[None],axis=2)
                nearest = distance.argmin(axis=1)
                valid = distance.min(axis=1)<=.45
                counts = np.bincount(nearest[valid],minlength=8)
                metrics = run["metrics"][variant]
                passed = (counts.tolist()==metrics["mode_counts"] and int((counts>=21).sum())==metrics["covered_modes"]
                          and abs(float(valid.mean())-metrics["inlier_fraction"])<=1e-8)
                checks.append({"cell":key,"variant":variant,"metric":"mode_coverage","pass":bool(passed)})
    if seen!=expected: errors.append(f"Missing {len(expected-seen)} required cells")
    for key,group in groups.items():
        first_run,first_arrays=group[0]
        for run,arrays in group[1:]:
            if any(not np.array_equal(arrays[name],first_arrays[name]) for name in ("heldout","generation_noise")):
                errors.append(f"Unmatched held-out/sampling inputs for {key}")
            if any(run.get(name)!=first_run.get(name) or not isinstance(run.get(name),str) or len(run[name])<64
                   for name in ("initial_weights_sha256","training_prefix_5000_sha256")):
                errors.append(f"Unmatched or missing initialization/training-prefix provenance for {key}")
    return {"name":"independent EMA endpoint metrics","correct":sum(c["pass"] for c in checks),
            "total":240,"checks":checks,"errors":errors,"required_cells":len(expected),"observed_cells":len(seen),
            "automatic_controls_pass":not errors,
            "scope":"Saved-array metrics, paired evaluation inputs and all checkpoint sample replays using the trusted prior denoiser/sampler. Training duration/history and scientific inference still require separate review."}


def accuracy_and_loss(logits, labels, indices):
    import numpy as np
    selected = logits[indices].astype(np.float64)
    truth = labels[indices]
    shifted = selected-selected.max(axis=1,keepdims=True)
    loss = np.log(np.exp(shifted).sum(axis=1))-shifted[np.arange(len(truth)),truth]
    return float((selected.argmax(axis=1)==truth).mean()),float(loss.mean())


def score_grok(workspace, measurements):
    import numpy as np
    expected={(seed,decay) for seed in range(1001,1005) for decay in (0,1)}
    seen,checks,errors,groups=set(),[],[],{}
    for run in measurements["runs"]:
        key=(run["seed"],run["weight_decay"])
        if key not in expected or key in seen or run["phase"]!="confirmation" or run["updates"]!=100000:
            errors.append(f"Unexpected, duplicated or incomplete trajectory: {key}");continue
        seen.add(key)
        arrays=npz(workspace,run["arrays"]);weights=npz(workspace,run["weights"])
        groups.setdefault(run["seed"],[]).append((run,arrays))
        pairs,labels=arrays["pairs"],arrays["labels"]
        canonical=np.array([(a,b) for a in range(97) for b in range(97)])
        if not np.array_equal(pairs,canonical) or not np.array_equal(labels,pairs.sum(axis=1)%97):
            raise ValueError("Modular-addition pairs/labels differ from the task")
        train,test=arrays["train_indices"],arrays["test_indices"]
        if any(not np.issubdtype(arrays[name].dtype,np.integer) for name in
               ("pairs","labels","train_indices","test_indices","predictions")):
            raise ValueError("Pairs, labels, indices and predictions must be integer arrays")
        if not (len(train)==2822 and len(test)==6587 and len(set(train)&set(test))==0 and
                set(train)|set(test)==set(range(9409))): raise ValueError("Invalid train/test partition")
        logits=arrays["logits"]
        if logits.shape!=(9409,97) or not np.array_equal(arrays["predictions"],logits.argmax(axis=1)):
            raise ValueError("Prediction/logit mismatch")
        for split,indices in (("train",train),("test",test)):
            acc,loss=accuracy_and_loss(logits,labels,indices)
            for metric,value,tolerance in (("accuracy",acc,1e-7),("loss",loss,5e-5+1e-6*abs(loss))):
                name=split+"_"+metric
                checks.append({"cell":key,"metric":name,"value":value,"pass":bool(abs(value-run["metrics"][name])<=tolerance)})
        a,b=weights["input_weight"],weights["output_weight"]
        if a.shape!=(128,194) or b.shape!=(97,128): raise ValueError("MLP checkpoint dimensions differ")
        # Bias-free one-hot MLP, independently reconstructed without candidate code.
        hidden=np.maximum(a[:,pairs[:,0]].T+a[:,97+pairs[:,1]].T,0)
        reconstructed=hidden@b.T
        disagreement=reconstructed.argmax(axis=1)!=arrays["predictions"]
        scale=1e-4+1e-4*np.abs(logits)
        errors_within_tolerance=np.abs(reconstructed-logits)<=scale
        # Float32 MPS/CPU reductions can swap a numerical tie; preserve exact
        # agreement counts and require every logit to match within tolerance.
        checks.append({"cell":key,"metric":"checkpoint_predictions", "pass":bool(errors_within_tolerance.all()),
                       "exact_prediction_agreement":int((~disagreement).sum()),"total_predictions":9409,
                       "maximum_logit_error":float(np.abs(reconstructed-logits).max()),
                       "tolerance":"abs <= 1e-4 + 1e-4*abs(retained_logit)"})
        curve=read(confined(workspace,run["curve"]))
        steps=[row["step"] for row in curve]
        if steps[0]!=0 or steps[-1]!=100000 or any(not 0<v-u<=100 for u,v in zip(steps,steps[1:])):
            errors.append(f"Incomplete or unordered learning curve: {key}")
    if seen!=expected:errors.append(f"Missing {len(expected-seen)} required trajectories")
    for seed,group in groups.items():
        if len(group)!=2:continue
        first,a=group[0];second,b=group[1]
        if not np.array_equal(a["train_indices"],b["train_indices"]) or not np.array_equal(a["test_indices"],b["test_indices"]):
            errors.append(f"Unmatched partitions across weight-decay conditions for seed {seed}")
        initial=first.get("initial_weights_sha256")
        if not isinstance(initial,str) or len(initial)<64 or second.get("initial_weights_sha256")!=initial:
            errors.append(f"Unmatched or missing initial-state provenance for seed {seed}")
    return {"name":"independent modular-addition endpoints/checkpoints","correct":sum(c["pass"] for c in checks),
            "total":40,"checks":checks,"errors":errors,"required_trajectories":8,"observed_trajectories":len(seen),
            "automatic_controls_pass":not errors,
            "scope":"Labels, partition coverage, endpoint metrics, final checkpoint predictions and curve coverage. Training history and scientific interpretation require separate review."}


def score(workspace):
    workspace=Path(workspace).resolve()
    submission=read(confined(workspace,"submission.json"))
    artifacts={}
    for key in ("manuscript","review","artifact_manifest"):
        path=confined(workspace,submission[key]);artifacts[key]={"path":submission[key],"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    task=submission["task_id"]
    if task=="core-culp": numerical=original_core_score(workspace,submission)
    else:
        measurements=read(confined(workspace,submission["measurements"]))
        if measurements["format"]!="research-measurements-v1" or measurements["task_id"]!=task:
            raise ValueError("Unsupported measurement format or task identity")
        numerical={"ema-schedule":score_ema,"modular-addition":score_grok}[task](workspace,measurements)
    return {"task_id":task,"claimed_execution_status":submission["execution_status"],"numerical":numerical,
        "artifacts":artifacts,"substantive_review":"pending","overall_completion":"unproven",
        "scorer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("workspace",type=Path);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit("Use a new score path; prior scores are immutable")
    try:result=score(args.workspace)
    except (ValueError,KeyError,OSError,TypeError,IndexError,zipfile.BadZipFile) as exc:result={"status":"unscorable","error":str(exc),"overall_completion":"unproven"}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({key:result[key] for key in ("task_id","status","error","overall_completion") if key in result}))
