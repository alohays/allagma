"""AI-generated follow-up runner. Scientific mechanism: supplied science.py.

Run only via inputs/compute.py. Every destination is append-only at attempt level.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import time

# The broker caps MPS high watermark at .2; PyTorch's default low watermark
# 1.4 is incompatible. Lower the low watermark, preserving the broker cap.
os.environ["PYTORCH_MPS_LOW_WATERMARK_RATIO"] = "0.1"
import numpy as np
import torch
from science import Denoiser, dataset, draw, schedule, sliced_wasserstein, mode_coverage, projections, mixture_centers

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("raw", "ema099", "ema0999")

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+"\n")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

def state_arrays(model):
    return {k: v.detach().cpu().numpy().copy() for k,v in model.state_dict().items()}

def state_digest(arrays):
    h = hashlib.sha256()
    for k in sorted(arrays):
        h.update(k.encode()+b"\0")
        h.update(np.ascontiguousarray(arrays[k]).tobytes())
    return h.hexdigest()

def prefix_digest(a):
    h = hashlib.sha256()
    for name, x in (("clean", a["train"][a["indices"][:5000]]), ("noise", a["noise"][:5000]), ("timesteps", a["timesteps"][:5000])):
        h.update(name.encode()+b"\0")
        h.update(np.ascontiguousarray(x).tobytes())
    return h.hexdigest()

def source_snapshot():
    paths = [ROOT/"study/science.py", ROOT/"study/run.py", ROOT/"protocols/protocol-v1.json", ROOT/"LICENSE"]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    revision = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    out = ROOT/"source-snapshots"/revision
    out.mkdir(parents=True, exist_ok=True)
    for p in paths:
        dest = out/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(p, dest)
        assert sha(dest) == sha(p)
    dump(out/"hashes.json", hashes)
    return revision, hashes

def sync(device):
    if device == "mps":
        torch.mps.synchronize()

def lr_at(step, duration, policy):
    return 3e-4 if policy == "constant" else 3e-4*.5*(1+math.cos(math.pi*(step-1)/duration))

def qualify(out):
    checks = []
    def check(name, condition, detail=None):
        if not condition:
            raise AssertionError((name, detail))
        checks.append({"name": name, "passed": True, "detail": detail})
    x = np.array([[0.,0.],[1.,2.],[-2.,1.]])
    check("sw1 identity", sliced_wasserstein(x,x) == 0.)
    shift = np.array([2.,-3.])
    expected = float(np.abs(projections()@shift).mean())
    check("sw1 translation all reference directions", abs(sliced_wasserstein(x,x+shift)-expected)<1e-12, expected)
    check("sw1 sorting and known 1D distance", sliced_wasserstein(np.array([[0.,0.],[2.,0.]]), np.array([[3.,0.],[1.,0.]]), np.array([[1.,0.]])) == 1.)
    centers = mixture_centers()
    check("coverage all center modes", mode_coverage(np.repeat(centers, 256, axis=0))["covered"] == 8)
    z = np.full((2048,2), 99.)
    z[:20] = centers[0]
    check("coverage threshold below 21 of all draws", mode_coverage(z)["covered"] == 0)
    z[20] = centers[0]
    mc = mode_coverage(z)
    check("coverage threshold 21 and outlier denominator", mc["covered"] == 1 and mc["counts"][0] == 21 and mc["inlier_fraction"] == 21/2048)
    z = np.tile(centers[0], (2048,1)); z[:,1] += .45
    check("coverage includes radius boundary", mode_coverage(z)["counts"][0] == 2048)
    z[:,1] += 1e-6
    check("coverage excludes outside radius", mode_coverage(z)["counts"][0] == 0)
    co = schedule()
    check("DDPM finite and terminal near zero", all(np.isfinite(v).all() for v in co.values()) and co["abar"][-1]<1e-6 and co["posterior_std"][0] == 0., float(co["abar"][-1]))
    check("LR terminal schedule distinction", lr_at(2501,5000,"cosine") == 1.5e-4 and lr_at(5001,10000,"cosine") == 1.5e-4 and lr_at(5001,5000,"cosine") == 0.)
    check("constant LR unchanged", lr_at(10000,10000,"constant") == 3e-4)
    torch.manual_seed(71)
    m = Denoiser(); e = copy.deepcopy(m)
    check("EMA initial copy and parameter count", state_digest(state_arrays(m)) == state_digest(state_arrays(e)) and sum(p.numel() for p in m.parameters()) == 296450)
    with torch.no_grad():
        before = [p.clone() for p in e.parameters()]
        for p in m.parameters(): p.add_(1.)
        torch._foreach_lerp_(list(e.parameters()), list(m.parameters()), .01)
    check("EMA one-step recurrence", all(torch.allclose(p,b+.01,atol=1e-7,rtol=1e-6) for p,b in zip(e.parameters(),before)))
    check("EMA buffers unchanged", all(torch.equal(a,b) for a,b in zip(m.buffers(),e.buffers())))
    # Two implementations of a short training computation must agree.
    c = {k: torch.tensor(v,dtype=torch.float32) for k,v in co.items()}
    clean = torch.tensor(dataset("moons", 8, 71)); noise = torch.arange(16,dtype=torch.float32).reshape(8,2)/10
    t = torch.arange(8)
    via_torch = c["sqrt_abar"][t,None]*clean+c["sqrt_one_minus"][t,None]*noise
    via_numpy = (co["sqrt_abar"][t.numpy(),None]*clean.numpy()+co["sqrt_one_minus"][t.numpy(),None]*noise.numpy()).astype(np.float32)
    check("precomputed noisy-input equivalence", np.allclose(via_numpy,via_torch.numpy(),atol=3e-7,rtol=2e-7))
    dump(out, {"checks": checks, "all_passed": True, "confirmation_used": False})
    return checks

def inputs_for(name, seed, path):
    if path.exists():
        with np.load(path,allow_pickle=False) as f: return {k:f[k] for k in f.files}
    rng = np.random.default_rng(seed+100000)
    a = {"train": dataset(name,100000,seed+1000000), "heldout": dataset(name,2048,seed+2000000)}
    a["indices"] = rng.integers(0,100000,(10000,256))
    a["noise"] = rng.normal(size=(10000,256,2)).astype(np.float32)
    a["timesteps"] = rng.integers(0,100,(10000,256))
    a["generation_noise"] = np.random.default_rng(seed+3000000).normal(size=(100,2048,2)).astype(np.float32)
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,**a)
    return a

def run(args):
    start = time.monotonic()
    out = Path(args.output)
    out.mkdir(parents=True,exist_ok=False)
    cfg = vars(args).copy()
    dump(out/"config.json", cfg)
    dump(out/"status.json", {"status":"started", "scientific_replicate": args.phase=="confirmation"})
    revision, hashes = source_snapshot()
    if args.phase == "confirmation":
        freeze = json.loads((ROOT/"protocols/freeze.json").read_text())
        assert freeze["source_revision"] == revision
        assert args.seed in json.loads((ROOT/"protocols/protocol-v1.json").read_text())["design"]["confirmation_seeds"][args.dataset]
        assert args.device == freeze["device"]
    else:
        assert args.seed == {"moons":71,"gmm8":81}[args.dataset]
    if args.qualify:
        qualify(out/"qualification.json")
    torch.set_num_threads(1)
    assert args.device != "mps" or torch.backends.mps.is_available()
    assert os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") != "1"
    torch.manual_seed(args.seed)
    model = Denoiser().to(args.device)
    initial = state_arrays(model)
    np.savez_compressed(out/"initial-weights.npz", **initial)
    init_hash = state_digest(initial)
    emas = {k:copy.deepcopy(model).requires_grad_(False) for k in VARIANTS[1:]}
    shared = Path(args.shared)/f"{args.dataset}-{args.seed}.npz"
    a = inputs_for(args.dataset,args.seed,shared)
    prefix = prefix_digest(a)
    co = schedule()
    c = {k:torch.tensor(v,dtype=torch.float32,device=args.device) for k,v in co.items()}
    noisy_np = (co["sqrt_abar"][a["timesteps"],None]*a["train"][a["indices"]]+co["sqrt_one_minus"][a["timesteps"],None]*a["noise"]).astype(np.float32)
    noisy = torch.tensor(noisy_np,device=args.device)
    noise = torch.tensor(a["noise"],device=args.device)
    timesteps = torch.tensor(a["timesteps"],dtype=torch.float32,device=args.device)
    eval_noise = torch.tensor(a["generation_noise"],device=args.device)
    parameters = list(model.parameters())
    opt = torch.optim.AdamW(parameters,lr=3e-4,weight_decay=.01,foreach=True)
    sync(args.device)
    train_start = time.monotonic(); eval_seconds = 0.; train_samples=[]; entries=[]
    provenance = {"initial_weights_sha256":init_hash,"training_prefix_5000_sha256":prefix,"heldout_sha256":digest(a["heldout"]),"generation_noise_sha256":digest(a["generation_noise"]),"source_revision":revision,"source_hashes":hashes,"shared_inputs":str(shared),"initial_weights":str(out/"initial-weights.npz"),"hash_definition":"initial: sorted key+NUL+state bytes; prefix: clean+NUL+float32 train[indices[:5000]], noise+NUL+float32 noise[:5000], timesteps+NUL+int64 timesteps[:5000]; other arrays contiguous bytes","device":args.device,"dtype":"float32","environment":{"python":platform.python_version(),"torch":torch.__version__,"numpy":np.__version__,"platform":platform.platform(),"fallback":False},"attempt_id":out.name,"training_trace":str(out/"trace.jsonl")}
    dump(out/"provenance.json",provenance)
    milestones = [args.steps] if args.phase=="pilot" else ([5000,10000] if args.policy=="constant" else [args.duration])
    limit = args.steps if args.phase=="pilot" else args.duration
    with (out/"trace.jsonl").open("x",buffering=1) as trace:
        for step in range(1,limit+1):
            model.train(); opt.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(model(noisy[step-1],timesteps[step-1]),noise[step-1])
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(parameters,.5,foreach=False)
            lr = lr_at(step,args.duration,args.policy)
            opt.param_groups[0]["lr"] = lr; opt.step()
            with torch.no_grad():
                for key,decay in (("ema099",.99),("ema0999",.999)):
                    torch._foreach_lerp_(list(emas[key].parameters()),parameters,1-decay)
            if step==1 or step%100==0 or step==limit:
                value=float(loss.detach().cpu()); gn=float(norm.detach().cpu())
                assert np.isfinite(value) and np.isfinite(gn)
                row={"step":step,"noise_mse":value,"preclip_grad_norm":gn,"lr":lr,"ema_updates":step,"elapsed_seconds":time.monotonic()-start}
                trace.write(json.dumps(row)+"\n")
                if step==1 or step%1000==0: print(json.dumps(row),flush=True)
            if step not in milestones: continue
            sync(args.device); evstart=time.monotonic()
            train_samples.append({"step":step,"cumulative_training_seconds":evstart-train_start-eval_seconds})
            arrays={"heldout":a["heldout"],"generation_noise":a["generation_noise"]}; weights={}; metrics={}
            for name,m in {"raw":model,**emas}.items():
                m.eval()
                for key,val in state_arrays(m).items(): weights[name+"__"+key]=val
                sample=draw(m,eval_noise,c)
                assert sample.dtype == np.float32 and sample.shape==(2048,2) and np.isfinite(sample).all()
                arrays[name]=sample; metrics[name]={"sw1":sliced_wasserstein(sample,a["heldout"])}
                if args.dataset=="gmm8":
                    mc=mode_coverage(sample)
                    metrics[name].update({"mode_counts":mc["counts"],"covered_modes":mc["covered"],"inlier_count":sum(mc["counts"]),"inlier_fraction":mc["inlier_fraction"]})
            ap=out/f"step{step}-arrays.npz"; wp=out/f"step{step}-weights.npz"
            np.savez_compressed(ap,**arrays); np.savez_compressed(wp,**weights)
            entry={**provenance,"dataset":args.dataset,"seed":args.seed,"updates":step,"schedule":args.policy,"schedule_duration":args.duration,"phase":args.phase,"arrays":str(ap),"weights":str(wp),"metrics":metrics,"config":str(out/"config.json")}
            entries.append(entry); dump(out/f"step{step}-measurement.json",entry)
            sync(args.device); eval_seconds += time.monotonic()-evstart
    # Load all final states into fresh models, regenerate as a distinct pilot qualification.
    regen=[]
    if args.phase=="pilot":
        with np.load(entries[-1]["weights"],allow_pickle=False) as w:
            for name in VARIANTS:
                loaded=Denoiser().to(args.device)
                loaded.load_state_dict({k.split("__",1)[1]:torch.tensor(w[k],device=args.device) for k in w.files if k.startswith(name+"__")},strict=True)
                regenerated=draw(loaded,eval_noise,c)
                delta=float(np.max(np.abs(regenerated-arrays[name])))
                assert delta <= 2e-5
                regen.append({"variant":name,"max_abs_difference":delta,"passed":True})
        dump(out/"load-and-regenerate.json",regen)
    timing={"total_seconds":time.monotonic()-start,"training_seconds":train_samples[-1]["cumulative_training_seconds"],"evaluation_seconds":eval_seconds,"milestones":train_samples,"updates":limit,"seconds_per_update":train_samples[-1]["cumulative_training_seconds"]/limit}
    dump(out/"timing.json",timing)
    dump(out/"status.json",{"status":"completed","cells":len(entries),"timing":timing})
    print(json.dumps({"output":str(out),"timing":timing}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",choices=["moons","gmm8"],required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--policy",choices=["constant","cosine"],required=True)
    p.add_argument("--duration",type=int,choices=[5000,10000],required=True)
    p.add_argument("--phase",choices=["pilot","confirmation"],required=True)
    p.add_argument("--steps",type=int,default=1000)
    p.add_argument("--device",choices=["cpu","mps"],default="mps")
    p.add_argument("--output",required=True)
    p.add_argument("--shared",default="evidence/inputs")
    p.add_argument("--qualify",action="store_true")
    run(p.parse_args())

if __name__=="__main__": main()
