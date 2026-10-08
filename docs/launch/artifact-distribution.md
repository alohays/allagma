# Source and research artifact distribution

The default first-use path is a small sparse source checkout. It runs the Python
core, all catalog modules and offline toy without historical model weights,
native traces, study dependencies or the Node documentation toolchain.
Full research evidence is optional and remains immutable in Git for this release.

## Prepared release assets

Run `python3 tools/package_source.py --output build/source-release` to create a
deterministic source TAR.GZ, a file-by-file digest manifest and `SHA256SUMS`.
The generator refuses to replace an existing asset. The archive includes core,
methods/adapters, the offline example, small native-study inputs and conformance.
It is a source distribution, not a wheel. The release workflow prepares this
asset for inspection; it does not publish a GitHub release or package.

The owner can later attach these exact validated assets to an immutable release
tag. Do not use a GitHub-generated whole-repository ZIP as the advertised small
download: that includes retained research evidence. A future artifact service
may hold hash-addressed copies, but no external hosting account or storage bill
is required by this launch package.

## Optional study archives

| Illustrative package | Compressed archive bytes | Pinned wheel bytes | Scope |
| --- | ---: | ---: | --- |
| CORE CULP r01 | 1,079,830 | 63,793,956 | Original capsule reproduction and full independent replay |
| Modular addition r04 | 69,799,505 | 181,338,022 | Eight 100k-update trajectories, curves and checkpoints |
| EMA r07 | 829,100,336 | 181,338,022 | 24 training trajectories, 96 states and paired analyses |

Sizes come from the committed package parts and `external_wheels` indexes.
Expanded workspaces and temporary environments require additional space.
Wheel pins describe the actual macOS/arm64 environments; other platforms need
their own qualification. Cached exact wheels can replace downloads.

Archives are divided into parts of at most 32 MiB, restored as a stream, and
verified against the package index. Never rename a changed archive to an old
digest. Missing or damaged parts should fail verification, not silently reduce
the study. Terminal-queue supplements are distinct from the original archive.

## What goes on the documentation site

The site includes selected figures, numerical summaries and source-linked
artifact previews. It does not duplicate complete scientific packages, hosted
model transcripts, account receipts or dependency wheels. Preview transformations
must name their source and preserve exact values; label abridged or reused
material. Videos are local assets with captions and lazy loading, without a
third-party video embed or tracking script.

## Retention and future changes

Keep frozen bundles, attempts, original scoring failures and later corrections.
If a privacy review requires removal from a public distribution, preserve the
original privately and record the redaction separately. A public history rewrite
requires an explicit owner decision; a normal documentation change must not
destroy evidence. See the [publication review](publication-review.md) before
changing repository visibility.

Review media sizes, archive indexes, licenses and public-data exposure for every
release. Keep the lightweight source asset independent of optional studies and
documentation dependencies.
