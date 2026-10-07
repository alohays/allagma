"""Independently check supporting diagnostics omitted by the first verifier."""
import csv
import json
import math
from pathlib import Path
import sys

from compute import ROOT, execute


def run():
    # The outer launcher uses system Python. Scientific dependencies are
    # imported only after execute() launches the isolated, budgeted worker.
    import numpy as np
    from scipy.spatial.distance import cdist
    from scipy.stats import t, wasserstein_distance
    campaign=ROOT/"campaigns/ema-v1"
    out=campaign/"analyses/a001/outputs"
    summary=json.loads((out/"summary.json").read_text())
    csv_rows=list(csv.DictReader((out/"per-seed.csv").open()))
    paired=list(csv.DictReader((out/"paired-differences.csv").open()))
    centers=np.array([[2*math.cos(k*math.pi/4),2*math.sin(k*math.pi/4)] for k in range(8)])
    theta=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    directions=np.column_stack((np.cos(theta),np.sin(theta)))
    controls=[]
    values={}
    checked_rows=0
    def close(a,b):
        assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12),(a,b)
    for path in sorted(campaign.glob("runs/confirm-*/attempts/*/raw.json")):
        record=json.loads((path.parent/"record.json").read_text())
        if record["status"]!="succeeded":
            continue
        raw=json.loads(path.read_text())
        name,seed=raw["dataset"],raw["seed"]
        n=raw["input"]["eval_size"]
        rng=np.random.default_rng(seed+4_000_000)
        if name=="moons":
            angles=rng.uniform(0,math.pi,n)
            side=rng.integers(0,2,n)
            reference=np.column_stack((np.where(side==0,np.cos(angles),1-np.cos(angles)),np.where(side==0,np.sin(angles),.5-np.sin(angles))))
            reference+=rng.normal(0,.03,(n,2))
            reference[:,0]=(reference[:,0]+.3)*2-1
            reference[:,1]=(reference[:,1]+.3)*3-1
        else:
            reference=centers[rng.integers(0,8,n)]+rng.normal(0,.15,(n,2))
        reference=reference.astype(np.float32).astype(np.float64)
        heldout=np.array(raw["heldout"],dtype=np.float64)
        floor=float(np.mean([wasserstein_distance(reference@d,heldout@d) for d in directions]))
        expected=next(c for c in summary["holdout_controls"] if (c["dataset"],c["seed"])==(name,seed))
        close(floor,expected["holdout_vs_independent_holdout_sw1"])
        controls.append((name,seed))
        for checkpoint in raw["checkpoints"]:
            step=checkpoint["step"]
            for variant,observation in checkpoint["variants"].items():
                row=next(r for r in csv_rows if (r["dataset"],int(r["seed"]),int(r["updates"]),r["weights"])==(name,seed,step,variant))
                close(row["sw1"],observation["sw1"])
                numeric={"sw1":observation["sw1"]}
                if name=="gmm8":
                    samples=np.array(observation["samples"],dtype=np.float64)
                    distances=cdist(samples,centers)
                    nearest=distances.argmin(axis=1)
                    counts=np.array([np.count_nonzero((nearest==k)&(distances[:,k]<=.45)) for k in range(8)])
                    numeric.update(covered_modes=int(np.count_nonzero(counts>=math.ceil(.01*n))),
                        inlier_fraction=float(counts.sum()/n),mode_total_variation=float(np.abs(counts/n-.125).sum()/2))
                    for key in ("covered_modes","inlier_fraction","mode_total_variation"):
                        close(row[key],numeric[key])
                    close(observation["mode_coverage"]["total_variation"],numeric["mode_total_variation"])
                values[(name,seed,step,variant)]=numeric
                checked_rows+=1
    assert checked_rows==60 and len(controls)==10 and len(csv_rows)==60 and len(paired)==40
    secondary_intervals=0
    for comparison in summary["comparisons"]:
        name,step,ema=comparison["dataset"],comparison["updates"],comparison["ema"]
        differences=[]
        modes=[]
        inliers=[]
        for seed in comparison["seeds"]:
            raw=values[(name,seed,step,"raw")]
            average=values[(name,seed,step,ema)]
            delta=average["sw1"]-raw["sw1"]
            differences.append(delta)
            row=next(r for r in paired if (r["dataset"],int(r["seed"]),int(r["updates"]),r["ema"])==(name,seed,step,ema))
            close(row["sw1_difference"],delta)
            if name=="gmm8":
                modes.append(average["covered_modes"]-raw["covered_modes"])
                inliers.append(average["inlier_fraction"]-raw["inlier_fraction"])
                close(row["mode_difference"],modes[-1])
                close(row["inlier_difference"],inliers[-1])
        loo=[float(np.mean([d for j,d in enumerate(differences) if j!=i])) for i in range(5)]
        np.testing.assert_allclose(comparison["leave_one_out_mean_range"],[min(loo),max(loo)],atol=1e-12,rtol=0)
        if name=="gmm8":
            for key,vector in (("mode_difference",modes),("inlier_difference",inliers)):
                mean=float(np.mean(vector));se=float(np.std(vector,ddof=1)/np.sqrt(5))
                report=comparison[key]
                close(mean,report["mean"]);close(se,report["se"])
                np.testing.assert_allclose(report["ci95_t"],[mean-t.ppf(.975,4)*se,mean+t.ppf(.975,4)*se],atol=1e-12,rtol=0)
                secondary_intervals+=1
    result={"status":"pass","per_seed_csv_rows_checked":checked_rows,"paired_csv_rows_checked":len(paired),
            "independent_holdout_controls_checked":len(controls),"leave_one_out_ranges_checked":8,
            "supporting_paired_intervals_checked":secondary_intervals,
            "scope":"Independent SciPy geometry and projected W1 verify all confirmation CSV metrics, mode counts, inlier mass discrepancy, holdout controls, paired supporting intervals and leave-one-seed-out ranges. Complements the first verifier's primary metrics and saved-weight sampling checks."}
    target=ROOT/"evidence/supporting-verification.json"
    with target.open("x") as file:
        file.write(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    if sys.argv[1:]==["--worker"]:
        run()
    elif not sys.argv[1:]:
        raise SystemExit(execute("supporting-verification",[str(ROOT/".venv/bin/python"),str(Path(__file__).resolve()),"--worker"],45))
    else:
        raise SystemExit("Run without arguments for budgeted verification")
