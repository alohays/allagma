"""Independent retained-evidence checks. Run through the common broker.

SW1/coverage/contrasts are reimplemented here instead of calling analysis metrics.
"""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import numpy as np
from run import dump, sha, state_digest, prefix_digest, VARIANTS

def load(path): return json.loads(Path(path).read_text())
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def own_sw1(x,y):
    theta=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    directions=np.stack([np.cos(theta),np.sin(theta)],axis=0)
    return float(np.mean(np.abs(np.sort(x.astype(np.float64)@directions,axis=0)-np.sort(y.astype(np.float64)@directions,axis=0))))
def own_coverage(x):
    theta=np.arange(8)*2*np.pi/8
    centers=2*np.stack([np.cos(theta),np.sin(theta)],axis=1)
    d=((x.astype(np.float64)[:,None,:]-centers[None,:,:])**2).sum(axis=2)
    nearest=d.argmin(axis=1); valid=d[np.arange(len(x)),nearest]<=.45**2
    counts=[int(np.sum(valid&(nearest==k))) for k in range(8)]
    return counts,int(np.sum(np.array(counts)>=21)),int(valid.sum()),float(valid.mean())

def main():
    measurements=load("measurements.json");summary=load("analysis/summary.json");freeze=load("protocols/freeze.json")
    assert measurements["format"]=="research-measurements-v1"
    assert sha(measurements["protocol"])==freeze["protocol_sha256"]
    assert sha("study/science.py")==sha("inputs/materials/prior-study/science.py")
    expected={(ds,s,t,p) for ds,seeds in (("moons",range(4001,4005)),("gmm8",range(5001,5005))) for s in seeds for t in (5000,10000) for p in ("constant","cosine")}
    index={(r["dataset"],r["seed"],r["updates"],r["schedule"]):r for r in measurements["runs"]}
    assert len(measurements["runs"])==len(index)==32 and set(index)==expected
    shared={};initial={};seen={};scores={};maxdiff=0.;coverage_count=0
    for key,r in index.items():
        ds,seed,updates,policy=key
        assert r["device"]=="mps" and r["source_revision"]==freeze["source_revision"] and r["phase"]=="confirmation"
        for pathkey,hashkey in (("arrays","arrays_sha256"),("weights","weights_sha256")):
            assert sha(r[pathkey])==r[hashkey]
        if r["shared_inputs"] not in shared:
            with np.load(r["shared_inputs"],allow_pickle=False) as f:a={k:f[k] for k in f.files}
            assert a["train"].shape==(100000,2) and a["train"].dtype==np.float32
            assert a["indices"].shape==(10000,256) and a["timesteps"].shape==(10000,256)
            assert a["noise"].shape==(10000,256,2) and a["noise"].dtype==np.float32
            rng=np.random.default_rng(seed+100000)
            assert np.array_equal(a["indices"],rng.integers(0,100000,(10000,256)))
            assert np.array_equal(a["noise"],rng.normal(size=(10000,256,2)).astype(np.float32))
            assert np.array_equal(a["timesteps"],rng.integers(0,100,(10000,256)))
            assert np.array_equal(a["generation_noise"],np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32))
            shared[r["shared_inputs"]]={"prefix":prefix_digest(a),"heldout":a["heldout"],"generation_noise":a["generation_noise"]}
        sh=shared[r["shared_inputs"]]
        assert sh["prefix"]==r["training_prefix_5000_sha256"]
        with np.load(r["initial_weights"],allow_pickle=False) as f:ini={k:f[k] for k in f.files}
        assert state_digest(ini)==r["initial_weights_sha256"]
        checks=[r[k] for k in ("initial_weights_sha256","training_prefix_5000_sha256","heldout_sha256","generation_noise_sha256")]
        if (ds,seed) in seen:assert seen[ds,seed]==checks
        seen[ds,seed]=checks
        with np.load(r["arrays"],allow_pickle=False) as a:
            assert np.array_equal(a["heldout"],sh["heldout"]) and np.array_equal(a["generation_noise"],sh["generation_noise"])
            assert digest(a["heldout"])==r["heldout_sha256"] and digest(a["generation_noise"])==r["generation_noise_sha256"]
            for v in VARIANTS:
                assert a[v].shape==(2048,2) and a[v].dtype==np.float32 and np.isfinite(a[v]).all()
                own=own_sw1(a[v],a["heldout"]);diff=abs(own-r["metrics"][v]["sw1"]);maxdiff=max(maxdiff,diff);assert diff<1e-12
                scores[key+(v,)]=own
                if ds=="gmm8":
                    cnt,cov,n,frac=own_coverage(a[v]);m=r["metrics"][v]
                    assert m["mode_counts"]==cnt and m["covered_modes"]==cov and m["inlier_count"]==n and m["inlier_fraction"]==frac
                    coverage_count+=1
        with np.load(r["weights"],allow_pickle=False) as w:
            assert len(w.files)==3*len(ini)
            for v in VARIANTS:
                state={k[len(v)+2:]:w[k] for k in w.files if k.startswith(v+"__")}
                assert set(state)==set(ini) and all(state[k].shape==ini[k].shape and state[k].dtype==np.float32 and np.isfinite(state[k]).all() for k in ini)
                assert all(np.array_equal(state[k],ini[k]) for k in ini if k.endswith("frequencies"))
        trace=[json.loads(x) for x in Path(r["training_trace"]).read_text().splitlines()]
        cfg=load(r["config"])
        assert trace[-1]["step"]==cfg["duration"] and any(x["step"]==updates for x in trace)
        assert cfg["duration"]==(10000 if policy=="constant" else updates)
        for x in trace:
            lr=3e-4 if policy=="constant" else .00015*(1+math.cos(math.pi*(x["step"]-1)/cfg["duration"]))
            assert abs(lr-x["lr"])<1e-18 and x["ema_updates"]==x["step"] and math.isfinite(x["noise_mse"])
        assert load(Path(r["config"]).parent/"status.json")["status"]=="completed"
    contrast_checks=0;max_statdiff=0.
    for target in ("paired_ema_minus_raw","ema_effect_contrasts","absolute_sw1_contrasts"):
        for row in summary[target]:
            ds,v=row["dataset"],row["variant"]
            def score(seed,t,p):
                x=scores[ds,seed,t,p,v]
                return x-scores[ds,seed,t,p,"raw"] if target!="absolute_sw1_contrasts" else x
            expected_values=[]
            for seed in row["seeds"]:
                if target=="paired_ema_minus_raw":val=score(seed,row["updates"],row["schedule"])
                elif row["contrast"]=="schedule_cosine_minus_constant":val=score(seed,row["condition"],"cosine")-score(seed,row["condition"],"constant")
                elif row["contrast"]=="duration_10000_minus_5000":val=score(seed,10000,row["condition"])-score(seed,5000,row["condition"])
                else:val=(score(seed,10000,"cosine")-score(seed,5000,"cosine"))-(score(seed,10000,"constant")-score(seed,5000,"constant"))
                expected_values.append(val)
            assert len(expected_values)==4 and np.allclose(expected_values,row["values"],atol=1e-12,rtol=0)
            avg=sum(expected_values)/4;se=math.sqrt(sum((x-avg)**2 for x in expected_values)/3)/2;ci=[avg-3.182446305284263*se,avg+3.182446305284263*se]
            assert abs(avg-row["mean"])<1e-12 and np.allclose(ci,row["ci95"],atol=1e-12,rtol=0)
            pvalue=sum(abs(sum(s*x for s,x in zip(signs,expected_values))/4)>=abs(avg)-1e-15 for signs in itertools.product([-1,1],repeat=4))/16
            assert pvalue==row["sign_flip_p"]
            max_statdiff=max(max_statdiff,abs(avg-row["mean"]),float(np.max(np.abs(np.array(ci)-row["ci95"]))))
            contrast_checks+=1
    csv_rows=list(csv.DictReader(Path("analysis/seed-metrics.csv").open()))
    assert len(csv_rows)==96
    for row in csv_rows:assert abs(float(row["sw1"])-scores[row["dataset"],int(row["seed"]),int(row["updates"]),row["schedule"],row["variant"]])<1e-12
    dump("analysis/verification.json",{"all_passed":True,"cells":32,"states":96,"distinct_training_seeds":8,"complete_training_trajectories":len({r["attempt_id"] for r in index.values()}),"matched_seed_groups":len(seen),"shared_input_files":len(shared),"known_sample_shapes_and_float32":True,"reference_science_byte_identical":True,"initial_state_prefix_heldout_and_generation_hashes_verified":True,"exact_training_random_stream_replay":True,"final_update_and_lr_traces_verified":True,"all_state_entries_and_buffers_present":True,"independent_sw1_max_abs_difference":maxdiff,"independent_coverage_states":coverage_count,"independent_summary_intervals_checked":contrast_checks,"independent_summary_max_abs_difference":max_statdiff,"script_sha256":sha(__file__),"measurements_sha256":sha("measurements.json"),"summary_sha256":sha("analysis/summary.json"),"scope":"data and numerical/code audit by the same AI author; independent formulas, not independent peer review"})
    print(json.dumps({"all_passed":True,"cells":32,"states":96,"contrast_checks":contrast_checks,"max_metric_difference":maxdiff}))

if __name__=="__main__":main()
