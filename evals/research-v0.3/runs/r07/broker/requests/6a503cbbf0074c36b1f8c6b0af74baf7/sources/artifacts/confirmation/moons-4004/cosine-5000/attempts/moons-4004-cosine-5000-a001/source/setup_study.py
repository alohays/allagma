"""Study-owned setup; invoke only through inputs/compute.py --category setup."""
import json
import os
from pathlib import Path
import platform
import shutil
import sys

root = Path.cwd()
campaign = root / 'campaigns/ema-schedule-v1'
campaign.mkdir(parents=True, exist_ok=True)
for name in ('evidence', 'study', 'artifacts/pilot', 'artifacts/confirmation', '.tmp/mpl'):
    (root/name).mkdir(parents=True, exist_ok=True)
if not (campaign/'lock.yaml').exists():
    shutil.copyfile(root/'.allagma/lock.yaml', campaign/'lock.yaml')
for source, dest in [('science.py', 'study/science.py'), ('LICENSE', 'LICENSE-AI-SCIENTIST')]:
    if not (root/dest).exists():
        shutil.copyfile(root/'inputs/materials/prior-study'/source, root/dest)
lock = json.loads((campaign/'lock.yaml').read_text())
bundle = root/'.allagma/bundles'/lock['bundle_id']
sys.path.insert(0, str(bundle))
from allagma.bundles import resolve_entry
entries = {module: resolve_entry(root, module, 'ema-schedule-v1') for module in lock['modules']}
(campaign/'method-resolution.json').write_text(json.dumps(entries, indent=2)+'\n')
os.environ['MPLCONFIGDIR'] = str(root/'.tmp/mpl')
import numpy as np
import torch
import scipy
import matplotlib
torch.set_num_threads(1)
env = {'python': platform.python_version(), 'platform': platform.platform(),
       'numpy': np.__version__, 'torch': torch.__version__, 'scipy': scipy.__version__,
       'matplotlib': matplotlib.__version__, 'mps_available': torch.backends.mps.is_available(),
       'threads': torch.get_num_threads(), 'bundle_id': lock['bundle_id'],
       'lock_id': lock['lock_id'], 'selection_intent_matches': True}
(root/'evidence/environment.json').write_text(json.dumps(env, indent=2)+'\n')
print(json.dumps(env))
