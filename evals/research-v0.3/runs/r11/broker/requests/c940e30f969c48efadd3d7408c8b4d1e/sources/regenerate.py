"""Regenerate retained samples from saved NPZ weights, without retraining."""
import argparse,json,os,time
os.environ.setdefault('PYTORCH_MPS_LOW_WATERMARK_RATIO','0.1')
from pathlib import Path
import numpy as np
import torch
from science import Denoiser, draw, schedule
from study import load_state,json_write,file_hash

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['moons','gmm8']);p.add_argument('--seed',type=int)
    p.add_argument('--measurements',default='measurements.json');p.add_argument('--out',required=True)
    args=p.parse_args();torch.set_num_threads(1);start=time.monotonic();results=[]
    runs=json.loads(Path(args.measurements).read_text())['runs']
    for r in runs:
        if args.dataset and r['dataset']!=args.dataset:continue
        if args.seed and r['seed']!=args.seed:continue
        device=r['device'];coeff={k:torch.tensor(v,dtype=torch.float32,device=device) for k,v in schedule().items()}
        with np.load(r['arrays'],allow_pickle=False) as ar,np.load(r['weights'],allow_pickle=False) as weights:
            noise=torch.tensor(ar['generation_noise'],device=device)
            for variant in ('raw','ema099','ema0999'):
                model=Denoiser().to(device);load_state(model,weights,variant+'__');model.eval()
                generated=draw(model,noise,coeff);expected=ar[variant]
                maximum=float(np.max(np.abs(generated-expected)));rms=float(np.sqrt(np.mean((generated-expected)**2)))
                assert maximum<=1e-6, f'Sample regeneration mismatch {maximum}'
                results.append(dict(dataset=r['dataset'],seed=r['seed'],updates=r['updates'],schedule=r['schedule'],variant=variant,
                                    device=device,max_absolute_error=maximum,rms_error=rms,exact_equal=bool(np.array_equal(generated,expected)),
                                    weights_sha256=file_hash(r['weights']),arrays_sha256=file_hash(r['arrays'])))
        print(json.dumps(dict(seed=r['seed'],schedule=r['schedule'],updates=r['updates'],verified=True)),flush=True)
    assert results
    json_write(args.out,dict(status='passed',kind='saved-weight sampling without retraining',variants_checked=len(results),
                            seconds=time.monotonic()-start,results=results))

if __name__=='__main__':main()
