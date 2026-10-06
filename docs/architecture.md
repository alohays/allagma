# Architecture and guarantees

A method owns a research procedure. A recipe owns its ordering, roles, branches
and stopping conditions. An adapter owns delivery or execution. Contracts own
artifact meaning; evaluation packs own checking criteria. Policies and profiles
own authorization/resource limits and composition preferences. Distribution
assembles those artifacts from one coherent release.

`registry.json` is the readable catalog. Each module has a stable ID and an
adjacent `module.yaml`; IDs are independent of directory and distribution names.
Methods and recipes use portable `SKILL.md` frontmatter containing only name and
description. Provider paths and tool mappings remain in host adapters.

The Python code is a collection of deterministic helpers, not a required agent
or a general workflow engine. An agent can follow the same methods with file
handoffs. Executable recipes use small declared settings; the toy driver is a
bounded walkthrough of those handoffs. No model chooses scientific conclusions
inside the helper layer.

## Configuration and authorization

Resolution applies module defaults, recipe defaults, profile settings, study
settings, override files and finally the current request. Within study settings,
explicit override files win. The lock records each leaf's origin, input digests,
profile identity and effective values. Campaign snapshots freeze all of them.
Configuration may narrow available capabilities; it cannot add authorization.

`unset` budgets are not unlimited. The default local adapter has bounded job
timeouts and requires a finite protocol. It performs no paid API calls, model
calls or publication. Resource ceilings count every attempt, including failures
and interruptions. Measured wall time includes process overhead; cancellation
and startup add a small bounded delay. Recovery records whether time is measured
or conservatively charged from an uncertain worker's deadline.

Host permissions remain authoritative. These helpers do not implement an OS
sandbox, and study-owned programs execute with the invoking user's permissions.
Only execute code you have authorized. A missing execution capability blocks
execution; it does not erase the scientific qualification step. Sequential file
handoffs replace optional native subagents without removing review obligations.

## Evidence and scientific ownership

The study owns its brief, scientific protocol, generators, runner, evaluator,
analysis, claims and paper. The framework owns identity, capture, resource
checks, version routing and evidence links. A successful process is not a
scientific result; a study-owned evaluator must qualify the raw output.

`phase`, `execution_status` and `assurance` are separate. Known-answer pilots
precede confirmation, and the helper rejects overlapping seed sets. Protocol
changes require a new campaign; record the amendment's reason and affected runs
in the new protocol. The prior protocol and attempts remain intact.

Started and terminal attempt records have separate immutable paths. A retry
uses a new attempt directory. Workers own their child timeout independently
of the controller. An uncertain attempt is recovered as interrupted, never as
success inferred from a leftover file. Completed outputs are digest-checked
before the engine skips a run. Local mutation locks prevent two controllers
from writing one study concurrently.

Analysis records point to raw manifests, code revisions, configuration,
exclusions, uncertainty and outputs. Claims include both supporting and
contradicting evidence. The audit recursively verifies dependencies, reruns the
analysis and regenerates the deterministic toy manuscript. Changed evidence
produces stale-claim findings without modifying the original claim ledger.
Review verdicts refer to a material digest and state their coverage. The default
review is deterministic, not independent scientific peer review.

Content hashes detect changes against retained references; they are not digital
signatures or protection against rewriting an entire trusted history. Keep a
study's source and evidence under version control or other retained storage.

## Deliberate limits

Supported execution is a local POSIX Python process. Generic instruction use,
Codex packaging and Claude Code packaging share contracts, but native activation
and research quality need separate qualification. Remote jobs, automatic
population search, arbitrary independent module-version solving, scientific
Noemetric experiments and public publication are outside v0.2.
