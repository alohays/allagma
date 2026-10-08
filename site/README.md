# Allagma documentation site

This separate Astro Starlight project needs Node 22.12+ and Python 3.11+.
It is not a dependency of Allagma's Python runtime.

```sh
cd site
npm ci
npm run build
npm run preview
```

Open `http://127.0.0.1:4321/allagma/`. The production base is `/allagma/` on
`https://alohays.github.io`; there is no custom domain. `npm run dev` provides
live editing, but production search requires a build.

Canonical prose lives in the root repository documents named by
`content-map.json`. `sync-content.mjs` copies them during every build, rewrites
known document links to site routes, preserves other evidence links back to
GitHub, and adds source/edit links. Never edit ignored generated pages. The
homepage and components are site-owned; numerical previews cite retained inputs.

Run `npx playwright install chromium` once, then `npm test` after building.
Tests cover production routes, search, keyboard access, mobile layouts and media.
The static link check is included in `npm run build`; external link checks are
separate to avoid making ordinary pull requests depend on every upstream site.

`postcss-selector-parser` is narrowly overridden to 7.1.6 under `postcss-nested`
to resolve the inherited selector-complexity advisory. Remove the override when
the upstream dependency updates, after a production build and browser checks.
The lockfile and monthly dependency PRs keep updates explicit.

The build also assembles shipped dependency notices at
`generated/third-party-licenses.txt`. Pagefind's npm packages omit the root
license, so their pinned upstream notices are retained in `licenses/` and checked
against installed versions. Review that fallback when updating Pagefind.

Public Pages deployment is gated and manually activated later by the owner.
Building this project or pushing source does not change repository visibility,
publish a release, or enable Pages. See the launch owner checklist when complete.
