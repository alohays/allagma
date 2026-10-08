"""Post-review targeted verification of coverage summaries and reference controls."""
import json,math
from pathlib import Path
import numpy as np
from verify import independent_sw1
from study import json_write

def main():
    s=json.loads(Path('analysis/summary.json').read_text());runs=json.loads(Path('measurements.json').read_text())['runs']
    values={};control_checks=[];coverage_checks=[];loo_checks=[]
    for r in runs:
        if r['dataset']!='gmm8':continue
        with np.load(r['arrays'],allow_pickle=False) as a:
            theta=np.arange(8)*math.pi/4;centers=2*np.stack((np.cos(theta),np.sin(theta)),axis=1)
            for variant in ('raw','ema099','ema0999'):
                squared=((a[variant].astype(float)[:,None]-centers)**2).sum(axis=2)
                nearest=squared.argmin(axis=1);inside=squared[np.arange(2048),nearest]<=.45**2
                counts=[int(np.sum(inside&(nearest==i))) for i in range(8)]
                values[r['seed'],r['updates'],r['schedule'],variant]=(int(inside.sum()),sum(c>=21 for c in counts))
    for c in s['coverage']:
        rows=[values[seed,c['updates'],c['schedule'],c['variant']] for seed in c['seeds']]
        counts=[x[0] for x in rows];coverage=[x[1] for x in rows];fractions=np.array(counts)/2048
        assert counts==c['inlier_counts'] and coverage==c['covered_modes']
        half=3.182446305284263*np.std(fractions,ddof=1)/2;mean=float(fractions.mean())
        assert mean==c['inlier_fraction']['mean'] and np.allclose([mean-half,mean+half],c['inlier_fraction']['ci95'],atol=1e-12,rtol=0)
        coverage_checks.append(dict(updates=c['updates'],schedule=c['schedule'],variant=c['variant'],passed=True))
    for c in s['finite_sample_controls']:
        path=Path(f"evidence/inputs-retained/confirmation/{c['dataset']}-{c['seed']}/evaluation.npz")
        with np.load(path,allow_pickle=False) as a:value=independent_sw1(a['heldout'],a['independent_heldout'])
        assert abs(value-c['heldout_vs_independent_sw1'])<1e-12
        control_checks.append(dict(dataset=c['dataset'],seed=c['seed'],sw1=value,passed=True))
    for group in ('conditions','contrasts','absolute_sw1'):
        for c in s[group]:
            a=np.array(c['values']);loo=[float(np.delete(a,i).mean()) for i in range(len(a))]
            assert np.allclose(loo,c['leave_one_out_means'],atol=1e-14,rtol=0)
            assert c['seeds_negative']==int((a<0).sum())
            loo_checks.append(dict(group=group,dataset=c['dataset'],variant=c['variant'],passed=True))
    schedule=[c for c in s['contrasts'] if c['target']=='delta_vs_raw' and c['contrast'].startswith('schedule_')]
    diagnostics=dict(schedule_contrasts_positive=sum(c['mean']>0 for c in schedule),schedule_contrast_count=len(schedule),
      schedule_contrast_loo_range=[min(min(c['leave_one_out_means']) for c in schedule),max(max(c['leave_one_out_means']) for c in schedule)],
      all_schedule_contrast_loo_means_positive=all(min(c['leave_one_out_means'])>0 for c in schedule),
      cosine_effect_intervals_include_zero=all(c['ci95'][0]<=0<=c['ci95'][1] for c in s['conditions'] if c['schedule']=='cosine'),
      duration_effect_intervals_include_zero=all(c['ci95'][0]<=0<=c['ci95'][1] for c in s['contrasts'] if c['target']=='delta_vs_raw' and c['contrast'].startswith('duration_')),
      interaction_intervals_include_zero=all(c['ci95'][0]<=0<=c['ci95'][1] for c in s['contrasts'] if c['target']=='delta_vs_raw' and c['contrast']=='interaction'))
    result=dict(status='passed',coverage_summary_checks=coverage_checks,independent_reference_checks=control_checks,
                leave_one_seed_out_summaries_checked=len(loo_checks),diagnostics=diagnostics,
                reason='Report-r1 critique requested direct checks for supporting table intervals and heldout controls, beyond primary SW1 verification.')
    json_write('evidence/supporting-verification.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
