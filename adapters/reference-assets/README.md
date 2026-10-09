# Bounded reference acquisition

This optional adapter retrieves selected papers, source archives, code, model
weights and dataset files. It runs during preparation, outside scientific
workers. All HTTP requests require `--online`; provided files and intact cached
objects work offline. The adapter never accepts terms automatically, executes
downloaded code or loads model weights.

Use `reference cache-init`, then `reference acquire --directory REFERENCES` with
an `assets.json` manifest. `--provided` names a local-only JSON map from asset IDs
to supplied file paths. Keep that binding file outside versioned notes. The
public `retrieval.json` uses paths relative to the cache, public source URLs,
revisions, licenses, hashes, sizes and explicit acquisition states.

The default cache is `.allagma-reference-cache` in the current directory. Choose
another path within a Git working tree with `--cache`. Initialization resolves
`git rev-parse --path-format=absolute --git-path info/exclude`, preserves existing
entries and appends the cache exclusion. It works when `.git` is a linked-worktree
file. A cache containing tracked files is rejected. Each selected cache has one
total ceiling; use the same explicit cache path to share it between worktrees.

Defaults are 256 MiB downloaded per asset, 512 MiB expanded per asset, 1 GiB
retained per study, 4 GiB per cache, 20 GiB minimum free disk, 2 GiB cumulative
transfers per study and two acquisition attempts per asset. Timeouts and archive
file-count limits are also configurable. Storage accounting includes partials,
failed extraction and quarantine. Reuse checks hashes before returning a path.
Transfer reservations are persisted before reading; a killed process retains
that reservation. Resumption uses HTTP ranges with a strong ETag or an expected
digest, validates Content-Range, and charges repeated bytes. A server that ignores
Range causes a fully charged restart. A new invocation never resets the ledger.

`reference policy --policy POLICY.json` can lower limits. Raising adopted limits
or lowering the free-space reserve requires a researcher decision with
`decision: expand-acquisition-limits`, `approved_by`, `approved_at`, `reason`,
`previous_policy_sha256` and `policy_sha256`, passed via `--approval`. Ask the
researcher before writing this decision. Gated assets similarly require a
decision bound to their asset identity and license URL. Authentication and
interactive license acceptance remain with the researcher; supplied local files
can be imported after the decision. Tokens are never recorded in public URLs.

`reference verify-cache` checks all available objects and extracted files.
Corruption is explicit. `reference quarantine --asset-id ID` preserves damaged
bytes and removes their reusable identity; a later acquire is a new charged
attempt. Historical retrieval manifests and attempts remain evidence. Interrupted
extraction is retained in quarantine before restarting. Archive traversal,
symlinks, hardlinks, devices, encrypted ZIPs and duplicate members are rejected.

Failed protected-input materializations retain partial files and their reserved
bytes with a terminal failure record. A new lock owner records an abandoned
preparation as interrupted; the existence of a ledger entry alone is not treated
as proof that a copying process is still active.

For initial downloads without a supplied expected hash, the first observed
digest is trust on first acquisition. Code/model/data revisions must appear in
the retrieval URL or be bound to an expected digest. A commit string alone does
not authenticate arbitrary bytes. Paper PDFs and sources retain their explicit
version. A successful transfer is not a license clearance or scientific review.

After inspecting an initial acquisition, copy its observed hash and size into
the public asset request to pin future retrievals. Already verified objects are
reused without another transfer, including when extraction must resume. For an
asset restored from a larger package, `acquisition: provided` makes its public
URL provenance-only and requires the exact local file on first import.

TLS certificate and hostname verification remain enabled. On a python.org macOS
installation without its optional CA link, the adapter uses the existing system
CA bundle. An explicit trusted `SSL_CERT_FILE` works through Python's normal TLS
configuration. Acquisition runs in a main process so an elapsed-time deadline
can interrupt stalled or slowly delivered transfers as well as extraction.
