# Ablation Design Hygiene Note

## Status

This note documents a diagnostic-design correction discovered while auditing `artifacts/corrected_v2/`. The existing `corrected_v2` outputs remain historical **EXECUTED / DIAGNOSTIC** evidence and are not rewritten or relabeled as canonical results.

## Duplicate condition found

The historical ablation matrix contained both `trajectory_predictive` and `no_link_lifetime_urgency`.

In the implementation, `PredictiveUtilityScheduler` and `LinkLifetimeScheduler` use the same constant-acceleration forecast and the same base predictive utility. The only additional term in `LinkLifetimeScheduler` is multiplied by `lifetime_weight`. Therefore, a `LinkLifetimeScheduler` run with `lifetime_weight=0` is behaviorally equivalent to the `trajectory_predictive` condition.

Accordingly, `no_link_lifetime_urgency` is no longer generated as a separate paper ablation. The scientifically interpretable comparison is:

- `trajectory_predictive`: predictive scheduling without link-lifetime urgency;
- `link_lifetime`: the same predictive utility augmented with link-lifetime urgency.

Historical equality between `trajectory_predictive` and `no_link_lifetime_urgency` in `artifacts/corrected_v2/paper_ablations/` is therefore expected and must not be treated as independent replication or as evidence that a separately implemented policy happened to produce the same result.

## Full-channel reference

The matrix also contains both `link_lifetime` and `full_channel`. These are intentionally equivalent under the default configuration. `full_channel` is retained only as the named reference point used by the channel-model ablation (`range_only_channel` -> `range_pointing_channel` -> `full_channel`, with the BER-source comparison alongside it).

`full_channel` must therefore **not** be counted as an independent scheduler condition, an additional statistical comparison, or extra evidence. For scheduler-level claims, use `link_lifetime`. For the channel-model ablation, `full_channel` may be shown as the reference label.

## Publication rule

Canonical reruns and manuscript statistics must operate on scientifically distinct conditions. Alias/reference rows may be used for plotting clarity only when explicitly identified as such and must not inflate sample size, the number of independent comparisons, or the strength of evidence.

No historical artifact has been deleted. A canonical rerun is still required before publication claims are frozen.
