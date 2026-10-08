"""Evidence inventory, attempt accounting, material revisions, and package validation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import hashlib
from run import dump, sha

def load(p):return json.loads(Path(p).read_text())

def ledger():
    rows=[];totals={"compute":0.,"setup":0.}
    for p in Path(".compute/requests").glob("*.json"):
        req=load(p);response=Path(".compute/responses")/(req["request_id"]+".json")
        row={**req,"request_file":str(p),"request_sha256":sha(p),"response_file":str(response)}
        if response.exists():
            res=load(response);row.update({"status":res["result"]["status"],"charged_seconds":res["result"].get("charged_seconds",0.),"response_sha256":sha(response),"injected_interruption":res.get("injected_interruption",False),"ended_at":res["result"].get("ended_at"),"peak_rss_bytes":res["result"].get("peak_rss_bytes"),"peak_storage_bytes":res["result"].get("peak_storage_bytes")})
            totals[req["category"]]+=row["charged_seconds"]
            for stream in ("stdout","stderr"):
                sp=response.with_name(req["request_id"]+"-"+stream+".txt")
                if sp.exists():row[stream]={"path":str(sp),"sha256":sha(sp)}
        else:row["status"]="response_pending_at_snapshot"
        rows.append(row)
    rows.sort(key=lambda r:r.get("ended_at","9999"))
    pending=[r for r in rows if r["status"]=="response_pending_at_snapshot"]
    compute=[r for r in rows if r["category"]=="compute"]
    conservative={k:totals[k]+sum(r["timeout_seconds"]+1 for r in pending if r["category"]==k) for k in totals}
    assert conservative["compute"]<=1800 and conservative["setup"]<=300 and len(compute)<=64
    result={"as_of":datetime.now(timezone.utc).isoformat(),"accounting":"completed receipts charged by measured supervisor wall time; current packaging request has no response until this process exits","charged_seconds_completed":totals,"conservative_upper_including_pending":conservative,"compute_requests":len(compute),"setup_requests":len(rows)-len(compute),"pending_requests":len(pending),"attempts":rows}
    dump("evidence/execution-ledger.json",result)
    return result

def material_revision(name):
    out=Path("revisions")/name
    out.mkdir(parents=True,exist_ok=False)
    for path in ("REPORT.md","analysis/summary.json","analysis/verification.json","analysis/main-figure.png"):
        p=Path(path);dest=out/p.name;shutil.copyfile(p,dest)
    dump(out/"revision.json",{"name":name,"created_at":datetime.now(timezone.utc).isoformat(),"materials":{p.name:{"path":str(p),"sha256":sha(p)} for p in out.iterdir() if p.is_file()}})

def manifest():
    exclude_prefixes=(".venv/",".venv-reproduction/",".tmp/",".compute/","inputs/materials/wheels/")
    entries=[]
    for p in sorted(Path(".").rglob("*")):
        if not p.is_file() or p.is_symlink():continue
        path=str(p)
        if path.startswith(exclude_prefixes) or "__pycache__" in p.parts or path=="artifact-manifest.json":continue
        role="documentation"
        if path.startswith("evidence/"):role="raw_evidence" if p.suffix==".npz" else "execution_evidence"
        elif path.startswith("analysis/"):role="derived_analysis"
        elif path.startswith("study/"):role="study_source"
        elif path.startswith("source-snapshots/"):role="source_snapshot"
        elif path.startswith("inputs/"):role="supplied_material"
        elif path.startswith("protocols/"):role="frozen_protocol"
        elif path.startswith("revisions/"):role="review_material_revision"
        entries.append({"path":path,"sha256":sha(p),"bytes":p.stat().st_size,"role":role})
    wheels=[{"path":str(p),"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(Path("inputs/materials/wheels").glob("*.whl"))]
    dump("artifact-manifest.json",{"format":"research-artifact-manifest-v1","task_id":"ema-schedule","created_at":datetime.now(timezone.utc).isoformat(),"exclusions":["virtual environments","temporary caches and bytecode","self (avoids recursive hash)","broker files (paths/hashes retained in execution ledger)"],"artifacts":entries,"offline_wheelhouse":wheels,"coverage":{"confirmation_cells":32,"model_states":96,"training_trajectories":24,"seed_pairs_per_dataset":4},"entrypoints":{"reproduce":"study/reproduce.sh","recompute":"study/recompute.sh","regenerate":"study/regenerate.py"}})
    return entries

def validate():
    sub=load("submission.json");assert sub["task_id"]=="ema-schedule" and sub["execution_status"]=="complete"
    for k in ("manuscript","review","artifact_manifest","measurements"):
        assert not Path(sub[k]).is_absolute() and Path(sub[k]).is_file()
    for k in ("reproduce","recompute"):
        assert sub[k]["cwd"]=="." and isinstance(sub[k]["argv"],list) and all(isinstance(x,str) for x in sub[k]["argv"])
    assert load("analysis/verification.json")["all_passed"]
    assert load("analysis/recompute-audit.json")["all_passed"]
    assert load("analysis/claims.json")["all_passed"] and load("analysis/claims.json")["report_sha256"]==sha("REPORT.md")
    assert load("analysis/regenerate-moons.json")["count"]==48 and load("analysis/regenerate-moons.json")["all_passed"]
    assert load("analysis/regenerate-gmm8.json")["count"]==48 and load("analysis/regenerate-gmm8.json")["all_passed"]
    review=load("review.json")
    assert sha(review["material_revision"]["manuscript"])==review["material_revision"]["manuscript_sha256"]
    for entry in load("artifact-manifest.json")["artifacts"]:assert sha(entry["path"])==entry["sha256"]
    # Every rendered data row must be present verbatim in the English report.
    table=Path("analysis/tables.md").read_text();report=Path("REPORT.md").read_text()
    assert table in report
    assert "AI-generated" in report and "full schedule" in report and "multiplicity" in report
    return {"all_passed":True,"submission_schema":True,"manifest_hashes":True,"review_revision_hash":True,"reported_tables_exactly_match_recomputed_data":True,"numerical_and_regeneration_checks":True}

def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=["ledger","revision","finalize","validate"]);p.add_argument("--name");args=p.parse_args()
    if args.action=="ledger":print(json.dumps(ledger(),indent=2))
    elif args.action=="revision":material_revision(args.name);print(args.name)
    elif args.action=="finalize":
        accounting=ledger();manifest();result=validate();dump("analysis/package-verification.json",result);manifest()
        print(json.dumps({"verification":result,"accounting":{k:v for k,v in accounting.items() if k!="attempts"}},indent=2))
    else:print(json.dumps(validate(),indent=2))

if __name__=="__main__":main()
