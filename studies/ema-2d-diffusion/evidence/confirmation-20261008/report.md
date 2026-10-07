All ten confirmation trajectories completed serially through `python3 manage.py confirm`, each on attempt 001. Every terminal record succeeded, every evaluator check passed, and all recorded input/output digests matched. Analysis has not been performed.

The unchanged post-pilot decision was created by `python3 manage.py freeze` at 2026-10-07T15:28:26.950456+00:00. The measured-cost forecast was 284.8384268725058 seconds, including the 120-second analysis/reproduction reserve, against 1699.627220249083 seconds available. The freeze was not overwritten.

Campaign: `ema-v1`. Protocol: `ema-2d-v1`. Bundle: `b-2b63431e34a085598aaade78`. Lock identity: `7287e278da3e264dc83704d42c334dd5845da048f59c9967343545fc4ec6c329`. Freeze SHA-256: `e7b37fee3ca7331f7743f73a52de0528a3f1e2ce5d4e83aa2d385674c6ac9eca`.

Coverage includes moons seeds 1001–1005 and gmm8 seeds 2001–2005, with raw, EMA 0.99 and EMA 0.999 at updates 5,000 and 10,000. All 60 confirmation variant/checkpoint cells retain 2,048 generated draws, shared within-trajectory held-out data and checkpoint weights. The ten independent trajectories remain the experimental units. The four pilots are retained separately.

All 240 confirmation evaluator checks passed (21 for each moons trajectory and 27 for each gmm8 trajectory). These checks cover native MPS, complete trajectories, seeded holdout reconstruction, finite samples, checkpoint digests, projected W1 cross-checks against SciPy and mixture diagnostics. This is deterministic evaluation, not scientific peer review.

| Trajectory | Attempt | Evaluator checks | Attempt seconds | Charged seconds |
| --- | --- | ---: | ---: | ---: |
| confirm-moons-1001 | confirm-moons-1001-a001 | 21 | 14.786150750005618 | 14.887783417012542 |
| confirm-moons-1002 | confirm-moons-1002-a001 | 21 | 14.528551374794915 | 14.660432290984318 |
| confirm-moons-1003 | confirm-moons-1003-a001 | 21 | 14.669013707898557 | 14.827178166015074 |
| confirm-moons-1004 | confirm-moons-1004-a001 | 21 | 14.738839250057936 | 14.894481624942273 |
| confirm-moons-1005 | confirm-moons-1005-a001 | 21 | 14.703115375014022 | 14.874637250090018 |
| confirm-gmm8-2001 | confirm-gmm8-2001-a001 | 27 | 14.718288999982178 | 14.863816291093826 |
| confirm-gmm8-2002 | confirm-gmm8-2002-a001 | 27 | 14.732857916969806 | 14.895416624844074 |
| confirm-gmm8-2003 | confirm-gmm8-2003-a001 | 27 | 14.710514124948531 | 14.855775916948915 |
| confirm-gmm8-2004 | confirm-gmm8-2004-a001 | 27 | 14.782785458024591 | 14.933858915930614 |
| confirm-gmm8-2005 | confirm-gmm8-2005-a001 | 27 | 14.922793708974496 | 15.09641645802185 |

The study ledger charges 249.16257670680062 of 1800.0 seconds, leaving exactly **1550.8374232931994 seconds**. The separate 1650.0-second campaign attempt ceiling has 1443.4033467913978 seconds remaining. There are 3 remaining attempt slots (15 of 18 used). The study total includes all setup-check failures, the interruption and the 15.3-second feasibility charge.

Retained unsuccessful evidence comprises `pilot-moons-11-a001`, interrupted after 100 updates and explicitly excluded from scientific evidence, and the two earlier failed setup-check receipts `001-known-answer-checks.json` and `002-known-answer-checks-corrected.json`. There were no new failed, interrupted, timed-out or retried confirmation attempts.

All 253 preexisting protected files remain byte-identical. The protocol, frozen scientific sources, bundle, orchestration and resource ceilings were preserved. No model overrides, extra agents or additional model sessions were created by this session.

The final campaign state is phase `analysis`, execution status `ready`, assurance `unreviewed`, with no next training run. This state indicates that the run plan is complete and analysis is ready to begin; no analysis command has been run.

Evidence: [preflight](preflight.json), [freeze command](freeze-command.json), [result](result.json), [final status](final-status.json), and the ten per-trajectory inspection records in this directory. The `evidence/compute/009` through `018` receipts retain scientific commands and timings.
