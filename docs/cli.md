# Command-line reference

Run commands from the source checkout with `python3 -m allagma`. Python 3.11+
and a POSIX system are required. JSON output is intended for inspection and
automation. Paths below are examples; existing evidence destinations must not
be reused as if they were empty.

| Command family | Purpose |
| --- | --- |
| `check` | Validate catalog metadata, files, contracts and composition |
| `doctor` | Inspect offline or native prerequisites and optionally the current study lock; no execution |
| `init`, `entry`, `verify` | Prepare a study, resolve exact method text, check its lock |
| `toy` | Execute the full offline known-answer study |
| `campaign start/run/analyze/audit/status` | Manage frozen campaigns and analysis revisions |
| `research prepare/run/status` | Prepare a brief/material/resource workspace and explicitly invoke the native host |
| `resource init/run/status/recover` | Supervise finite local resource reservations and receipts |
| `update check/plan/reconcile/validate/adopt/rollback/recover` | Change composition at a campaign boundary |
| `migrate plan/apply/rollback/recover` | Apply or recover a scaffold migration |
| `validate-record` | Validate an evidence record against its declared contract |
| `compare` | Run the bounded context-method fixture comparison |
| `acceptance` | Generate complete I1–I5 evidence and offline conformance results |

## Discover exact flags

```sh
python3 -m allagma --help
python3 -m allagma campaign --help
python3 -m allagma research --help
python3 -m allagma resource --help
```

The site also generates a complete command help page from the actual parser on
every build. The executable's `--help` is authoritative for flag syntax.

## Small useful commands

```sh
python3 -m allagma check --module context/active-brief
python3 -m allagma entry --study work/my-first-study --campaign toy-v1 --module research/audit
python3 -m allagma campaign status --study work/my-first-study --campaign toy-v1
python3 -m allagma validate-record work/my-first-study/campaigns/toy-v1/analyses/a001/record.json
```

`entry` identifies the exact method, bundle and digest. `campaign audit` dispatches
through that campaign's helper, even when the central checkout has changed.
`validate-record` checks a record's shape; it does not independently verify
every scientific claim referenced by that record.

## Exit status and costs

`python3 -m allagma doctor` checks Python/POSIX support, the source catalog and
toy resources. Add `--study PATH` to inspect the current lock, intent freshness
and generated-file ownership. Each failed check includes a remedy; independent
checks still run. JSON has `diagnostic_version: 1`; exit 0 means all selected
checks passed, 1 means a prerequisite failed, and 2 means invalid invocation.
Malformed prerequisite documents, including wrong JSON shapes or excessive
nesting, appear as failed checks with remedies; other checks still run.

`doctor --scope native --codex /path/to/codex` additionally checks macOS,
`sandbox-exec` presence and executable availability. It never invokes Codex,
reads authentication or model configuration, contacts a service, installs
software, acquires a study mutation lock or repairs files. It does not test
account access, model support, scientific dependencies, resource capacity or
native activation. A pass is a prerequisite report, not qualification. Use
`python3 -B` if interpreter bytecode caches in the source checkout are unwanted.

Nonzero exits indicate a command or validation failure. Inspect JSON receipts
as well as the exit code: process completion, scientific correctness and assurance
are distinct. Only `research run` deliberately launches an authenticated model
session. The default catalog, toy and conformance commands do not.

See [first study](guides/first-study.md), [native study](guides/native-study.md),
[resource supervision](resource-supervision.md) and [versioning](versioning.md)
for complete workflows rather than isolated flags.
