"""Prove parser correction leaves all frozen numerical calculations unchanged."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

repo=Path(__file__).resolve().parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
original=load('original_score',repo/'evals/research-v0.3/frozen/source/evals/research-v0.3/score.py')
corrected=load('corrected_score',repo/'evals/research-v0.3/score_curve_compat.py')
workspace=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve()
data=json.loads((workspace/'analysis/measurements.json').read_text())
paths=copy.deepcopy(data)
for run in paths['runs']:
    assert isinstance(run['curve'],list)
    assert json.loads((workspace/run['curve_path']).read_text())==run['curve']
    run['curve']=run['curve_path']
before=original.score_grok(workspace,paths)
after=corrected.score_grok(workspace,data)
assert before==after
assert before['correct']==before['total']==40 and not before['errors']
result={'status':'pass','checks':40,'scope':'Frozen scorer with existing equivalent curve-file references equals corrected scorer with the specified inline JSON lists; candidate artifacts unchanged.','candidate_files_modified':False}
if output.exists():raise RuntimeError('Preserve existing correction validation')
output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
