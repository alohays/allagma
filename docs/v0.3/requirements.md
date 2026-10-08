# Allagma v0.3 acceptance ledger

Status: implementation, twelve-session evaluation, three task packages, release
repairs, reproduction and rc2 acceptance are verified. Final authorized Git
publication remains pending. The full owner request and commit/push instruction
are retained in [GOAL.md](../../GOAL.md). Historical v0.2 and frozen evaluation
evidence remain immutable; each receipt identifies its actual source and scope.

| ID | Required outcome | Evidence needed | Current state |
| --- | --- | --- | --- |
| V3-01 | Brief-to-package reusable workflow in a fresh Codex session | Native planning, implementation, bounded execution, recovery, critique, reporting and recomputation from an initial brief | Passed across all three families; all six Allagma packages complete with zero follow-up guidance. Exact frozen methods/recipe read in each [native treatment trace](../../evals/research-v0.3/postprocess-checks/treatment-compliance-final.json). |
| V3-02 | EMA duration/schedule follow-up | Identifiable design, held-out measurements, paired seed uncertainty, local execution and scientific audit | All four runs pass 240/240. [Illustrative r07](../../studies/ema-schedule/RESULTS.md): 32 cells, four seeds/dataset, independently checked inputs/checkpoints and 114 summaries; r12 additionally reruns full CPU training in a fresh environment. |
| V3-03 | Modular-addition regularization/generalization study | Fixed split, learning curves, thresholds, regularization controls, seed uncertainty and execution | All four runs pass 40/40 and execution review. [Illustrative r04](../../studies/modular-addition/RESULTS.md): eight 100k trajectories, evidence 8/8. No prespecified 95% grokking event; censored outcomes retained. |
| V3-04 | External computational reproduction | CORE compatibility preflight; original science/questions/scoring retained; grounded execution/answers | CULP selected after local preflight. All four runs pass original 6/6 and evidence 8/8. [Illustrative r01](../../studies/core-culp/RESULTS.md) preserves source label defect and passes full clean-checkout reproduction. |
| V3-05 | Local finite resources and isolated environments | Hardware/environment receipts, bounded pilots, finite compute/timeout/request/memory/storage policy and enforced ledgers | [All twelve controls pass](../../evals/research-v0.3/postprocess-checks/cohort-controls-final.json); failures retained, no expansion. Real broker MPS repair and final-storage regressions pass separately; sampling/GPU limits remain explicit. |
| V3-06 | Separate model resource accounting | Existing authentication, observed model/settings, token usage/account checkpoints, no project model pins | All twelve public native receipts and checkpoints retained. [Comparison](COMPARISON.md) reports separate native/scientific costs and raw token fields without double-counting; control audit verifies model/config identities and absence of pins. |
| V3-07 | Twelve controlled evaluation runs | Three tasks × two conditions × two isolated fresh sessions; matched common controls and complete traces | 12/12 terminal, 12/12 science verified, 10/12 packages complete, zero subsequent interventions. Original r03/r06 review-binding gaps remain outcomes. |
| V3-08 | Evaluation integrity | Pre-evaluation freeze, development/final separation, protected scorers/references, integrity/isolation probes | [Final archive audit](../../evals/research-v0.3/postprocess-checks/frozen-archive-final.json) verifies all 127 frozen files, twelve input sets and twelve packages. Real native/worker protection probes retained. |
| V3-09 | Honest comparative evidence | Correctness, evidence/completion, interventions, resources, failures and uncertainty | [Final comparison](COMPARISON.md) and generated twelve-run report publish every outcome, six paired contrasts and two-session ranges. No broad superiority, independent-peer-review or corrected-GPU-performance claim. |
| V3-10 | General support follows demonstrated need | Need-to-change ledger, study-owned science, offline standard-library conformance/toy | [Development record](development.md), [defect corrections](defects.md), and final [I1–I5 receipt](evidence/rc2/acceptance/acceptance.json): 113 tests with no skips, complete toy, independent rational-arithmetic audit and archived replay. |
| V3-11 | Full clean-checkout reproduction | Fresh setup, full execution of at least one study, result recomputation/comparison | [Passed for r01](../../evals/research-v0.3/validation/clean-r01-results/verification.json): clean Git clone, exact package/wheels, fresh environment, all original scripts, graph checks and separate raw recomputation. Source revision predates rc2 repairs, which have separate final checks. |
| V3-12 | Critically reviewed task packages | Three full packages, scoped critique and resolved critical defects | CORE r01, modular r04 and EMA r07 retained and verified. Every numerical state/manifest/review requirement audited. Full-broker MPS, exit-storage and transport defects corrected with unchanged before evidence. No reproduced critical defect remains open in scope. |
| V3-13 | Release candidate and migration | English notes/migration, historical bundle verification, acceptance, commits and origin push | [0.3.0rc2 notes](../releases/0.3.0rc2.md), contract 0.2 compatibility and 5,944-file acceptance archive complete. Coherent commits retained; final authorized publication pending. |

## Development order and decision boundaries

1. Inspect current mechanisms and source studies. Preflight source task science,
   licenses, local compatibility and resource use before selecting a task.
2. Run bounded development pilots. Record assistance and failures. Extract only
   reusable mechanics justified by those observations; keep scientific code in
   studies. Develop scorers separately from candidate-writable workspaces.
3. Test end-to-end development sessions and isolation. Freeze workflow, inputs,
   scoring, resource ceilings and run order before final evaluation starts.
4. Execute all twelve final runs without task-specific follow-up guidance.
   Retain failures as outcomes. Any subsequent repair is separate from frozen
   comparison results and discloses assistance and changed scope.
5. Complete task packages, critical-defect fixes, clean-checkout reproduction,
   comparison and release audit. Commit coherent increments, then push origin.

The user authorizes routine workload selection and finite resource limits based
on pilots. A material unresolved scientific choice or expansion beyond an
adopted ceiling requires the user-input tool. Negative findings do not block
completion; missing execution, verification or deliverables do.

## Initial observations

On 8 October 2026 the starting checkout was clean at `6d2daf0`. The framework
declares v0.2.0. Native EMA support is study-specific: its supervisor has fixed
budget constants and its native launcher contains a fixed study interruption
condition. These are development candidates, not yet evidence for a general
replacement. The local host reports 14 CPU cores and 51,539,607,552 bytes RAM;
approximately 103 GiB disk space is available. The initial account checkpoint
reports ordinary usage allowed and 5% of the weekly Codex window consumed.

At that initial checkpoint no final evaluation had started. Current progress is
recorded in the table above and `evals/research-v0.3/progress.json`. No frozen
historical study, bundle, attempt, result or review has been edited.
