# Fairness-weight diagnostic

**Status:** EXECUTED / DIAGNOSTIC / NON-CANONICAL

This note records the paired five-seed fairness-weight sweep for the `deadline_aware_lifetime` scheduler. It is mechanism-development evidence only. It must not be presented as final inference or as a tuned production/canonical scheduler.

## Frozen diagnostic design

- Predictive policy: `deadline_aware_lifetime`.
- Reactive reference: `reactive_greedy`.
- Fairness weights: 0, 0.05, 0.10, 0.15, 0.20, 0.30.
- Paired seeds: 20260827--20260831.
- Regimes: 50 ms deadline, 500 ms deadline, offered load 1.1, and reference-SNR offset +3 dB.
- Total rows: 140.

The sweep was introduced after the utility-term ablation identified the fairness term as a plausible source of packet-level objective conflict. Consequently, these four regimes are development regimes and must not be reused as an unbiased test set for selecting a final fairness weight.

## Paired goodput findings

The values below are mean predictive-minus-reactive goodput differences. The intervals are paired percentile-bootstrap 95% intervals over the five diagnostic seeds and are descriptive only; five seeds are too few for final publication inference.

| Regime | w=0 | w=0.05 | w=0.10 | w=0.15 | w=0.20 | w=0.30 |
|---|---:|---:|---:|---:|---:|---:|
| deadline 0.05 s | +0.0564 [0.0180, 0.0978] | +0.0008 [-0.0830, 0.0882] | -0.0612 [-0.1472, 0.0438] | -0.1564 [-0.2620, -0.0104] | -0.2248 [-0.3576, -0.0808] | -0.4096 [-0.5700, -0.2492] |
| deadline 0.5 s | +0.1430 [0.0814, 0.2046] | +0.1550 [0.1098, 0.2002] | +0.1654 [0.1302, 0.1958] | +0.1614 [0.1236, 0.1990] | +0.1496 [0.1172, 0.1894] | +0.0568 [-0.0470, 0.1606] |
| offered load 1.1 | +0.0416 [-0.0158, 0.0990] | +0.0362 [-0.0368, 0.1092] | -0.0010 [-0.0984, 0.0852] | -0.0684 [-0.1654, 0.0186] | -0.1608 [-0.2530, -0.0504] | -0.3392 [-0.5080, -0.1720] |
| SNR offset +3 dB | +0.0376 [0.0134, 0.0590] | +0.0450 [0.0302, 0.0626] | +0.0510 [0.0234, 0.0786] | +0.0514 [0.0236, 0.0774] | +0.0478 [0.0378, 0.0560] | -0.1138 [-0.1982, -0.0294] |

## Mechanistic interpretation

The sweep supports a conditional objective-conflict interpretation. A fixed fairness pressure can reverse the sign of packet-level goodput value in tight-deadline and high-load regimes. This is not evidence that trajectory prediction itself becomes inaccurate in those regimes.

At the 50 ms deadline, zero fairness weight improves both goodput (+0.0564 Mbps) and demand-normalized Jain fairness (+0.0933) relative to the reactive reference. Increasing fairness pressure raises fairness further but eventually causes a substantial goodput loss. At the 500 ms deadline, weights from 0 through 0.20 all retain a positive diagnostic goodput advantage; weight 0.10 has the largest mean advantage (+0.1654 Mbps) in this sampled grid. Under offered load 1.1, the positive/neutral region is near low fairness weights, whereas weight 0.20 is clearly harmful in this diagnostic. At +3 dB, weights 0 through 0.20 are positive in goodput, while 0.30 reverses the sign.

The chosen-link outage fraction was zero throughout these sweep runs. Therefore the observed HELP/HURT changes cannot be explained simply by selecting physically unusable links. They are consistent with service-order, queue, deadline, and fairness interactions after a usable link has been identified.

## What this does not justify

Do not select `fairness_weight=0.10` merely because it has the largest mean goodput in two of these four development regimes. That would be post-hoc tuning on the same regimes used to discover the mechanism. Do not claim an optimal fairness weight, a universal Pareto point, or final statistical significance from five seeds.

## Prospective selection rule

The next scheduler-weight decision must be made prospectively. Use a separate development population/regime set to choose a weight under an explicit multi-objective constraint, then freeze it before evaluation on held-out regimes/scenarios. A defensible development rule is:

1. Require predictive goodput to be non-inferior to the reactive reference within a predeclared packet-scale margin in every development regime.
2. Among weights satisfying that constraint, maximize the worst-case demand-normalized fairness improvement.
3. Break remaining ties by lower P95 latency, not by test-set goodput.
4. Freeze the selected weight and evaluate it unchanged on held-out mobility/traffic/channel regimes with more independent scenario/episode units.

If no nonzero weight satisfies the non-inferiority constraint, retain zero fairness weight as the throughput-oriented predictive variant and report fairness as a separate trade-off rather than hiding the conflict.

## Paper implication

A stronger current hypothesis is:

> The packet-level value of future mobility/link information is conditional on both the operating regime and the scheduling objective. In particular, fairness pressure can dominate the value of otherwise useful predictive information under packet urgency or congestion.

This remains a hypothesis until the prospective held-out evaluation is completed.
