---
type: note
created: 2026-10-06
updated: 2026-10-06
tags: [personal, research/autonomous-agents, architecture, reproducibility]
status: decided
---

# Allagma source and study version protocol

The central Allagma source continues to evolve while **each study and campaign retains its selected release bundle**. Normal execution and resume use that lock. Discovering a release, checking whether it is compatible, and adopting it are separate operations. The [[allagma-reference-decisions-2026-10-06|reference decision record]] explains the strategy and alternatives.

## Ownership and file layout

| Area | Owner and update rule |
|---|---|
| Allagma source repository | The maintained source of methods, recipes, adapters, contracts, evaluation packs, and profile examples; contributions and releases originate here |
| Study `.allagma/bundles/<bundle-id>/` | An immutable local copy generated from a release; agents read and use it rather than editing it in place |
| Study `allagma.yaml` | Selection intent and study settings owned by the user, including the recipe, modules, profiles, and adapters |
| Study `.allagma/lock.yaml` | The active resolution to exact releases, module revisions, and bundle contents; maintained by update tooling |
| Study `overrides/` and `modules-local/` | User-owned settings and local variants, with the base module ID and replacement scope recorded |
| Brief, domain code, data, paper, claims | Owned by the study and excluded from bundle replacement |
| Campaign lock snapshot | The configuration actually used by that campaign; authoritative for resume and interpretation of its runs |

The `.allagma/` name marks a generated area, not a privacy or local-only storage guarantee. Locks, selected small bundles, and provenance needed for reproduction can be committed to the study repository. Credentials, complete personal profiles, and large raw data follow separate storage policies.

The study owns its scaffold after generation. Updates do not replace the user's complete `AGENTS.md` or `CLAUDE.md`. Native entrypoints are confined to generated files in the Allagma namespace or explicitly managed include regions, recorded in an ownership manifest.

## Release and lock semantics

Initially, select the required modules from **one coherent Allagma release**. Module IDs and contract versions are separate, but an independent package resolver for arbitrary module-version combinations is not part of the initial implementation. External helper dependencies may have their own environment locks.

| Lock content | Purpose |
|---|---|
| Schema version, Allagma release, immutable source revision | Identify the interpretation rules and source |
| Recipe, selected module IDs, source revisions, dependencies | Reconstruct the composition and complete set of required resources |
| Contract versions, host adapter, capabilities | Describe compatibility and execution prerequisites |
| Bundle ID, file inventory, digests | Check that installed content matches the selected release |
| Generator version, scaffold origin, generation answers | Reconstruct the baseline for a later scaffold migration |
| Effective configuration, profile provenance, override references | Separate resolved choices from study modifications |

Record both the release tag and its immutable source revision. Published tags and bundle contents are not repurposed. A lock cannot consist only of a mutable branch such as `main` or the word `latest`. Required resources resolve inside the bundle rather than through symlinks to a developer's home directory or central working checkout.

The lock reproduces source and configuration. It cannot fix the sampling or server implementation of a closed model service. Run records separately identify the model, runtime, and effective settings actually used.

## Study creation and execution

Creating a study records the selected scaffold release and generation answers, exports the required methods, recipe, and adapters, and checks dependency closure and entrypoints. The lock and user-owned overrides are stored separately. Normal execution must not upgrade the lock automatically.

At campaign start, snapshot the active lock and effective configuration. Every run and resume resolves methods through that campaign snapshot. A later change to the study's active lock does not redirect earlier campaigns to another bundle. Host entrypoints select or recover a campaign first, then read its bundle; they do not substitute the newest user-global skills.

If selection intent and the lock disagree, expose the mismatch rather than resolving a new configuration silently. Distinguish applying edited settings to a new campaign from resuming an earlier campaign with its original lock. This follows the principle of uv's `--locked`, which detects a required lock change; it is not the same as `--frozen`, which uses the lock without checking freshness. [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)

## Update protocol

