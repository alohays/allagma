# Working on Allagma

Keep public code and technical documentation in English. The implementation
specification is in `docs/specification/`; `docs/implementation-status.md` tracks
the I1–I5 acceptance evidence. Use Python 3.11+ and the standard library for the
default conformance kit and toy study. Run `python3 -m allagma check` for the
catalog and `python3 -m unittest discover -s conformance -v` for behavior checks.

Methods are canonical, portable Agent Skills. Put provider integration in
adapters, study science in the study, and generated copies in bundles. Do not
edit a locked bundle, erase an attempt, or report a mocked host as qualified.
Keep phase, execution status, and assurance distinct. A deterministic check
only establishes the coverage it actually tests.

Preserve the user's GUI model selection. Do not add `model` or `review_model`
overrides to project-level `.codex/config.toml`, including project profiles,
unless the user explicitly requests a fixed model for that project. Model
upgrades, harness setup, and recommendations do not authorize pinning a project
model. Keep personal defaults in user-level configuration.
