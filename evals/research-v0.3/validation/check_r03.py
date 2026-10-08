"""Independent checks of r03 paired statistics, transitions and saved optimizer state."""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t
import torch

root=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
measurements=json.loads((root/'analysis/measurements.json').read_text())
analysis=json.loads((root/'analysis/results.json').read_text())
observations=[]
for run in measurements['runs']:
    curve=run['curve']
    assert len(curve)==1001 and [r['step'] for r in curve]==list(range(0,100001,100))
    memorization=next(curve[i]['step'] for i in range(len(curve)-2)
                      if all(r['train_accuracy']>=.99 for r in curve[i:i+3]))
    maximum=max(r['test_accuracy'] for r in curve)
    assert maximum<.9
    transition=next(r for r in analysis['primary_transitions'] if r['seed']==run['seed'] and r['weight_decay']==run['weight_decay'])
    assert transition['memorization']['onset_step']==memorization
    assert transition['generalization']['onset_step'] is None and transition['generalization']['censor_step']==100000
    assert transition['lag_updates'] is None and not transition['delayed_grokking']
    path=root/run['weights']
    checkpoint=torch.load(path.with_name('checkpoint.pt'),map_location='cpu',weights_only=True)
    assert checkpoint['step']==100000
    assert all(int(value['step'])==100000 for value in checkpoint['optimizer']['state'].values())
    with np.load(path,allow_pickle=False) as weights:
        assert np.array_equal(checkpoint['model']['input.weight'].numpy(),weights['input_weight'])
        assert np.array_equal(checkpoint['model']['output.weight'].numpy(),weights['output_weight'])
    observations.append({'seed':run['seed'],'weight_decay':run['weight_decay'],'memorization_onset':memorization,
                         'maximum_heldout_accuracy':maximum,'checkpoint_and_optimizer_updates':100000})
effects={}
for metric in ['test_accuracy','test_loss']:
    differences=[]
    for seed in range(1001,1005):
        rows={r['weight_decay']:r for r in measurements['runs'] if r['seed']==seed}
        differences.append(rows[1]['metrics'][metric]-rows[0]['metrics'][metric])
    x=np.asarray(differences,dtype=np.float64);mean=float(x.mean());sd=float(x.std(ddof=1))
    interval=[mean-float(t.ppf(.975,3))*sd/2,mean+float(t.ppf(.975,3))*sd/2]
    probability=sum(abs(float(np.mean(x*np.array(signs))))>=abs(mean)-1e-14
                    for signs in itertools.product([-1,1],repeat=4))/16
    expected=analysis['effects'][metric]
    np.testing.assert_allclose(expected['ci95'],interval,rtol=1e-12,atol=1e-12)
    assert abs(expected['mean']-mean)<1e-12 and expected['exact_sign_flip_p']==probability
    effects[metric]={'mean':mean,'ci95':interval,'exact_sign_flip_p':probability,'independent_units':4}
result={'status':'pass','completed_cells':len(observations),'observations':observations,'effects':effects,
        'scope':'Independent endpoint effects/t intervals/sign flips, complete curve grid, memorization/censoring, all final optimizer counters and safe checkpoint-to-NPZ identity. No second training replay.'}
if output.exists():raise RuntimeError('Use a new validation receipt')
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','completed_cells':len(observations),'effects':effects}))
