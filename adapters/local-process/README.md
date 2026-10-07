# Execute study-owned runner and evaluator in bounded local subprocesses.

The helper launches argument arrays without a shell. It snapshots executable inputs, bounds each attempt, saves stdout/stderr, records failure/interruption and never overwrites an attempt. The study owns scientific code. No network or paid API runner is supplied. This adapter requires artifact access and authorized local execution.
# Additional v0.3 development supervisor

The optional [local resource supervisor](../../docs/resource-supervision.md)
wraps study-owned commands with explicit finite profiles and immutable job
receipts. It is separate from the existing campaign budget and does not change
historical campaign execution. Its watchdog coverage and limits are documented
in that guide.
