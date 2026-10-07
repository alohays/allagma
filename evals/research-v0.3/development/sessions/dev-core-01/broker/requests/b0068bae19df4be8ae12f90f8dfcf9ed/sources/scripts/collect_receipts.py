"""Bookkeeping only: preserve broker request/response deliveries and their history."""
import json
from pathlib import Path
import shutil

root = Path.cwd()
target = root / "evidence/broker"
target.mkdir(parents=True, exist_ok=True)
history = []
for response in sorted((root / ".compute/responses").glob("*.json")):
    request = root / ".compute/requests" / response.name
    if not request.exists():
        continue
    value = json.loads(response.read_text())
    details = json.loads(request.read_text())
    destination = target / response.stem
    destination.mkdir(exist_ok=True)
    shutil.copyfile(request, destination / "request.json")
    shutil.copyfile(response, destination / "response.json")
    for name in ["stdout.txt", "stderr.txt"]:
        path = response.parent / (response.stem + "-" + name)
        if path.exists():
            shutil.copyfile(path, destination / name)
    history.append({"request_id": response.stem, "label": details["label"], "category": details["category"],
                    "marked_attempt": details["attempt"], "timeout_seconds": details["timeout_seconds"],
                    "argv": details["argv"], "cwd": details["cwd"],
                    "outcome": value, "evidence_directory": str(destination)})
history.sort(key=lambda x: x["outcome"].get("result", {}).get("ended_at", ""))
(root / "evidence/execution-history.json").write_text(json.dumps(history, indent=2) + "\n")
