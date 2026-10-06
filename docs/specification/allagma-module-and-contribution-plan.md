---
type: note
created: 2026-10-06
updated: 2026-10-06
tags: [personal, research/autonomous-agents, architecture, open-source]
status: decided
---

# Allagma modules and contributions

An Allagma module has a defined responsibility, an input/output contract, declared capabilities, a small example, and a way to check its behavior. Someone changing a research method should not need to understand provider integration code or release tooling. This document defines the module and contribution rules for [[framework-design|Allagma design v0.2]].

## Ownership boundaries

| Unit | Decisions it owns | Example replacement |
|---|---|---|
| Method | How to select context, plan, critique, analyze, experiment, or write | Use an active brief and relevant evidence instead of the complete history |
| Recipe | Method ordering, branches, loops, termination, and selected roles | Replace a single proposal/review sequence with candidate generation and comparison |
| Adapter | Host tools, runners, sources, stores, and external engines | Connect the same reviewer role to Claude Code or another agent backend |
| Contract | Shared records, input/output meaning, schema compatibility | Add an evidence field and migrate earlier records |
| Evaluation pack | Behavioral examples, comparison tasks, scoring and checking procedures | Replace the fixtures used to assess context omissions, cost, and usefulness |
| Policy and profile | Authorization, resources, personal preferences, default composition | Change when the user intervenes or which recipe is preferred |
| Distribution | Resolution into bundles and delivery of updates and migrations | Replace local export with release-asset downloads while preserving lock semantics |

The first six units are independently managed artifacts. Distribution is the small set of tools and protocols that assembles them. The initial release qualifies a coherent combination; it does not require seven services or package managers.

Context and memory do not need another plugin system. Selection and summarization are methods, search and storage connections are adapters, and provenance and artifact references are contracts. Scheduling and external optimization start as combinations of adapters and recipes. Add a new boundary only when these categories cannot represent an independent change cleanly.

## Shared method and recipe format

