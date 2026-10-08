# Execute study-owned runner and evaluator in bounded local subprocesses.

The helper launches argument arrays without a shell. It snapshots executable inputs, bounds each attempt, saves stdout/stderr, records failure/interruption and never overwrites an attempt. The study owns scientific code. No network or paid API runner is supplied. This adapter requires artifact access and authorized local execution.

## Additional v0.3 resource supervisor

The optional [local resource supervisor](../../docs/resource-supervision.md)
wraps study-owned commands with explicit finite profiles and immutable job
receipts. It is separate from the existing campaign budget and does not change
historical campaign execution. Its watchdog coverage and limits are documented
in that guide.

The optional `broker.py` and `compute_client.py` provide a common local
resource queue for controlled agent evaluations. Controller-owned policies,
receipts and source snapshots stay outside candidate access. Both comparison
conditions use the same client. It supplies process accounting and isolation,
not scientific planning or analysis. On this Mac, its scientific worker profile
supports MPS while denying network connections and writes outside the workspace.
Inputs can be read-only and controller material is unreadable. A new request
preserves a failed earlier request, and missing delivery files can be restored
from the authoritative outcome without executing again.

The native Codex permission profile and this scientific worker sandbox are
separate: the former keeps direct agent commands confined, while the latter
permits the GPU runtime needed by requested scientific computation. The
controller must service the queue and retain its own records. The frozen v0.3
cohort used this interface for twelve native research sessions. The rc2 broker
corrects an MPS allocator mismatch by explicitly setting high watermark 0.2,
low watermark 0.1 and disabled implicit fallback. An actual full-broker MPS
forward/backward, AdamW, checkpoint/resume and access-denial regression passes.
The frozen comparison retains the original defect and autonomous recoveries;
it does not measure corrected GPU throughput. A controller killed mid-request requires
explicit reconciliation of its resource receipt; never infer that an absent
response permits a retry.
