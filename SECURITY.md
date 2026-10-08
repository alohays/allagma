# Security reporting and boundaries

Do not put credentials, private data, exploit details affecting other users, or
unredacted runtime logs in a public issue. Use GitHub's private **Report a
vulnerability** channel when it is enabled on the public repository:
[private security report](https://github.com/alohays/allagma/security/advisories/new).
If that channel is unavailable during launch preparation, open an issue that
only asks for a private reporting channel; include no vulnerability details.
The maintainer will establish a private contact before receiving sensitive data.

Reports should identify the affected release, component, prerequisites, impact
and a minimal reproduction using synthetic data. Coordinate disclosure with
the maintainer. There is no bug bounty or guaranteed response time.

The latest release candidate, **0.3.0rc2**, is the maintained source line.
Historical bundles remain available for reproduction; they retain historical
behavior and do not automatically receive fixes. Prepare a new study or adopt
an update at a campaign boundary when applying a fix.

## Trust boundaries

Study programs and supplied materials are code/data the researcher chooses to
trust. A content digest detects change; it does not make malicious code safe.
Do not run untrusted research packages on a machine with sensitive material.
The local resource supervisor uses operational process, RSS and storage checks;
it is not an adversarial sandbox or an instantaneous GPU-memory quota.

The optional macOS native broker applies filesystem/network restrictions within
its documented scope. The [host matrix](docs/host-support.md) and
[resource guide](docs/resource-supervision.md) state what was actually tested.
Never infer isolation or scientific validity from a fixture-only pass.

Keep authentication in the host's user-level store. Allagma's default methods
install no hooks, subagents or project model overrides. Fork pull-request checks
run without privileged secrets; native account sessions are not part of public
contribution CI.
