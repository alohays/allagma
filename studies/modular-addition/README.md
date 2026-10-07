# Modular addition: regularization and generalization

Status: development pilots only. No confirmation result or final-evaluation
outcome exists yet. This study investigates generalization after memorization
on modular addition, comparing regularized and unregularized training on a
fixed held-out partition. Its scientific code belongs to the study, separate
from Allagma's workflow and resource adapters.

The initial feasibility pilot uses modulus 97, a 30% training split and a
37,248-parameter two-layer ReLU MLP with one-hot ordered-pair inputs. It compares
AdamW weight decay while holding other optimizer settings fixed. This is an
adapted bounded experiment, not an exact replication of the original
[Power et al. study](https://arxiv.org/abs/2201.02177) or its
[transformer implementation](https://github.com/openai/grok).

Pilot seed 17 is reserved for development and must not enter final confirmation.
Pilot learning curves and resource receipts will determine a finite training
horizon. A missing generalization transition within that horizon is a censored
or negative result, not a reason to reinterpret training accuracy as success.
