"""NumPy/ctypes interface to the retained float32 native engine."""
from pathlib import Path
import ctypes as C
import numpy as np

FP=C.POINTER(C.c_float);IP=C.POINTER(C.c_int)
def fp(a):
    assert a.dtype==np.float32 and a.flags.c_contiguous
    return a.ctypes.data_as(FP)
def ip(a):
    assert a.dtype==np.int32 and a.flags.c_contiguous
    return a.ctypes.data_as(IP)

class Engine:
    def __init__(self,pairs,labels,u,v,library='build/engine.dylib',state=None):
        self.lib=C.CDLL(str(Path(library).resolve()))
        self.lib.engine_create.argtypes=[C.c_int];self.lib.engine_create.restype=C.c_void_p
        self.lib.engine_free.argtypes=[C.c_void_p]
        self.lib.engine_forward.argtypes=[C.c_int,IP,FP,FP,FP,FP]
        self.lib.engine_grad.argtypes=[C.c_void_p,IP,IP,FP,FP,FP,FP]
        self.lib.engine_steps.argtypes=[C.c_void_p,IP,IP,FP,FP,FP,FP,FP,FP,C.c_int,C.c_int,C.c_float]
        self.pairs=np.ascontiguousarray(pairs,dtype=np.int32);self.labels=np.ascontiguousarray(labels,dtype=np.int32)
        self.u=np.ascontiguousarray(u,dtype=np.float32).copy();self.v=np.ascontiguousarray(v,dtype=np.float32).copy()
        for name,array in [('m1',self.u),('q1',self.u),('m2',self.v),('q2',self.v)]:
            setattr(self,name,np.zeros_like(array) if state is None else np.ascontiguousarray(state[name]).copy())
        self.step=0 if state is None else int(state['step'])
        self.work=self.lib.engine_create(len(self.pairs))
    def close(self):
        if self.work:self.lib.engine_free(self.work);self.work=None
    def forward(self,pairs):
        pp=np.ascontiguousarray(pairs,dtype=np.int32)
        h=np.empty((len(pp),128),np.float32);z=np.empty((len(pp),97),np.float32)
        self.lib.engine_forward(len(pp),ip(pp),fp(self.u),fp(self.v),fp(h),fp(z))
        return z
    def gradients(self):
        g1=np.empty_like(self.u);g2=np.empty_like(self.v)
        self.lib.engine_grad(self.work,ip(self.pairs),ip(self.labels),fp(self.u),fp(self.v),fp(g1),fp(g2))
        return g1,g2
    def advance(self,count,weight_decay):
        self.lib.engine_steps(self.work,ip(self.pairs),ip(self.labels),fp(self.u),fp(self.v),fp(self.m1),fp(self.q1),fp(self.m2),fp(self.q2),self.step,count,float(weight_decay))
        self.step+=count
    def state(self):
        return {'u':self.u,'v':self.v,'m1':self.m1,'q1':self.q1,'m2':self.m2,'q2':self.q2,'step':np.array(self.step,dtype=np.int64)}

def make_data(seed):
    pairs=np.stack(np.meshgrid(np.arange(97),np.arange(97),indexing='ij'),axis=-1).reshape(-1,2).astype(np.int32)
    labels=(pairs[:,0]+pairs[:,1])%97
    order=np.random.default_rng(seed).permutation(9409)
    return pairs,labels,order[:2822],order[2822:]

def initial(seed):
    import torch
    generator=torch.Generator(device='cpu').manual_seed(seed)
    u=torch.empty((128,194),dtype=torch.float32).uniform_(-194**-.5,194**-.5,generator=generator)
    v=torch.empty((97,128),dtype=torch.float32).uniform_(-128**-.5,128**-.5,generator=generator)
    return np.ascontiguousarray(u.numpy().T),np.ascontiguousarray(v.numpy())

def metrics(logits,labels,train,test):
    result={}
    for name,ix in [('train',train),('test',test)]:
        z=logits[ix].astype(np.float64);y=labels[ix]
        m=z.max(1)
        loss=m+np.log(np.exp(z-m[:,None]).sum(1))-z[np.arange(len(ix)),y]
        result[name+'_accuracy']=float((z.argmax(1)==y).mean())
        result[name+'_loss']=float(loss.mean())
    return result