| Operation | Work performed | Result |
|---|---|---|
| Check | Inspect available releases and compatibility information | Current configuration, available targets, affected modules; active files remain unchanged |
| Plan | Select an exact target revision and generate a candidate bundle in a temporary directory | Added, changed, or retired modules; configuration changes; affected paths; required migrations |
| Reconcile | Compare base, local, and target states; inspect overrides and generated-file ownership | Applicable changes and unresolved conflicts, without overwriting local data |
| Validate | Check contracts, adapter requirements, targeted examples, and applicable migrations | Evidence for adopting the change, with remaining limits identified |
| Adopt | Update the bundle, active lock, and generated entrypoints together at a campaign boundary | A reviewable update commit and record; earlier campaign snapshots remain intact |

Routine updates may proceed within existing user authorization. The protocol does not require a new confirmation for every update. Ask only for a decision that is needed because scope, cost, or permissions would expand, or because a conflict cannot be resolved without understanding the user's intent.

A locally edited file inside a generated bundle must not be overwritten as if it were pristine. Move the change into a local module or override, or incorporate it into the maintained source, then plan the update again. A migration that changes user-owned files identifies those paths and their changed meaning separately in the update diff.

## Scaffold migration

Method updates and study-layout changes are separate. A migration that changes layout, configuration shape, or root entrypoints declares its source and target scaffold versions, generation answers, affected user paths, and transformation.

Preserve a generation baseline and compare base, local, and target states, following Copier's approach to distinguishing local changes from template evolution. Leave unresolved conflicts for review. Replacing user-owned areas with a fresh template, as a recopy operation can do, is not the normal update path. [Copier update](https://copier.readthedocs.io/en/stable/updating/)

Start with explicit migrations and a small exporter. If repeated scaffold changes make template regeneration useful, Copier can implement a migration adapter. Executing a research method must remain independent of whether Copier is installed.

## Version rules and deprecation

Patch releases contain compatible corrections. Minor releases add compatible modules, recipes, or settings. Major releases change an existing public contract or configuration meaning incompatibly. During 0.x development, a minor release may be a breaking boundary; release notes identify the change and migration. A prompt edit also changes distributed content and therefore receives a new source revision. Version numbers alone do not promise unchanged performance.

A deprecated module names its replacement, migration, and earliest retirement release. Honor the announced period of coexistence before retiring a stable module. New resolution may exclude a retired module while preserving bundles already locked by studies. Updates do not rewrite earlier run artifacts or claims with new results.

This follows nf-core's principles of delivering template changes as a separate diff and pinning modules to explicit revisions. Allagma does not require a `TEMPLATE` branch or update bot. If needed later, the same Check and Plan results can be delivered through an automated pull request. [nf-core template sync](https://nf-co.re/docs/developing/template-syncs/overview/), [module update](https://nf-co.re/docs/nf-core-tools/cli/modules/update)

## Rollback and reproduction

Before adoption, the existing lock and bundle remain authoritative. If an adopted configuration causes a problem, select the earlier bundle and configuration snapshot through a new update record. Rollback preserves Git history and research results.

Reverting only the bundle is insufficient if a scaffold migration also transformed user-owned code or data. An inverse migration or a preserved pre-migration state is then required. A failed update records the last completed operation. Earlier campaigns resume against their own locks.

Retain the release assets and module sources referenced by a study. Check campaign references before removing a local bundle. Retirement in the central repository or deletion of a branch must not remove a study's only reproducible copy.

## Initialization acceptance scenarios

1. The same release and selection produce generic, Claude Code, and Codex entrypoints that refer to the same method sources and contracts.
2. Editing the central source leaves a locked study bundle and an active campaign unchanged.
3. Upgrading a context method or recipe preserves study-owned code and overrides.
4. Update planning exposes local edits to generated files and contract mismatches.
5. An earlier campaign can resume with its lock after a newer release replaces or retires one of its modules.
6. Scaffold migration and bundle updates are distinguishable, and the outcome of rollback can be checked.

These scenarios are acceptance criteria for the future exporter and adapters. The protocol above is the adopted design.
