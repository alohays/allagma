"""Known-answer controls for transition/censoring and paired analysis logic."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from analyze import transitions,uncertainty,endpoint_metrics

def curve(train_at=200,test_at=1500):
    return [{'step':s,'train_accuracy':.99 if s>=train_at else .1,'test_accuracy':.95 if s>=test_at else .1,'train_loss':1.,'test_loss':1.} for s in range(0,2001,100)]

def main():
    base=curve();r=transitions(base)
    assert r['memorization']['time']==200 and r['memorization']['confirmation_time']==400
    assert r['generalization']['time']==1500 and r['generalization']['confirmation_time']==1700
    assert r['lag']==1300 and r['delayed_grokking']
    assert not transitions(curve(test_at=200))['delayed_grokking']
    late=transitions(curve(test_at=1900))
    assert late['generalization']['time'] is None and late['generalization']['censor_time']==2000
    assert late['lag'] is None and late['lag_lower_bound_exclusive']==1600
    spike=curve(test_at=9999);spike[15]['test_accuracy']=.99
    assert not transitions(spike)['generalization']['observed']
    dip=curve();dip[9]['train_accuracy']=.98
    assert not transitions(dip)['delayed_grokking']
    no_mem=curve(train_at=9999)
    assert transitions(no_mem)['memorization']['time'] is None and transitions(no_mem)['lag'] is None
    assert transitions(curve(test_at=1900),sustain=1)['generalization']['time']==1900
    u=uncertainty([1,2,3,4]);assert u['n']==4 and u['mean']==2.5
    assert abs(u['sample_sd']-math.sqrt(5/3))<1e-14 and u['exact_signflip_two_sided_p']==.125
    m=endpoint_metrics(np.zeros((4,97),np.float32),np.array([0,1,0,1]),np.array([0,1]),np.array([2,3]))
    assert m['train_accuracy']==m['test_accuracy']==.5
    assert abs(m['train_loss']-math.log(97))<1e-14 and m['train_loss']==m['test_loss']
    result={'status':'passed','controls':['First-point onset and third-point confirmation','Inclusive .99/.95 thresholds','Delayed versus simultaneous transitions','Final-window right censoring without invented time','Isolated spike rejected','Training dip disqualifies continuous-memorization criterion','Missing memorization yields missing lag','Single-point sensitivity','Four-unit paired mean/SD and exact sign-flip enumeration','Uniform-logit known-answer cross-entropy and accuracy'],'analysis_sha256':hashlib.sha256(Path('study/analyze.py').read_bytes()).hexdigest()}
    Path('evidence/analysis-controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
