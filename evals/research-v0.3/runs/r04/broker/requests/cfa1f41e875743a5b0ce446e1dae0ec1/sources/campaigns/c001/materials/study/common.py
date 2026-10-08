"""Study-owned deterministic data, model, artifact and metric functions."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    p = Path(path)
    return {'path':p.as_posix(),'sha256':sha(p),'media_type':'application/json' if p.suffix=='.json' else 'application/octet-stream','retention':'retained'}

def source_revision():
    files = sorted(Path('study').glob('*.py'))
    return hashlib.sha256(''.join(f'{p}:{sha(p)}\n' for p in files).encode()).hexdigest()

def configure():
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)

def data(seed):
    pairs = np.array([(a,b) for a in range(97) for b in range(97)],dtype=np.int64)
    labels = (pairs[:,0]+pairs[:,1]) % 97
    perm = np.random.default_rng(seed).permutation(len(pairs))
    return pairs,labels,perm[:2822],perm[2822:]

def inputs(pairs):
    return F.one_hot(torch.from_numpy(pairs),num_classes=97).float().reshape(-1,194)

def model(seed):
    torch.manual_seed(seed)
    return torch.nn.Sequential(torch.nn.Linear(194,128,bias=False),torch.nn.ReLU(),torch.nn.Linear(128,97,bias=False))

def optimizer(net,wd):
    return torch.optim.AdamW(net.parameters(),lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=wd,foreach=False)

def state_np(net):
    return {'input_weight':net[0].weight.detach().cpu().numpy().copy(),
            'output_weight':net[2].weight.detach().cpu().numpy().copy()}

def state_hash(net):
    h = hashlib.sha256()
    for name,arr in state_np(net).items():
        h.update(name.encode()+str(arr.shape).encode()+str(arr.dtype).encode()+arr.tobytes())
    return h.hexdigest()

@torch.no_grad()
def evaluate(net,x,y,tr,te,step):
    logits = net(x)
    row={'step':step}
    for name,ix in [('train',tr),('test',te)]:
        z,t=logits[ix],y[ix]
        row[name+'_accuracy']=float((z.argmax(1)==t).double().mean().item())
        row[name+'_loss']=float(F.cross_entropy(z,t).item())
    return row,logits.numpy().copy()

def numpy_metrics(logits,labels,tr,te):
    z=logits.astype(np.float64)
    mx=z.max(axis=1)
    losses=mx+np.log(np.exp(z-mx[:,None]).sum(axis=1))-z[np.arange(len(z)),labels]
    correct=z.argmax(axis=1)==labels
    return {f'{name}_{metric}':float(value[ix].mean()) for name,ix in [('train',tr),('test',te)]
            for metric,value in [('accuracy',correct),('loss',losses)]}
