---
type: note
created: 2026-10-05
updated: 2026-10-06
tags: [personal, research/autonomous-agents, architecture]
status: decided
---

# Allagma research harness design v0.2

Allagma is a design for a research harness that can work with any large language model (LLM) agent. It maintains reusable research methods and recipes, connects an idea and available resources to a manuscript with supporting evidence, and improves its own methods through use. It starts as a personal research project, with a contribution model that lets others work on one module at a time.

This specification defines the implementation target. The [[1-projects/maangeek/auto-research-design-2026-10/README|project overview]] explains the relationship between Allagma and its first study, Noemetric.

## 1. Agent portability

Research instructions and artifact contracts are independent of the agent vendor. A **method** defines a research procedure; a **recipe** composes methods into a workflow; an **adapter** connects that workflow to a host or execution environment. Codex, Claude Code, and generic entrypoints are generated from the same source.

Methods use the [Agent Skills format](https://agentskills.io/specification): Markdown instructions with supporting files. A host without native skills support can read those files or receive their contents through an adapter. Cloud hosts can use bundled assets or an artifact API. The [client integration guide](https://agentskills.io/client-implementation/adding-skills-support) describes these delivery options.

| Boundary | Shared Allagma contract | Host-specific integration |
|---|---|---|
| Discovery and activation | Method ID, name, description, activation conditions | Registration paths, commands, prompt UI, context injection |
| Execution | Roles, inputs, outputs, procedure, artifact references | File access, command execution, external job tools |
| Review and parallel work | Reviewer responsibilities, assurance, sequential or parallel semantics | Subagent API, separate sessions, reviewer transport |
| Continuity | Study and campaign state; run and claim records | Hooks, scheduled wake-ups, host memory, scheduler |
| Permissions and models | Required capabilities and a record of what was used | User and host authorization, GUI model selection, authentication |

Native hooks, subagents, MCP servers, and vendor APIs are optional integrations. The default recipe must be expressible through instructions and artifact handoffs. A method that needs a specific capability, such as experiment execution, declares it. If that capability is absent, an explicitly defined equivalent fallback may be used; otherwise, the missing connection is reported for that step. Required scientific checks cannot be dropped as an undocumented fallback.

Shared methods do not embed host tool names or provider-specific frontmatter. Claude Code's invocation controls, native subagent execution, and dynamic context injection belong in its adapter. Codex discovery settings and optional `agents/openai.yaml` metadata belong in Codex packaging. [Claude Code skills](https://code.claude.com/docs/en/skills), [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)

| Initial delivery path | Entrypoint inside a study | Relationship to the source |
|---|---|---|
| Generic agent | `ALLAGMA.md` and the selected bundle's catalog | The same instructions are read from files or injected into context |
| Codex | `.agents/skills/allagma-*/SKILL.md` | Generated from shared methods, with host appearance and dependency metadata |
| Claude Code | `.claude/skills/allagma-*/SKILL.md` | Generated from shared methods, with invocation, hook, and subagent settings confined to the host layer |

Installation is scoped to the study by default. A future global bootstrap may locate the study or campaign lock, but must not inject the newest global methods into a pinned run. Existing user entrypoints are preserved; naming conflicts are resolved within the Allagma namespace.

The initial qualification targets are the generic entrypoint, Claude Code, and Codex. Each adapter records its host version, capabilities, and tested scope. Portable packaging does not establish identical research quality or complete execution support on every host.

## 2. Module boundaries

| Unit | Responsibility | Reason for separating it |
|---|---|---|
| Method | A research procedure, such as context selection, planning, critique, experimentation, or synthesis | A procedure can change without duplicating workflows or provider code |
| Recipe | Method ordering, branching, iteration, termination, and role assignment | New loop designs can reuse and compare existing methods |
| Adapter | Connections to hosts, runners, sources, storage, or external optimizers | Runtime changes do not redefine the research procedure |
| Contract | Shared record schemas and their meaning | Methods have a common basis for handoffs and migration |
| Evaluation pack | Examples, conformance cases, comparison tasks, and scoring scope | The evaluation criterion remains distinct from the implementation being changed |
| Policy and profile | Authorization boundaries, resource constraints, preferences, and default composition | Operating choices remain separate from research logic |
| Distribution | Source selection, bundles, locks, releases, and study updates | Central development can continue while studies preserve their chosen versions |

These are ownership boundaries, not a requirement for seven separately deployed services. Context selection is a method; memory and search stores are adapters; their records are contracts. Tools and schedulers should first be expressed as adapters. Add another module category only when a recurring, independent change cannot be represented by these boundaries.

A module declares its stable ID, input and output contract, required and optional capabilities, settings, dependencies, resources, source lineage, lifecycle, maintainer, and evaluation example. The [[allagma-module-and-contribution-plan|module and contribution plan]] defines these fields.

Initial compositions use modules qualified together in one Allagma release. The registry starts as a readable manifest. A general plugin marketplace and an independent dependency resolver for every module are outside the initial implementation.

## 3. Research and improvement loops

A research recipe addresses a scientific question. An improvement recipe changes how Allagma conducts research. They produce different artifacts and require different evaluations. A change made for one study does not automatically become a shared default.

| Loop | Inputs | Outputs and evaluation |
|---|---|---|
| Research | Idea, resources, study question, data, protocol | Evidence, analysis, claims, manuscript; judged by the supported conclusion and its limits |
| Improvement | Repeated friction or failures, usage feedback, new references, contributor proposals | Candidate methods, recipes, or adapters; comparisons; adoption, rejection, replacement, retirement; releases |

The design draws on three projects. The [[allagma-extensibility-audit-2026-10-06|design lineage audit]] identifies the source files and mechanisms.

| Reference | Design adopted | Allagma adaptation |
|---|---|---|
| ARIS | Composable research workflows, focused active context, persistent records, canonical helpers, maintenance informed by use | A curated method set and a default recipe that includes manuscript writing; no inherited fixed model, score, or approval policy |
| RRSI | Open edit space, component-level hypotheses and history, cost-aware selection, failed-attempt memory, pruning | Methods, recipes, and adapters can all change; initial comparisons may be directed by an agent or a maintainer |
| AntOmniEvo | Separate System, Evaluator, Proposer, and selection roles; file-based tunable artifacts; candidate lineage | Replaceable boundaries and candidate packages; a complete external optimizer requires its own adapter and recipe |

RRSI's decision to adopt a new incumbent differs from AntOmniEvo's parent selection and population elimination. The runtimes are not assumed to be interchangeable. RRSI also considers cost and novelty within a noise band; its selection policy cannot be reduced to accepting only score gains larger than the noise estimate.

## 4. Research inputs and personal configuration

The user supplies an idea, available data or code, resources, and the desired output. The agent develops the research brief and proceeds with planning, implementation, reruns, and writing within existing authorization. Questions are reserved for missing information that would materially change the result.

| Brief field | Meaning |
|---|---|
| `question`, `motivation`, `success_criteria` | The question and the conditions under which the work would be useful |
| `resources` | Compute and backend access, data, storage, time, cost ceilings |
| `capabilities` | Available execution, network, and external actions, with their authorization limits |
| `constraints` | Baselines, definitions, license conditions, and user preferences to preserve |
| `output` | A manuscript draft and evidence package by default; the requested format or a generic article |
| `stop_rules` | How to stop and report budget exhaustion, repeated failure, absent signal, or required external input |

An unspecified budget is `unset`, not unlimited. Design work and available local analysis may continue. Writing a manuscript does not authorize its submission.

Configuration precedence is: current user request, study overrides, personal profile, recipe defaults, then module defaults. Configuration cannot expand host permissions. The effective configuration records both the resolved values and their origins. A campaign freezes these values; later profile edits do not alter an active campaign.

Public profile examples are separate from personal profiles. Reporting language, writing style, and preferred methods are configurable. Preserve the user's GUI model selection; do not add project-level `model` or `review_model` pins without an explicit request. A fixed model in a comparison campaign is an experimental control recorded for that campaign, not a permanent project model pin.

## 5. Framework and study ownership

Allagma owns common workflows, module contracts, configuration resolution, evidence links, and the improvement process. A study owns its question, scientific metrics, generators or simulators, domain runners, evaluators, analysis, raw evidence, and manuscript.

A study evaluator assesses scientific results. An Allagma evaluation pack assesses the behavior or usefulness of a method, recipe, or adapter. A successful runner invocation or completed manuscript establishes neither a scientific hypothesis nor an improvement in research capability.

Computational research is the first execution target. Literature studies, theory, simulation, training, and measurement may use different recipes and study adapters rather than a single mandatory experiment sequence.

## 6. Default research lifecycle

| Phase | Outputs | Evidence required to advance |
|---|---|---|
| Scope | Brief, literature and evidence map, novelty uncertainty | A testable question and a clear relationship to prior work |
| Protocol | Hypotheses, controls, metrics, analysis plan, budget | Defined evaluation and dataset boundaries, including failure criteria |
| Pilot | Small actual runs, calibration, cost and variance estimates | Known-answer controls and runner/evaluator qualification |
| Campaign | Raw evidence and failures under a frozen protocol | The declared stopping or completeness condition |
| Analysis | Recomputable tables and figures, sensitivity analysis, negative findings | Links to raw artifacts and the analysis revision |
| Manuscript | Claims, methods, results, limits, bibliography | Traceable evidence and scope for empirical claims |
| Audit | Reproduction report, claim audit, unresolved limitations | A research package that distinguishes completed checks from remaining limits |

These phases define responsibilities in the default recipe. Different methods or loop structures may produce the same outputs. A study type may explicitly omit an inapplicable experimental phase. Negative and inconclusive conclusions are valid outcomes. Budget exhaustion produces a partial package with the reason for stopping.

Keep `phase`, `execution_status`, and `assurance` separate. A fresh-context review from the same model family is provisional critique. Deterministic checks provide assurance only within their coverage. Protocol amendments record the reason, affected runs, and new revision without overwriting results. Discovery and pilot data are not reused as untouched confirmation data.

## 7. Shared evidence contracts

| Record | Required content and invariant |
|---|---|
| `StudySpec` | Reconstruct the question, release and bundle lock, profile provenance, effective configuration, resource policy, and protocol revision |
| `ExperimentSpec` | Identify the hypothesis, inputs, runner/evaluator versions, seed policy, budget, expected artifacts, and editable versus fixed boundaries |
| `RunRecord` | Record run and attempt IDs, timestamps, exact inputs and outputs, environment and model/data revisions, usage, status, and errors; a retry never erases an earlier attempt |
| `AnalysisRecord` | Link the raw manifest, analysis revision/configuration, outputs, exclusions, and uncertainty; reported numbers must be recomputable from the same inputs |
| `ClaimRecord` | Connect claim text to supporting and contradicting evidence, scope, limitations, and status; changes to evidence make dependent claims stale |
| `ReviewRecord` | Record reviewer/backend, material revision, criteria, verdict, findings, and trace; a verdict is not reused for an unreviewed revision |

Machine-readable records carry a schema version. Markdown supplies explanations for readers. Raw artifacts are append-only in meaning; large data has content references and a retention policy. Numbers generated in prose do not become results without verification. Bibliographic metadata and whether a source supports a claim are checked separately.

## 8. Adoption and replacement

The improvement process is: source or usage feedback, proposal, candidate, comparison, decision, release. Each record identifies the component and hypothesis, baseline and candidate, outcome, cost, user intervention, and the reason for adoption, rejection, replacement, or retirement. A result from one study is not automatically generalized to all research.

Module lifecycle states are proposed, experimental, stable, deprecated, and retired. **Default selection belongs to a recipe or profile.** Merging an experimental contribution and selecting it for the default recipe are separate decisions. Replacements name the new ID, migration, and rationale. Historical bundles remain available after retirement.

Comparisons control the controller, tasks, and resources except for the factor under study. They consider evaluation noise, operating cost, and added complexity. A new model or paper is a reason to investigate, not sufficient evidence for adoption. Removing unhelpful scaffolding is also an improvement.

Automatic harness search can be added when usage history and suitable comparison tasks justify it. The same proposal and decision records support manual or agent-assisted maintenance from the start. See the [[allagma-module-and-contribution-plan|lifecycle and contribution rules]].

## 9. Distribution and study versions

The default distribution is a **study-local bundle of methods, recipes, and adapters selected from one release, with an exact lock**. The central source can evolve while each study and campaign retains its selected configuration. The [[allagma-reference-decisions-2026-10-06|reference decisions]] explain the choice.

The bundle is generated; the brief, domain code, and local overrides belong to the study. Normal execution and resume never upgrade a lock. Updates follow Check, Plan, Reconcile, Validate, and Adopt, with adoption at a campaign boundary. Scaffold migration is separate from method updates.

The initial implementation uses one distribution path rather than mandatory submodules, a live shared checkout, and a package runtime together. Helper dependencies can have separate environment locks. The [[allagma-study-version-protocol|study version protocol]] governs bundle contents, ownership, migration, and rollback.

## 10. Open-source contributions

Contributions should be small enough to review independently. A contributor can work on a method, recipe, adapter, evaluation, document, or example. The default conformance kit and toy study must run without paid APIs or a GPU. Checks are proportional to the change; a full research campaign is not required for every pull request.

Initialization includes a contributor guide, module-authoring example, governance and review ownership, issue and pull request templates, and release and migration notes. Changes to a public contract or default behavior that have broad effects start with a short design proposal. Small fixes do not require that process. The project license and third-party notices are settled before the first public release. Public documentation is in English; personal reporting language is selected through a profile.

## 11. Initial repository and acceptance criteria

```text
allagma/
  README.md
  AGENTS.md
  CONTRIBUTING.md
  GOVERNANCE.md
  CODE_OF_CONDUCT.md
  LICENSE
  methods/                    # portable SKILL.md, manifest, resources
  recipes/                    # default research and improve-allagma
  adapters/                   # generic, host, runner, evaluator integrations
  contracts/                  # shared artifact schemas and compatibility
  policies/                   # operating-policy examples
  profiles/                   # public composition examples
  evals/                      # module comparisons and general fixtures
  conformance/                # generic and host adapter contract checks
  examples/toy-study/          # a baseline requiring no external account
  templates/study/             # initial scaffold; then owned by the study
  tools/                      # validators, bundle export, update planning
  docs/                       # architecture, adoption, authoring, releases
  .github/                    # contribution templates and targeted CI
```

| Milestone | Deliverable | Acceptance evidence |
|---|---|---|
| I1. Portable foundation | Canonical methods, one default recipe, generic/Claude Code/Codex entrypoints | A small walkthrough uses the same method contracts and artifacts without native hooks or subagents |
| I2. Replaceable composition | An alternative context method, a reviewer adapter change, a new recipe | Each replacement works without duplicating or broadly rewriting other shared modules |
| I3. Contributor path | A minimal module example, conformance kit, ownership and lifecycle documentation | A contributor can change one module and run its targeted checks without an external account |
| I4. Versioned studies | Bundle and lock, overrides, update and migration examples | Central changes do not leak into a pinned campaign; a study can be reconstructed after an update, retirement, or rollback |
| I5. Research walkthrough | Toy raw output, analysis, claim, and short manuscript | Evidence links and records for success, failure, and interruption are demonstrated |

Build small I1-I4 examples alongside the I5 walkthrough. Supporting every provider or optimizer is not a prerequisite for the first study. Resume, budget, and measurement checks are added before an adapter performs the corresponding real work.

## 12. Decisions and implementation priorities

The selected architecture is a portable core, replaceable methods and recipes, explicit adapter and contract boundaries, a lifecycle separate from default selection, an accessible contribution process, and coherent release bundles with study locks. Implementation should establish these boundaries through small working examples.

Package distribution, remote scheduling, the scale of automatic search, and additional hosts depend on actual use. The license and release responsibilities must be settled before publication. These later choices do not defer the portable core or study ownership rules.

The [[allagma-extensibility-audit-2026-10-06|v0.1 design audit]] and Git history retain the earlier rationale. The current supporting decisions are in [[allagma-reference-decisions-2026-10-06]], and the v0.2 implementation-planning record is [[allagma-plan-update-task-state]].
