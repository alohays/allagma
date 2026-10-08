"""Bind verified numerical results, manuscript, claims and the locked reviewer."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
from ledger import main as ledger_main
from report import make_report

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,o):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(o,indent=2,allow_nan=False)+'\n')
def ref(p):return {'path':str(p),'sha256':sha(p),'media_type':'application/json' if Path(p).suffix=='.json' else 'text/plain','retention':'retained'}

def main():
    ledger_main()
    comparison=json.loads(Path('analysis-repeat/recomputation-comparison.json').read_text());assert all(comparison.values())
    results=json.loads(Path('analysis/results.json').read_text());verification=json.loads(Path('analysis/verification.json').read_text())
    assert results['execution_status']=='complete' and results['n_complete_pairs']==4
    assert len(verification['checks'])==8 and all(c['checkpoint_predictions_exact'] for c in verification['checks'])
    shutil.copyfile('analysis/measurements.json','measurements.json')
    summary=make_report()
    c=Path('campaigns/modular-addition');lock=json.loads((c/'lock.yaml').read_text());bundle=Path('.allagma/bundles')/lock['bundle_id']
    sys.path.insert(0,str(bundle))
    from allagma.contracts import validate_record
    analysis={'schema_version':'0.2','record_type':'AnalysisRecord','analysis_id':'retained-data-v1','raw_manifest':ref('analysis/raw-manifest.json'),'analysis_revision':sha('study/analyze.py'),'code':ref('study/analyze.py'),'configuration':{'protocol':ref(c/'protocol.json'),'independent_unit':'paired seed','n':4,'uncertainty':'approximate paired t interval; exact sign-flip sensitivity'},'outputs':[ref(p) for p in sorted(Path('analysis').iterdir()) if p.is_file()],'exclusions':[{'path':str(p),'reason':'pilot, excluded from confirmation'} for p in sorted(Path('evidence').glob('pilot-*'))],'uncertainty':results['uncertainty_scope'],'dependencies':[ref(c/'protocol.json'),ref('analysis-repeat/recomputation-comparison.json')]}
    validate_record(analysis);dump(c/'analysis-record.json',analysis)
    claims=[]
    texts=[('memorization',f"Memorization met the frozen criterion in {summary['memory']}/8 confirmation cells.",'supported'),
           ('endpoint-effect',f"Across four paired seeds, decay 1 minus decay 0 changed held-out accuracy by {summary['accuracy']['mean']:.12g} and loss by {summary['loss']['mean']:.12g} at 100000 updates.",'supported'),
           ('delayed-grokking',f"The primary delayed-grokking criterion was observed in {summary['grokking']}/8 cells by the fixed horizon; absent events are right-censored.",'supported'),
           ('generalization-threshold',f"The primary sustained 95% held-out-accuracy threshold was observed in {summary['generalization']}/8 cells by 100000 updates.",'supported')]
    for name,text,status in texts:
        claim={'schema_version':'0.2','record_type':'ClaimRecord','claim_id':name,'text':text,'supporting':[ref('analysis/results.json'),ref('analysis/verification.json')],'contradicting':[],'dependencies':[ref('analysis/raw-manifest.json'),ref(c/'protocol.json'),ref('study/analyze.py')],'scope':'Four prescribed paired seeds, float32 bias-free MLP, fixed modular-addition split and 100000-update horizon','limitations':['Small seed count and approximate t intervals','Finite horizon and operational transition definition','Native float32 backend not a full transformer replication','Author critique is not independent peer review'],'status':status,'supersedes':None}
        validate_record(claim);claims.append(claim);dump(c/'claims'/(name+'.json'),claim)
    payload={'study':'.','material':ref('REPORT.md'),'claims':claims,'criteria':['Exact eight-cell fixed horizon','No held-out optimization or adaptive confirmation selection','Four paired seeds and explicit uncertainty','Censoring and primary/sensitivity definitions','Raw logits, checkpoints and repeated analysis','Material/evidence hashes and explicit review scope']}
    dump('review-input.json',payload)
    adapter=bundle/'adapters/reviewer-checklist/review.py'
    subprocess.run([sys.executable,str(adapter),'review-input.json','review-checklist.json'],check=True)
    checklist=json.loads(Path('review-checklist.json').read_text());assert checklist['verdict']=='pass'
    critique=json.loads(Path('study/critique-template.json').read_text());critique['material']=ref('REPORT.md')
    critique['verification_passed']=True
    for finding in critique['findings']:
        if finding['status']=='resolved_by_verification':finding['status']='resolved'
    dump('critique.json',critique)
    review={'schema_version':'0.2','record_type':'ReviewRecord','review_id':'modular-addition-review-v1','reviewer':'Locked Allagma checklist plus author scientific critique','backend':'reviewer/checklist; study-owned numerical audit; author reasoning','backend_version':lock['modules']['reviewer/checklist']['revision'],'material':ref('REPORT.md'),'criteria':payload['criteria'],'verdict':'pass','findings':[f"{f['id']} [{f['status']}]: {f['finding']} {f['resolution']}" for f in critique['findings']],'trace':[ref('review-input.json'),ref('review-checklist.json'),ref('critique.json'),ref('analysis/verification.json'),ref('analysis-repeat/recomputation-comparison.json')],'assurance':'provisional','coverage':checklist['coverage']+' Study-owned checks additionally cover all final arrays, exact partitions, predictions from saved weights, eight independent PyTorch checkpoint reloads, source/protocol/parent hashes and repeated numerical analysis. Scientific interpretation is author-reviewed, not independent peer review. Historical gradient trajectories and a second fresh training campaign were not independently replayed.'}
    validate_record(review);dump('review.json',review)
    submission={'task_id':'modular-addition','execution_status':'complete','manuscript':'REPORT.md','review':'review.json','artifact_manifest':'artifact-manifest.json','measurements':'measurements.json','reproduce':{'argv':['python3','study/reproduce.py','--output','reproduced-study'],'cwd':'.'},'recompute':{'argv':['python3','inputs/compute.py','--category','compute','--label','retained-data-recompute','--timeout','60','--','.venv/bin/python','study/analyze.py','--out','recomputed','--verify-checkpoints','--compare','analysis'],'cwd':'.'},'completion_assessment':'All eight fixed-horizon cells, preserved interruption/failures, raw evidence, independent endpoint/checkpoint validation, repeated retained-data analysis and provisional scientific critique delivered. Full second training campaign not rerun; no independent peer review.'}
    dump('submission.json',submission)
    dump(c/'state.json',{'phase':'audit','execution_status':'complete','assurance':'provisional','stop_reason':'Declared eight-cell completeness and verification','review':ref('review.json'),'protocol_sha256':sha(c/'protocol.json')})
    make_manifest()
    print(json.dumps(summary,indent=2))

def make_manifest():
    roots=['study','evidence','campaigns','analysis','analysis-repeat','build']
    paths=set()
    for root in roots:
        paths.update(p for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update(Path(p) for p in ['REPORT.md','REPRODUCE.md','SCOPE.md','PROTOCOL-draft.md','review.json','review-input.json','review-checklist.json','critique.json','measurements.json','submission.json','inputs/BRIEF.md','inputs/COMPUTE.md','inputs/RESOURCES.json','inputs/compute.py','inputs/materials/SOURCES.md','inputs/materials/MEASUREMENTS.md','.allagma/lock.yaml'])
    # Include all completed broker receipts and their local streams at seal time.
    receipts=list(Path('.compute/responses').glob('*.json'))
    for response in receipts:
        paths.add(response);request=Path('.compute/requests')/response.name
        if request.exists():paths.add(request)
        paths.update(Path('.compute/responses').glob(response.stem+'-*.txt'))
    dump('artifact-manifest.json',{'format':'research-artifact-manifest-v1','task_id':'modular-addition','files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'exclusions':['The manifest itself (avoids a self hash cycle)','Environment, wheelhouse, caches and generated bundle content; retained locks identify dependencies','The in-flight seal request and later final-verification request/receipt/output; retained locally after this manifest snapshot'],'receipt_coverage':'All completed local broker receipts present at seal time; all later receipts also remain in .compute/responses.'})

if __name__=='__main__':main()
