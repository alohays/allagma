"""Source provenance bookkeeping; no scientific imports or computations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(path):
    entries = {str(p.relative_to(path)): file_hash(p) for p in sorted(path.rglob("*"))
               if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    revision = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return entries, revision


def main():
    original, orig_hash = tree(ROOT / "source/original")
    adapted, adapt_hash = tree(ROOT / "source/adapted")
    supplied, _ = tree(ROOT / "inputs/materials/capsule-6460826")
    assert original == supplied, "Original copy must match every supplied capsule file"
    changed = [p for p in original if original[p] != adapted.get(p)]
    assert set(changed) == {"code/wine_sample.py", "code/zoo_sample.py"}
    for dataset in ["wine", "zoo"]:
        rel = f"code/{dataset}_sample.py"
        raw = (ROOT / "source/original" / rel).read_bytes()
        expected = raw.replace(b"import pandas\n", b"import pandas\nfrom pathlib import Path\n")
        expected = expected.replace(f"'/data/{dataset}.txt'".encode(),
            f"Path(__file__).resolve().parents[1] / 'data' / '{dataset}.txt'".encode())
        assert expected == (ROOT / "source/adapted" / rel).read_bytes(), rel
    record = {"format": "culp-source-revision-v1", "original": original, "adapted": adapted,
              "original_tree_sha256": orig_hash, "adapted_tree_sha256": adapt_hash,
              "tree_hash_method": "SHA256 of UTF-8 compact sorted JSON mapping relative paths to file SHA256",
              "protocol_sha256": file_hash(ROOT / "PROTOCOL.md"),
              "changed_files": changed, "original_matches_supplied": True,
              "only_declared_path_edits": True}
    target = ROOT / "evidence/source-revision.json"
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if target.exists():
        assert target.read_text() == text, "Frozen source revision changed"
    else:
        target.write_text(text)
    print(json.dumps({k: record[k] for k in ["original_tree_sha256", "adapted_tree_sha256", "protocol_sha256", "changed_files"]}, indent=2))


if __name__ == "__main__":
    main()
