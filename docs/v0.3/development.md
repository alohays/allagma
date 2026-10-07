# Development evidence and decisions

The acceptance ledger is [requirements.md](requirements.md). Nothing in this
development log counts as a final comparison run.

## Reusable resource supervision

The completed EMA study's `compute.py` demonstrated serial timeout reservations,
conservative crash accounting and separate model-deliberation cost. Its budget,
attempt count, working directory and initial charge are hard-coded. Its native
reporting repair also exposed the need to run dependency-using verification in
the study environment. These observed needs motivate a study-independent local
resource supervisor; scientific hypotheses and evaluators remain study-owned.

The new `allagma resource` helper freezes a supplied finite profile, retains
immutable reservations and separate outcomes, charges uncertain work fully,
refuses automatic restart of unresolved work, and distinguishes compute from
environment setup. It adds process-tree RSS and study-storage watchdogs plus a
per-file kernel limit. RSS is not exact MPS allocation accounting. Polling may
overshoot a threshold; this is operational resource control, not adversarial
containment. Evaluation isolation is a separate requirement.

Actual conformance probes initially exposed a macOS host restriction on process
group signaling. Direct signaling of observed, identity-checked child processes
works on this host. The supervisor now uses that path as well; it does not leave
a timed-out child running after declaring termination. Launch uncertainty keeps
the reservation charged until explicit recovery.

## Initial development ceiling

The [development profile](../../evals/research-v0.3/development/resource-profile.json)
allows 1,800 seconds of scientific computation and 900 seconds of environment
setup, at most 24 computational attempts, 180 seconds per computational command,
8 GiB observed process RSS, 6 GiB workspace storage and 512 MiB per file. The
polling interval is 0.25 seconds with a 0.5-second termination grace. This is a
development envelope, not an inherited final-evaluation budget. Final task
ceilings will be chosen from observed pilots and frozen before evaluation.

## External task preflight

The public CORE-Bench training metadata and four capsule HTTP manifests were
inspected. Two CPU candidates were downloaded for source/environment preflight:
BorderT-GRAANK (`capsule-2011424`, 246,776 compressed bytes) and CULP
(`capsule-6460826`, 13,752 compressed bytes). Archives were checked for unsafe
paths, special files, links and an expanded-size ceiling before extraction.
No original scientific run has yet been declared compatible. Original results
are excluded from candidate input packages. Legacy container dependency pins
need local compatibility checks; changing an API import or data path must be
disclosed and must not change scientific parameters or scoring.

Sources: [CORE-Bench](https://github.com/siegelz/core-bench),
[native Codex execution](https://learn.chatgpt.com/docs/non-interactive-mode),
[skill evaluation guidance](https://developers.openai.com/blog/eval-skills).
