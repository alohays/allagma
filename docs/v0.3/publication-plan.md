# Publication of the completed v0.3 work

The owner's instruction in [GOAL.md](../../GOAL.md) is authoritative: commit
coherent progress and push to `origin` after all required work and checks pass.
That instruction is also retained in the goal document. The qualified release
commit `46fd7855796a3c0885c6730ce8622350c7877a8a` has now been pushed to
`origin/main`, with exact local/remote equality verified in the
[publication receipt](evidence/publication/push.json).

Origin is hosted on GitHub. The retained source, scientific arrays and archives
required approximately 3.4 GiB of new uncompressed Git objects for this work.
Final scientific archive parts are at most 32 MiB. GitHub enforces a
[2 GiB limit per push](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit),
so publication used three transfers.

After cohort completion, release repairs and acceptance, the original remote
head was verified as `6d2daf0`. Ordinary fast-forward batches published
`c937e43`, then `82d2cb9`, then the qualified release head `46fd785`. The batches
contained approximately 1.16, 1.33 and 0.91 GiB of new uncompressed objects,
respectively; these are object-size sums, not measured network payloads. Each
push succeeded. No force push, history rewrite, model configuration change or
paid storage service was used. GitHub accepted a preserved 60.25 MB development
archive with a recommendation warning; no artifact exceeded its 100 MB limit.

The first two CI workflows completed successfully for both targeted conformance
and acceptance. The receipt records those observations; later CI results remain
available in the repository's Actions history. The final publication bookkeeping
is a separate commit, followed by another ordinary push and remote-head check.

Full scientific artifacts remain retained. Archive transport and dependency
hydration are described in [RETENTION.md](../../evals/research-v0.3/RETENTION.md).
