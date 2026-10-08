"""Recompute all statistics and the main figure from retained sample arrays."""
from __future__ import annotations
import argparse
import csv
import itertools
import json
import os
from pathlib import Path
from datetime import datetime, timezone
os.environ.setdefault("MPLCONFIGDIR", str(Path(".tmp/matplotlib").resolve()))
import numpy as np
from scipy.stats import t as student_t
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["svg.hashsalt"]="ema-schedule-v1"
from science import sliced_wasserstein, mode_coverage
from run import dump, sha, VARIANTS

def interval(values):
    x=np.asarray(values,dtype=float); n=len(x); mean=float(x.mean())
    sd=float(x.std(ddof=1)) if n>1 else None
    se=sd/np.sqrt(n) if n>1 else None
    half=float(student_t.ppf(.975,n-1)*se) if n>1 else None
    p=float(np.mean([abs(np.mean(x*np.array(s)))>=abs(mean)-1e-15 for s in itertools.product([-1,1],repeat=n)]))
    return {"n":n,"mean":mean,"sd":sd,"se":se,"ci95":[mean-half,mean+half] if half is not None else None,"sign_flip_p":p,"values":x.tolist(),"leave_one_seed_out_means":[float(np.delete(x,i).mean()) for i in range(n)] if n>1 else [],"negative_count":int((x<0).sum())}

