# PR #14 review repairs - 10 October 2026

The owner requested that [PR #14](https://github.com/alohays/allagma/pull/14)
be made ready for merge. The review of `72e88c3` reported four reproduced
findings. Each is fixed in a separate commit with a regression that fails on
the affected behavior. The PR remains unmerged.

| Finding | Repair | Evidence |
| --- | --- | --- |
| [P1: ancillary-file replacement](https://github.com/alohays/allagma/pull/14#discussion_r4232801295) | `004d2cb`: reading notes occupy a dedicated per-reference namespace; map/index links are remapped; copies reject existing targets; evidence IDs cannot address generated paths. The verification build invokes the unpacked archive's own builder. | Six colliding note names, overwrite refusal, and a real TeX build with a note named `build.py`. `tools/test_paper_archive.py` runs this regression in Paper output CI. |
| [P2: preparation storage](https://github.com/alohays/allagma/pull/14#discussion_r4232801582) | `288e3b9`: admission measures the protected dossier, snapshot receipt and working copy before workspace creation. Copies stream only planned bytes and verify their hashes. | A 3 MB note under a 2 MB ceiling is refused before creating either output. Separate cases check single versus double copies, a fitting dossier, source growth and equal-size content changes. |
| [P2: policy metadata](https://github.com/alohays/allagma/pull/14#discussion_r4232801846) | `b16b063`: admit history plus atomic replacement bytes together under the proposed policy while holding the cache lock. | Repeated unchanged adoptions stop within capacity. Cache-limit, atomic-overhead and free-space refusals leave policy and history unchanged. |
| [P2: review identity](https://github.com/alohays/allagma/pull/14#discussion_r4232802062) | `db1f367`: bind each section role to its path and content hash. | Swapping abstract and limitations invalidates both reviews; reordering JSON keys alone does not. |

The [regression manifest](evidence/pr14-revisions/regressions.json) links
before/after logs, their hashes and the actual collision-build receipt. Fixtures
use temporary data and local I/O; they are not scientific qualification evidence.

## Combined validation

The [full acceptance receipt](evidence/pr14-revisions/acceptance.json) passes
**184 conformance tests and I1-I5** against runtime source
`sha256:bd4aae1be759b3802d7aa075a38839004fd6f8f4bc24c158890da38bc5fbbcd1`.
The toy workflow retains 24 confirmation replicates, 26 successful attempts,
one deliberate failure and one interruption. Its 521-reference audit passes
without findings. Native host checks retain their stated fixture/routing scope.

The completed EMA paper recomputes all 114 retained summaries. New
[scientific](../../studies/ema-schedule/publications/reference-r2/reviews/pr14-scientific.json)
and [prose](../../studies/ema-schedule/publications/reference-r2/reviews/pr14-humanizer.json)
reviews bind its unchanged text to the corrected section mapping. Original
reviews and delivery artifacts remain intact. The new
[source archive](../../studies/ema-schedule/publications/reference-r2/artifacts/review-r1/paper-source.tar.gz)
contains the repaired namespace and renewed review records. Its SHA-256 is
`d1d63141f243632fca1656b7d2a88e72aa53f81fa2ef60a10c64784e5e0c2559`.

The [delivery receipt](../../studies/ema-schedule/publications/reference-r2/artifacts/review-r1/delivery.json)
records two clean TeX Live 2024 builds, including execution of the archive's
own entrypoint. The PDF SHA-256 remains
`7aea0bb5cac8bd0a108a977aaf48c70cdd23cbbde5a08b97b4eed9c34d0c98ce`.
All eight pages were freshly rendered and inspected. Their image hashes also
match the earlier visual review. The optional CI job repeats the collision
regression and demo build on TeX Live 2023.

[Combined validation](evidence/pr14-revisions/validation.json) also records
380 canonical documentation links, a 43-page production build with 2,828 local
links/assets, all 18 desktop/mobile browser tests and seven compact-source
boundary tests. No frozen science, evaluation, contract, media or project model
configuration changed.

The PR checks are authoritative for the latest pushed commit. This repair work
does not merge, deploy, submit to arXiv, acquire new reference assets, start a
native model session or change adopted resource limits. Review judgments remain
agent-assisted maintainer checks, not independent scientific peer review.
