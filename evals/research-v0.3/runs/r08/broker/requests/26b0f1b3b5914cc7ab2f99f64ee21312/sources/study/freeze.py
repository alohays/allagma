"""Pilot-only qualification and conservative complete-work forecast, before confirmation."""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from run import dump, source_snapshot, sha

paths=[Path("evidence/pilot")/p for p in ("moons71-attempt02","gmm81-cosine5000","moons71-cosine5000")]
for p in paths:
    assert json.loads((p/"status.json").read_text())["status"]=="completed"
    assert all(x["passed"] for x in json.loads((p/"load-and-regenerate.json").read_text()))
assert json.loads((paths[0]/"qualification.json").read_text())["all_passed"]
assert json.loads((paths[1]/"qualification.json").read_text())["all_passed"]
provs=[json.loads((p/"provenance.json").read_text()) for p in paths]
matching=["initial_weights_sha256","training_prefix_5000_sha256","heldout_sha256","generation_noise_sha256"]
assert all(provs[0][k]==provs[2][k] for k in matching)
assert not list(Path("evidence/confirmation").glob("*/config.json"))
timings=[json.loads((p/"timing.json").read_text()) for p in paths]
worst_rate=max(t["seconds_per_update"] for t in timings)
eval_rate=max(t["evaluation_seconds"] for t in timings)
# Deliberately budget 2x the slowest pilot slope plus generous startup/storage.
forecast=200000*worst_rate*2+24*8+32*eval_rate*2+180
receipts=[];charges={"setup":0.,"compute":0.}; attempts=0
for request in Path(".compute/requests").glob("*.json"):
    req=json.loads(request.read_text());response=Path(".compute/responses")/(req["request_id"]+".json")
    if response.exists():
        r=json.loads(response.read_text());charge=r["result"].get("charged_seconds",0.)
        charges[req["category"]]+=charge
        attempts+=req["category"]=="compute"
        receipts.append({"request_id":req["request_id"],"label":req["label"],"category":req["category"],"status":r["result"]["status"],"charged_seconds":charge,"injected_interruption":r.get("injected_interruption",False),"response":str(response)})
assert any(r["injected_interruption"] for r in receipts)
assert forecast+charges["compute"]<1800
assert attempts+24+10<=64
revision,hashes=source_snapshot()
freeze={"revision":"confirmation-freeze-v1","frozen_at":datetime.now(timezone.utc).isoformat(),"protocol":"protocols/protocol-v1.json","protocol_sha256":sha("protocols/protocol-v1.json"),"source_revision":revision,"source_hashes":hashes,"device":"mps","dtype":"float32","pilot_evidence":[str(p) for p in paths],"qualification":"all known answers passed, both datasets sampled, saved states regenerated, moons input and initial-state hashes match across schedules; actual full 5000-update cosine pilot traces end at 5000","matching_hashes":{k:provs[0][k] for k in matching},"forecast":{"required_trajectories":24,"required_updates":200000,"required_cells":32,"required_model_states":96,"slowest_pilot_seconds_per_update":worst_rate,"worst_pilot_three_variant_evaluation_seconds":eval_rate,"remaining_work_seconds_conservative":forecast,"formula":"200000 * slowest pilot sec/update * 2 + 24 * 8 startup/input seconds + 32 * worst 3-state evaluation seconds * 2 + 180 analysis/verification/recovery seconds","charged_before_freeze":charges,"projected_total_compute_seconds":forecast+charges["compute"],"remaining_attempts_planned_upper":34},"decisions":"Use reference MPS float32 path and original scientific definitions unchanged. No tuning on confirmation. No selection for favorable pilot EMA results.","confirmation_data_used":False}
dump("protocols/freeze.json",freeze)
dump("evidence/recovery.json",{"initial_attempt":"evidence/pilot/moons71-attempt01","interrupted_request_id":next(r["request_id"] for r in receipts if r["injected_interruption"]),"recovery_attempt":"evidence/pilot/moons71-attempt02","method":"fresh deterministic pilot from same configuration/seed in a new directory; no partial outputs pooled; interruption happened before retained training trace","setup_recovery":"MPS default low watermark 1.4 exceeded broker high .2; set low .1, preserve high .2","receipts_at_freeze":receipts})
print(json.dumps(freeze["forecast"],indent=2))
