"""Check the central report claims against retained/recomputed numerical evidence."""
import json
from pathlib import Path
from run import dump,sha

def main():
    s=json.loads(Path("analysis/summary.json").read_text())
    r=json.loads(Path("measurements.json").read_text())["runs"]
    claims=[]
    def check(name,actual,expected,evidence):
        assert actual==expected,(name,actual,expected)
        claims.append({"claim":name,"observed":actual,"expected":expected,"passed":True,"evidence":evidence})
    check("complete cells and states",[s["n_cells"],s["n_states"]],[32,96],["measurements.json","analysis/verification.json"])
    contrasts=s["ema_effect_contrasts"]
    schedule=[x for x in contrasts if x["contrast"]=="schedule_cosine_minus_constant"]
    duration=[x for x in contrasts if x["contrast"]=="duration_10000_minus_5000"]
    interaction=[x for x in contrasts if x["contrast"]=="interaction"]
    check("all schedule effect contrasts have positive observed means",[len(schedule),sum(x["mean"]>0 for x in schedule)],[8,8],["analysis/summary.json#/ema_effect_contrasts"])
    resolved=[[x["dataset"],x["variant"],x["condition"]] for x in schedule if x["ci95"][0]>0]
    check("only two moons 5k schedule intervals exclude zero",resolved,[["moons","ema099",5000],["moons","ema0999",5000]],["analysis/summary.json#/ema_effect_contrasts"])
    check("all duration contrast intervals include zero",[len(duration),sum(x["ci95"][0]<=0<=x["ci95"][1] for x in duration)],[8,8],["analysis/summary.json#/ema_effect_contrasts"])
    check("all interaction intervals include zero",[len(interaction),sum(x["ci95"][0]<=0<=x["ci95"][1] for x in interaction)],[4,4],["analysis/summary.json#/ema_effect_contrasts"])
    for pol,expected in (("constant",[-.062730,-.053400]),("cosine",[-.004116,.000576])):
        means=[x["mean"] for x in s["paired_ema_minus_raw"] if x["updates"]==5000 and x["schedule"]==pol]
        check("5k mean EMA effect range: "+pol,[round(min(means),6),round(max(means),6)],expected,["analysis/summary.json#/paired_ema_minus_raw"])
    coverage=[r0["metrics"][v]["covered_modes"] for r0 in r if r0["dataset"]=="gmm8" for v in ("raw","ema099","ema0999")]
    check("GMM8 coverage ceiling",[len(coverage),min(coverage),max(coverage)],[48,8,8],["measurements.json"])
    inliers=[x["mean_inlier_fraction"] for x in s["gmm8_coverage"]]
    check("GMM8 mean inlier-fraction range",[round(min(inliers),6),round(max(inliers),6)],[.976440,.990356],["analysis/summary.json#/gmm8_coverage"])
    for ds in ("moons","gmm8"):
        reg=json.loads(Path(f"analysis/regenerate-{ds}.json").read_text())
        check("saved-weight sample regeneration: "+ds,[reg["count"],reg["all_passed"],reg["max_abs_sample_difference"]],[48,True,0.0],[f"analysis/regenerate-{ds}.json"])
    check("minimum attainable two-sided sign-flip p with four pairs",2/(2**4),.125,["protocols/protocol-v1.json#/evaluation"])
    dump("analysis/claims.json",{"all_passed":True,"claims":claims,"report_sha256":sha("REPORT.md"),"summary_sha256":sha("analysis/summary.json"),"script_sha256":sha(__file__)})
    print(json.dumps({"claims_checked":len(claims),"all_passed":True}))

if __name__=="__main__":main()
