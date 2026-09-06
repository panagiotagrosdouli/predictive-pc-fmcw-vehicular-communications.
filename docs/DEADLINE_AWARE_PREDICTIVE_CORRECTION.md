# Deadline-Aware Predictive Lifetime Diagnostic

Status: **IMPLEMENTED; NOT YET CANONICALLY VALIDATED**

## Motivation

The corrected five-seed decision audit showed that `predictive_utility` and
`link_lifetime` can make nearly identical decisions while both differ strongly
from `reactive_greedy`. In the tight-deadline and high-load diagnostic regimes,
those predictive decisions can reduce goodput even when scheduled links are not
in outage. This indicates that the limiting mechanism is not merely link
forecast quality or the lifetime bonus. Packet urgency can dominate the value
of future-link information.

## Diagnostic mechanism

`deadline_aware_lifetime` is intentionally introduced as a separate scheduler;
it does **not** replace `link_lifetime` and must not retroactively reinterpret
historical artifacts.

For each vehicle, let `D` be the head-of-line packet time-to-deadline in slots
and `H` the prediction horizon in slots. The predictive weight is

`w(D,H) = clip((D - 1) / max(1, H - 1), 0, 1)`

for finite deadlines. Infinite deadlines use `w=1`.

The score is

`U = (1-w) U_current_packet + w U_link_lifetime`.

`U_current_packet` uses only current realized-link state plus queue, packet
deadline, fairness, and switching terms. `U_link_lifetime` is the existing
causal predictive utility with packet-aware link-expiry urgency.

Therefore:

- packets due within one slot do not let longer-horizon link predictions
  dominate the decision;
- packets with slack approaching or exceeding the prediction horizon recover
  the full predictive scheduler;
- intermediate deadlines interpolate continuously rather than switching via an
  arbitrary binary regime threshold.

## Scientific interpretation

This is a falsifiable diagnostic mechanism, not an optimality claim. It tests
whether prediction should be weighted by **decision relevance in packet time**,
not only by forecast confidence or link lifetime.

The key comparisons are:

1. `reactive_greedy` vs `predictive_utility`: value/cost of generic prediction;
2. `predictive_utility` vs `link_lifetime`: incremental lifetime-urgency value;
3. `link_lifetime` vs `deadline_aware_lifetime`: incremental packet-time
   relevance correction;
4. `deadline_aware_lifetime` vs `oracle`: remaining information/decision gap.

## Evidence rules

The first run remains `EXECUTED_DIAGNOSTIC`. It must use the same paired seeds,
traffic randomness, mobility generation, realized-link packet evaluator, and
representative HELP/HURT regimes as the previous decision audit. Negative
results must be retained.

No manuscript claim should state that the new scheduler solves the HURT regimes
until the paired diagnostic has executed successfully and its decision-level and
packet-level outputs have been inspected. Canonical publication evidence still
requires the frozen publication protocol and canonical artifact path.
