"""Append a reporting revision after native critique; retain prior publications."""
import csv
import json
import os
from pathlib import Path
import sys

from compute import ROOT, execute
from publication import content, reference


def build():
    analysis=ROOT/"campaigns/ema-v1/analyses/a001"
    summary=json.loads((analysis/"outputs/summary.json").read_text())
    source=analysis/"paper/manuscript.md"
    destination=ROOT/"publication/v2/manuscript.md"
    paper=content(source,destination)
    old_claim_link=os.path.relpath(analysis/"paper/claims.json",destination.parent)
    paper=paper.replace(f"]({old_claim_link})", "](claims.json)")
    comparisons=summary["comparisons"]
    early=[c["mean"] for c in comparisons if c["updates"]==5000]
    late=[c["mean"] for c in comparisons if c["updates"]==10000]
    assert all(c["ci95_t"][0]<=0<=c["ci95_t"][1] for c in comparisons if c["updates"]==10000)
    rows=list(csv.DictReader((analysis/"outputs/per-seed.csv").open()))
    modes=[int(r["covered_modes"]) for r in rows if r["dataset"]=="gmm8"]
    interpretation=(f"The observed benefit was concentrated at 5,000 updates: the four mean paired differences "
        f"ranged from {min(early):.6f} to {max(early):.6f}. At 10,000 updates they ranged from "
        f"{min(late):.6f} to {max(late):.6f}, and every interval included zero. "
        f"Observed mixture mode counts ranged from {min(modes)} to {max(modes)} across all confirmation "
        "variants and checkpoints. A zero observed difference and a collapsed t interval for this "
        "saturated count do not establish population equivalence.\n\n")
    paper=paper.replace("## Results\n\n","## Results\n\n"+interpretation)
    paper=paper.replace("## Discussion and limitations\n\n","## Discussion and limitations\n\n"
        "Checkpoint age and learning-rate position change together in this one cosine-decay training "
        "trajectory. The observed early-versus-late pattern therefore does not isolate training duration "
        "from the optimizer schedule. The independent verification is split into primary metric/weight "
        "checks and a separate supporting-diagnostics check; neither is independent scientific peer review.\n\n")
    paper=paper.replace("## References\n\n",
        "This reporting revision adds claim records for Table 2 and the checkpoint-pattern interpretation. "
        "The [supporting verification](../../evidence/supporting-verification.json) independently checks "
        "mode/inlier summaries, finite-sample controls and leave-one-seed-out diagnostics. "
        "[Publication provenance](record.json) retains the prior draft and publication, scripts and exact "
        "evidence. No training result or frozen numerical analysis was changed.\n\n## References\n\n")
    claims=json.loads((analysis/"paper/claims.json").read_text())
    summary_ref=reference(analysis/"outputs/summary.json")
    supporting_ref=reference(ROOT/"evidence/supporting-verification.json")
    for index,c in enumerate((c for c in comparisons if c["dataset"]=="gmm8"),9):
        mode,inside=c["mode_difference"],c["inlier_difference"]
        claims.append({"schema_version":"0.2","record_type":"ClaimRecord","claim_id":f"C{index}",
            "text":f"At {c['updates']} updates, {c['ema']} minus raw has mean covered-mode difference {mode['mean']:.3f}, 95% t interval [{mode['ci95_t'][0]:.3f}, {mode['ci95_t'][1]:.3f}], and mean inlier-fraction difference {inside['mean']:.4f}.",
            "supporting":[summary_ref,supporting_ref],"contradicting":[],
            "dependencies":[reference(analysis/"record.json"),reference(analysis/"raw-manifest.json")],
            "scope":"Descriptive Table 2 values across five paired confirmation seeds for gmm8",
            "limitations":["Coverage can saturate; zero observed differences do not establish population equivalence.","Unadjusted small-sample intervals; no independent scientific peer review."],
            "status":"supported","supersedes":None})
    claims.append({"schema_version":"0.2","record_type":"ClaimRecord","claim_id":"C13",
        "text":interpretation.strip(),"supporting":[summary_ref,reference(analysis/"outputs/per-seed.csv","text/csv")],
        "contradicting":[],"dependencies":[reference(analysis/"record.json"),supporting_ref],
        "scope":"Observed checkpoint pattern in this model, optimizer schedule, two synthetic distributions and five confirmation seeds per dataset",
        "limitations":["Checkpoint age and learning-rate position are confounded.","No universal EMA superiority or population equivalence claim."],
        "status":"supported","supersedes":None})
    return paper,claims


def run():
    assert json.loads((ROOT/"evidence/supporting-verification.json").read_text())["status"]=="pass"
    paper,claims=build()
    directory=ROOT/"publication/v2"
    directory.mkdir(exist_ok=False)
    (directory/"manuscript.md").write_text(paper)
    (directory/"claims.json").write_text(json.dumps(claims,sort_keys=True,indent=2)+"\n")
    assert build()==(paper,claims)
    record={"status":"pass","version":2,"reason":"Address native review findings about supporting-diagnostic verification, missing Table 2 claim records and interpretation scope",
        "prior_publication":reference(ROOT/"publication/record.json"),
        "draft":reference(ROOT/"campaigns/ema-v1/analyses/a001/paper/manuscript.md","text/markdown"),
        "output":reference(directory/"manuscript.md","text/markdown"),"claims":reference(directory/"claims.json"),
        "script":reference(Path(__file__).resolve(),"text/x-python"),
        "primary_verification":reference(ROOT/"evidence/independent-verification.json"),
        "supporting_verification":reference(ROOT/"evidence/supporting-verification.json"),
        "scientific_analysis":reference(ROOT/"campaigns/ema-v1/analyses/a001/record.json"),
        "scope":"Deterministic reporting revision and claim completeness; all frozen training data and numerical analysis remain their original artifacts"}
    (directory/"record.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    (ROOT/"publication/latest.json").write_text(json.dumps({"version":2,"manuscript":"publication/v2/manuscript.md","record":reference(directory/"record.json")},indent=2)+"\n")
    print(json.dumps(record,indent=2))


if __name__=="__main__":
    if sys.argv[1:]==["--worker"]:
        run()
    elif not sys.argv[1:]:
        raise SystemExit(execute("publication-revision-2",[str(ROOT/".venv/bin/python"),str(Path(__file__).resolve()),"--worker"],15))
    else:
        raise SystemExit("Run without arguments for the budgeted reporting revision")
