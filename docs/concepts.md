# The records behind a study

Allagma gives a coding agent a research process it can carry between sessions.
Its methods ask the agent to formulate a question, freeze a protocol, execute
within limits, inspect uncertainty and tie claims to evidence. The helper
retains the artifacts that let a researcher check what actually happened.

## Three useful distinctions

**A study is the continuing question; a campaign is one frozen plan.** A study
can contain several campaigns when a protocol changes. A campaign points to
exact methods, scientific code, inputs and settings. An analysis revision gives
a particular interpretation of included results without overwriting the old one.

**A run is a planned observation; an attempt is an execution.** A failed attempt
and its retry are two attempts at one run. They are not two independent
scientific observations. Pilots also do not become untouched confirmation data.

**Completion is not assurance.** Phase says where the workflow is, execution
status says what the process did, and assurance says what kind of checking was
performed. A completed session with a deterministic audit is not an independent
scientific peer review.

## How the pieces fit

| Piece | Responsibility | Example |
| --- | --- | --- |
| Method | Portable instructions with an input/output contract | Form a protocol, analyze results, audit claims |
| Recipe | Ordering, handoffs, branches and stopping rules | The default research workflow |
| Adapter | Connect a host, runner or reviewer to those contracts | Codex skill delivery or local execution |
| Bundle | Exact copies selected for a study | Methods plus the helper at a content digest |
| Lock | Identity, composition and configuration of that bundle | The campaign's `lock.yaml` |
| Claim | A scoped statement linked to supporting/contradicting evidence | Supported average effect, contradicted universal claim |

Methods are canonical Agent Skills. Provider-specific behavior belongs in
adapters. Hypotheses, training code, metrics and statistical choices belong in
the study. A locked copy is generated evidence, not another editable source.

## What the agent still has to do

Allagma does not supply the scientific answer, choose a universally valid
statistical test, or replace expert judgment. An agent can still misunderstand
a source, write a bad experiment or overinterpret data. The records make those
failures more inspectable; deterministic tests cover only what they test.

For implementation detail, continue to [architecture](architecture.md),
[contracts](contracts.md), [study-owned programs](study-adapters.md),
or [versioning](versioning.md).
