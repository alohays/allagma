# Allagma study entrypoint

Select or recover a campaign first. Its `campaigns/<campaign>/lock.yaml` is authoritative for resume; otherwise use `.allagma/lock.yaml` and compare selection intent. Read `bundle_id` and open `.allagma/bundles/<bundle_id>/CATALOG.md`. Use only that bundle's methods and helpers. A newer global skill or study lock cannot replace a campaign snapshot.

For a machine-checked path, run `python3 .allagma/bundles/<bundle_id>/tools/allagma.py entry --study . --campaign <campaign> --module <method-id-or-role>`. Omit `--campaign` only for a new study phase. Required capabilities must be available; sequential artifact handoffs are the default. Shared contracts are in the bundle's `contracts/` directory.