def write_csv(path, rows):
    if not rows: return
    with Path(path).open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument("--evidence",default="evidence/confirmation");p.add_argument("--output",default="analysis");p.add_argument("--measurements",default="measurements.json")
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    runs=[]; rows=[]; index={}; checks=[]
    for path in sorted(Path(args.evidence).glob("*/step*-measurement.json")):
        run=json.loads(path.read_text())
        if run["phase"]!="confirmation":continue
        key=(run["dataset"],run["seed"],run["updates"],run["schedule"])
        if key in index: raise ValueError(f"duplicate cell {key}")
        with np.load(run["arrays"],allow_pickle=False) as a:
            assert a["heldout"].shape==(2048,2) and a["generation_noise"].shape==(100,2048,2)
            for v in VARIANTS:
                value=sliced_wasserstein(a[v],a["heldout"])
                checks.append(abs(value-run["metrics"][v]["sw1"]))
                run["metrics"][v]={"sw1":value}
                if run["dataset"]=="gmm8":
                    mc=mode_coverage(a[v]);run["metrics"][v].update({"mode_counts":mc["counts"],"covered_modes":mc["covered"],"inlier_count":sum(mc["counts"]),"inlier_fraction":mc["inlier_fraction"]})
                rows.append({"dataset":run["dataset"],"seed":run["seed"],"updates":run["updates"],"schedule":run["schedule"],"variant":v,"sw1":value,"covered_modes":run["metrics"][v].get("covered_modes",""),"inlier_count":run["metrics"][v].get("inlier_count",""),"inlier_fraction":run["metrics"][v].get("inlier_fraction","")})
        run["arrays_sha256"]=sha(run["arrays"]);run["weights_sha256"]=sha(run["weights"])
        runs.append(run);index[key]=run
    dump(args.measurements,{"format":"research-measurements-v1","task_id":"ema-schedule","protocol":"protocols/protocol-v1.json","runs":runs})
    write_csv(out/"seed-metrics.csv",rows)
    paired=[];contrasts=[];absolute=[];coverage=[];quality=[]
    protocol=json.loads(Path("protocols/protocol-v1.json").read_text())
    for ds,seeds in protocol["design"]["confirmation_seeds"].items():
        complete=[s for s in seeds if all((ds,s,t,pol) in index for t in (5000,10000) for pol in ("constant","cosine"))]
        if not complete: continue
        def value(seed,t,pol,v):return index[ds,seed,t,pol]["metrics"][v]["sw1"]
        def delta(seed,t,pol,v):return value(seed,t,pol,v)-value(seed,t,pol,"raw")
        for t in (5000,10000):
            for pol in ("constant","cosine"):
                quality.append({"dataset":ds,"updates":t,"schedule":pol,"seeds":complete,"mean_sw1":{v:float(np.mean([value(s,t,pol,v) for s in complete])) for v in VARIANTS}})
        for v in VARIANTS[1:]:
            for t in (5000,10000):
                for pol in ("constant","cosine"):
                    paired.append({"dataset":ds,"variant":v,"updates":t,"schedule":pol,"seeds":complete,**interval([delta(s,t,pol,v) for s in complete])})
        for target in ("ema_effect","absolute_sw1"):
            for v in (VARIANTS[1:] if target=="ema_effect" else VARIANTS):
                fn=delta if target=="ema_effect" else value
                destination=contrasts if target=="ema_effect" else absolute
                for t in (5000,10000):
                    destination.append({"dataset":ds,"variant":v,"contrast":"schedule_cosine_minus_constant","condition":t,"seeds":complete,**interval([fn(s,t,"cosine",v)-fn(s,t,"constant",v) for s in complete])})
                for pol in ("constant","cosine"):
                    destination.append({"dataset":ds,"variant":v,"contrast":"duration_10000_minus_5000","condition":pol,"seeds":complete,**interval([fn(s,10000,pol,v)-fn(s,5000,pol,v) for s in complete])})
                destination.append({"dataset":ds,"variant":v,"contrast":"interaction","condition":"duration_contrast_cosine_minus_constant","seeds":complete,**interval([(fn(s,10000,"cosine",v)-fn(s,5000,"cosine",v))-(fn(s,10000,"constant",v)-fn(s,5000,"constant",v)) for s in complete])})
        if ds=="gmm8":
            for t in (5000,10000):
                for pol in ("constant","cosine"):
                    for v in VARIANTS:
                        m=[index[ds,s,t,pol]["metrics"][v] for s in complete]
                        coverage.append({"updates":t,"schedule":pol,"variant":v,"seeds":complete,"covered_modes":[x["covered_modes"] for x in m],"inlier_counts":[x["inlier_count"] for x in m],"inlier_fractions":[x["inlier_fraction"] for x in m],"mean_inlier_fraction":float(np.mean([x["inlier_fraction"] for x in m]))})
    summary={"revision":"analysis-v1","n_cells":len(runs),"n_states":len(rows),"complete_required_design":len(runs)==32,"paired_ema_minus_raw":paired,"ema_effect_contrasts":contrasts,"absolute_sw1_contrasts":absolute,"absolute_cell_quality":quality,"gmm8_coverage":coverage,"uncertainty":"unadjusted two-sided 95% Student t intervals over seeds, df=n-1; exact two-sided sign flip sensitivity; four seeds imply minimum p .125","max_metric_recompute_difference":max(checks) if checks else None}
    dump(out/"summary.json",summary)
    crows=[]
    for target,items in (("paired_ema_minus_raw",paired),("ema_effect_contrasts",contrasts),("absolute_sw1_contrasts",absolute)):
        for item in items:
            for seed,val in zip(item["seeds"],item["values"]):
                crows.append({"target":target,"dataset":item["dataset"],"variant":item["variant"],"contrast":item.get("contrast","ema_minus_raw"),"condition":str(item.get("condition",str(item.get("updates"))+"_"+item.get("schedule",""))),"seed":seed,"value":val})
    write_csv(out/"seed-contrasts.csv",crows)
    with (out/"tables.md").open("w") as f:
        f.write("| Dataset | EMA | Updates | Policy | Mean EMA − raw SW1 | 95% t interval |\n|---|---|---:|---|---:|---|\n")
        for x in paired:f.write(f"| {x['dataset']} | {x['variant']} | {x['updates']} | {x['schedule']} | {x['mean']:.6f} | [{x['ci95'][0]:.6f}, {x['ci95'][1]:.6f}] |\n")
        f.write("\n| Dataset | EMA | Contrast | Condition | Mean | 95% t interval |\n|---|---|---|---|---:|---|\n")
        for x in contrasts:f.write(f"| {x['dataset']} | {x['variant']} | {x['contrast']} | {x['condition']} | {x['mean']:.6f} | [{x['ci95'][0]:.6f}, {x['ci95'][1]:.6f}] |\n")
        f.write("\n| GMM8 updates | Policy | State | Covered modes (four seeds) | Mean inlier fraction |\n|---:|---|---|---|---:|\n")
        for x in coverage:f.write(f"| {x['updates']} | {x['schedule']} | {x['variant']} | {x['covered_modes']} | {x['mean_inlier_fraction']:.6f} |\n")
        f.write("\n| Dataset | Updates | Policy | Mean raw SW1 | Mean EMA0.99 SW1 | Mean EMA0.999 SW1 |\n|---|---:|---|---:|---:|---:|\n")
        for x in quality:f.write(f"| {x['dataset']} | {x['updates']} | {x['schedule']} | {x['mean_sw1']['raw']:.6f} | {x['mean_sw1']['ema099']:.6f} | {x['mean_sw1']['ema0999']:.6f} |\n")
    fig,axes=plt.subplots(2,2,figsize=(11,7.5),sharex=True)
    colors={"constant":"#2166ac","cosine":"#b2182b"}
    cells=[(5000,"constant"),(5000,"cosine"),(10000,"constant"),(10000,"cosine")]
    for i,ds in enumerate(("moons","gmm8")):
        for j,v in enumerate(VARIANTS[1:]):
            ax=axes[i,j];ax.axhline(0,color=".45",lw=.8)
            for k,(t,pol) in enumerate(cells):
                found=[x for x in paired if (x["dataset"],x["variant"],x["updates"],x["schedule"])==(ds,v,t,pol)]
                if not found:continue
                x=found[0]
                ax.scatter(k+np.linspace(-.12,.12,len(x["values"])),x["values"],s=26,color=colors[pol],alpha=.8,zorder=3)
                ax.errorbar(k,x["mean"],yerr=[[x["mean"]-x["ci95"][0]],[x["ci95"][1]-x["mean"]]],fmt="D",color="black",markersize=5,capsize=4,zorder=4)
            ax.set_title(f"{ds} · {v}");ax.set_xticks(range(4),["5k\nconstant","5k\ncosine","10k\nconstant","10k\ncosine"]);ax.grid(axis="y",alpha=.2)
            ax.set_ylabel("EMA − raw Sliced W1")
    fig.suptitle("EMA differences by learning-rate policy and terminal duration\nDots: paired seeds · diamonds/bars: mean and unadjusted 95% t interval",fontsize=12)
    fig.tight_layout()
    fixed_date=datetime(2026,10,8,tzinfo=timezone.utc)
    for ext in ("png","pdf","svg"):
        metadata={"CreationDate":fixed_date,"ModDate":fixed_date} if ext=="pdf" else ({"Date":"2026-10-08"} if ext=="svg" else {})
        fig.savefig(out/f"main-figure.{ext}",dpi=180,metadata=metadata)
    plt.close(fig)
    dump(out/"analysis-provenance.json",{"script_sha256":sha(__file__),"science_sha256":sha("study/science.py"),"inputs":[{"path":r["arrays"],"sha256":r["arrays_sha256"]} for r in runs],"measurements_sha256":sha(args.measurements)})
    print(json.dumps({"n_cells":len(runs),"n_states":len(rows),"max_metric_recompute_difference":summary["max_metric_recompute_difference"]}))

if __name__=="__main__":main()
