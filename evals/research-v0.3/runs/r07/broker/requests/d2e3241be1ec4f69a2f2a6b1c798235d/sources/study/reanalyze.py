"""A second output directory from the same immutable raw evidence."""
import json
from analyze import analyze

summary=analyze('artifacts','reanalysis')
print(json.dumps({'effects':[{k:e[k] for k in ('dataset','variant','contrast','schedule','updates','mean','ci95','sign_flip_p') if k in e} for e in summary['effects']],
    'absolute_cells':[{k:e[k] for k in ('dataset','variant','schedule','updates','mean') if k in e} for e in summary['absolute_sw1'] if e['contrast']=='cell'],
    'coverage':summary['coverage']},indent=2))
