"""Retain v1 and make a narrow, explicit numerical-validation correction."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path('study').resolve()))
from common import ref,write_json

source=Path('study/analyze.py').read_text()
old1="assert metric_error<1e-5,(r['seed'],metric_error)"
new1="assert all(np.isclose(metrics[k],r['metrics'][k],atol=1e-6,rtol=1e-6) for k in metrics),(r['seed'],metric_error)"
old2="assert all(abs(curve[-1][k]-metrics[k])<1e-5 for k in metrics)"
new2="assert all(np.isclose(curve[-1][k],metrics[k],atol=1e-6,rtol=1e-6) for k in metrics)"
assert source.count(old1)==1 and source.count(old2)==1
target=Path('scripts/analyze_v1_1.py')
assert not target.exists()
# An explicit import path is the only non-validation change to make the copied
# script runnable from its revision directory.
source=source.replace('import numpy as np','import sys\nsys.path.insert(0,str(Path("study").resolve()))\nimport numpy as np',1)
target.write_text(source.replace(old1,new1).replace(old2,new2))
write_json('campaigns/c001/amendments/evaluator-v1.1.json',{
 'revision':'evaluator-v1.1','kind':'numerical validation tolerance correction; primary analysis unchanged',
 'reason':'Float32 mean cross-entropy at large loss has larger absolute rounding than a fixed 1e-5 bound. Reuse check failed even with bitwise identical checkpoint logits. Use atol=1e-6 plus rtol=1e-6; report all measured discrepancies.',
 'trigger_receipt':ref('.compute/responses/4b0598c1039944fa8eaea9b0d46a1071.json'),
 'old_analyzer':ref('study/analyze.py'),'new_analyzer':ref(target),
 'affected_runs':['s1001-wd0','s1001-wd1','s1002-wd0','s1002-wd1','s1003-wd0','s1003-wd1','s1004-wd0','s1004-wd1'],
 'handoff_contract':'Existing and future c001 raw training evidence remains eligible: no model, split, optimizer, seed, horizon, transition rule, uncertainty formula or computed endpoint is changed. Only comparison acceptance tolerance changes; float64 recomputed values are still the reported metrics.',
 'validation':'Check every final checkpoint/NPZ logits exactly, compare independent NumPy forward and metrics, and rerun analysis twice. Keep original analyzer frozen and executable for historical inspection.'})
print(json.dumps({'new_analyzer':str(target),'primary_protocol_unchanged':True}))
