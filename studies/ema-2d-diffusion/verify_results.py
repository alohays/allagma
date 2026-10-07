"""Independent evidence walk, SciPy metrics and saved-weight sample reproduction.

Run through the compute supervisor. This verifier does not use the study
analyzer for its statistics or SciPy reference W1 calculations.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t, wasserstein_distance
from scipy.spatial.distance import cdist
import torch

ROOT=Path(__file__).resolve().parent
CAMPAIGN=ROOT/"campaigns/ema-v1"
sys.path.insert(0,str(CAMPAIGN/"materials/domain"))
from science import Denoiser, draw, schedule


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    protocol=json.loads((CAMPAIGN/"protocol.json").read_text())
    freeze=json.loads((ROOT/"confirmation-freeze.json").read_text())
    assert sha(CAMPAIGN/"protocol.json")==freeze["protocol_sha256"]
    for name,digest in freeze["code"].items():
        assert sha(CAMPAIGN/"materials"/name)==digest
    expected={r["id"]:r for r in protocol["runs"]}
    checked=set()
    statuses={}
    successes={}
    interrupted=[]
    for path in sorted(CAMPAIGN.glob("runs/*/attempts/*/record.json")):
        record=json.loads(path.read_text())
        statuses[record["status"]]=statuses.get(record["status"],0)+1
        for reference in record["inputs"]+record["outputs"]:
            assert sha(ROOT/reference["path"])==reference["sha256"]
            checked.add(reference["path"])
        if record["status"]=="interrupted":
            interrupted.append(record["attempt_id"])
        if record["status"]!="succeeded":
            continue
        assert record["run_id"] not in successes
        raw=json.loads((path.parent/"raw.json").read_text())
        assert raw["input"]==expected[record["run_id"]]["input"]
        assert "fault" not in raw["input"]
        assert json.loads((path.parent/"evaluation.json").read_text())["valid"] is True
        successes[record["run_id"]]=(path,record,raw)
    assert set(successes)==set(expected)
    assert len(interrupted)>=1
    pilot_seeds={r["input"]["seed"] for r in expected.values() if r["split"]=="pilot"}
    confirmation_seeds={r["input"]["seed"] for r in expected.values() if r["split"]=="confirmation"}
    assert not pilot_seeds&confirmation_seeds
    summary=json.loads((CAMPAIGN/"analyses/a001/outputs/summary.json").read_text())
    manifest=json.loads((CAMPAIGN/"analyses/a001/raw-manifest.json").read_text())
    assert len(manifest["raw"])==10
    theta=np.random.default_rng(7321).uniform(0,2*np.pi,128)
    directions=np.column_stack((np.cos(theta),np.sin(theta)))
    estimates={}
    metric_checks=0
    coverage_checks=0
    weight_checks=0
    reproduction=[]
    for run_id,(path,record,raw) in successes.items():
        archive=np.load(path.parent/"weights.npz",allow_pickle=False)
        heldout=np.array(raw["heldout"],dtype=np.float64)
        for checkpoint in raw["checkpoints"]:
            scores={}
            for name,value in checkpoint["variants"].items():
                sample=np.array(value["samples"],dtype=np.float64)
                sw=float(np.mean([wasserstein_distance(sample@d,heldout@d) for d in directions]))
                assert abs(sw-value["sw1"])<1e-12
                scores[name]=sw
                metric_checks+=1
                if raw["dataset"]=="gmm8":
                    centers=np.array([[2*math.cos(k*math.pi/4),2*math.sin(k*math.pi/4)] for k in range(8)])
                    distances=cdist(sample,centers)
                    nearest=distances.argmin(axis=1)
                    counts=[sum(int(nearest[i])==k and distances[i,k]<=.45 for i in range(len(sample))) for k in range(8)]
                    measured=value["mode_coverage"]
                    assert measured["counts"]==counts
                    assert measured["covered"]==sum(n>=math.ceil(.01*len(sample)) for n in counts)
                    assert abs(measured["inlier_fraction"]-sum(counts)/len(sample))<1e-12
                    coverage_checks+=1
                prefix=f"step{checkpoint['step']}__{name}__"
                state={key[len(prefix):]:archive[key] for key in archive.files if key.startswith(prefix)}
                vector=np.concatenate([state[k].ravel() for k in sorted(state)])
                assert hashlib.sha256(vector.tobytes()).hexdigest()==value["weights_sha256"]
                weight_checks+=1
                if raw["seed"] in (1001,2001):
                    model=Denoiser().to("mps")
                    model.load_state_dict({key:torch.tensor(arr,device="mps") for key,arr in state.items()})
                    model.eval()
                    noise=np.random.default_rng(raw["seed"]+3_000_000).normal(size=(100,raw["input"]["eval_size"],2)).astype(np.float32)
                    coefficients={key:torch.tensor(arr,dtype=torch.float32,device="mps") for key,arr in schedule().items()}
                    regenerated=draw(model,torch.tensor(noise,device="mps"),coefficients)
                    error=float(np.abs(regenerated-sample).max())
                    assert error<=2e-5, (run_id,name,checkpoint["step"],error)
                    reproduction.append({"run":run_id,"updates":checkpoint["step"],"weights":name,"max_sample_absolute_error":error})
            if record["split"]=="confirmation":
                for name in ("ema099","ema0999"):
                    estimates.setdefault((raw["dataset"],checkpoint["step"],name),[]).append((raw["seed"],scores[name]-scores["raw"]))
    for row in summary["comparisons"]:
        pairs=sorted(estimates[(row["dataset"],row["updates"],row["ema"])])
        assert len(pairs)==5 and [x[0] for x in pairs]==row["seeds"]
        v=np.array([x[1] for x in pairs])
        mean=float(v.mean())
        se=float(np.sqrt(sum((v-mean)**2)/(len(v)-1))/math.sqrt(len(v)))
        ci=[mean-t.ppf(.975,4)*se,mean+t.ppf(.975,4)*se]
        np.testing.assert_allclose(v,row["differences"],atol=1e-12,rtol=0)
        np.testing.assert_allclose(ci,row["ci95_t"],atol=1e-12,rtol=0)
        statistics=[abs(np.mean(v*np.array(signs))) for signs in itertools.product((-1,1),repeat=5)]
        assert abs(np.mean(np.array(statistics)>=abs(mean)-1e-14)-row["sign_flip_p_two_sided"])<1e-12
    output={"status":"pass","attempt_statuses":statuses,"interrupted_attempts":interrupted,
            "distinct_direct_reference_checks":len(checked),"scipy_projected_w1_checks":metric_checks,
            "independent_mixture_coverage_checks":coverage_checks,
            "saved_weight_digest_checks":weight_checks,"paired_interval_checks":len(summary["comparisons"]),
            "sample_regeneration":reproduction,
            "scope":"Every trajectory and raw/checkpoint digest; all reported SW1 scores and paired confidence intervals independently recomputed. Saved-weight sampling re-executed on the two prespecified first confirmation seeds, all three variants and both checkpoints. No retraining or independent peer review."}
    (ROOT/"evidence/independent-verification.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(json.dumps(output,indent=2))


if __name__=="__main__":
    main()
