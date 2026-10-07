"""Single-case and paired-condition policies belong to the study, not core math."""
from pathlib import Path
import tempfile
import unittest

from allagma import campaigns
from allagma.demo import create_toy
from allagma.files import AllagmaError,read_json,write_json

ROOT=Path(__file__).resolve().parents[1]

ANALYZER='''import json,sys
from pathlib import Path
root,manifest,output=map(Path,sys.argv[1:])
raw=json.loads(manifest.read_text())
output.mkdir(parents=True)
(output/'summary.json').write_text(json.dumps({'eligible_runs':len(raw['raw']),'uncertainty':'No population inference for this deterministic counting check'},sort_keys=True)+'\\n')
'''
WRITER='''import hashlib,json,sys
from pathlib import Path
root,analysis,output=map(Path,sys.argv[1:])
record=json.loads(analysis.read_text());summary=root/record['outputs'][0]['path']
value=json.loads(summary.read_text())
def ref(path):
 return {'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'media_type':'application/json','retention':'retain-with-study'}
claim={'schema_version':'0.2','record_type':'ClaimRecord','claim_id':'count','text':str(value['eligible_runs'])+' eligible run',
 'supporting':[ref(summary)],'contradicting':[],'dependencies':[ref(analysis)],'scope':'This deterministic fixture only',
 'limitations':['No population uncertainty estimated'],'status':'supported','supersedes':None}
output.mkdir(parents=True)
(output/'claims.json').write_text(json.dumps([claim],sort_keys=True)+'\\n')
(output/'manuscript.md').write_text(str(value['eligible_runs'])+' eligible deterministic run. No population inference.\\n')
'''


class StudyAnalysisPolicy(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.study=create_toy(ROOT,Path(self.temporary.name)/'study')
        self.protocol=read_json(self.study/'protocol.json')

    def test_one_confirmation_case_completes_analysis_and_audit(self):
        pilot=next(r for r in self.protocol['runs'] if r['split']=='pilot')
        confirmation=next(r for r in self.protocol['runs'] if r['split']=='confirmation')
        self.protocol['runs']=[pilot,confirmation]
        self.protocol.pop('minimum_confirmation_runs',None)
        self.protocol['uncertainty']='No population inference; deterministic fixture count only'
        (self.study/self.protocol['analyzer']).write_text(ANALYZER)
        (self.study/self.protocol['writer']).write_text(WRITER)
        write_json(self.study/'protocol.json',self.protocol)
        campaigns.start_campaign(self.study,'one-case')
        campaigns.run_campaign(self.study,'one-case')
        result=campaigns.analyze_campaign(self.study,'one-case')
        self.assertEqual(result['configuration']['minimum_confirmation_runs'],1)
        self.assertEqual(campaigns.audit_campaign(self.study,'one-case')['verdict'],'pass')

    def test_declared_larger_minimum_still_blocks_partial_analysis(self):
        self.protocol['minimum_confirmation_runs']=100
        write_json(self.study/'protocol.json',self.protocol)
        campaigns.start_campaign(self.study,'minimum')
        campaigns.run_campaign(self.study,'minimum',stop_after=3)
        with self.assertRaisesRegex(AllagmaError,'at least 100'):
            campaigns.analyze_campaign(self.study,'minimum',allow_partial=True)

    def test_paired_seed_requires_explicit_distinct_conditions(self):
        self.protocol['paired_seeds']=True
        confirmations=[r for r in self.protocol['runs'] if r['split']=='confirmation']
        confirmations[1]['input']['seed']=confirmations[0]['input']['seed']
        write_json(self.study/'protocol.json',self.protocol)
        with self.assertRaisesRegex(AllagmaError,'condition_id'):
            campaigns.start_campaign(self.study,'paired-invalid')
        confirmations[0]['condition_id']='baseline';confirmations[1]['condition_id']='treatment'
        write_json(self.study/'protocol.json',self.protocol)
        campaigns.start_campaign(self.study,'paired-valid')
        value=read_json(self.study/'campaigns/paired-valid/protocol.json')
        self.assertTrue(value['paired_seeds'])


if __name__=='__main__':unittest.main()
