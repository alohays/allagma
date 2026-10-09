"""Offline literature records, critical reading links and portable snapshots.

Fetching bytes and running TeX belong to optional adapters. These helpers never
access the network, infer authorship or turn a bibliographic match into a
scientific endorsement.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from .files import (AllagmaError, canonical, confined, digest, file_hash,
                    read_json, utcnow, write_bytes, write_json, write_text)

FORMAT = "allagma-reference-map-v1"
CATEGORIES = ("primary", "implementation", "baseline", "competing", "gaps")
PHASES = ("planning", "implementation", "analysis", "writing")
ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{0,79}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")


def require(condition, message):
    if not condition:
        raise AllagmaError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def raw_cache_file(root, path):
    root, path = Path(root).resolve(), Path(path).absolute()
    parent = path.parent
    while parent.is_relative_to(root):
        if (parent / ".allagma-reference-cache.json").exists():
            return True
        if parent == root:
            break
        parent = parent.parent
    return False


def public_url(value):
    """Only public provenance URLs, never credential-bearing retrieval links."""
    require(nonempty(value), "A public source URL is required")
    parsed = urlsplit(value)
    require(parsed.scheme in ("http", "https") and parsed.hostname and not
            (parsed.username or parsed.password), "Use a public HTTP(S) URL without credentials")
    require(not re.search(r"token|signature|credential|password|api.?key|x-amz-|x-goog-", parsed.query, re.I),
            "Do not retain signed or credential-bearing URLs in public reference records")
    return value


def empty_map(question="", mode="provided-only"):
    return {"format": FORMAT, "question": question, "mode": mode,
            "coverage": {"queries": [], "limitations": [
                "No external literature search has been recorded. Assess supplied sources before making novelty claims."],
                "categories": {name: {"status": "limited", "reason": "Not assessed yet."}
                               for name in CATEGORIES}}, "records": [], "decisions": []}


def normalized_title(value):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", value).casefold())


def identities(record):
    meta = record["metadata"]
    values = {"title:" + normalized_title(meta["title"]) + ":" + str(meta["year"]) + ":" +
              normalized_title(meta["authors"][0])}
    if meta.get("doi"):
        doi = re.sub(r"^https?://(?:dx\.)?doi.org/|^doi:\s*", "", meta["doi"], flags=re.I).strip().lower()
        require(bool(re.fullmatch(r"10\.\d{4,9}/\S+", doi)), "Invalid DOI identifier")
        values.add("doi:" + doi)
    if meta.get("arxiv"):
        arxiv = re.sub(r"^https?://arxiv.org/(?:abs|pdf)/|^arxiv:\s*", "", meta["arxiv"], flags=re.I)
        arxiv = re.sub(r"(?:v\d+)?(?:\.pdf)?$", "", arxiv.strip())
        require(bool(re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7})", arxiv)), "Invalid arXiv identifier")
        values.add("arxiv:" + arxiv)
    return values


def validate_map(value, *, directory=None, require_review=False, retrieval=None):
    require(isinstance(value, dict) and value.get("format") == FORMAT, "Unsupported reference map")
    require(isinstance(value.get("question"), str), "Reference map requires its study question")
    require(value.get("mode") in ("online", "offline", "provided-only"), "Invalid reference coverage mode")
    coverage = value.get("coverage", {})
    require(isinstance(coverage.get("limitations"), list) and all(map(nonempty, coverage["limitations"])),
            "Coverage limitations must be explicit text entries")
    if value["mode"] != "online":
        require(bool(coverage["limitations"]), "Offline/provided-only research requires coverage limitations")
    require(set(coverage.get("categories", {})) == set(CATEGORIES), "Assess every reference coverage category")
    for category in coverage["categories"].values():
        require(category.get("status") in ("covered", "limited", "not-applicable") and nonempty(category.get("reason")),
                "Coverage categories require a status and reason")
    require(isinstance(coverage.get("queries"), list), "Record the literature search queries")
    for query in coverage["queries"]:
        require(all(nonempty(query.get(k)) for k in ("query", "source", "date", "selection")),
                "Each search needs query, source, date and selection rationale")
        if query.get("url"):
            public_url(query["url"])
    records = value.get("records")
    require(isinstance(records, list), "Reference records must be a list")
    seen, keys, passage_ids = {}, set(), set()
    assets = {item["id"]: item for item in (retrieval or {}).get("assets", [])}
    for record in records:
        key = record.get("id", "")
        require(isinstance(key, str) and ID.fullmatch(key) and key not in keys, "Reference IDs must be unique citation keys")
        keys.add(key)
        meta = record.get("metadata", {})
        require(nonempty(meta.get("title")) and isinstance(meta.get("authors"), list) and meta["authors"]
                and all(map(nonempty, meta["authors"])), f"{key}: title and author metadata are required")
        require(type(meta.get("year")) is int and 1000 <= meta["year"] <= 9999, f"{key}: invalid publication year")
        public_url(meta.get("url"))
        for identity in identities(record):
            require(identity not in seen, f"Duplicate reference: {key} and {seen.get(identity)}; merge their evidence")
            seen[identity] = key
        roles = record.get("roles", [])
        require(roles and isinstance(roles, list) and set(roles) <= set(CATEGORIES), f"{key}: declare its literature roles")
        require(nonempty(record.get("relevance")), f"{key}: explain study relevance")
        require(isinstance(record.get("limitations"), list) and record["limitations"]
                and all(map(nonempty, record["limitations"])), f"{key}: retain critical limitations")
        consequences = record.get("consequences", {})
        require(set(consequences) == set(PHASES) and all(map(nonempty, consequences.values())),
                f"{key}: record consequences for planning, implementation, analysis and writing")
        verification = record.get("bibliography", {})
        require(verification.get("status") in ("unverified", "verified", "conflict"), f"{key}: invalid bibliographic status")
        if verification["status"] == "verified":
            require(nonempty(verification.get("checked_at")) and verification.get("sources"),
                    f"{key}: verified metadata needs dated primary sources")
            fields = set()
            for source in verification["sources"]:
                public_url(source.get("url"))
                require(nonempty(source.get("locator")) and isinstance(source.get("fields"), list),
                        f"{key}: metadata verification needs a locator and checked fields")
                fields.update(source["fields"])
                if "sha256" in source:
                    require(bool(SHA.fullmatch(source["sha256"])), "Invalid metadata source digest")
            require({"title", "authors", "year"} <= fields, f"{key}: verify title, authors and year separately")
        passages = record.get("passages")
        require(isinstance(passages, list), f"{key}: passages must be a list")
        for passage in passages:
            pid = f"{key}:{passage.get('id', '')}"
            require(ID.fullmatch(passage.get("id", "")) and pid not in passage_ids, f"{key}: duplicate or invalid passage ID")
            passage_ids.add(pid)
            require(all(nonempty(passage.get(k)) for k in ("locator", "summary", "claim", "limitation")),
                    f"{pid}: located passage, claim assessment and limitation are required")
            require(passage.get("assessment") in ("supports", "contradicts", "context", "unassessed"),
                    f"{pid}: invalid support assessment")
            public_url(passage.get("url"))
            if passage.get("asset_id"):
                require(SHA.fullmatch(passage.get("sha256", "")), f"{pid}: source asset requires a digest")
                if retrieval is not None:
                    asset = assets.get(passage["asset_id"], {})
                    require(asset.get("status") == "available" and asset.get("sha256") == passage["sha256"],
                            f"{pid}: citation source does not match acquired bytes")
        if require_review:
            require(verification["status"] == "verified" and passages and
                    all(p["assessment"] != "unassessed" for p in passages), f"{key}: critical reading is incomplete")
        if record.get("note"):
            require(directory is not None, "A reference directory is required to validate reading notes")
            note = confined(directory, record["note"])
            require(note.is_file(), f"{key}: reading note is missing")
            require(not raw_cache_file(directory, note), "Version useful reading notes outside raw reference caches")
    decisions = value.get("decisions")
    require(isinstance(decisions, list), "Reference decisions must be a list")
    for decision in decisions:
        require(decision.get("phase") in PHASES and nonempty(decision.get("decision")) and
                isinstance(decision.get("references"), list) and bool(decision["references"]),
                "Study decisions require a phase, explanation and cited passage IDs")
        require(set(decision["references"]) <= passage_ids, "A decision refers to an unknown source passage")
    if require_review and not records:
        require(coverage["limitations"] and all(c["status"] != "covered" for c in coverage["categories"].values()),
                "An empty map cannot claim covered literature")
    return value


def add_record(value, record, *, directory=None):
    """Merge exact identities; conflicts and ambiguous bridges require review."""
    value = deepcopy(value)
    candidate = {**value, "records": [record], "decisions": []}
    validate_map(candidate, directory=directory)
    matches = [r for r in value["records"] if identities(r) & identities(record)]
    require(len(matches) <= 1, "This record bridges different references; resolve the identity conflict explicitly")
    if not matches:
        value["records"].append(record)
    else:
        existing = matches[0]
        for name in ("title", "authors", "year"):
            left, right = existing["metadata"][name], record["metadata"][name]
            require((normalized_title(left) == normalized_title(right) if name == "title" else left == right),
                    f"Duplicate identity has conflicting {name}; resolve the metadata before merging")
        for name in ("roles", "limitations", "passages"):
            for item in record[name]:
                if item not in existing[name]:
                    existing[name].append(item)
        # Do not silently replace a critical reading, a citation key, or its
        # verification status. New interpretation belongs in its reading note.
        for name, val in record["metadata"].items():
            if name in existing["metadata"]:
                same_doi = name == "doi" and {v for v in identities(existing) if v.startswith("doi:")} == {
                    v for v in identities(record) if v.startswith("doi:")}
                require(existing["metadata"][name] == val or name in ("title", "url") or same_doi,
                        f"Conflicting metadata field: {name}")
            else:
                existing["metadata"][name] = val
    return validate_map(value, directory=directory)


def tex_escape(value):
    return "".join({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
                    "^": r"\textasciicircum{}"}.get(char, char) for char in str(value))


def bibliography(value):
    entries = []
    for record in value["records"]:
        if record["bibliography"]["status"] != "verified":
            continue
        meta = record["metadata"]
        fields = {"title": "{" + tex_escape(meta["title"]) + "}",
                  "author": " and ".join(tex_escape(author) for author in meta["authors"]),
                  "year": str(meta["year"]), "howpublished": tex_escape(meta.get("venue", "Preprint or source repository")),
                  "url": tex_escape(meta["url"])}
        for name in ("doi", "arxiv"):
            if meta.get(name):
                fields["doi" if name == "doi" else "eprint"] = tex_escape(meta[name])
        if meta.get("arxiv"):
            fields["archivePrefix"] = "arXiv"
        entries.append("@misc{" + record["id"] + ",\n" + "\n".join(
            f"  {name} = {{{content}}}," for name, content in fields.items()) + "\n}")
    return "\n\n".join(entries) + "\n"


def render_index(value):
    lines = ["# Reference index", "", value["question"] or "Study question has not been recorded.", "",
             f"Coverage mode: **{value['mode']}**. Metadata accuracy and scientific support are reviewed separately.", "",
             "## Coverage", ""]
    lines += [f"- {name}: {item['status']}. {item['reason']}" for name, item in value["coverage"]["categories"].items()]
    lines += ["", *[f"- Limit: {item}" for item in value["coverage"]["limitations"]], "", "## Read on demand", ""]
    for record in value["records"]:
        meta = record["metadata"]
        label = f"[{record['id']}]({record['note']})" if record.get("note") else f"`{record['id']}`"
        lines.append(f"- {label}: {meta['title']} ({meta['year']}); {', '.join(record['roles'])}. "
                     f"Metadata: {record['bibliography']['status']}. {record['relevance']}")
    lines += ["", "Read `map.json` for located passages, disagreements, limitations and phase decisions. "
              "Read individual notes and retained source assets when needed. `citations.bib` includes only "
              "metadata marked verified; that status does not verify a claim.", ""]
    return "\n".join(lines)


def refresh(directory, *, require_review=False):
    directory = Path(directory)
    retrieval = read_json(directory / "retrieval.json") if (directory / "retrieval.json").exists() else None
    value = validate_map(read_json(directory / "map.json"), directory=directory,
                         require_review=require_review, retrieval=retrieval)
    write_text(directory / "INDEX.md", render_index(value))
    write_text(directory / "citations.bib", bibliography(value))
    return {"status": "pass", "records": len(value["records"]), "map_sha256": digest(value),
            "review_required": require_review, "scope": "Record consistency, not independent scientific review"}


def initialize(directory, *, question="", mode="provided-only"):
    directory = Path(directory)
    require(not (directory / "map.json").exists(), "Reference map already exists")
    value = validate_map(empty_map(question, mode))
    write_json(directory / "map.json", value, immutable=True)
    refresh(directory)
    return value


def snapshot(directory, destination, *, require_review=False):
    """Freeze notes and public manifests only; never traverse a raw cache."""
    directory, destination = Path(directory), Path(destination)
    require(not destination.exists(), "Reference snapshot destination already exists")
    result = refresh(directory, require_review=require_review)
    value = read_json(directory / "map.json")
    names = {"map.json", "INDEX.md", "citations.bib"}
    names.update(r["note"] for r in value["records"] if r.get("note"))
    names.update(n for n in ("assets.json", "retrieval.json") if (directory / n).is_file())
    payloads = {name: confined(directory, name).read_bytes() for name in sorted(names)}
    for name in payloads:
        require(not any(p.startswith(".") for p in Path(name).parts), "Hidden cache paths are not reference notes")
        require(Path(name).suffix in (".json", ".md", ".bib", ".txt"), "Reference snapshots contain notes, not raw downloads")
    for name, data in payloads.items():
        write_bytes(confined(destination, name), data, immutable=True)
    files = {name: file_hash(destination / name) for name in payloads}
    record = {"format": "allagma-reference-snapshot-v1", "created_at": utcnow(),
              "files": files, "map_sha256": result["map_sha256"]}
    write_json(destination / "snapshot.json", record, immutable=True)
    return record


def verify_snapshot(directory):
    directory = Path(directory)
    value = read_json(directory / "snapshot.json")
    require(value.get("format") == "allagma-reference-snapshot-v1", "Invalid reference snapshot")
    for name, expected in value["files"].items():
        require(file_hash(confined(directory, name)) == expected, f"Reference snapshot changed: {name}")
    require(digest(read_json(directory / "map.json")) == value["map_sha256"], "Reference map digest changed")
    return value
