"""Offline validation and rendering inputs for an optional evidence-linked paper.

The TeX process and source-archive integration live in adapters/arxiv. A paper
is additional output; ordinary study reports do not require this module or TeX.
"""
from __future__ import annotations

from pathlib import Path
import math
import re

from . import references
from .files import AllagmaError, confined, digest, file_hash, read_json, utcnow, write_json, write_text
from .references import ID, nonempty, require, tex_escape

FORMAT = "allagma-paper-output-v1"
SECTIONS = ("abstract", "introduction", "related-work", "methods", "results", "discussion", "limitations")


def default_configuration():
    return {"format": FORMAT, "output": "report"}


def initialize(study, configuration, *, title, authors):
    study, configuration = Path(study).resolve(), Path(configuration).resolve()
    require(configuration.is_relative_to(study), "Keep the paper configuration inside its study")
    if configuration.exists():
        require(read_json(configuration) == default_configuration(), "Preserve the existing paper configuration; use a new revision")
    config = {"format": FORMAT, "output": "arxiv", "title": title, "date": utcnow()[:10],
              "authors": authors, "references": "references", "template": {"name": "allagma-preprint"},
              "sections": {name: f"paper/sections/{name}.tex" for name in SECTIONS}, "appendices": [],
              "evidence": {}, "values": {}, "claims": [], "figures": [], "tables": [], "review": {}}
    author_tex(config)
    for name, path in config["sections"].items():
        target = confined(study, path)
        require(not target.exists(), "Paper section already exists; keep existing prose in a new configured revision")
    for name, path in config["sections"].items():
        write_text(confined(study, path), f"% TODO: write the {name.replace('-', ' ')} from retained evidence.\n", immutable=True)
    write_json(configuration, config)
    return {"status": "initialized", "configuration": str(configuration), "scope": "Authoring scaffold, not a completed paper"}


def json_pointer(value, pointer):
    require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "Use an RFC 6901 JSON pointer")
    try:
        for key in pointer.split("/")[1:]:
            key = key.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                require(re.fullmatch(r"0|[1-9][0-9]*", key), "Invalid JSON array index")
                value = value[int(key)]
            else:
                value = value[key]
    except (KeyError, IndexError, TypeError) as exc:
        raise AllagmaError(f"Missing result at JSON pointer: {pointer}") from exc
    return value


def format_value(value, specification="text"):
    if specification == "text":
        require(isinstance(value, (str, int, float)) and not isinstance(value, bool), "A paper value must be scalar text or a number")
        return str(value)
    require(isinstance(specification, str) and re.fullmatch(r"d|\.[0-9]{1,2}[fge]", specification), "Unsupported paper number format")
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), "Paper numbers must be finite")
    if specification == "d":
        require(float(value).is_integer(), "Integer formatting cannot truncate a scientific value")
        value = int(value)
    return format(value, specification)


