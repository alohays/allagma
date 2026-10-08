# Candidate package retention

`retention.py` is a transport utility outside the frozen scientific scorer. Run
collection only after the native session and all its computation have stopped.
It reads the candidate workspace without editing any artifact, archives regular
source/evidence files, and verifies they did not change during collection.

Archives are divided into 32 MiB parts so individual files fit ordinary Git
transport. The index records each part and the complete archive SHA-256, plus
every retained file's hash and size. Virtual environments, caches and mutation
locks are excluded. Terminal computation requests, responses and logs are
retained because candidate manifests and reviews can link to these files.
Authoritative computation history is also retained separately by the controller.
A missing or inconsistent candidate manifest is
reported as an error, not converted into evidence of completion.

Supplied wheelhouse files are retained as exact filename/size/hash references.
This avoids placing a >100 MB PyTorch wheel in Git or duplicating installed
environments. Restore them from an exact local cache or explicitly download
the pinned distribution, then check the hash before use. A matching dependency
version string alone is insufficient.

```sh
python3 evals/research-v0.3/retention.py collect \
  --source /path/to/finished-candidate --destination /path/to/new-package
python3 evals/research-v0.3/retention.py restore \
  --source /path/to/new-package --destination /path/to/new-workspace \
  --wheel-cache /path/to/verified-wheel-cache
```

Use `--download-wheels` instead of a cache when explicitly preparing a fresh
environment from the package index. Dependency acquisition is setup work; all
scientific execution remains local. Restoration verifies exact file bytes but
does not establish scientific reproducibility. Execute the delivered full-study
and raw-data recomputation commands separately and retain their actual outcomes.

## Historical terminal-queue omission

The first transport version excluded `.compute/`. Inspection of r04 showed that
its manifest and review directly reference terminal receipts there. This was a
controller transport omission, not a missing candidate artifact. The candidate
bytes were still present and their authoritative counterparts were retained.

For the already collected r01–r04 archives, retain the omitted bytes without
replacing any original index or archive part:

```sh
python3 evals/research-v0.3/retention.py supplement \
  --source /path/to/finished-candidate --destination /path/to/existing-package
```

The supplement verifies all originally indexed candidate files before copying,
binds itself to the original package index, and records each added file's hash.
`restore` automatically hydrates and checks this supplement. New collections
include the terminal queue directly. Start a new broker for any reproduction;
it ignores requests already present when it starts, so retained historical
requests are evidence, not requests to execute again.

The regression check `python3 evals/research-v0.3/test_retention.py -v` covers
new collection, restoration of historical supplements and altered-byte rejection.

## Internal dependency aliases

Run r05's fresh-environment smoke test used an absolute symlink to its supplied
wheel directory. The initial transport rejected that link; its failed collection
receipt is retained. Collection now records internal links explicitly rather
than traversing, discarding or silently dereferencing them. External, missing
and excluded targets are rejected.

The index preserves the original literal link target, the resolved target within
the candidate, and the relative target used on restoration. Restore hydrates the
regular files and exact dependency wheels first, then recreates each alias to
the same retained content at its new location. Regular file bytes and the
candidate workspace are unchanged. The original absolute link string remains
in metadata; relocation of that string is an explicit transport operation, not
a claim of byte-identical symlink text. Tests cover internal alias relocation
and rejection of external targets. Existing archives remain readable.

## Artifact-manifest containers

The common task brief does not prescribe the name of the manifest's entry list.
Collection recognizes a `files` list, an `artifacts` list, a direct list, or a
direct path-to-digest mapping, with the same path and SHA-256 checks. The first
r06 collection reported an unsupported format because its list was named
`artifacts`. That original index remains unchanged; the separate
`runs/r06/manifest-verification.json` verifies all 456 entries. This is a
controller-parser correction, not a missing candidate artifact or a scientific
scoring change.

```sh
python3 evals/research-v0.3/retention.py verify-manifest \
  --source /path/to/candidate-or-restored-package \
  --destination /path/to/new-verification-receipt.json
```

The receipt reports only the declared paths/hashes and count actually checked.
Scientific correctness, manifest coverage and package completion need their
separate substantive review.

## Stream large archives during restoration

The 829,100,336-byte r07 archive exposed a transport error: the original restorer
combined its parts into a temporary file, exceeding the validation profile's
536,870,912-byte per-file ceiling. The failed request and original source revision
remain in r07's restoration evidence. The archive and candidate are unchanged.

Restoration now checks each part, streams gzip/tar extraction with a 1 MiB
buffer, verifies the combined archive digest, and checks every extracted file.
It creates no combined archive file. The actual r07 restoration passed under
the unchanged profile. A POSIX regression also restores an archive larger than
an enforced file limit while each individual output remains below that limit;
altered-part rejection is tested separately. This change does not raise any
resource ceiling or alter scientific evidence.
