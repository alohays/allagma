"""Recompute paired confirmation metrics and deterministic result figures."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t
from science import dataset, sliced_wasserstein, mode_coverage


def load_checked(study, reference):
    path = study/reference["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
        raise ValueError("Evidence digest mismatch: "+reference["path"])
    return json.loads(path.read_text())


def interval(values):
    values = np.asarray(values, dtype=np.float64)
    n = len(values)
    if n < 2:
        raise ValueError("At least two independent seeds needed per dataset")
    mean = float(values.mean())
    se = float(values.std(ddof=1)/np.sqrt(n))
    margin = float(t.ppf(.975, n-1)*se)
    return {"n": n, "mean": mean, "se": se, "ci95_t": [mean-margin, mean+margin]}


def write_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(study, manifest_path, destination):
    manifest = json.loads(manifest_path.read_text())
    raws = [load_checked(study, ref) for ref in manifest["raw"]]
    raws.sort(key=lambda r:(r["dataset"], r["seed"]))
    destination.mkdir(parents=True, exist_ok=False)
    rows, paired, comparisons, controls = [], [], [], []
    for raw in raws:
        if raw["input"]["phase"] != "confirmation" or "fault" in raw["input"]:
            raise ValueError("Pilot or interrupted attempt entered confirmation analysis")
        heldout = np.asarray(raw["heldout"])
        second = dataset(raw["dataset"], len(heldout), raw["seed"]+4_000_000)
        controls.append({"dataset":raw["dataset"], "seed":raw["seed"], "holdout_vs_independent_holdout_sw1":sliced_wasserstein(heldout,second)})
        for checkpoint in raw["checkpoints"]:
            scores = {}
            for name, variant in checkpoint["variants"].items():
                sample = np.asarray(variant["samples"])
                sw = sliced_wasserstein(sample, heldout)
                coverage = mode_coverage(sample) if raw["dataset"] == "gmm8" else None
                row = {"dataset":raw["dataset"], "seed":raw["seed"], "updates":checkpoint["step"],
                       "weights":name, "sw1":sw, "covered_modes":coverage["covered"] if coverage else "",
                       "inlier_fraction":coverage["inlier_fraction"] if coverage else "",
                       "mode_total_variation":coverage["total_variation"] if coverage else ""}
                rows.append(row)
                scores[name] = row
            for name in ("ema099", "ema0999"):
                paired.append({"dataset":raw["dataset"], "seed":raw["seed"], "updates":checkpoint["step"],
                    "ema":name, "sw1_difference":scores[name]["sw1"]-scores["raw"]["sw1"],
                    "mode_difference":scores[name]["covered_modes"]-scores["raw"]["covered_modes"] if coverage else "",
                    "inlier_difference":scores[name]["inlier_fraction"]-scores["raw"]["inlier_fraction"] if coverage else ""})
    for name in ("moons", "gmm8"):
        seeds = [r["seed"] for r in raws if r["dataset"] == name]
        if len(seeds) != len(set(seeds)):
            raise ValueError("Duplicate confirmation seed")
        for step in (5000,10000):
            for ema in ("ema099","ema0999"):
                subset = [p for p in paired if p["dataset"] == name and p["updates"] == step and p["ema"] == ema]
                values = np.array([p["sw1_difference"] for p in subset])
                info = interval(values)
                permutations = [abs(float((values*np.array(signs)).mean())) for signs in itertools.product((-1,1),repeat=len(values))]
                loo = [float(np.delete(values,i).mean()) for i in range(len(values))]
                comparisons.append({"dataset":name,"updates":step,"ema":ema,**info,
                    "differences":values.tolist(),"seeds":[p["seed"] for p in subset],
                    "improved_seeds":int((values<0).sum()),
                    "sign_flip_p_two_sided":float(np.mean(np.array(permutations)>=abs(info["mean"])-1e-14)),
                    "leave_one_out_mean_range":[min(loo),max(loo)],
                    "mode_difference":interval([p["mode_difference"] for p in subset]) if name=="gmm8" else None,
                    "inlier_difference":interval([p["inlier_difference"] for p in subset]) if name=="gmm8" else None})
    summary = {"format":"ema-analysis-v1","trajectories":len(raws), "per_dataset_seeds":{name:sorted(r["seed"] for r in raws if r["dataset"]==name) for name in ("moons","gmm8")},
               "metric":"Mean empirical projected W1 over 128 fixed random unit directions (seed 7321)",
               "uncertainty":"Unadjusted two-sided 95% Student t intervals across paired seed differences; eight comparisons, descriptive; exact sign-flip sensitivity assumes sign exchangeability",
               "comparisons":comparisons,"holdout_controls":controls,"exclusions":manifest["exclusions"]}
    (destination/"summary.json").write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+"\n")
    write_csv(destination/"per-seed.csv", rows)
    write_csv(destination/"paired-differences.csv", paired)
    write_csv(destination/"holdout-controls.csv", controls)
    figures(raws, comparisons, destination)


def figures(raws, comparisons, destination):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.hashsalt":"ema-2d-v1",
                         "axes.spines.top":False,"axes.spines.right":False})
    colors = {"ema099":"#0072B2","ema0999":"#D55E00"}
    fig,axes=plt.subplots(2,2,figsize=(9,6),layout="constrained")
    for i,name in enumerate(("moons","gmm8")):
        for j,step in enumerate((5000,10000)):
            ax=axes[i,j]
            for k,ema in enumerate(("ema099","ema0999")):
                row=next(c for c in comparisons if (c["dataset"],c["updates"],c["ema"])==(name,step,ema))
                offsets=np.linspace(-.1,.1,row["n"])
                ax.scatter(k+offsets,row["differences"],s=30,alpha=.75,color=colors[ema],label="Seeds" if k==0 else None)
                lo,hi=row["ci95_t"]
                ax.errorbar(k,row["mean"],yerr=[[row["mean"]-lo],[hi-row["mean"]]],fmt="D",color="black",capsize=5,label="Mean ± 95% t CI" if k==0 else None)
            ax.axhline(0,color="0.4",linewidth=.8,linestyle="--")
            ax.set(xticks=[0,1],xticklabels=["EMA 0.99","EMA 0.999"],title=f"{'Two moons' if name=='moons' else 'Eight Gaussians'} · {step:,} updates",ylabel="Δ Sliced W1 (EMA − raw)")
            ax.grid(axis="y",alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle("Weight EMA: paired held-out quality\nNegative differences favor EMA; five new seeds per dataset",fontsize=13)
    fig.savefig(destination/"paired-quality.png",dpi=200)
    fig.savefig(destination/"paired-quality.svg",metadata={"Date":None})
    plt.close(fig)
    fig,axes=plt.subplots(2,4,figsize=(11,5.8),layout="constrained")
    for i,name in enumerate(("moons","gmm8")):
        raw=min((r for r in raws if r["dataset"]==name),key=lambda r:r["seed"])
        checkpoint=next(c for c in raw["checkpoints"] if c["step"]==10000)
        for j,variant in enumerate(("heldout","raw","ema099","ema0999")):
            points=np.array(raw["heldout"] if variant=="heldout" else checkpoint["variants"][variant]["samples"])
            axes[i,j].scatter(points[:1024,0],points[:1024,1],s=2,alpha=.35,color="#333333" if variant=="heldout" else "#0072B2")
            axes[i,j].set(xlim=(-3,4),ylim=(-3,4),aspect="equal",title={"heldout":"Held-out target","raw":"Raw weights","ema099":"EMA 0.99","ema0999":"EMA 0.999"}[variant],xlabel="x₁")
            if j==0:
                axes[i,j].set_ylabel(f"{name} · seed {raw['seed']}\nx₂")
    fig.suptitle("Prespecified first confirmation seed · 10,000 updates\nFirst 1,024 of 2,048 draws; identical sampling noise within each trajectory",fontsize=12)
    fig.savefig(destination/"samples.png",dpi=200)
    fig.savefig(destination/"samples.svg",metadata={"Date":None})
    plt.close(fig)


if __name__=="__main__":
    analyze(*map(Path,sys.argv[1:]))
