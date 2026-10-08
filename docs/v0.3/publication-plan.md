# Publish the completed v0.3 work

The owner's instruction in [GOAL.md](../../GOAL.md) is authoritative: commit
coherent progress and push to `origin` after all required work and checks pass.
No v0.3 push has been made at this planning checkpoint.

Origin is hosted on GitHub. The retained source, scientific arrays and archives
already occupy approximately 1.7 GiB of local Git objects, before the final EMA
packages. Each archive part is at most 32 MiB. GitHub enforces a
[2 GiB limit per push](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit),
so the final publication may need multiple transfers.

After completing the cohort, release repair and acceptance audit, inspect the
actual remote branch and choose ascending milestone commits whose incremental
objects fit comfortably below that limit. Push them as ordinary fast-forward
updates to the existing branch, ending at the verified release head. Do not
force-push, rewrite historical evidence, or change model configuration. All such
transfers occur during the authorized final publication step, not during active
evaluation. Record the final remote/local commit equality and push outcomes.

Full scientific artifacts remain retained. Archive transport and dependency
hydration are described in [RETENTION.md](../../evals/research-v0.3/RETENTION.md).
