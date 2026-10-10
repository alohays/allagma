# Governance and review ownership

Yunsung Lee (GitHub `@alohays`) is the initial maintainer and final decision
maker. `.github/CODEOWNERS` assigns review ownership; module manifests identify
the owner of each supported responsibility. Delegation can be recorded as the
contributor base grows. No review response time is promised.

[Repository rules](.github/rulesets/README.md) require PRs and passing CI on the
default branch, prevent force pushes and deletion, and prevent updates or
deletion of release tags. They have no standing administrator or bot bypass.
The single-maintainer configuration does not require approval votes on the
maintainer's own PRs. Maintainer review and merge decisions remain required;
consider one required approval when a second active maintainer can provide it.

Discuss disagreements with concrete examples, compatibility effects and
evaluation scope. The maintainer records the decision and rationale in the
issue, proposal or ImprovementRecord. Rejected proposals remain available as
history; new evidence can justify reconsideration. Report conduct concerns
privately using the maintainer's published contact options rather than posting
personal details in an issue.

Module states are proposed, experimental, stable, deprecated and retired.
Proposed modules need a responsibility, difference, owner and example.
Experimental modules pass contracts and an example and state their limits.
Stable modules complete relevant evaluation and qualification within their
declared scope. Public defaults select stable modules; private compositions
may explicitly opt into experiments. Default selection is not a lifecycle state.

Deprecation names a replacement or alternative, migration and earliest
retirement release. Stable options coexist with their replacement in at least
one subsequent compatible release. Breaking retirement uses a breaking release
(a minor boundary during 0.x), with explicit release notes. An unsuccessful
experimental module may retire directly. Historical releases and bundles remain
available regardless of current support.

Only the maintainer publishes releases initially. Before publication, verify
the MIT license and notices, run the release acceptance command, review the
support matrix, settle migrations and preserve exact release assets. Local
development snapshots are marked unpublished. Tags and published contents are
never repurposed. A contributor approval is separate from scientific review
and from authorization to execute a user's study.
