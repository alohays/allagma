# Modular addition: regularization and generalization

Status: the first fully verified Allagma confirmation package is r04. See
[results and reproduction](RESULTS.md). The 12-session comparison remains in
progress. This study investigates generalization after memorization
on modular addition, comparing regularized and unregularized training on a
fixed held-out partition. Its scientific code belongs to the study, separate
from Allagma's workflow and resource adapters.

The initial feasibility pilot uses modulus 97, a 30% training split and a
37,248-parameter two-layer ReLU MLP with one-hot ordered-pair inputs. It compares
AdamW weight decay while holding other optimizer settings fixed. This is an
adapted bounded experiment, not an exact replication of the original
[Power et al. study](https://arxiv.org/abs/2201.02177) or its
[transformer implementation](https://github.com/openai/grok).

Development seeds 17 and 29 are excluded from final confirmation. The frozen
comparison uses paired seeds 1001–1004 and exactly 100,000 updates per condition.
No trajectory reached the 95% sustained generalization threshold in r04;
this is a censored finding at the fixed horizon, not an eventual-outcome claim.
