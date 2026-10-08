"""Compare fresh retraining with original retained evidence; broker only."""
import argparse
import json
from pathlib import Path
import numpy as np
from common import ROOT,read,write,ref,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);a=p.parse_args()
    dst=ROOT/a.destination
    original=read(ROOT/'analysis/measurements.json')['runs'];replayed=read(dst/'analysis/measurements.json')['runs']
    def key(r):return r['dataset'],r['seed'],r['updates'],r['schedule']
    lookup={key(r):r for r in replayed};assert len(original)==len(replayed)==32
    results=[]
    for r in original:
        rr=lookup[key(r)];delta={};exact={}
        for field in ['initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256','source_revision']:
            assert r[field]==rr[field]
        for field in ['arrays','weights']:
            old=np.load(ROOT/r[field],allow_pickle=False);new=np.load(dst/rr[field],allow_pickle=False)
            assert set(old.files)==set(new.files)
            delta[field]=max(float(np.max(np.abs(old[k]-new[k]))) for k in old.files)
            exact[field]=all(np.array_equal(old[k],new[k]) for k in old.files)
            assert all(np.allclose(old[k],new[k],rtol=1e-5,atol=1e-6) for k in old.files)
        results.append({'cell':list(key(r)),'max_abs_error':delta,'bitwise_equal':exact})
    write(dst/'comparison.json',{'status':'pass','scope':'Fresh environment, 24 training trajectories, 32 cells, all 96 generated samples and saved states; duplicates are not pooled as scientific replicates.',
        'original_measurements':ref(ROOT/'analysis/measurements.json'),'replayed_measurements':ref(dst/'analysis/measurements.json'),'cells':results,'complete_cells':32})
    print(json.dumps({'status':'pass','cells':32,'all_bitwise_equal':all(all(r['bitwise_equal'].values()) for r in results)}))

if __name__=='__main__':main()
