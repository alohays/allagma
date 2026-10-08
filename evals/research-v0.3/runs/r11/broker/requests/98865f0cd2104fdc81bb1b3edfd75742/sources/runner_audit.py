"""Pilot-only resumption/pairing audit before opening confirmation."""
import json
from pathlib import Path
import numpy as np
from study import json_write, array_hash

def main():
    resumed=Path('evidence/cells/pilot/gmm8-81-cosine-2000/update-2000')
    full=Path('evidence/pilot-equivalence/cells/pilot/gmm8-81-cosine-2000/update-2000')
    comparisons=[]
    for name in ('arrays.npz','weights.npz'):
        with np.load(resumed/name,allow_pickle=False) as a,np.load(full/name,allow_pickle=False) as b:
            assert set(a.files)==set(b.files)
            for key in a.files:
                error=float(np.max(np.abs(a[key]-b[key])))
                assert error<=1e-6, f'{name}:{key}: {error}'
                comparisons.append(dict(file=name,key=key,max_absolute_error=error,exact_equal=bool(np.array_equal(a[key],b[key]))))
    r1=json.loads((resumed/'record.json').read_text());r2=json.loads((full/'record.json').read_text())
    for key in ('initial_weights_sha256','training_prefix_5000_sha256','heldout_sha256','generation_noise_sha256'):assert r1[key]==r2[key]
    first=[json.loads(x) for x in Path('evidence/attempts/pilot-gmm8-segment1/trace.jsonl').read_text().splitlines()]
    second=[json.loads(x) for x in Path('evidence/attempts/pilot-gmm8-segment2/trace.jsonl').read_text().splitlines()]
    assert first[0]['step']==1 and first[-1]['step']==1000 and second[0]['step']==1001 and second[-1]['step']==2000
    assert first[0]['lr']==.0003 and second[-1]['lr']==0
    json_write('evidence/runner-audit.json',dict(status='passed',confirmation_data_used=False,
               resume_equivalence=comparisons,trace_update_ranges=[[1,1000],[1001,2000]],
               matched_provenance=True,duplicate_pilot_not_an_independent_replicate=True))
    print(json.dumps(dict(status='passed',comparisons=len(comparisons),max_absolute_error=max(x['max_absolute_error'] for x in comparisons))))

if __name__=='__main__':main()
