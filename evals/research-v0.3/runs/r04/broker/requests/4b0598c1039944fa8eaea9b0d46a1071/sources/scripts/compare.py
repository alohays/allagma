"""Compare deterministic analysis JSONs between separate output directories."""
import hashlib
import json
from pathlib import Path
import sys
a,b=map(Path,sys.argv[1:3])
checks={}
for name in ['summary.json','per-seed.json','validation.json','raw-manifest.json']:
    aa,bb=(a/name).read_bytes(),(b/name).read_bytes()
    checks[name]={'identical_bytes':aa==bb,'sha256':hashlib.sha256(aa).hexdigest()}
    assert aa==bb,name
output={'passed':True,'primary':str(a),'recomputed':str(b),'checks':checks,
        'coverage':'All endpoint, paired-effect, uncertainty, transition, sensitivity, verification and raw-manifest JSON values. Figures are regenerated; image bytes are not a numerical equality criterion.'}
(b/'comparison.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
