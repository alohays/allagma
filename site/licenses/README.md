# Notices missing from the installed package roots

Pagefind and its default UI 1.5.2 declare MIT but omit a standalone license file
from their npm package roots. The build includes the complete upstream notice
from [Pagefind v1.5.2](https://github.com/Pagefind/pagefind/blob/v1.5.2/LICENSE).
The default UI bundles Svelte and declares its build dependency as `^4.2.1`;
the [Svelte 4.2.1 MIT notice](https://github.com/sveltejs/svelte/blob/svelte%404.2.1/LICENSE.md)
is included as well. This does not assert which patch version the upstream UI
build used.

The build checks the Pagefind package versions before applying these pinned
notices. When updating Pagefind, inspect the new upstream license/package
contents and update this fallback. Other installed dependency notices are
collected directly from their package roots. The generated appendix identifies
build-time dependencies as well as browser assets and makes no claim that every
listed component is shipped to the browser.
