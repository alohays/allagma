"""Check the exact retained native-host behaviors, not general model quality."""
import hashlib
import json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
CAMPAIGN=ROOT/"campaigns/ema-v1"


def read(path):
    return json.loads(Path(path).read_text())


def ref(path):
    return {"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    lock=read(CAMPAIGN/"lock.yaml")
    labels=["02-interrupted","03-fresh-pilots","04-confirmation","05-analysis","06-reporting-revision","07-reporting-repair"]
    sessions=[]
    route_evidence=[]
    commands={}
    thread_ids=[]
    for label in labels:
        directory=ROOT/"evidence/native"/label
        receipt=read(directory/"session.json")
        events=[json.loads(line) for line in (directory/"events.jsonl").read_text().splitlines()]
        assert ref(directory/"events.jsonl")["sha256"]==receipt["events_sha256"]
        observed=[e["thread_id"] for e in events if e["type"]=="thread.started"]
        assert observed==receipt["thread_ids"] and len(observed)==1
        assert "resume" not in receipt["command"] and "fork" not in receipt["command"]
        assert not any(arg in ("--model","-m") or arg.startswith(("model=","review_model=")) for arg in receipt["command"])
        assert receipt["cli_version"]=="codex-cli 0.160.1"
        assert receipt["exit_code"]==(1 if label=="02-interrupted" else 0)
        assert receipt["host_interrupted"]==(label=="02-interrupted")
        commands[label]=[e["item"] for e in events if e["type"]=="item.completed" and e.get("item",{}).get("type")=="command_execution" and e["item"].get("exit_code")==0]
        for item in commands[label]:
            if "allagma.py entry " in item["command"] and "--campaign ema-v1" in item["command"]:
                try:
                    value=json.loads(item["aggregated_output"])
                except json.JSONDecodeError:
                    continue
                if not isinstance(value,dict) or not {"lock_id","bundle_id","module_id","path","sha256"} <= value.keys():
                    continue  # A script can quote a routing command in its own report.
                assert value["lock_id"]==lock["lock_id"] and value["bundle_id"]==lock["bundle_id"]
                path=Path(value["path"])
                assert path.is_relative_to(ROOT/".allagma/bundles"/lock["bundle_id"])
                assert hashlib.sha256(path.read_bytes()).hexdigest()==value["sha256"]
                route_evidence.append({"session":label,"item_id":item["id"],"module":value["module_id"],"path":str(path.relative_to(ROOT)),"sha256":value["sha256"]})
        thread_ids.extend(observed)
        sessions.append({"label":label,"thread_id":observed[0],"receipt":ref(directory/"session.json"),"trace":ref(directory/"events.jsonl")})
    assert len(set(thread_ids))==6
    expected={"research/protocol","research/experiment","research/analysis","research/writing","research/audit"}
    assert expected<={r["module"] for r in route_evidence}
    all_commands=[{**item,"session":label} for label,items in commands.items() for item in items]
    skill_reads=[]
    for method in ("protocol","experiment","analysis","writing","audit"):
        wrapper=f".agents/skills/allagma-{method}/SKILL.md"
        canonical=f"methods/allagma-{method}/SKILL.md"
        assert any(wrapper in item["command"] and "Read the study" in item["aggregated_output"] for item in all_commands)
        canonical_path=ROOT/".allagma/bundles"/lock["bundle_id"]/canonical
        exact_text=canonical_path.read_text().strip()
        matches=[item for item in all_commands if exact_text in item["aggregated_output"]
                 and canonical in item["command"]+item["aggregated_output"]]
        assert matches, f"No actual read of the complete locked {method} skill"
        skill_reads.append({"module":"research/"+method,"session":matches[0]["session"],
                            "item_id":matches[0]["id"],"source":ref(canonical_path)})
    original=CAMPAIGN/"runs/pilot-moons-11/attempts/001"
    retry=CAMPAIGN/"runs/pilot-moons-11/attempts/002"
    a,b=read(original/"record.json"),read(retry/"record.json")
    assert a["status"]=="interrupted" and b["status"]=="succeeded"
    assert a["exit_code"]==-15 and a["bundle_id"]==b["bundle_id"]==lock["bundle_id"]
    assert read(original/"partial-training.json")=={"updates":100,"seed":11,"scientific_evidence":False}
    assert not (original/"raw.json").exists()
    assert datetime.fromisoformat(a["ended_at"].replace("Z","+00:00"))<datetime.fromisoformat(b["started_at"].replace("Z","+00:00"))
    assert any("manage.py pilot" in item["command"] for item in commands["03-fresh-pilots"])
    freeze=read(ROOT/"confirmation-freeze.json")
    frozen_at=datetime.fromisoformat(freeze["frozen_at"])
    records=[read(path) for path in CAMPAIGN.glob("runs/*/attempts/*/record.json")]
    assert sum(r["status"]=="succeeded" and r["split"]=="pilot" for r in records)==4
    confirmations=[r for r in records if r["split"]=="confirmation"]
    assert len(confirmations)==10 and all(r["status"]=="succeeded" for r in confirmations)
    assert all(datetime.fromisoformat(r["started_at"].replace("Z","+00:00"))>frozen_at for r in confirmations)
    manifest=read(CAMPAIGN/"analyses/a001/raw-manifest.json")
    assert len(manifest["raw"])==10 and len(manifest["exclusions"])==5
    assert read(CAMPAIGN/"latest-audit.json")["verdict"]=="pass"
    assert read(ROOT/"evidence/independent-verification.json")["status"]=="pass"
    assert read(ROOT/"publication/record.json")["status"]=="pass"
    assert read(ROOT/"evidence/supporting-verification.json")["status"]=="pass"
    assert read(ROOT/"publication/v2/record.json")["status"]=="pass"
    assert "machine-generated with OpenAI Codex" in (ROOT/"publication/manuscript.md").read_text()
    from compute import ledger
    budget=ledger()
    assert budget["charged_seconds"]<1800 and budget["attempts"]==15
    assert all(e["status"]!="running" for e in budget["entries"])
    from publication import content
    assert (ROOT/"publication/manuscript.md").read_text()==content(CAMPAIGN/"analyses/a001/paper/manuscript.md",ROOT/"publication/manuscript.md")
    from revise_publication import build
    revised,claims=build()
    assert (ROOT/"publication/v2/manuscript.md").read_text()==revised
    assert read(ROOT/"publication/v2/claims.json")==claims and len(claims)==13
    report={"status":"pass","date":"2026-10-08 Asia/Seoul","scope":"Explicit native Codex CLI skill invocation, exact canonical method routing, bounded real MPS study execution, interrupted-host/fresh-session continuation, native analysis/audit/publication handoff for this study",
        "bundle_id":lock["bundle_id"],"lock_id":lock["lock_id"],"source_revision":lock["source_revision"],
        "sessions":sessions,"campaign_routes":route_evidence,"canonical_skill_reads":skill_reads,
        "recovery_attempts":[ref(original/"record.json"),ref(retry/"record.json")],
        "confirmation_freeze":ref(ROOT/"confirmation-freeze.json"),
        "complete_plan":{"pilot_successes":4,"confirmation_successes":10,"interrupted_attempts":1},
        "budget":{k:v for k,v in budget.items() if k!="entries"},
        "native_model_observations":ref(ROOT/"evidence/native/model-observations.json"),
        "accepted_publication":ref(ROOT/"publication/v2/record.json"),
        "supporting_verification":ref(ROOT/"evidence/supporting-verification.json"),
        "excluded_claims":["Implicit skill-trigger reliability","Other models, hosts or hardware","Desktop UI interaction","General autonomous research quality","Independent scientific peer review","OS security sandbox isolation"]}
    target=ROOT/"evidence/host-qualification.json"
    target.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
