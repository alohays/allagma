# Toy-to-paper walkthrough validation

Issue [#19](https://github.com/alohays/allagma/issues/19) is the first available
task in the contributor overview inspected on 10 October 2026. The implementation
starts from main `174e200b508b07f022ba36233db54ca0b60e48e1`, independently of the
documentation-only queue refresh in #24. It adds a study-owned example and a
[literal walkthrough](../guides/toy-to-paper.md), without changing the toy
experiment, framework paper contract, frozen studies or existing publications.

The helper tests use a real completed offline toy and exercise preparation,
explicit review input, result locators, missing/stale reviews, altered evidence,
revision preservation and refusal of adapted/partial studies. Their review
inputs are labeled structural fixtures, not scientific judgments. The literal
walkthrough additionally requires reading the generated evidence and prose;
its review records identify the executor's self-review, not an independent peer.

The recorded command/environment receipt and rendered review are added after
the fresh small-checkout run. This document does not itself claim that an
unrecorded platform or manuscript has been qualified.
