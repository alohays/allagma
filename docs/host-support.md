# Host support and qualification

All hosts route to the same bundle catalog, canonical instructions and evidence
contracts. Generic delivery uses `ALLAGMA.md`. Codex uses study-local
`.agents/skills/allagma-*/SKILL.md`; Claude Code uses
`.claude/skills/allagma-*/SKILL.md`. Native wrappers select the campaign before
loading method text. Existing root instructions and user skills are preserved.

These paths follow [OpenAI's Build skills documentation](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code's skills documentation](https://code.claude.com/docs/en/skills).
Shared frontmatter follows the [Agent Skills specification](https://agentskills.io/specification).
The sources were rechecked during the self-audit on 7 October 2026. No provider-specific frontmatter,
hooks, subagents, tool allowlists or model overrides are required by the default
recipe. Optional metadata can be added in a host adapter when actually needed.

| Path | Qualification in v0.2 | What is not established |
| --- | --- | --- |
| Generic/Python local | Actual complete toy execution, restart, recomputation and artifact audit | General scientific or model research quality |
| Codex | Format and contract checked; registration/conflict/campaign-routing fixtures | Real native activation/tool-use smoke; model quality |
| Claude Code | Format and contract checked; registration/conflict/campaign-routing fixtures | Real native activation/tool-use smoke; model quality |

The acceptance report records OS, Python, installed host versions when found,
date, capabilities and exact tested scope. Local inspection found `codex-cli
0.151.0` and Claude Code `2.1.217` on 6 October 2026; these are **version probes**,
not assertions that either host ran the research workflow. The no-account kit
does not launch paid or authenticated model sessions.

A future host smoke check should retain evidence for skill discovery/activation,
capability mapping, lock routing and the shared artifact handoff, with host and
backend versions. Output quality needs a separate evaluation pack. Do not infer
complete execution support from loading a skill file.

Without native skills, read or inject the exact generic files. Without native
subagents, use sequential artifact handoffs. Without local execution or an
explicitly equivalent runner, report the missing capability and continue only
the applicable design work. Do not bypass qualification or fabricate results.
