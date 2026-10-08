"""Archived original reuse check; retained because its absolute tolerance failed."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path('study').resolve()))
import numpy as np
import torch
from common import configure,model,inputs,numpy_metrics
configure()
r=json.loads(Path(sys.argv[1]).read_text())
assert r['complete'] and r['updates']==100000
a=np.load(r['arrays'],allow_pickle=False)
net=model(r['seed']);ck=torch.load(r['checkpoint'],map_location='cpu',weights_only=False)
net.load_state_dict(ck['model'])
with torch.no_grad():assert np.array_equal(net(inputs(a['pairs'])).numpy(),a['logits'])
assert np.array_equal(a['predictions'],a['logits'].argmax(1))
metrics=numpy_metrics(a['logits'],a['labels'],a['train_indices'],a['test_indices'])
assert all(abs(metrics[k]-r['metrics'][k])<1e-5 for k in metrics)
manifest=Path('artifact-manifest.json')
if manifest.exists():
    entries={x['path']:x for x in json.loads(manifest.read_text())['files']}
    for key in ['arrays','weights','checkpoint','curve','initial_weights']:
        path=r[key]
        assert path in entries and hashlib.sha256(Path(path).read_bytes()).hexdigest()==entries[path]['sha256']
print(json.dumps({'validated':sys.argv[1],'step':100000}))
