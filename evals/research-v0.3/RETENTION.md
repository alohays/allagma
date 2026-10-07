# Candidate package retention

`retention.py` is a transport utility outside the frozen scientific scorer. Run
collection only after the native session and all its computation have stopped.
It reads the candidate workspace without editing any artifact, archives regular
source/evidence files, and verifies they did not change during collection.

Archives are divided into 32 MiB parts so individual files fit ordinary Git
transport. The index records each part and the complete archive SHA-256, plus
every retained file's hash and size. Virtual environments, caches and transient
computation queues are excluded; authoritative computation history is retained
separately by the controller. A missing or inconsistent candidate manifest is
reported as an error, not converted into evidence of completion.

Supplied wheelhouse files are retained as exact filename/size/hash references.
This avoids placing a >100 MB PyTorch wheel in Git or duplicating installed
environments. Restore them from an exact local cache or explicitly download
the pinned distribution, then check the hash before use. A matching dependency
version string alone is insufficient.

```sh
python3 evals/research-v0.3/retention.py collect \
  --source /path/to/finished-candidate --destination /path/to/new-package
python3 evals/research-v0.3/retention.py restore \
  --source /path/to/new-package --destination /path/to/new-workspace \
  --wheel-cache /path/to/verified-wheel-cache
```

Use `--download-wheels` instead of a cache when explicitly preparing a fresh
environment from the package index. Dependency acquisition is setup work; all
scientific execution remains local. Restoration verifies exact file bytes but
does not establish scientific reproducibility. Execute the delivered full-study
and raw-data recomputation commands separately and retain their actual outcomes.
