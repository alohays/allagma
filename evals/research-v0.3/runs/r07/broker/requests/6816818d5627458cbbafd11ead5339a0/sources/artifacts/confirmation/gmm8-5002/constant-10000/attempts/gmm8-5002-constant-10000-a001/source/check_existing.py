"""Validate successful artifact digests before dispatcher skip/resume."""
import argparse
import json
from common import ROOT,sha

p=argparse.ArgumentParser();p.add_argument('--base',required=True);args=p.parse_args()
count=0
for path in (ROOT/args.base/'confirmation').glob('*/*/attempts/*/result.json'):
    result=json.loads(path.read_text())
    assert result['status']=='succeeded'
    for item in result['outputs']:
        assert sha(ROOT/item['path'])==item['sha256'],item['path']
    for cell_path in result['measurements']:
        cell=json.loads((ROOT/cell_path).read_text())
        assert cell['attempt_id']==result['attempt_id']
    count+=1
print(json.dumps({'successful_attempts_verified':count}))
