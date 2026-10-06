# Author one module

A small contribution should involve one directory and a registry entry.
`methods/allagma-context-active-brief/` is the minimal executable reference:
portable instructions, `module.yaml`, a thin `select.py` helper and an input
fixture. The full-record alternative keeps the same input/output contract.

1. Copy the directory to a new `allagma-*` name.
2. Set the matching `name` in SKILL.md and a new stable `id` in module.yaml.
3. Describe the behavioral difference and activation conditions. Keep host
   commands, model pins and native tool names out of shared instructions.
4. Retain or explicitly migrate the input/output contract. Declare required
   capabilities, all resources and dependencies, settings, owner, lifecycle,
   source lineage, adaptation, example and evaluation scope.
5. Register the ID/path in `registry.json`, or use an explicit study-local
   overlay. Start as experimental until qualification supports a stable scope.
6. Run the targeted module check and the executable example. Test the behavior
   you changed; broad research claims need a suitable comparison.

```sh
python3 -m allagma check --module context/active-brief
python3 methods/allagma-context-active-brief/select.py \
  methods/allagma-context-active-brief/example.json /tmp/context-example.json
python3 -m allagma validate-record /tmp/context-example.json
```

The thin context helper uses its adjacent manifest's ID in the output, so a
derived method retains its own producer identity without copying the selector
implementation. To change the algorithm, supply a helper implementing the same
ContextRecord contract and update the example. Source checks validate naming,
frontmatter, capability/dependency closure and resource paths.

## Recipes and adapters

A recipe has portable instructions and `recipe.json`: roles, steps with method
IDs and consumed/produced contracts, branches, stopping conditions and supported
settings. `recipe/research` and `recipe/replication` share methods; replication
requests two reanalysis passes instead of one. The helper implements this small
declared control surface, not an arbitrary workflow language. New loop engines
must supply their own helper as a resource and qualify its semantics.

Adapters map capabilities and artifact handoffs to a host or local runner.
`reviewer/checklist` and `reviewer/trace` accept the same input and produce the
same verdict/findings/coverage handoff, then the framework records ReviewRecord.
The second checks additional dependency digests. Both are explicitly
deterministic examples, not real-model reviewers.

For a host adapter, provide capability mapping, installation paths, missing-
capability behavior, fake-host fixtures and usage notes. Native provider
settings belong in its generated packaging. A host version probe alone is not
activation qualification. Required scientific checks cannot disappear as an
undocumented fallback.

## Improvement and lifecycle

Run `python3 -m allagma compare --output work/comparison-1` to inspect a bounded
candidate/proposal/measurement/decision example. Keep controller, evaluator,
task split and resources fixed apart from the factor under study. Record cost,
noise, intervention and complexity. Preserve rejected and unevaluated candidates;
an environment failure before evaluation is `not evaluated`.

Adoption, replacement, retirement and default selection are separate decisions.
The local comparison does not change defaults. See [governance](../GOVERNANCE.md)
for support-state requirements and deprecation windows. Adding another module
is not itself an improvement metric.

Reverse the comparison with `--baseline context/active-brief --candidate
context/full-record` to produce the measured cost-based rejection example.
Each comparison retains the actual candidate/baseline files, common runtime,
fixed fixtures, execution trace and decision. A backend failure produces a
`not evaluated` record with its partial trace and does not become a quality score.
