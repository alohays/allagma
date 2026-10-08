# Controller validation allocation

This is a separate initial allocation for independent scoring, checkpoint replay,
package verification and the required clean-checkout study reproduction. It does
not change any candidate's frozen resource ceiling or improve its recorded
outcome. All computation is local; scientific dependencies remain in isolated
environments. The 1,800-second compute, 600-second setup and 64-request ceilings
include failed validation attempts. Per-command limits are finite. The allowance
is based on measured development execution/replay costs with room for cold setup
and the complete required validation scope. Any expansion needs user input.

## Prepared MPS regression — execution pending

`check_mps_broker.py` and its worker `mps_broker_canary.py` are prepared for the
post-cohort broker correction. At this checkpoint only syntax and CLI parsing
have been checked; these files do not establish MPS qualification yet. Keep the
frozen comparison source unchanged until every assigned session is terminal.

After the release broker explicitly supplies high watermark 0.2 and low
watermark 0.1, execute through the complete broker environment:

```sh
python3 evals/research-v0.3/validation/check_mps_broker.py \
  --workspace work/v03-validation/mps-broker-rc2 \
  --ledger evals/research-v0.3/validation/resources \
  --record evals/research-v0.3/validation/mps-broker-rc2 \
  --wheels work/v03-development/wheelhouse-torch
```

This creates a fresh study environment, installs exact local wheel versions,
and charges setup and one compute request to the existing finite validation
allocation. It verifies known-answer MPS forward/backward work, AdamW updates,
checkpoint reload and resumed training, while exercising real read/write/network
denials. The controller establishes that a loopback listener is reachable;
connection refusal or a missing protected file cannot count as sandbox denial.
The worker never repairs its own environment variables. Source hashes, process
receipts, failed requests and the final result remain retained. A failed run
must use new output directories for any retry.

This test covers the scientific broker. Native-agent permission-profile checks,
scientific results, default offline conformance and GPU-memory-accounting limits
remain separate qualification dimensions.
