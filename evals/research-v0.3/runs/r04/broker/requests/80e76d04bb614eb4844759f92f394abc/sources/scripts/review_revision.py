"""Preserve review v1 and correct two reporting ambiguities without reanalysis."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path('study').resolve()))
from common import ref,write_json
sys.path.insert(0,str(Path('.allagma/bundles/b-9a39b70665ba909edb8abc13').resolve()))
from allagma.composition import review as checklist
from allagma.contracts import validate_record

archive=Path('audit-history/review-001');archive.mkdir(parents=True,exist_ok=False)
for name in ['REPORT.md','review.json','review-input.json','review-findings.json','review-checklist.json','verification.json']:
    shutil.copyfile(name,archive/name)
old=Path('REPORT.md').read_text()
new=old.replace('All four per-seed differences and their intervals are shown above;',
                'The four per-seed differences and intervals for their mean are shown above;')
new=new.replace('Exact coverage and tolerances are in [analysis/primary/validation.json](analysis/primary/validation.json).',
                'Check results and measured discrepancies are in [analysis/primary/validation.json](analysis/primary/validation.json); exact coverage and acceptance tolerances are documented in [REPRODUCE.md](REPRODUCE.md).')
assert new!=old
Path('REPORT.md').write_text(new)
finding={'id':'R10','status':'resolved','severity':'reporting clarity',
 'finding':'The wording could imply confidence intervals for individual seeds, and the validation link named tolerances stored in the reproduction guide.',
 'resolution':'Clarified that intervals describe the mean paired effect and linked the actual tolerance documentation; primary data and analyses are unchanged.',
 'evidence':['REPORT.md','REPRODUCE.md','audit-history/review-001/REPORT.md']}
findings=json.loads(Path('review-findings.json').read_text());findings['findings'].append(finding)
write_json('review-findings.json',findings)
payload=json.loads(Path('review-input.json').read_text());payload['material']=ref('REPORT.md')
write_json('review-input.json',payload)
check=checklist(payload,strict=False);assert check['verdict']=='pass';write_json('review-checklist.json',check)
review=json.loads(Path('review.json').read_text());review['review_id']='c001-r002';review['material']=ref('REPORT.md')
review['findings'].append('R10 (resolved): '+finding['finding']+' '+finding['resolution'])
review['trace']=[ref(t['path']) for t in review['trace']]
validate_record(review);write_json('review.json',review);write_json('campaigns/c001/records/review.json',review)
context=json.loads(Path('campaigns/c001/context-audit.json').read_text())
context['content']['report']=ref('REPORT.md');context['content']['review']=ref('review.json')
write_json('campaigns/c001/context-audit.json',context)
write_json(archive/'revision.json',{'revision':1,'max_revisions':2,'finding':finding,
 'old_report':ref(archive/'REPORT.md'),'new_report':ref('REPORT.md'),
 'history_note':'Archived review and verification retain their original material digests. Their original root-relative material paths refer to the then-current revision; the matching bytes are preserved beside them here.',
 'analysis_unchanged':True,'next_step':'Re-run current-material verification before packaging.'})
print(json.dumps({'review_revision':2,'editorial_revision_cycles':1,'analysis_unchanged':True}))
