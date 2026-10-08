"""Named-revision critique, locked reviewer handoff, and delivery manifest."""
import json
from pathlib import Path
import subprocess
import sys
from common import ROOT,CAMP,BUNDLE,read,write,ref,sha,now
sys.path.insert(0,str(BUNDLE))
from allagma.contracts import validate_record

def main():
    summary=read(ROOT/'analysis/summary.json');assert summary['complete']
    claims=read(ROOT/'claims.json')
    for claim in claims:validate_record(claim)
    # The material inventory is immutable and deliberately excludes its own
    # digest and downstream review/manifest files to avoid circular hashes.
    materials=[ROOT/p for p in ['REPORT.md','REPRODUCE.md','SCOPE.md','INTERPRETATION.md','claims.json',
        'analysis/summary.json','analysis/report-numbers.json','analysis/measurements.json','analysis/contrasts.json',
        'analysis/raw-manifest.json','analysis/main-figure.png','analysis/record.json',
        'evidence/verification.json','recomputed-r1/comparison.json','evidence/resource-usage.json',
        'reproduction/full-r1/comparison.json','study/runner.py','study/reference.py','study/analyze.py','study/verify.py','study/write_report.py','study/package.py',
        'campaigns/ema-schedule-v1/protocol.json','campaigns/ema-schedule-v1/confirmation-freeze.json',
        'campaigns/ema-schedule-v1/run-manifest.json','campaigns/ema-schedule-v1/RECOVERY.md']]
    write(ROOT/'material-r1.json',{'revision':'material-r1','created_at':now(),'files':[ref(p) for p in materials],
        'scope':'Final manuscript, primary evidence, replay/recomputation verification, frozen protocol, implementation and recovery. No independent peer review.'})
    findings=[
      'Design: the required 32 cells are present. Constant checkpoints share one actual trajectory, whereas the two cosine horizons have distinct attempts and terminal updates. Within-seed initial states, actual training prefixes, heldout draws and generation noise match; verification checks the retained arrays, not just declared seeds.',
      'Inference: all eight mean schedule contrasts are positive, but only the two moons/5000 schedule intervals exclude zero. All duration and interaction intervals include zero. The manuscript distinguishes this descriptive pattern from a general EMA recommendation and from equivalence.',
      'Small-sample limitation: n=4 gives df=3 t intervals that are sensitive to distributional assumptions and individual seeds. Exact sign-flip sensitivity cannot attain two-sided p<0.125. The best-looking t intervals must not be presented as multiplicity-adjusted discoveries; the report states this and retains all seed values and leave-one-out means.',
      'Mechanism limitation: policy changes affect the whole learning-rate path and cumulative optimization history. Changing the cosine horizon also changes the earlier rate path. The factorial comparison addresses the prior missing controls but does not isolate endpoint learning rate, EMA lag, or noise suppression; causal mechanism language is explicitly withheld.',
      'Coverage limitation: every GMM8 state covers eight modes under the original all-draw threshold, so coverage is saturated. This is a ceiling, not evidence of density equivalence. Mode/inlier counts and fractions plus SW1 remain available.',
      'Measurement limitation: only one 2048-point heldout draw and one generation-noise stream per seed are used, with fixed 128 projection directions. Common random numbers support pairing but do not eliminate Monte Carlo error. No new independent-noise or sample-size sensitivity study was performed.',
      'Verification: independent vectorized metric calculations agree; all 96 saved model states regenerate their arrays. Separate-directory raw-data reanalysis and fresh-environment full retraining both agree. Repeated runs remain verification evidence and do not increase n.',
      'Recovery: one controlled timeout and three qualification failures are preserved under distinct IDs, followed by a passing pilot before confirmation. No confirmation scientific code was tuned after data access. The MPS compatibility fix lowered its low watermark without raising the broker cap.',
      'Performance scope: device selection used a conservative pilot forecast that includes cold-start costs. It does not establish an intrinsic CPU-versus-MPS speed ranking, and no cross-backend scientific equivalence claim is made.',
      'Review scope: this substantive critique is from the same Codex session as implementation and reporting. The locked reviewer adapter checks evidence structure and digests; it cannot independently judge scientific validity. The package claims provisional review assurance, with no independent peer-review claim.',
      'Generalization and literature: results concern one small synthetic diffusion model, two distributions, two durations and two decays. Upstream papers were not retrieved offline; the report separates inherited source metadata from verified local implementation and makes no novelty claim.'
    ]
    criteria=['All required cells and reference mechanism','Untouched confirmation and frozen estimands','Actual matched input provenance',
        'Paired seed uncertainty and multiplicity','Full-policy contrasts without endpoint-only mechanism inference','GMM8 original coverage rule and ceiling',
        'Retained failures and resource compliance','Raw-data recomputation and saved-weight regeneration','Fresh-environment retraining','English evidence-linked reporting','Explicit assurance scope']
    write(ROOT/'evidence/critique-r1.json',{'revision':'material-r1','material':ref(ROOT/'material-r1.json'),'reviewer':'Same-session Codex self-critique','criteria':criteria,'findings':findings,'unresolved_limitations':['Four seeds','No simultaneous inference','No mechanism isolation','No independent-noise sensitivity','Coverage ceiling','No independent scientific peer review','Offline literature'],'blocking_issues':[]})
    payload={'study':str(ROOT),'material':ref(ROOT/'material-r1.json'),'claims':claims,'criteria':criteria,'evidence':[ref(ROOT/'evidence/verification.json'),ref(ROOT/'evidence/critique-r1.json')]}
    write(ROOT/'evidence/review-input-r1.json',payload)
    adapter=BUNDLE/'adapters/reviewer-checklist/review.py'
    subprocess.run([sys.executable,str(adapter),str(ROOT/'evidence/review-input-r1.json'),str(ROOT/'evidence/reviewer-checklist-r1.json')],check=True,cwd=ROOT)
    checked=read(ROOT/'evidence/reviewer-checklist-r1.json');assert checked['verdict']=='pass',checked
    review={'schema_version':'0.2','record_type':'ReviewRecord','review_id':'ema-schedule-material-r1',
      'reviewer':'Locked Allagma reviewer/checklist plus same-session Codex substantive critique',
      'backend':'reviewer/checklist; same-author model critique','backend_version':'Allagma 0.3.0rc1, bundle b-9a39b70665ba909edb8abc13; current Codex session',
      'material':ref(ROOT/'material-r1.json'),'criteria':criteria,'verdict':'pass','findings':findings,
      'trace':[ref(ROOT/'evidence/critique-r1.json'),ref(ROOT/'evidence/reviewer-checklist-r1.json'),ref(ROOT/'evidence/review-input-r1.json'),ref(ROOT/'evidence/verification.json')],
      'assurance':'provisional','coverage':'Named material-r1. Deterministic schemas/direct evidence digests plus independent metric implementation, provenance and resampling checks; same-author substantive scientific critique. No independent scientific peer review. Pass concerns package conformance and appropriately limited claims.'}
    validate_record(review);write(ROOT/'review.json',review)
    submission={'task_id':'ema-schedule','execution_status':'complete','manuscript':'REPORT.md','review':'review.json','artifact_manifest':'artifact-manifest.json','measurements':'analysis/measurements.json',
      'reproduce':{'argv':['python3','study/reproduce.py','--destination','reproduction/full-r2'],'cwd':'.'},
      'recompute':{'argv':['python3','inputs/compute.py','--category','compute','--label','retained-recompute-submission','--timeout','30','--','.venv/bin/python','study/analyze.py','--raw-manifest','analysis/raw-manifest.json','--output','recomputed-r2','--compare','analysis'],'cwd':'.'},
      'completion_assessment':'All 32 confirmation cells, 96 checkpoints/sample states, paired effects/contrasts, figure, raw-evidence recomputation, saved-weight regeneration and full fresh-environment retraining completed. Scientific inference is limited by four seeds and multiplicity; review is provisional, not independent peer review.',
      'material_revision':'material-r1','successful_full_reproduction':'reproduction/full-r1/comparison.json','saved_weight_verification':'evidence/verification.json'}
    write(ROOT/'submission.json',submission)
    write(CAMP/'state-final.json',{'phase':'audit','execution_status':'complete','assurance':'provisional','material':ref(ROOT/'material-r1.json'),'stop_reason':'Declared completeness achieved','review':ref(ROOT/'review.json')})
    # Inventory all retained deliverables/evidence, excluding environments,
    # transient bytecode/cache, and this manifest/final verification outputs.
    files=[]
    selected=['study','campaigns','analysis','evidence','recomputed-r1','reproduction/full-r1','inputs','.compute','.allagma/bundles/b-9a39b70665ba909edb8abc13']
    for top in selected:
        for p in sorted((ROOT/top).rglob('*')):
            rel=p.relative_to(ROOT)
            if any(part in ['.venv','__pycache__','.mpl-cache'] for part in rel.parts):continue
            if p.is_file() and not p.is_symlink():files.append(ref(p))
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and p.suffix in ['.md','.json'] and p.name not in ['artifact-manifest.json','package-verification.json']:files.append(ref(p))
    files.append(ref(ROOT/'LICENSE-AI-Scientist'))
    files.append(ref(ROOT/'allagma.yaml'))
    files.append(ref(ROOT/'.allagma/lock.yaml'))
    unique={f['path']:f for f in files}
    write(ROOT/'artifact-manifest.json',{'format':'ema-artifact-manifest-v1','created_at':now(),'material_revision':'material-r1','files':list(unique.values()),
        'coverage':'Retained scientific data, weights, source snapshots, frozen workflow, pilot/failure evidence, analysis, fresh-reproduction evidence, reports and delivered broker logs at packaging cutoff. Environments/caches excluded; pinned wheelhouse included. This manifest and subsequently emitted package-verification/receipt files are intentionally excluded to avoid circular digests.'})
    print(json.dumps({'status':'complete','review':'pass','assurance':'provisional','manifest_files':len(unique)}))

if __name__=='__main__':main()