The instructions read by users and agents live in an Agent Skills-compatible `SKILL.md`, with structured Allagma metadata in an adjacent `module.yaml`. Common frontmatter centers on `name` and `description`. Host invocation controls, models, hooks, and tool allowlists belong only in generated host entrypoints. A generic agent can consume the same instructions and resources through file access or prompt injection. [Agent Skills specification](https://agentskills.io/specification), [client integration](https://agentskills.io/client-implementation/adding-skills-support)

The initial module contract contains:

| Fields | Meaning |
|---|---|
| `id`, `kind`, `entry` | Stable identity, responsibility, entry path within the bundle |
| `contract`, `inputs`, `outputs` | Artifact meaning and schema versions consumed and produced |
| `requires`, `optional` | Required capabilities and optional enhancements, rather than host tool names |
| `dependencies`, `resources` | Modules and supporting files that must travel with the module |
| `settings` | Configuration meaning, defaults, and allowed values |
| `lifecycle`, `maintainer` | Support status and review responsibility |
| `sources`, `adaptation` | Upstream revisions and locations, with Allagma's changes identified |
| `evaluation`, `examples` | Locations of checks and usage examples |
| `compatibility`, `replacement` | Host and contract requirements, plus a replacement path when deprecated |

For example, `context/active-brief` may require artifact read/write access and make search optional. It does not require a tool literally named `Read`, or a particular Codex tool. An adapter maps those capabilities to available host actions. Stable IDs are separate from distribution names. Generated skill names use the `allagma-` namespace and respect host naming limits.

A recipe declares its method IDs, input/output connections, branches, stopping rules, roles, and capabilities. Initial control flow is expressed in Markdown and small configuration files. A loop that needs executable logic can add a helper owned by the recipe. An alternative engine is an explicit dependency; it does not justify separate provider-specific copies of the shared methods.

## Configuration and personal preferences

Resolve configuration in this order: current user request, study overrides, personal profile, recipe defaults, module defaults. These settings cannot expand host, organization, or system permissions. Record the resulting values and their origins, then freeze them when a campaign starts.

The public repository contains profile examples. Personal profiles, credentials, and private study content are kept out of public releases. An explicitly stated preference is a basis for profile configuration. A claim that an agent-generated change improves performance requires comparison evidence. A single environmental failure must not become a permanent rule for every host.

## Lifecycle and default selection

| State | Permitted use | Requirement for advancement or transition |
|---|---|---|
| proposed | Review the source and design idea | Identify the responsibility, difference from alternatives, owner, and a small example |
| experimental | Use in studies that explicitly select it | Pass contract checks and an example; state limitations and supported hosts |
| stable | Support within the declared compatibility scope | Complete relevant evaluation and host qualification; provide documentation and maintenance ownership |
| deprecated | Continue existing use while moving to a replacement | Record the reason, replacement or alternative, migration, and earliest retirement release |
| retired | Exclude from new selections | Honor the announced migration window and replacement path; retain historical bundles |

**Default is a selection, not a lifecycle state.** A recipe or profile chooses the modules to use. Public default recipes and profiles select stable modules. A personal profile may explicitly opt into an experimental composition while identifying it as such. A module becoming stable does not change every user's defaults. Merging a contribution and promoting it to stable are separate decisions.

A rejected proposal remains in proposal history without entering the distribution catalog. An experimental module may move directly to retired when its results warrant that decision. Stable deprecation commitments differ from experimental support, but artifacts already referenced by studies are preserved in either case.

A replacement connects the old and new IDs, changes to inputs or outputs, migration instructions, and comparison evidence. Plan deprecation so the old and new options can coexist in at least one subsequent compatible release, and name the earliest retirement release. A removal that breaks an existing contract is delivered as a breaking release. During 0.x development, a minor release may be that boundary; release notes must identify the break explicitly.

Retirement does not delete earlier releases. Studies and runs that reference a module must remain reconstructable. Manifests and release notes identify unsupported scope. Historical reproduction and current support are different commitments.

## Improvement records

An improvement record identifies the target, hypothesis, source revision, baseline and candidate, evaluation used, outcome, cost, user intervention, and the reason for adoption, rejection, replacement, or retirement. RRSI's component, history, and selection mechanisms inform this record; AntOmniEvo's candidate artifacts provide a useful representation of the material being compared. The [[allagma-extensibility-audit-2026-10-06|design lineage audit]] gives the source locations.

A candidate stopped by an environmental problem before evaluation is `not evaluated`, not a measured negative result. A method rejected under one model, task, or environment may be reconsidered when those conditions change. Its earlier evidence remains part of the record. The number of modules is not an improvement metric.

## A contributor's first change

A first contribution should require understanding one module or example. The default development environment and conformance checks must work without paid model APIs or a GPU. Claims about real model behavior require the relevant evidence, but documentation, schema, and adapter-mock changes do not require a full research campaign.

| Contribution | Minimum submission | Review scope |
|---|---|---|
| Documentation or example | An example consistent with the change, with sources where needed | Links, rendering, and agreement with the documented contract |
| Method | Manifest, instructions, example, evaluation fixture, source and attribution | Inputs and outputs, capabilities, intended benefit |
| Recipe | Method connections, branches, stopping conditions, a small walkthrough | Reuse of methods, missing handoffs, cycles, and termination |
| Host adapter | Capability mapping, fake-host tests, installation and usage notes | Shared contract; real-host support claims need separate smoke evidence |
| Evaluation pack | Task provenance, expected behavior, scoring scope | The evaluation target, leakage boundaries, repeatability |
| Contract or distribution change | Design decision, compatibility and migration examples | Earlier and new studies, generated-file ownership |

The contribution process is an issue or direct pull request, targeted checks, maintainer review, merge, and release. Small documentation changes and bug fixes do not need a preliminary proposal. Broad changes to a public contract, ownership rule, or default behavior start with a short design proposal. External contributions require maintainer review; that process is separate from the user's existing authorization for work in a personal workspace.

Initially, the project maintainer makes final decisions and records review ownership for modules. Ownership can be delegated as the contributor base grows. Do not promise a review response time before there is capacity to meet it.

## Contributor materials required at initialization

- `CONTRIBUTING.md`: the first example, where to make each kind of change, targeted checks, and the pull request process.
- `docs/module-authoring.md`: a minimal module, recipe and adapter examples, contracts, and capability rules.
- `GOVERNANCE.md` and `CODEOWNERS`: decision and review responsibilities, including how disagreements are handled.
- `CODE_OF_CONDUCT.md` and issue/pull request templates: entrypoints for bug reports, methods, and adapters.
- `examples/toy-study/` and `conformance/`: small reference cases requiring no external account.
- `CHANGELOG.md`, release notes, and migration examples: enough information for consumers to assess a change.
- `LICENSE` and applicable attribution/notices: select the project license before the first public release and record the conditions of files actually reused.

Public code, documentation, and contribution templates use English. Personal reporting language is a profile setting. Contributors should not have to reproduce the maintainer's personal preferences or provider accounts.

## Verification cost and support claims

The support matrix records adapter and host versions, operating environment, capabilities, fixtures checked, and the date. Distinguish **format compatible**, **contract checked**, and **host qualified**. Loading a skill file does not establish complete research-workflow support.

A shared method change checks the generic path and the contracts of supported host entrypoints. Fake-host tests assess data handoffs and capability behavior. Real-host smoke checks assess activation, tool mapping, and artifact handoffs. Evaluation packs assess output quality separately. Allagma does not promise byte-identical reproduction of hosted-model sampling or backend behavior.

Module publication and study updates follow the [[allagma-study-version-protocol|study version protocol]].
