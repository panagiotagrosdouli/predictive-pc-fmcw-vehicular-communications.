# Corrected Link-Urgency Mechanism and Rerun Rules

Status: **IMPLEMENTED AND EXECUTED DIAGNOSTICALLY; NOT CANONICAL**.

This note freezes the scientific meaning of the corrected link-lifetime scheduler and records the first post-correction mechanism diagnostics. None of the diagnostic executions below are canonical publication evidence.

## 1. Failure mechanism in the previous heuristic

The previous lifetime bonus was

`closing_pressure * normalized_queue * currently_usable`.

It treated every currently usable closing link as urgent whenever packets were queued. That is not sufficient to establish packet-level value. A link can be closing while the head-of-line packet has an earlier deadline; in that case the packet deadline, not link expiry, is the binding service constraint. Adding both deadline urgency and an unconditional lifetime bonus double-counts urgency and can divert service from higher-value transmissions.

This mechanism is consistent with the historical development observation that link-lifetime scheduling can improve fairness while losing aggregate goodput in some operating regions. That historical observation remains diagnostic evidence only and is not proof that this mechanism is the unique cause.

## 2. Corrected causal definition

For vehicle `i`, let `L_i` be predicted remaining usable-link lifetime in slots and `D_i` the head-of-line packet time-to-deadline in slots. The lifetime bonus is active only if

`L_i < D_i`.

The corrected term is

`U_life(i) = closing_pressure(i) * queue(i) * currently_usable(i) * 1[L_i < D_i]`,

where

`closing_pressure(i) = clip((H - L_i) / H, 0, 1)`

and `H` is the prediction horizon.

Interpretation: the link is packet-relevant urgent only when the predicted communication opportunity disappears before the packet itself expires. If the packet expires first, the existing deadline term is the relevant urgency signal and the lifetime term is zero.

## 3. What this correction does not claim

It does not prove that the corrected scheduler is optimal. It does not prove that prediction improves communication performance. It does not retroactively validate `artifacts/corrected_v1` or `artifacts/corrected_v2`. It does not change historical artifacts. It does not turn diagnostic results into canonical results.

The corrected scheduler is a falsifiable mechanism candidate for the paper question: when does predicted mobility/link state have packet-level scheduling value?

## 4. Required comparison after the correction

Any new scheduler study must keep paired mobility scenarios and paired traffic randomness across policies. At minimum compare:

- `reactive_greedy`: no future information;
- `predictive_utility`: future link utility without link-lifetime bonus;
- corrected `link_lifetime`: packet-aware link-expiry urgency;
- `oracle`: evaluator/reference with perfect future information, not a deployable method.

Classical predictor variants remain useful for separating forecast quality from scheduling utility. Oracle must not be described as an achievable scheduler.

## 5. First post-correction mechanism diagnostic

The decision-level diagnostic compares selected receivers slot by slot using identical synthetic scenarios and paired traffic randomness. It is labeled **EXECUTED / DIAGNOSTIC**.

At the default reference condition (`offered_load=0.72`, `deadline_s=1.2`, `H=10`, `slot_duration_s=0.1`), corrected Link-Lifetime changes the Predictive-Utility decision in only 1 of 12 episodes. Averaged over all episodes, only about 2.85% of slots differ; the one affected episode has a 34.2% changed-slot fraction. The mean incremental Link-Lifetime gain over Predictive Utility is only about +0.00075 Mbps goodput, with zero incremental P95-latency difference. This shows that the corrected lifetime term is rarely decision-active at the default reference condition.

At `offered_load=0.9`, Link-Lifetime differs from Predictive Utility in 2 of 12 episodes and only about 0.56% of slots on average. Its mean incremental goodput difference is about +0.0031 Mbps. At an extremely short `deadline_s=0.05`, Link-Lifetime and Predictive Utility make identical decisions in all 12 episodes, exactly as the packet-relevance gate predicts: packet deadlines bind before future link expiry, so lifetime urgency contributes no separate scheduling information. At a 20-step horizon, Link-Lifetime again matches Predictive Utility in all 12 episodes under the tested reference traffic condition.

Oracle also changes decisions only sparsely relative to corrected Link-Lifetime in these diagnostics. At the reference condition it differs in 1 of 12 episodes; at the 20-step horizon it differs in 3 of 12. Therefore the small Oracle gap in aggregate packet metrics is not evidence that the predictor is perfect. It means that, under these synthetic conditions and this heuristic objective, additional future-state accuracy usually does not change the selected receiver.

The main mechanism conclusion from this diagnostic is narrower and stronger than the historical heuristic interpretation: **the large latency/fairness trade-off seen in the corrected benchmark is driven primarily by the broader Predictive-Utility objective, not by the corrected lifetime bonus itself.** The lifetime term is a conditional refinement whose value appears only when predicted link expiry is both packet-relevant and decision-changing.

## 6. Operating-region analysis

Do not reduce the result to one global mean. Report signed paired deltas versus reactive across offered load, prediction horizon, field of view, reference SNR, packet deadline, sensing uncertainty, traffic model/class, packet size, slot duration, vehicle count, and outage definition when those axes are part of the frozen study.

Use HELP / NEUTRAL / HURT only after a practical-equivalence rule and uncertainty rule are frozen. Until then, report signed deltas and paired-seed consistency rather than assigning an arbitrary neutral band.

A scientifically useful negative result is allowed: the corrected mechanism may still hurt under congestion, long horizons, poor sensing, or weak prediction. Those regimes must be retained.

## 7. Statistical unit and inference

The independent unit is the scenario/episode, not individual slots or packets. Comparisons are paired on scenario/episode and traffic randomness. Report effect sizes and uncertainty intervals. Multiplicity correction applies to families of inferential comparisons. Five traffic seeds alone must not be treated as five independent mobility populations when the same mobility realization is reused.

## 8. Evidence labels

- Existing `artifacts/corrected_v1` and `artifacts/corrected_v2`: **EXECUTED / DIAGNOSTIC / HISTORICAL**.
- Corrected scheduler implementation and unit tests: **IMPLEMENTED / CI-VERIFIED**.
- Post-correction benchmark, ablation, quick matrix, and decision-level mechanism workflow outputs: **EXECUTED / DIAGNOSTIC**.
- Only artifacts produced under the frozen canonical protocol and committed to the canonical artifact tree may be labeled **FROZEN / CANONICAL**.

## 9. Acceptance checks before paper claims

The corrected mechanism passes implementation design review because tests establish that: (a) link closure before packet deadline creates positive lifetime urgency; (b) packet deadline before link closure creates no lifetime bonus; (c) current outage creates no lifetime bonus; (d) empty queue creates no lifetime bonus; and (e) earlier predicted closure produces greater lifetime urgency under otherwise equal packet conditions. Repository CI and the dedicated corrected-scheduler diagnostic workflow pass after the correction.

The paper hypothesis remains **UNEVALUATED** until the corrected policy is run under the frozen canonical paired protocol. The diagnostic mechanism evidence may guide that protocol, but it cannot substitute for it.
