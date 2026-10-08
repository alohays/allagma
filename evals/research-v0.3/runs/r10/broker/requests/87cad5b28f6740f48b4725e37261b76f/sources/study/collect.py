"""Bookkeeping for permanent broker receipts and immutable raw selection."""
import argparse
import shutil
from common import ROOT, read, ref, tree_manifest, write


def history():
    for response in sorted((ROOT / ".compute/responses").glob("*.json")):
        value = read(response)
        request_id = value.get("request_id")
        request_path = ROOT / ".compute/requests" / f"{request_id}.json"
        if not request_path.exists():
            continue
        request = read(request_path)
        folder = ROOT / "evidence/broker" / request["label"]
        folder.mkdir(parents=True, exist_ok=True)
        for src, name in [(response, "response.json"), (request_path, "request.json")]:
            if not (folder / name).exists():
                shutil.copyfile(src, folder / name)
        for name in ("stdout.txt", "stderr.txt"):
            path = response.parent / f"{request_id}-{name}"
            if path.exists() and not (folder / name).exists():
                shutil.copyfile(path, folder / name)
    rows = []
    for path in sorted((ROOT / "evidence/broker").glob("*/response.json")):
        response = read(path)
        request = read(path.parent / "request.json")
        rows.append({"request_id": response["request_id"], "label": request["label"],
            "category": request["category"], "argv": request["argv"], "status": response["result"]["status"],
            "ended_at": response["result"]["ended_at"], "charged_seconds": response["result"]["charged_seconds"],
            "injected_interruption": response["injected_interruption"], "request": ref(path.parent / "request.json"), "response": ref(path)})
    rows.sort(key=lambda r: r["ended_at"])
    write(ROOT / "evidence/broker-history.json", {"receipts": rows,
        "totals": {c: sum(r["charged_seconds"] for r in rows if r["category"] == c) for c in ("setup", "compute")},
        "compute_requests": sum(r["category"] == "compute" for r in rows),
        "authority": "Copied common-broker responses; controller retains separate authoritative receipts"})


def raw():
    destination = ROOT / "evidence/raw-manifest.json"
    if destination.exists():
        raise SystemExit("Raw manifest already frozen; refusing overwrite")
    runs = []
    files = []
    exclusions = []
    for path in sorted((ROOT / "campaigns/culp-v1/runs").glob("*/attempts/*/record.json")):
        record = read(path)
        if record["split"] == "pilot" or record["status"] != "succeeded":
            exclusions.append({"record": ref(path), "reason": "pilot qualification" if record["split"] == "pilot" else record["status"]})
            continue
        folder = ROOT / "raw" / record["attempt_id"]
        assert (folder / "completion.json").is_file()
        runs.append({"dataset": record["run_id"], "attempt_id": record["attempt_id"],
            "directory": folder.relative_to(ROOT).as_posix(), "record": ref(path)})
        files += list(folder.rglob("*")) + [path]
    assert sorted(r["dataset"] for r in runs) == ["iris", "wine", "zoo"]
    files += [ROOT / "campaigns/culp-v1/protocol.json", ROOT / "campaigns/culp-v1/code-manifest.json", ROOT / "provenance/source-manifest.json"]
    write(destination, {"format": "culp-raw-manifest-v1", "runs": runs,
                       "files": tree_manifest(files), "exclusions": exclusions})
    interrupted = [r for r in read(ROOT / "evidence/broker-history.json")["receipts"] if r["injected_interruption"]]
    assert len(interrupted) == 1
    first = interrupted[0]
    successor = next(r for r in runs if r["dataset"] == "iris")
    write(ROOT / "evidence/recovery.json", {"interrupted_request": first,
        "successor": successor, "basis": "Authoritative terminal response marked injected_interruption=true before retry",
        "preservation": "Distinct request IDs, broker folders, raw attempt folders and RunRecords. Interrupted artifacts excluded, never overwritten.",
        "observation_timeouts": "None observed"})
    print("Frozen three successful datasets; retained interruption and pilot exclusions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["history", "raw"])
    args = parser.parse_args()
    history()
    if args.mode == "raw":
        raw()
