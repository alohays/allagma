"""Study environment probe, executed only through the common broker."""
import json, os, platform, sys
from pathlib import Path
import numpy as np
import torch
import matplotlib
import scipy
torch.set_num_threads(1)
Path('evidence').mkdir(exist_ok=True)
out = dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
           numpy=np.__version__, torch=torch.__version__, scipy=scipy.__version__,
           matplotlib=matplotlib.__version__, mps_available=torch.backends.mps.is_available(),
           threads=torch.get_num_threads(), fallback=os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK'),
           mps_high_watermark=os.environ.get('PYTORCH_MPS_HIGH_WATERMARK_RATIO'))
Path('evidence/environment.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out), flush=True)
