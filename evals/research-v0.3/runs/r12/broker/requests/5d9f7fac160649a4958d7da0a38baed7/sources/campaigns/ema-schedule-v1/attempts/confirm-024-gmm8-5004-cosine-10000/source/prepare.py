"""AI-generated study setup. Execute only through inputs/compute.py (setup)."""
import json
from pathlib import Path
import shutil
import sys
import hashlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.allagma/bundles/b-9a39b70665ba909edb8abc13'))
from allagma.bundles import verify_study, resolve_entry

def main():
    lock = verify_study(ROOT)
    campaign = ROOT / 'campaigns/ema-schedule-v1'
    campaign.mkdir(parents=True, exist_ok=True)
    for source, dest in [('.allagma/lock.yaml', campaign/'lock.yaml'),
                         ('inputs/materials/prior-study/science.py', ROOT/'study/reference.py'),
                         ('inputs/materials/prior-study/LICENSE', ROOT/'LICENSE-AI-Scientist'),
                         ('protocol.json', campaign/'protocol.json')]:
        if dest.exists():
            assert dest.read_bytes() == (ROOT/source).read_bytes(), str(dest)
        else:
            shutil.copyfile(ROOT/source, dest)
    entries = {m: resolve_entry(ROOT, m, 'ema-schedule-v1') for m in
               ['recipe/research','context','research/scope','research/protocol',
                'research/experiment','research/analysis','research/writing','research/audit','runner','reviewer']}
    (campaign/'resolved-methods.json').write_text(json.dumps(entries,indent=2)+'\n')
    snapshot = campaign/'pilot-source'
    snapshot.mkdir(exist_ok=True)
    for f in (ROOT/'study').glob('*.py'):
        shutil.copyfile(f, snapshot/f.name)
    print(json.dumps({'bundle_id':lock['bundle_id'], 'campaign':str(campaign.relative_to(ROOT)), 'status':'prepared'}))

if __name__ == '__main__': main()
