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
| Codex CLI 0.160.1 | Real explicit skill activation, campaign-lock routing, interrupted/fresh-session continuation and complete MPS diffusion study | Other models/versions, implicit triggering, desktop UI interaction and general research quality |
| Claude Code | Format and contract checked; registration/conflict/campaign-routing fixtures | Real native activation/tool-use smoke; model quality |

The acceptance report records OS, Python, installed host versions when found,
date, capabilities and exact tested scope. Local inspection found `codex-cli
0.151.0` and Claude Code `2.1.217` on 6 October 2026; these are **version probes**,
not assertions that either host ran the research workflow. The no-account kit
does not launch paid or authenticated model sessions.

On 8 October 2026 (Asia/Seoul), the separate
[weight EMA diffusion study](../studies/ema-2d-diffusion/README.md) executed the
native path using the desktop app's bundled CLI 0.160.1 and inherited
`gpt-6-astra` / `max` settings. No project model override was added. The older
0.151.0 CLI rejected that model, and its failure is retained. The native study
used actual MPS training, four pilots, ten new confirmation trajectories, a
deliberate interruption and fresh-session recovery, then analysis, audit,
independent recomputation and a reporting correction following native critique.

The [host report](../studies/ema-2d-diffusion/HOST-QUALIFICATION.md) and
[qualification receipt](../studies/ema-2d-diffusion/evidence/host-qualification.json)
link exact prompts, JSONL traces, thread IDs, helper paths, model observations,
locks and scientific outputs. This qualifies the recorded explicit workflow on
that environment; it does not infer implicit skill-trigger reliability or
general research quality. The default no-account conformance kit still does
not launch native model sessions. Other hosts need their own execution evidence.

Without native skills, read or inject the exact generic files. Without native
subagents, use sequential artifact handoffs. Without local execution or an
explicitly equivalent runner, report the missing capability and continue only
the applicable design work. Do not bypass qualification or fabricate results.