def author_tex(config):
    attribution = config["authors"]
    require(attribution.get("mode") in ("named", "anonymous"), "Choose named authors or an explicit anonymous draft")
    require(nonempty(attribution.get("supplied_by")) and nonempty(attribution.get("supplied_at")),
            "Record researcher-supplied attribution; never infer paper authors from repository metadata")
    if attribution["mode"] == "anonymous":
        require(not attribution.get("entries"), "Anonymous draft mode cannot also declare named authors")
        return "Anonymous draft"
    entries = attribution.get("entries")
    require(isinstance(entries, list) and entries, "Supply at least one paper author")
    rendered = []
    for author in entries:
        require(nonempty(author.get("name")), "Every configured author needs a name")
        value = tex_escape(author["name"])
        if author.get("affiliation"):
            value += r"\\ {\small " + tex_escape(author["affiliation"]) + "}"
        if author.get("email"):
            require(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", author["email"]), "Invalid author email")
            value += r"\\ {\small\texttt{" + tex_escape(author["email"]) + "}}"
        if author.get("orcid"):
            require(re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", author["orcid"]), "Use a complete ORCID identifier")
            value += r"\\ {\small ORCID: " + tex_escape(author["orcid"]) + "}"
        rendered.append(value)
    return r" \and ".join(rendered)


def _source(study, source):
    require(isinstance(source, dict) and nonempty(source.get("path")), "Evidence requires a study-relative path")
    path = confined(study, source["path"])
    require(not references.raw_cache_file(study, path), "Keep raw reference downloads out of the public paper archive; retain a derived result or public-safe manifest")
    require(path.is_file() and file_hash(path) == source.get("sha256"), f"Missing or changed paper evidence: {source['path']}")
    return path


def review_fingerprint(study, config):
    """Bind reviews to prose, attribution, citations and the evidence selection."""
    review_ids = {item.get("record") for item in config.get("review", {}).values()}
    selected = {key: item for key, item in config.get("evidence", {}).items() if key not in review_ids}
    content = {key: config.get(key) for key in ("title", "date", "authors", "template", "claims", "values", "figures", "tables")}
    content.update(evidence=selected,
                   sections={role: {"path": path, "sha256": file_hash(confined(study, path))}
                             for role, path in config["sections"].items()},
                   appendices=[{**item, "sha256": file_hash(confined(study, item["path"]))} for item in config.get("appendices", [])],
                   reference_map_sha256=file_hash(confined(study, config["references"]) / "map.json"))
    return digest(content)


def validate(study, config):
    study = Path(study).resolve()
    require(config.get("format") == FORMAT and config.get("output") in ("report", "arxiv"), "Invalid study paper output configuration")
    if config["output"] == "report":
        return {"status": "disabled", "output": "report", "scope": "Existing report behavior; no TeX integration invoked"}
    require(nonempty(config.get("title")) and nonempty(config.get("date")), "Paper title and fixed date are required")
    require(not re.search(r"\b(?:TODO|TBD|PLACEHOLDER|REQUIRED)\b", config["title"] + " " + config["date"]),
            "Complete the paper title and fixed date")
    authors = author_tex(config)
    if (study / "inputs/PAPER.json").is_file():
        request = read_json(study / "inputs/PAPER.json")
        require(request.get("output") == "arxiv" and request.get("authors") == config["authors"],
                "Paper attribution differs from the protected researcher request; prepare a new authorized revision")
    reference_directory = confined(study, config["references"])
    retrieval = read_json(reference_directory / "retrieval.json") if (reference_directory / "retrieval.json").exists() else None
    literature = references.validate_map(read_json(reference_directory / "map.json"), directory=reference_directory,
                                         require_review=True, retrieval=retrieval)
    if literature["records"]:
        require(set(references.PHASES) <= {d["phase"] for d in literature["decisions"]},
                "A paper must record reference consequences throughout planning, implementation, analysis and writing")
    require(set(config.get("sections", {})) == set(SECTIONS), "Provide every required English paper section")
    section_text = {}
    for name, path in config["sections"].items():
        section_text[name] = confined(study, path).read_text(encoding="utf-8")
        require(nonempty(section_text[name]) and not re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", section_text[name]),
                f"Paper section is incomplete: {name}")
    appendices = config.get("appendices", [])
    for appendix in appendices:
        require(nonempty(appendix.get("title")), "Appendices need descriptive titles")
        content = confined(study, appendix["path"]).read_text()
        require(nonempty(content) and not re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", content), "A declared appendix is incomplete")
        section_text["appendix-" + str(len(section_text))] = content
    text = "\n".join(section_text.values())
    # Authoring is plain TeX, but input files, bibliography and figures must
    # enter through the retained package specification, never ambient paths.
    require(not re.search(r"\\(?:input|include|includegraphics|bibliography|bibliographystyle|write|openout|read|catcode|usepackage|documentclass)\b", text),
            "Sections must use Allagma figure/table/value/claim macros; declare extra template files explicitly")
    evidence = config.get("evidence", {})
    require(isinstance(evidence, dict) and evidence, "A research paper requires retained study evidence")
    require(all(isinstance(key, str) and ID.fullmatch(key) for key in evidence),
            "Evidence IDs must be portable identifiers")
    paths = {key: _source(study, item) for key, item in evidence.items()}
    values = {}
    value_provenance = {}
    for key, item in config.get("values", {}).items():
        require(ID.fullmatch(key), "Invalid paper value ID")
        require(item.get("evidence") in paths, f"Unknown evidence for paper value: {key}")
        value = json_pointer(read_json(paths[item["evidence"]]), item["pointer"])
        values[key] = format_value(value, item.get("format", "text"))
        value_provenance[key] = {**item, "observed": value, "rendered": values[key]}

    def resolve_text(value):
        def replace(match):
            require(match[1] in values, f"Unknown result value: {match[1]}")
            return values[match[1]]
        return re.sub(r"\{\{value:([A-Za-z][A-Za-z0-9_-]*)\}\}", replace, value)

    passage_ids = {r["id"] + ":" + p["id"] for r in literature["records"] for p in r["passages"]}
    claims = {}
    for claim in config.get("claims", []):
        key = claim.get("id", "")
        require(ID.fullmatch(key) and key not in claims and nonempty(claim.get("text")), "Paper claims require unique IDs and text")
        require(claim.get("status") in ("supported", "negative", "inconclusive"), f"Declare the scope of claim {key}")
        require(claim.get("evidence") and claim.get("limitations"), f"{key}: retain result links and limitations")
        for link in claim["evidence"]:
            require(link.get("id") in paths and nonempty(link.get("locator")), f"{key}: invalid claim-to-result link")
            if link["locator"].startswith("#/"):
                json_pointer(read_json(paths[link["id"]]), link["locator"][1:])
        require(set(claim.get("citations", [])) <= passage_ids, f"{key}: unknown citation-to-passage link")
        claims[key] = resolve_text(claim["text"])
    require(claims, "Record the manuscript's empirical conclusions and evidence links")
    figures = {}
    for figure in config.get("figures", []):
        key = figure.get("id", "")
        require(ID.fullmatch(key) and key not in figures and figure.get("evidence") in paths, "Invalid paper figure")
        source = paths[figure["evidence"]]
        require(source.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg"), "Convert figures before packaging; arXiv does not convert them")
        require(nonempty(figure.get("caption")), "Retain an informative figure caption")
        require(type(figure.get("width", .95)) in (int, float) and 0 < figure.get("width", .95) <= 1, "Invalid figure width")
        figures[key] = {**figure, "caption": resolve_text(figure["caption"]), "source_path": str(source),
                        "target": f"figures/{key}{source.suffix.lower()}"}
    tables = {}
    for table in config.get("tables", []):
        key = table.get("id", "")
        require(ID.fullmatch(key) and key not in tables and table.get("evidence") in paths, "Invalid paper table")
        rows = json_pointer(read_json(paths[table["evidence"]]), table["pointer"])
        require(isinstance(rows, list) and rows and table.get("columns") and nonempty(table.get("caption")),
                "Tables require retained rows, columns and a caption")
        rendered_rows = []
        for row in rows:
            cells = []
            for column in table["columns"]:
                require(nonempty(column.get("title")), "Table column needs a title")
                pointers = column.get("pointers", [column.get("pointer", "")])
                rendered = [format_value(json_pointer(row, pointer), column.get("format", "text")) for pointer in pointers]
                pattern = column.get("pattern", "{0}")
                require(re.sub(r"\{[0-9]+\}", "", pattern).count("{") == 0 and
                        re.sub(r"\{[0-9]+\}", "", pattern).count("}") == 0, "Table patterns only interpolate numbered values")
                try:
                    cells.append(pattern.format(*rendered))
                except IndexError as exc:
                    raise AllagmaError("Table pattern references a missing value") from exc
            rendered_rows.append(cells)
        tables[key] = {**table, "caption": resolve_text(table["caption"]), "rendered_rows": rendered_rows}
    declared = {"Value": set(values), "Claim": set(claims), "Figure": set(figures), "Table": set(tables)}
    for kind, available in declared.items():
        used = set(re.findall(r"\\Allagma" + kind + r"\{([^}]+)\}", text))
        require(used <= available, f"Unknown Allagma{kind} ID in manuscript: {sorted(used - available)}")
        if kind != "Value":
            require(available <= used, f"Declared {kind.lower()} is absent from the manuscript: {sorted(available - used)}")
    cited = {key.strip() for match in re.findall(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}", text) for key in match.split(",")}
    available_citations = {r["id"] for r in literature["records"]}
    require(cited <= available_citations, f"Unverified or unknown manuscript citations: {sorted(cited - available_citations)}")
    review = config.get("review", {})
    for kind in ("scientific", "humanizer"):
        item = review.get(kind, {})
        require(item.get("status") == "complete" and nonempty(item.get("scope")) and item.get("record") in paths,
                f"Retain a scoped {kind} review before building the final paper package")
        record = read_json(paths[item["record"]])
        require(record.get("format") == "allagma-paper-review-v1" and record.get("kind") == kind
                and record.get("reviewed_content_sha256") == review_fingerprint(study, config),
                f"The {kind} review is stale or not bound to this manuscript revision")
    return {"status": "pass", "authors_tex": authors, "literature": literature, "sections": section_text,
            "evidence_paths": {key: str(path) for key, path in paths.items()}, "values": values,
            "value_provenance": value_provenance, "claims": claims, "figures": figures, "tables": tables,
            "citations": sorted(cited), "scope": "Artifact integrity and declared links; scientific support remains a reviewed judgment"}


def macros(validated):
    lines = ["% Generated from retained, hash-verified evidence. Do not hand-edit."]
    for name in ("Value", "Claim", "Figure", "Table"):
        lines.append(r"\newcommand{\Allagma" + name + r"}[1]{\csname Allagma" + name + r"#1\endcsname}")

    def definition(kind, key, body):
        lines.append(r"\expandafter\def\csname Allagma" + kind + key + r"\endcsname{" + body + "}")

    for key, value in validated["values"].items():
        definition("Value", key, tex_escape(value))
    for key, claim in validated["claims"].items():
        definition("Claim", key, tex_escape(claim))
    for key, figure in validated["figures"].items():
        definition("Figure", key, "\n" + r"\begin{figure}[htbp]\centering" + "\n" +
                   r"\includegraphics[width=" + str(figure.get("width", .95)) + r"\linewidth]{" + figure["target"] + "}\n" +
                   r"\caption{" + tex_escape(figure["caption"]) + r"}\label{fig:" + key + "}\n" + r"\end{figure}" + "\n")
    for key, table in validated["tables"].items():
        layout = []
        for column in table["columns"]:
            width = column.get("width_cm")
            if width is not None:
                require(type(width) in (float, int) and .3 <= width <= 16, "Invalid table column width")
                layout.append("p{" + str(width) + "cm}")
            else:
                alignment = column.get("align", "l")
                require(alignment in ("l", "c", "r"), "Invalid column alignment")
                layout.append(alignment)
        header = " & ".join(tex_escape(c["title"]) for c in table["columns"]) + r" \\"
        rows = "\n".join(" & ".join(tex_escape(cell) for cell in row) + r" \\" for row in table["rendered_rows"])
        body = ("\n{\\small\n" + r"\begin{longtable}{@{}" + "".join(layout) + "@{}}\n" +
                r"\caption{" + tex_escape(table["caption"]) + r"}\label{tab:" + key + r"}\\" + "\n" +
                r"\toprule " + header + r" \midrule\endfirsthead" + "\n" +
                r"\toprule " + header + r" \midrule\endhead" + "\n" + rows + "\n" +
                r"\bottomrule\end{longtable}" + "\n}\n")
        if table.get("breakable", True) is False:
            body = ("\n" + r"\begin{table}[htbp]\centering\small" + "\n" +
                    r"\caption{" + tex_escape(table["caption"]) + r"}\label{tab:" + key + "}\n" +
                    r"\begin{tabular}{@{}" + "".join(layout) + "@{}}\n" + r"\toprule " + header +
                    r" \midrule" + "\n" + rows + "\n" + r"\bottomrule\end{tabular}\end{table}" + "\n")
        definition("Table", key, body)
    return "\n".join(lines) + "\n"
