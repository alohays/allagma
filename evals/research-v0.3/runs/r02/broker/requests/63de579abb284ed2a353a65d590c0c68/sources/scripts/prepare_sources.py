"""Bookkeeping only: retain originals and apply the two path substitutions."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    supplied = ROOT / "inputs/materials/capsule-6460826"
    original = ROOT / "source/original"
    adapted = ROOT / "source/adapted"
    if original.exists() or adapted.exists():
        raise SystemExit("Source directories already exist; refusing to overwrite provenance")
    shutil.copytree(supplied, original)
    shutil.copytree(original, adapted)
    for dataset in ("wine", "zoo"):
        path = adapted / "code" / (dataset + "_sample.py")
        content = path.read_bytes()
        content = b"from pathlib import Path\n" + content.replace(
            ("'/data/" + dataset + ".txt'").encode(),
            ("Path(__file__).resolve().parents[1] / 'data' / '" + dataset + ".txt'").encode(),
        )
        path.write_bytes(content)
    entries = []
    patches = []
    for source in sorted(original.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(original)
        other = adapted / relative
        assert source.read_bytes() == (supplied / relative).read_bytes()
        entries.append({"path": relative.as_posix(), "original_sha256": digest(source),
                        "adapted_sha256": digest(other)})
        if source.read_bytes() != other.read_bytes():
            patches.extend(difflib.unified_diff(
                source.read_text().splitlines(keepends=True),
                other.read_text().splitlines(keepends=True),
                fromfile="source/original/" + relative.as_posix(),
                tofile="source/adapted/" + relative.as_posix()))
    revision = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    provenance = {"format": "culp-source-provenance-v1", "source_revision": revision,
                  "supplied_capsule": "inputs/materials/capsule-6460826",
                  "benchmark_commit": "e32a2980e72fe6eb04ee04eb749458f570625663",
                  "capsule_doi": "https://doi.org/10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5",
                  "revision_definition": "SHA-256 of json.dumps(files, sort_keys=True).encode()",
                  "files": entries}
    (ROOT / "source/provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (ROOT / "source/compatibility.patch").write_text("".join(patches))
    print(json.dumps({"source_revision": revision, "files": len(entries), "changed_scripts": ["wine", "zoo"]}))


if __name__ == "__main__":
    main()
