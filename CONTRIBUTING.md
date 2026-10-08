# Contributing to Allagma

Start with one module or example. Python 3.11+ on macOS or Linux is sufficient;
the default checks need no package installation, provider account or GPU.

```sh
python3 -m allagma check --module context/active-brief
python3 methods/allagma-context-active-brief/select.py \
  methods/allagma-context-active-brief/example.json /tmp/my-context-result.json
python3 -m unittest conformance.test_modules -v
```

Use a fresh result filename because evidence is immutable. The first command
checks the module's metadata, resources and contract. The second runs its
example. The third includes an actual one-module contribution fixture.
See [module authoring](docs/module-authoring.md) for a minimal change.

| Change | Minimum local checks |
| --- | --- |
| Documentation | Read the rendered Markdown; `python3 tools/check_docs.py` |
| Method | `check --module ID`, its executable example, relevant fixture |
| Context behavior | `conformance.test_modules`, `allagma compare` |
| Recipe or adapter | Relevant module check and `conformance.test_research` |
| Contracts | `conformance.test_contracts`, affected producers/consumers |
| Export, update, configuration | `conformance.test_versions` |
| Release | Full conformance and a fresh `allagma acceptance` |

The CI change selector runs these inexpensive checks by scope. A real research
campaign is not required for an ordinary contribution. Claims about a model or
host require evidence for that claim; fixture success must not be described as
real-host or scientific-quality qualification.

Use an issue or a direct pull request. Small fixes and documentation changes
need no prior proposal. A broad change to a public contract, ownership rule or
default behavior starts with a short proposal describing the problem,
alternatives, compatibility, migration and evaluation. The implementation follows
the adopted design in `docs/specification/`; current qualification is recorded
in the release notes and acceptance ledger.

Include source lineage, the intended benefit, limits and targeted evidence.
Maintain English public documentation. Never commit credentials, full private
profiles or private study data. Distinguish original design inspiration from
adapted text/code and optional dependencies; preserve applicable licenses.

External contributions receive maintainer review before merge. Merging an
experimental module does not promote it to stable or select it as a default.
Release notes record public contract changes, deprecation and migration.
Read [governance](GOVERNANCE.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## Documentation and first contributions

Choose a [small, concrete task](docs/contributing/starter-tasks.md). Improve the
canonical Markdown document, not a generated site copy. `site/content-map.json`
maps those documents into the Astro Starlight site. For a site change:

```sh
cd site
npm ci
npm run build
npm run preview
```

Use Node 22.12+ and open `http://127.0.0.1:4321/allagma/`. Inspect light and
dark themes, mobile layout and keyboard navigation. The production build
includes internal link/fragment checks and search indexing. `npm test` runs
browser checks after `npx playwright install chromium`. See [site development](site/README.md).

Documentation tooling is separate from the Python runtime. Keep the core and
default toy standard-library-only. Public pull-request checks must not need
provider credentials, scientific training or privileged secrets. Do not add
model/review-model overrides to project-level configuration.

New media should include editable sources, descriptive alternatives, provenance
for scientific results and captions for video. Label reused results and time
compression; never present a mock as a successful host qualification.
