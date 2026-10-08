# Publication review

The repository remains private while the public-launch package is prepared.
This review covers the tracked tree, reachable Git history and retained archives;
it must be completed before the later visibility change. The scan is not a
guarantee that no secret or redistribution issue exists.

`tools/audit_publication.py` scans reachable historical blob and commit versions,
opens ZIP/TAR members, and reassembles distinct multipart archives from historical
trees. It records match categories, object identities and line numbers without
copying potentially sensitive values into its report. Binary contents receive
pattern scanning; they are not executed. A final receipt and manual disposition
will be recorded in the launch evidence directory.

## Redistribution boundaries already identified

Allagma's core is MIT. CORE capsule code is MIT and its data retain CC0.
EMA scientific code adapted from SakanaAI is under the **AI Scientist Source
Code License**, with usage restrictions and prominent machine-generation
disclosure requirements. Do not describe the entire evidence repository as
uniformly MIT or the adapted study code as unrestricted open source.
The complete license remains beside original and frozen adapted materials.
See [third-party notices](../../THIRD_PARTY_NOTICES.md).

No vendor credentials, private runtime homes or authentication stores belong
in public assets. Historical source paths, author email, native thread IDs and
machine metadata are privacy-relevant even when they are not authentication
secrets. Their disposition must be explicit before public visibility; the site
should not expose them just because an underlying receipt contains them.

## Current review status

The owner explicitly chose on 8 October 2026 to **keep the full history, with
author email, local home-directory paths and native session IDs documented for
launch review**. Preserve the original evidence; do not rewrite it to remove
these accepted metadata exposures. Selected website previews omit operational
details and provide source/digest links.

The [corrected initial scan](evidence/history-review-initial.json) covered 62
reachable commits, 7,560 blob versions, 12 multipart archives and 48,945 archive
members. It also opened 934 ZIP archives and 91 gzip-compressed data files.
It found email and local-path patterns, with **no matches for the credential/key
patterns used and no unhandled archive errors**. The earlier pass's gzip coverage
gap was corrected, with its original log retained locally.

The matched categories cover accepted owner metadata and upstream dependency
author/test-fixture metadata. Binary content was pattern-scanned; scientific
arrays were not executed as code. A final scan after the launch commits and
manual redistribution inventory remain required. No scan alone certifies
publication safety.

## Manual redistribution inventory

The selected package indexes retain nine license copies for CULP r01 (MIT code
and CC0 data across original/adapted/frozen copies), two for modular r04
(Allagma core and OpenAI's MIT reference), and four license/notice entries for
EMA r07, including its frozen scientific license. The [inventory](evidence/license-inventory.json)
records exact paths and digests. The complete applicable license text was
inspected in the retained source materials; its presence alone does not imply
unrestricted use of the AI Scientist adaptation.

Archived development packages may contain dependency wheels with their own
licenses and test fixtures. The recursive historical scan opens those wheel
archives; the compact default source distribution excludes all wheels and
third-party scientific adaptations. Final evaluation packages hydrate their
declared software wheels by exact hash instead of silently choosing new versions.

The launch notices now explicitly identify the OpenAI grok reference materials
inside frozen evaluation packages and the separately licensed EMA figure in
the film. Editable identity graphics are original. The documentation build
toolchain is isolated from the Python core. No account authentication files,
private runtime homes or credentials are selected for the site or release assets.

## Final implementation review

The [complete historical scan](evidence/history-review-final-source.json)
through `2a7b488` covers 66 commits, 7,668 blob versions and 54,889 archive
members, with no credential-pattern matches or unhandled archive errors.
The [subsequent delta review](evidence/history-review-delta.json) covers the
later narration correction and sparse-checkout guidance. Its two email-pattern
matches are a Playwright filename and accidental compressed-video bytes, not
contact information. Original source/evaluation/study trees remain byte-identical
to the qualified implementation baseline.

The built site was separately checked for the owner's absolute home-directory
prefix, with no matches. Curated capture-state previews omit that operational
field and record the transformation; raw capture evidence and the full Git
history remain retained. The authoritative limitations of pattern scanning and
the accepted historical metadata exposures still apply.
