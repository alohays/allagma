"""Compare deterministic analysis JSONs between separate output directories."""
import hashlib
import json
from pathlib import Path
import sys
a,b=map(Path,sys.argv[1:3])
checks={}
for directory in [a,b]:
    rows=json.loads((directory/'per-seed.json').read_text())
    sensitivity=[]
    for variant in rows[0]['sensitivity']:
        name,value=variant['varied'],variant['value']
        outcomes=[next(v['outcome'] for v in row['sensitivity'] if v['varied']==name and v['value']==value) for row in rows]
        sensitivity.append({'varied':name,'value':value,'generalized_count':sum(x['generalization']['event'] for x in outcomes),
                            'delayed_grokking_count':sum(x['delayed_grokking_observed'] for x in outcomes),'n_runs':len(outcomes)})
    encoded=json.dumps(sensitivity,indent=2,allow_nan=False)+'\n'
    target=directory/'sensitivity-summary.json'
    if target.exists():assert target.read_text()==encoded
    else:target.write_text(encoded)
for name in ['summary.json','per-seed.json','validation.json','raw-manifest.json','sensitivity-summary.json']:
    aa,bb=(a/name).read_bytes(),(b/name).read_bytes()
    checks[name]={'identical_bytes':aa==bb,'sha256':hashlib.sha256(aa).hexdigest()}
    assert aa==bb,name
output={'passed':True,'primary':str(a),'recomputed':str(b),'checks':checks,
        'coverage':'All endpoint, paired-effect, uncertainty, transition, sensitivity, verification and raw-manifest JSON values. Figures are regenerated; image bytes are not a numerical equality criterion.'}
(b/'comparison.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
