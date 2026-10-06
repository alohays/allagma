---
type: decision
created: 2026-10-06
updated: 2026-10-06
tags: [personal, research/autonomous-agents, architecture]
status: decided
---

# Allagma portability and versioning decisions

Allagma combines portable methods and host adapters, release bundles pinned inside each study, and separate scaffold migrations. This supports central maintenance without changing the methods used by an active study. It also lets a new contributor work without installing every supported runtime.

## A shared format for different agents

The [Agent Skills specification](https://agentskills.io/specification) defines `SKILL.md` and supporting files. Its `allowed-tools` field is experimental and may behave differently across hosts. The [client implementation guide](https://agentskills.io/client-implementation/adding-skills-support) distinguishes local file access from cloud delivery and prompt injection. Packaging compatibility and available execution capabilities therefore remain separate concerns.

[OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) describes progressive disclosure: discover a skill through its name and description, then load the full instructions. It also documents Codex's `.agents/skills` paths. [Claude Code skills](https://code.claude.com/docs/en/skills) adds invocation controls, subagent execution, and dynamic context injection to the open format. Allagma places those extensions in host adapters rather than shared method instructions.

**Decision:** Generate native skill entrypoints and a generic instruction entrypoint from one Markdown source. Adapters own registration paths, tool names, hooks, approval integration, and process invocation. The default recipe remains interpretable without native subagents or a vendor API. Automated execution requires the capabilities declared by the selected recipe.

## References for central sources and downstream projects

| Reference | Existing mechanism | Principle adopted by Allagma |
|---|---|---|
| [Copier update](https://copier.readthedocs.io/en/stable/updating/) | Regenerates the earlier template with its recorded answers, separates local changes from template evolution, and applies migrations; unresolved conflicts require review | Preserve the original template revision and generation answers; compare base, local, and target states for scaffold migration |
| [cruft](https://cruft.github.io/cruft/) | Records a Cookiecutter template commit and variables in `.cruft.json`; presents update diffs and supports excluded paths | Record provenance and file ownership at creation; do not make cruft mandatory when Allagma has no existing Cookiecutter base |
| [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) | Separates requirements from their resolution; `--locked` rejects a required lock change, whereas `--frozen` uses the lock without checking freshness; a newer release alone does not invalidate an existing lock | Separate use from upgrade; normal study execution keeps its lock and exposes a mismatch with selection intent |
| [nf-core template sync](https://nf-co.re/docs/developing/template-syncs/overview/) | Keeps an unmodified template on a `TEMPLATE` branch and offers downstream update pull requests that separate template changes from customization | Deliver updates as reviewable diffs; represent ownership through generated bundles and manifests without requiring a `TEMPLATE` branch |
| [nf-core module update](https://nf-co.re/docs/nf-core-tools/cli/modules/update) | Supports excluding modules from updates and choosing specific commits | Pin component revisions and specify the update target; initially select compatible components from a single Allagma release |
| [Git submodules](https://git-scm.com/docs/gitsubmodules) | A superproject's gitlink pins a commit in a separate repository | A reproducible alternative, but not the default because it requires consumers to manage a nested Git workflow |

These are references for working maintenance protocols. Their suitability for Allagma is judged against file-based consumption, the maintenance cost of a personal project, and the need to pin research configurations.

## Selected distribution strategy

Use a **study-local bundle with a release lock**. The initial exporter selects a recipe and its required modules and resources from one Allagma release. The bundle includes all required transitive resources. Execution does not depend on a live `main` checkout or a user-global skills directory. The lock records the resolved composition.

Research code, briefs, and overrides belong to the study; the shared bundle is generated. Local edits inside a bundle must be resolved as local modules, overrides, or source contributions before replacement. Adopting a central release is an explicit update operation that proceeds through diff review and validation within existing authorization.

The study owns its scaffold after generation. Layout and configuration-shape changes use versioned migrations with a preserved baseline, following Copier's approach. A template engine is not an initial runtime dependency. If repeated scaffold evolution makes regeneration useful, Copier can implement the migration adapter later.

## Alternatives not selected as defaults

| Alternative | Tradeoff and decision |
|---|---|
| Every study reads a central working checkout or global install | Convenient for development, but external edits can affect the next run; restrict this to development use |
| Continuously merge every study file from a template | Mixes research code and shared methods into the same merge surface; use template migration only for the scaffold |
| Mandatory submodule | Supports precise pins, but complicates source archives, cloud workspaces, and ordinary file-based consumption |
| A mandatory Python or Node package runtime | Appropriate for some helpers, but unnecessary for instruction-only use; lock helper dependencies separately |
| Independent module-version resolution from the start | Increases compatibility and resolver maintenance work; begin with a coherent release pin while retaining module IDs and contract metadata |

## Principles retained

Study-owned evaluators, explicit evidence contracts, valid negative results, and campaign pinning remain in force. A backend or model change should not require another copy of the research methods. Supporting a module as stable and choosing it as a personal default are separate decisions.

The [[allagma-extensibility-audit-2026-10-06|design lineage audit]] records the mechanisms borrowed from ARIS, RRSI, and AntOmniEvo. The additional check on 6 October 2026 found ARIS at `3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`. Its changes after `5895d19` affected only two README files, leaving the inspected methods unchanged. RRSI remained at `be50316e1db05914068a973f322770ef08ed7ba1`, and AntOmniEvo at `19008bd45963c1dce17a11c086b28a643774ac12`.
