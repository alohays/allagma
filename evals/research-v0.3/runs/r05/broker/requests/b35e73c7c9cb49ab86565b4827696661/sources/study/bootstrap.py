"""Campaign selection and canonical method resolution; no scientific work."""
from pathlib import Path
import json, shutil, sys, hashlib
root=Path.cwd()
lock=json.loads((root/'.allagma/lock.yaml').read_text())
campaign=root/'campaigns/modular-addition'
campaign.mkdir(parents=True,exist_ok=True)
target=campaign/'lock.yaml'
if target.exists():
    assert json.loads(target.read_text())==lock
else:
    shutil.copyfile(root/'.allagma/lock.yaml',target)
bundle=root/'.allagma/bundles'/lock['bundle_id']
sys.path.insert(0,str(bundle))
from allagma.bundles import resolve_entry,verify_study
verify_study(root)
methods=['recipe/research','context/active-brief','research/scope','research/protocol','research/experiment','research/analysis','research/writing','research/audit','runner','reviewer']
entries=[resolve_entry(root,method,'modular-addition') for method in methods]
(campaign/'resolved-methods.json').write_text(json.dumps(entries,indent=2)+'\n')
print(json.dumps({'campaign':str(campaign.relative_to(root)),'bundle_id':lock['bundle_id'],'methods_resolved':len(entries),'selection_intent':'matches study lock'}))
