# Execute study-owned runner and evaluator in bounded local subprocesses.

The helper launches argument arrays without a shell. It snapshots executable inputs, bounds each attempt, saves stdout/stderr, records failure/interruption and never overwrites an attempt. The study owns scientific code. No network or paid API runner is supplied. This adapter requires artifact access and authorized local execution.
