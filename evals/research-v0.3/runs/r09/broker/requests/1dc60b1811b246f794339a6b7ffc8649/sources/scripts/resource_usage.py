"""Resource receipt bookkeeping; no experiment or scientific result calculation."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    records = json.loads((ROOT / "evidence/broker/index.json").read_text())
    profile = json.loads((ROOT / "inputs/RESOURCES.json").read_text())["profile"]
    summaries = {}
    for category in ["setup", "compute"]:
        rows = [r for r in records if r["category"] == category]
        charge = sum(r["result"].get("charged_seconds", 0) for r in rows)
        assert charge <= profile["budgets_seconds"][category]
        summaries[category] = {"requests": len(rows), "charged_seconds": charge,
                               "ceiling_seconds": profile["budgets_seconds"][category]}
    assert summaries["compute"]["requests"] <= profile["attempt_limit"]
    output = {"format": "culp-resource-accounting-v1", "snapshot_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "All receipts archived in evidence/broker/index.json through this snapshot; the final manifest-verification receipt is retained separately after inventory sealing.",
              "categories": summaries, "compute_request_ceiling": profile["attempt_limit"],
              "noncompleted_requests": [r["request_id"] for r in records if r["result"]["status"] != "completed"],
              "max_sampled_process_tree_rss_bytes": max(r["result"].get("peak_rss_bytes", 0) for r in records),
              "max_sampled_storage_bytes": max(r["result"].get("peak_storage_bytes", 0) for r in records),
              "rss_ceiling_bytes": profile["rss_limit_bytes"], "storage_ceiling_bytes": profile["storage_limit_bytes"],
              "native_session_ceiling_seconds": 3600,
              "native_session_accounting": "Separate controller accounting, not measured by scientific broker; no native wall-time stop occurred.",
              "all_archived_charges_within_ceilings": True}
    (ROOT / "evidence/resource-usage.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
