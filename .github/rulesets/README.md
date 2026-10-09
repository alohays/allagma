# Repository rules

These JSON files are the reviewed GitHub REST API payloads for
`alohays/allagma`. GitHub does not automatically apply files in this directory:
an authorized repository administrator applies them separately and verifies the
live settings. No CI workflow receives an administration token.

## Default branch

[`main.json`](main.json) protects the default branch, currently `main`:

- Changes go through a pull request, with all review conversations resolved.
- The branch must be current with the base branch and pass `targeted`
  (Conformance) and `build-and-test` (Documentation). Both checks must originate
  from GitHub Actions, whose observed app ID is `15368`.
- Force pushes and deletion are blocked. The bypass list is empty, including
  for administrators and bots.
- Required approvals are zero while Allagma has one active maintainer. GitHub
  does not let authors approve their own PRs. External changes still receive
  maintainer review under [governance](../../GOVERNANCE.md).
- `CODEOWNERS` continues to identify ownership. Code Owner approval and approval
  of the last push are not required in this single-maintainer configuration.

GitHub also returns its default additional-approval setting for unattributed
Copilot PRs. It is recorded in the application receipt; GitHub documents that
it has no effect when the required approval count is zero. Revisit it when
increasing that count. See [additional approval behavior](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#additional-approval-for-unattributed-copilot-pull-requests).

Merge commits remain available to preserve original feature history and
authorship, as in the [recorded merges](../../docs/contributing/merged-prs.md).
Squash and rebase also remain available; linear history is not required.
Feature branches are outside this ruleset. Commit signing, merge queues and
deployment gates are not required.

The two required jobs run on every PR. `acceptance` is skipped on PR events, so
requiring that job would not enforce an acceptance run. Pages deployment,
manual release preparation and scheduled external-link checks are not PR gates.
Before renaming a required job or adding workflow path filters, update the
ruleset so every PR can report each required result. A skipped workflow can
leave a required check pending; a conditionally skipped job can count as passing.
See [GitHub's status-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

When a second maintainer can regularly review changes, consider requiring one
approval and dismissing stale approvals on new commits. Keep scientific review
and real-host qualification separate from repository review and deterministic CI.

## Release tags

[`release-tags.json`](release-tags.json) prevents updates and deletion of
`v*` tags, matching the `release_tag` convention in [`release.json`](../../release.json).
There are no bypass actors. New tags remain possible for users with the existing
write permissions, subject to the maintainer's release decision and qualification
process. Creating a tag does not run or certify that process. These rules do not
publish a release or make release assets immutable.

## Apply and inspect

First inspect the live rulesets and select the existing rule by its exact name:

```sh
gh api repos/alohays/allagma/rulesets --jq '.[] | {id, name, enforcement}'
gh api repos/alohays/allagma/rules/branches/main
```

For an existing rule, replace `RULESET_ID` with that rule's repository ID and
use its matching payload. For example, to update `main-protection`:

```sh
gh api --method PUT repos/alohays/allagma/rulesets/RULESET_ID \
  --input .github/rulesets/main.json
```

Use `release-tags.json` and its own ID for `release-tag-protection`. Only when a
rule does not exist, use `POST` to `repos/alohays/allagma/rulesets` with that
payload. Do not create duplicate rulesets. After an uncertain write result,
inspect the live rules before retrying.

Read each rule back and compare its name, target, enforcement, bypass list,
conditions and rule parameters with the payload:

```sh
gh api repos/alohays/allagma/rulesets/RULESET_ID \
  --jq '{name, target, enforcement, bypass_actors, conditions, rules}'
```

GitHub can include extra default parameters in its response. Also confirm that
`main` is protected, the feature branch is not targeted, and a new PR recognizes
both required jobs. API readback confirms configured protection; it does not
exercise a rejected force push or tag deletion. Routine verification must not
rewrite history, delete a tag or publish a test release.

Changes to these payloads and changes to the live settings are separate actions.
Record the application time, rule IDs and payload digests when applying a change.
The initial application is recorded in [`applied.json`](applied.json); it is a
historical receipt, not a live monitor. Administrators can still edit the
rulesets themselves; an empty bypass list controls normal Git and merge actions.

## References

- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
  and [REST API](https://docs.github.com/en/rest/repos/rules): configuration and application.
- [Jupyter nbformat rules](https://github.com/jupyter/nbformat/rules/506915):
  a PR requirement with zero required approvals.
- [MCP Python SDK rules](https://github.com/modelcontextprotocol/python-sdk/rules/3187917)
  and [pytest rules](https://github.com/pytest-dev/pytest/rules/19676373):
  review and CI gates for projects with multiple maintainers.
- [OpenSSF branch protection guidance](https://github.com/ossf/scorecard/blob/main/docs/checks.md#branch-protection):
  protect public history and require checks appropriate to project participation.

The reference settings were inspected on 10 October 2026. They inform this
configuration; they are not copied wholesale or treated as a universal standard.
