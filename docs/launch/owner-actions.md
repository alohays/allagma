# Owner actions for the later public launch

Preparation does not authorize activation. Keep the repository private until
the owner chooses to launch. Source commits, preview artifacts and local release
assets do not change visibility or create a public release.

## Review the prepared package

Read the [launch evidence ledger](requirements.md),
[publication review](publication-review.md), [third-party notices](../../THIRD_PARTY_NOTICES.md)
and [release notes](../releases/0.3.0rc2.md). The owner has already chosen to retain
the full history with author email, local paths and native session IDs disclosed.
Do not repeat that decision or rewrite frozen records as part of launch.

Preview locally from `site/` with `npm ci`, `npm run build`, then `npm run preview`.
Open `http://127.0.0.1:4321/allagma/`. The Python core does not need Node. Read
[capture instructions](../../media/CAPTURE.md) to inspect or regenerate the film.

## Activate the public surfaces

1. **Change repository visibility** to public only when the owner is ready.
   The working repository is `alohays/allagma`; no mirror or history replacement
   is required by the selected metadata policy.
2. **Enable GitHub Pages with GitHub Actions as its source.** The configuration
   uses `https://alohays.github.io/allagma/`. Set the repository Actions variable
   `ALLAGMA_PUBLIC_LAUNCH` to the exact string `true`. In the `github-pages`
   environment, require owner review if desired. Dispatch “Public documentation
   deployment” with `deploy: true`. Both public visibility and the variable are
   required; ordinary private pushes cannot deploy. Later relevant main-branch
   pushes can update the site automatically.
3. **Upload the social preview** from `media/social-preview.png` in repository
   Settings → Social preview. It is 1280×640 and under 1 MB. GitHub documents
   that an initial social-preview upload requires a public repository; an
   existing private preview can be changed. No initial preview was present here.
   See [GitHub's instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).
4. **Enable private vulnerability reporting** under Settings → Advanced Security.
   Test the “Report a vulnerability” link in `SECURITY.md` before announcing.
   Keep security details out of public issues. See
   [GitHub's private reporting instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
5. **Enable Discussions** with the prepared Q&A, Show and tell, and Ideas
   categories. Follow the [community plan](community-plan.md). Post the welcome
   only at launch; create the small number of starter tasks the maintainer is
   ready to review.

After Pages deploys, verify its production URL, search and movie playback, then
set the repository website field to that working URL. The description and
topics are already configured. A local preview cannot prove that the later
public deployment's DNS/permissions/cache are correct.

## Publish a release and announcements deliberately

The current software is **0.3.0rc2**, not an asserted stable 0.3.0 release.
The “Prepare release assets” workflow runs full acceptance and uploads reviewable
source assets without creating a tag or release. Inspect the resulting manifests
and exact source commit. Create an immutable release tag only after deciding its
version; do not repurpose an existing tag or label a candidate stable by editing
marketing copy. A version/publication-manifest change requires renewed acceptance
and regeneration of matching assets before publication.

Attach the compact source archive, manifest/checksum, release notes, and any
selected media package. Keep large study evidence opt-in with its existing
hashes and licenses; do not imply all archived scientific code is MIT.

Finally, adapt and post the [prepared launch copy](announcement.md), linking
only to now-working public endpoints. No announcement, release, Discussion,
issue on behalf of a hypothetical user, or public Pages deployment has been
posted by this preparation task.
