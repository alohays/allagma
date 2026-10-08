"""Final deterministic transitive artifact and numerical manuscript audit."""
import json
from pathlib import Path
import re
import sys
from common import ROOT,CAMP,BUNDLE,read,write,sha,ref,now
sys.path.insert(0,str(BUNDLE))
from allagma.contracts import validate_record
from allagma.bundles import verify_lock

def main():
    checked=set(); expanded=set()
    replay_root=ROOT/'reproduction/full-r1'
    def walk(obj,base=ROOT):
        if isinstance(obj,dict):
            if all(k in obj for k in ['path','sha256','media_type','retention']):
                p=base/obj['path'];assert p.is_file() and not p.is_symlink();assert sha(p)==obj['sha256'],str(p);checked.add(str(p.relative_to(ROOT)))
                if p.suffix in ['.json','.yaml'] and p not in expanded:
                    expanded.add(p)
                    nested_base=replay_root if p.is_relative_to(replay_root) and p.name!='comparison.json' else ROOT
                    walk(read(p),nested_base)
            for v in obj.values():walk(v,base)
        elif isinstance(obj,list):
            for x in obj:walk(x,base)
    manifest=read(ROOT/'artifact-manifest.json');walk(manifest)
    material=read(ROOT/'material-r1.json');walk(material)
    records=0
    paths=[CAMP/'study.json',CAMP/'context.json',ROOT/'analysis/record.json',ROOT/'review.json',*CAMP.glob('plan/*/spec.json'),*CAMP.glob('attempts/*/run-record.json')]
    for p in paths:
        v=read(p);validate_record(v);walk(v);records+=1
    for claim in read(ROOT/'claims.json'):validate_record(claim);walk(claim);records+=1
    verify_lock(ROOT,read(CAMP/'lock.yaml'))
    submission=read(ROOT/'submission.json');assert submission['task_id']=='ema-schedule' and submission['execution_status']=='complete'
    for k in ['manuscript','review','artifact_manifest','measurements']:
        assert not Path(submission[k]).is_absolute() and (ROOT/submission[k]).is_file()
    for k in ['reproduce','recompute']:
        assert isinstance(submission[k]['argv'],list) and all(isinstance(x,str) for x in submission[k]['argv'])
        assert not Path(submission[k]['cwd']).is_absolute()
    summary=read(ROOT/'analysis/summary.json');report=(ROOT/'REPORT.md').read_text()
    # Check every displayed effect/contrast table row exactly at its declared precision.
    for e in summary['effects']:
        expected=f"| {e['dataset']} | {e['updates']} | {e['schedule']} | {e['variant']} | {e['mean']:.6f} | [{e['ci95'][0]:.6f}, {e['ci95'][1]:.6f}] | {sum(x<0 for x in e['values'])}/4 | {e['signflip_p']:.3f} |"
        assert expected in report,expected
    for e in summary['contrasts']:
        expected=f"| {e['dataset']} | {e['variant']} | {e['contrast']} | {e['at']} | {e['mean']:.6f} | [{e['ci95'][0]:.6f}, {e['ci95'][1]:.6f}] | {e['signflip_p']:.3f} |"
        assert expected in report,expected
    numbers=read(ROOT/'analysis/report-numbers.json')
    assert numbers['positive_schedule_means']==8 and numbers['schedule_intervals_above_zero']==2
    assert all(e['ci95'][0]<=0<=e['ci95'][1] for e in summary['contrasts'] if e['contrast'] in ['duration','interaction'])
    assert numbers['coverage_range']==[8,8]
    # Verify links in the finished report and reproduction document.
    links=0
    for name in ['REPORT.md','REPRODUCE.md']:
        for target in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text()):
            if '://' in target:continue
            assert (ROOT/target.split('#')[0]).exists(),(name,target);links+=1
    # Every main run references a completed, distinct authoritative request.
    run_records=[read(p) for p in CAMP.glob('attempts/*/run-record.json')]
    assert sum(r['split']=='confirmation' and r['status']=='succeeded' for r in run_records)==24
    assert sum(r['status']=='interrupted' for r in run_records)==1
    assert sum(r['status']=='failed' for r in run_records)==3
    assert len(read(ROOT/'analysis/measurements.json')['runs'])==32
    assert read(ROOT/'reproduction/full-r1/comparison.json')['status']=='pass'
    assert read(ROOT/'recomputed-r1/comparison.json')['status']=='pass'
    verdict={'status':'pass','at':now(),'material_revision':'material-r1','material':ref(ROOT/'material-r1.json'),
      'manifest':ref(ROOT/'artifact-manifest.json'),'verified_file_digests':len(checked),'validated_allagma_records':records,
      'verified_report_links':links,'complete_confirmation_cells':32,'successful_confirmation_trajectories':24,
      'retained_interrupted_attempts':1,'retained_failed_pilot_attempts':3,
      'coverage':'Transitive reference digests, locked bundle, Allagma record contracts, submission paths and commands, all displayed effect/contrast rows, narrative pattern counts and report links. Underlying sample/checkpoint numerical checks are separately retained.'}
    write(ROOT/'package-verification.json',verdict);print(json.dumps(verdict,indent=2))

if __name__=='__main__':main()
