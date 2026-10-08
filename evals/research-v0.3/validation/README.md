# Controller validation allocation

This is a separate initial allocation for independent scoring, checkpoint replay,
package verification and the required clean-checkout study reproduction. It does
not change any candidate's frozen resource ceiling or improve its recorded
outcome. All computation is local; scientific dependencies remain in isolated
environments. The 1,800-second compute, 600-second setup and 64-request ceilings
include failed validation attempts. Per-command limits are finite. The allowance
is based on measured development execution/replay costs with room for cold setup
and the complete required validation scope. Any expansion needs user input.

## Actual full-broker MPS regression — passed

`check_mps_broker.py` and `mps_broker_canary.py` passed against corrected source
commit `5910b36` after every assigned native session was terminal. The receipt is
[mps-broker-rc2/validation.json](mps-broker-rc2/validation.json); the actual worker
result and checkpoint are retained in that directory with an evidence index.
The frozen comparison source remains unchanged.

The executed command used the complete broker environment with high watermark
0.2, low watermark 0.1 and disabled implicit fallback:

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

## Final scorer qualification and controller failure

All five optional scientific-scorer tests pass in job
`0057-rc2-scientific-scorer-qualification-absolute-paths`, including actual MPS
sample regeneration from a development checkpoint using trusted science. The
first invocation, job 0056, mistakenly supplied repository-relative executable
paths even though the ledger runs from `work/v03-validation`. Launch failed
before a process receipt. Explicit recovery preserved an abandoned outcome and
conservatively charged the full 124.75-second reservation; the corrected command
used absolute paths under a new job ID. No historical receipt or ceiling changed.

The final controller allocation and every failed scientific or transport check
remain in the ledger. Controller work is separate from native candidate costs
and cannot improve their original comparison outcomes.
