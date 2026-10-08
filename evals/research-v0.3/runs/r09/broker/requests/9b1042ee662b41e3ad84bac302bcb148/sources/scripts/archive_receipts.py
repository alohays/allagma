"""Copy delivered broker records out of its transient queue, without altering them."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evidence/broker")
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted((ROOT / ".compute/responses").glob("*.json")):
        response = json.loads(path.read_text())
        request_id = response["request_id"]
        request = ROOT / ".compute/requests" / (request_id + ".json")
        if not request.is_file():
            continue
        dest = out / request_id
        dest.mkdir(exist_ok=True)
        for source, name in [(request, "request.json"), (path, "response.json"),
                             (path.with_name(request_id + "-stdout.txt"), "stdout.txt"),
                             (path.with_name(request_id + "-stderr.txt"), "stderr.txt")]:
            if source.exists():
                target = dest / name
                if target.exists():
                    assert target.read_bytes() == source.read_bytes(), f"Receipt changed: {source}"
                else:
                    shutil.copyfile(source, target)
        req = json.loads(request.read_text())
        records.append({"request_id": request_id, "label": req["label"], "category": req["category"],
                        "marked_attempt": req["attempt"], "receipt": str((dest / "response.json").relative_to(ROOT)),
                        "result": response.get("result"),
                        "injected_interruption": response.get("injected_interruption", False)})
    (out / "index.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"Archived {len(records)} broker receipts in {args.output}")


if __name__ == "__main__":
    main()
