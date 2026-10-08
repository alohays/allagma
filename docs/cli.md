# Command-line reference

Run commands from the source checkout with `python3 -m allagma`. Python 3.11+
and a POSIX system are required. JSON output is intended for inspection and
automation. Paths below are examples; existing evidence destinations must not
be reused as if they were empty.

| Command family | Purpose |
| --- | --- |
| `check` | Validate catalog metadata, files, contracts and composition |
| `init`, `entry`, `verify` | Prepare a study, resolve exact method text, check its lock |
| `toy` | Execute the full offline known-answer study |
| `campaign start/run/analyze/audit/status` | Manage frozen campaigns and analysis revisions |
| `research prepare/run/status` | Prepare a brief/material/resource workspace and explicitly invoke the native host |
| `resource init/run/status/recover` | Supervise finite local resource reservations and receipts |
| `update check/plan/reconcile/validate/adopt/rollback/recover` | Change composition at a campaign boundary |
| `migrate plan/apply/rollback/recover` | Apply or recover a scaffold migration |
| `validate-record` | Validate an evidence record against its declared contract |
| `verify-evidence` | Read a record and its declared transitive references without executing study code |
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

## Read-only evidence inspection

```sh
python3 -B -m allagma verify-evidence --study work/my-first-study \
  --record campaigns/toy-v1/analyses/a001/paper/claims.json
```

The entry is a study-relative JSON record or nonempty list of records. The
command checks the current supported record contracts and SHA-256 references,
following references declared as `application/json` transitively. Shared
references are checked once. It collects independent failures with the referring
artifact and JSON location, rejects traversal/symlinks, and reports actual
coverage counts. Default limits are 10,000 file reads and 256 MiB of evidence
bytes; `--max-files` and `--max-bytes` must be positive integers. Reaching a limit
fails the check instead of reporting partial coverage as a pass.

JSON output has `verification_version: 1`. Exit 0 means the declared graph
passed these checks; exit 1 means findings or a limit stopped verification; exit
2 means invalid invocation. The computed entry hash identifies the inspected
bytes but is not a trusted signature. Unreferenced files, undeclared hash maps,
campaign completeness and lock freshness are outside this command's coverage.

Inspect a quiescent copy: there is no atomic snapshot or mutation lock. The
command does not import study code, execute helpers, contact a service, append
reviews, recover attempts or change assurance. `-B` also disables Python's
source bytecode cache. For recomputation and a new review, use the explicitly
mutating `campaign audit` command. Neither check establishes scientific truth
or native-host qualification. Historical evidence remains usable with its
original programs; the reader does not upgrade its lock or execute its bundle.

## Exit status and costs

Nonzero exits indicate a command or validation failure. Inspect JSON receipts
as well as the exit code: process completion, scientific correctness and assurance
are distinct. Only `research run` deliberately launches an authenticated model
session. The default catalog, toy and conformance commands do not.

See [first study](guides/first-study.md), [native study](guides/native-study.md),
[resource supervision](resource-supervision.md) and [versioning](versioning.md)
for complete workflows rather than isolated flags.
