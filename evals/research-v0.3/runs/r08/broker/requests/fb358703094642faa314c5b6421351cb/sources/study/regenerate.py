"""Load saved weights and generate again, without retraining or reading samples as input."""
import argparse
import json
from pathlib import Path
from run import dump, sha, VARIANTS
import numpy as np
import torch
from science import Denoiser, draw, schedule, sliced_wasserstein

p=argparse.ArgumentParser();p.add_argument("--measurements",default="measurements.json");p.add_argument("--dataset",choices=["moons","gmm8"]);p.add_argument("--output",required=True)
args=p.parse_args();torch.set_num_threads(1)
records=[]
for r in json.loads(Path(args.measurements).read_text())["runs"]:
    if args.dataset and r["dataset"]!=args.dataset:continue
    device=r["device"]
    with np.load(r["arrays"],allow_pickle=False) as a, np.load(r["weights"],allow_pickle=False) as w:
        c={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in schedule().items()}
        noise=torch.tensor(a["generation_noise"],device=device)
        for v in VARIANTS:
            model=Denoiser().to(device)
            model.load_state_dict({k[len(v)+2:]:torch.tensor(w[k],device=device) for k in w.files if k.startswith(v+"__")},strict=True)
            model.eval(); x=draw(model,noise,c)
            difference=float(np.max(np.abs(x-a[v])))
            sw1=sliced_wasserstein(x,a["heldout"])
            record={"dataset":r["dataset"],"seed":r["seed"],"updates":r["updates"],"schedule":r["schedule"],"variant":v,"weights":r["weights"],"weights_sha256":sha(r["weights"]),"max_abs_sample_difference":difference,"sw1":sw1,"sw1_difference":abs(sw1-r["metrics"][v]["sw1"]),"passed":difference<=2e-5 and abs(sw1-r["metrics"][v]["sw1"])<=2e-6}
            records.append(record)
            if not record["passed"]:raise AssertionError(record)
    print(json.dumps({"regenerated":r["arrays"],"states":3}),flush=True)
dump(args.output,{"method":"load all state_dict entries including buffers into fresh Denoiser; supplied DDPM draw; saved generation noise; no optimizer/training","device":"mps","count":len(records),"all_passed":all(r["passed"] for r in records),"max_abs_sample_difference":max(r["max_abs_sample_difference"] for r in records),"script_sha256":sha(__file__),"records":records})
