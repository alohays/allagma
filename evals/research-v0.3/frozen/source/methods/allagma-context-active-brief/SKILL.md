---
name: allagma-context-active-brief
description: Select focused campaign context while preserving constraints and evidence.
---

Select the campaign before selecting context. Read its lock, protocol revision and current status. With no campaign, read the study lock and report any mismatch with selection intent.

Always retain the question, constraints, stop rules, protocol and unresolved findings. Include evidence relevant to the current phase with its path and digest; summarize the rest without deleting permanent records. If the required context alone exceeds the requested size, report the overrun rather than silently dropping a constraint. ContextRecord records selected and omitted artifact IDs. Optional search may enrich this set but is not needed for the file-based fallback.

Use `select.py` with `example.json` for a deterministic selection example. This checks retention and size accounting, not the quality of model reasoning. Load the selected recipe and artifacts only when needed.
