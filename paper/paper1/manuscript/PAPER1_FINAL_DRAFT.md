# When Does Trajectory Prediction Help PC-FMCW/DPSK Vehicular Optical Scheduling?

## Abstract

Predictive scheduling is often motivated by the intuition that future vehicle motion reveals communication opportunities before a reactive scheduler can observe them. This paper tests that claim for a model-based PC-FMCW/DPSK vehicular optical link without assuming that prediction is universally beneficial. We implement a strictly causal chain from observed vehicle history to trajectory prediction, future relative geometry, predicted link quality, packet queues and deadlines, scheduling, and realized packet-level outcomes. Classical predictive policies and an Oracle information reference expose the value of future information, while a prospectively selected current-service guard constrains predictive urgency when it would sacrifice excessive immediate service opportunity. In a disjoint 20-seed synthetic holdout, the frozen 0.8 guard yields statistically supported goodput improvements over Reactive Greedy in three of four predeclared regimes: tight 0.05 s deadlines, 0.5 s deadlines, and a +3 dB reference-SNR condition. Under offered load 1.1, the goodput effect remains uncertain and tail latency worsens descriptively. These findings reject a universal prediction-gain claim. Prediction is most useful when future link evolution exposes actionable service opportunities, but can become neutral or harmful when capacity pressure makes immediate service efficiency dominant. The optical channel is an analytical PC-FMCW/DPSK-informed simulation model; no measured optical-link or real-world vehicular validation is claimed.

## 1. Introduction

PC-FMCW laser-headlamp concepts can combine sensing, illumination, and DPSK communication. A mobility-aware scheduler adds a distinct system-level question: should a receiver be served now because its predicted future geometry indicates that its communication opportunity is about to degrade or disappear?

A reactive scheduler sees current link quality. A predictive scheduler can estimate future relative range and bearing and therefore future modeled SNR, BER/PER, outage, and link lifetime. This information is potentially valuable near field-of-view, deadline, and link-loss boundaries. It is also risky. Forecast error can move a receiver across a hard optical boundary, and a scheduler that overvalues future urgency can sacrifice a strong current transmission opportunity.

Accordingly, the paper asks: **when, why, and under which operating regimes does causal future-motion/link information improve packet-level scheduling relative to reactive scheduling?** The contribution is not the assertion that prediction always helps, but a reproducible mechanism study that identifies positive, null, and harmful regimes.

## 2. Related Work

This work lies at the intersection of vehicular optical communication, trajectory forecasting, predictive radio/resource scheduling, and integrated sensing/communication. Its specific contribution is an auditable causal interface between motion forecasting and a PC-FMCW/DPSK-informed packet scheduler. Unlike an offline trajectory oracle, deployable policies never receive future ground truth. Unlike a pure trajectory-prediction benchmark, evaluation is performed on packet outcomes and explicitly tests whether geometric accuracy translates into communication value.

## 3. System Model

At decision slot t, the scheduler observes vehicle histories through t, packet queues, packet deadlines, and past service. A causal predictor produces future target positions over horizon H. Ego-relative range and bearing are mapped through the modeled optical link to future SNR, BER/PER, goodput, outage, and link-lifetime estimates.

The realized packet outcome is evaluated using the realized ground-truth-derived geometry at the current transmission slot. Forecasts affect decisions; they do not replace the realization model. Packet arrivals, deadlines, queue evolution, failed retransmissions, drops, and remaining right-censored packets obey queue-conservation checks.

The Part-A physical-layer reference is frozen separately. It supplies the PC-FMCW/DPSK premise and reference parameters, while the end-to-end geometry-to-link mapping used here remains a newly introduced analytical simulation assumption.

## 4. Problem Formulation and Proposed Method

For receiver i, a predictive scheduler evaluates a utility combining current/future modeled service, queue and deadline pressure, fairness/opportunity terms, and predicted link evolution. A generic decision is

`i* = argmax_i U_i(history_t, queue_t, deadlines_t, predicted_link_{t+1:t+H})`.

Link-Lifetime urgency increases priority when a currently usable receiver is predicted to lose service within the forecast horizon. Earlier diagnostics revealed an important failure mode: future urgency can reorder service away from a strong current opportunity, particularly under congestion.

The proposed Paper-1 refinement therefore uses a **current-service guard**. Predictive reordering is permitted only when the candidate preserves a specified fraction of the immediate service opportunity. The guard was selected prospectively on development seeds only; the frozen selected value is 0.8. This converts the research contribution from unconstrained prediction to **predictive scheduling with explicit protection of current service efficiency**.

## 5. Baselines and Information References

Reactive baselines include Random, Round Robin, Reactive Greedy, and Proportional Fair. Classical predictive methods use causal Last Position/CV/CA/Kalman/IMM-style motion information where configured, together with Predictive Utility and Link-Lifetime scheduling. The current-service-guarded predictive policy is the confirmatory Paper-1 method. Oracle uses perfect future positions only as an evaluator-side information reference; it is not deployable and is not described as a globally optimal offline scheduler.

Paired comparisons share scenarios, traffic traces, deadlines, and transmission random numbers. Future ground truth never enters a deployable scheduler decision.

## 6. Experimental Protocol

The confirmatory evidence is a prospectively selected synthetic holdout. Development used seeds 20261101--20261110. The frozen selected `service_guarded_80` policy was evaluated once on disjoint seeds 20261201--20261220.

Four regimes were predeclared: deadline 0.05 s, deadline 0.5 s, offered load 1.1, and reference SNR +3 dB. The primary endpoint is paired candidate-minus-Reactive goodput. Each regime therefore has 20 paired independent episode/seed observations; time samples are not treated as independent replicates.

The frozen analysis uses 100,000 paired percentile bootstrap replicates, a 95% confidence interval for the mean paired difference, a two-sided paired Wilcoxon signed-rank test, Holm correction over the four primary comparisons, paired Cohen dz, and win/loss/tie fractions. A practical margin of +/-0.001 Mbps defines HELP, HURT, or NEUTRAL_OR_UNCERTAIN.

Secondary metrics include PDR, latency, deadline/censoring outcomes, fairness, queue-at-disconnect, urgent/bulk PDR, scheduled SNR/BER/PER, outage, and link-lifetime diagnostics. Operating-region sweeps vary load, horizon, slot duration, receiver count, traffic, packet size/deadline, reference SNR, field of view, outage definition, and sensing assumptions.

## 7. Confirmatory Results

The frozen current-service guard improves goodput in three of the four predeclared holdout regimes.

| Regime | Delta goodput (Mbps) | 95% paired bootstrap CI | Holm p | Cohen dz | Classification |
|---|---:|---:|---:|---:|---|
| deadline 0.05 s | +0.03730 | [0.02195, 0.05365] | 0.001875 | 1.000 | HELP |
| deadline 0.5 s | +0.05680 | [0.04015, 0.07530] | 0.000527 | 1.384 | HELP |
| offered load 1.1 | +0.00860 | [-0.00230, 0.02050] | 0.295869 | 0.322 | NEUTRAL_OR_UNCERTAIN |
| reference SNR +3 dB | +0.01915 | [0.00790, 0.03120] | 0.019954 | 0.706 | HELP |

Thus, prediction is not uniformly beneficial. The strongest supported gain occurs at the 0.5 s deadline, whereas the high-load condition does not establish a practically positive goodput effect.

## 8. Statistical Analysis and Trade-offs

The confirmatory conclusions are based on episode-level paired inference. Three HELP regimes survive both the practical-margin rule and Holm-adjusted testing. The high-load result remains uncertain.

Secondary outcomes expose the multi-objective trade-off. At offered load 1.1, mean P95 latency is descriptively about 50 ms worse, with a bootstrap interval of [20, 85] ms, even though the goodput interval overlaps the neutral region. This is evidence against declaring the method superior based on goodput alone.

At deadline 0.05 s, the goodput gain is accompanied by a positive PDR difference and no observed P95-latency change in the frozen secondary summary. At deadline 0.5 s and +3 dB SNR, goodput/PDR gains coexist with small or uncertain latency changes. These secondary endpoints remain descriptive rather than newly promoted confirmatory hypotheses.

## 9. Ablations, Robustness, and Failure Modes

Existing diagnostics show that predictive scheduling can change sign across operating regimes. Earlier unconstrained Link-Lifetime scheduling produced only a small, statistically unsupported default-point goodput increase while worsening tail latency, and it could become harmful under high load or urgent/bulk traffic. The mechanism is service-order conflict: link-closure urgency is not identical to packet-deadline urgency or immediate service efficiency.

The current-service guard was introduced specifically in response to that mechanism and was selected prospectively before holdout evaluation. The holdout shows that it preserves supported gains in several regimes but does not solve high-load congestion. Therefore the guard is a constraint on predictive behavior, not evidence of an optimal scheduler.

Horizon, sensing/predictor degradation, link assumptions, fairness weight, and traffic/deadline sweeps are interpreted as robustness/mechanism studies. Prediction is expected to be most actionable near future service boundaries and least useful when forecasts do not alter the decision or when capacity pressure dominates.

## 10. Discussion

The results answer the central question conditionally. Future information has packet-level value when it changes service ordering before a relevant link/deadline boundary and when the opportunity cost of that reordering remains controlled. Better trajectory prediction alone is insufficient: the forecast must alter a communication-relevant decision in a beneficial direction.

The high-load null/uncertain result is scientifically important. It demonstrates that a predictive scheduler can possess useful future information without converting that information into a superior multi-objective outcome. Scheduler structure, queue pressure, and current service opportunity determine whether prediction can be exploited.

## 11. Limitations

The confirmatory holdout is synthetic. The optical link is model-based and uses reference-SNR/geometry assumptions rather than measured end-to-end vehicle optical calibration. The Part-A waveform work provides physical-layer provenance but does not constitute validation of the geometry-to-link model used by the scheduler. No road deployment, hardware-in-the-loop experiment, or measured vehicular optical channel is claimed.

The confirmatory study evaluates a finite set of predeclared operating regimes. The selected 0.8 guard is not claimed globally optimal. Secondary outcomes were not all primary hypotheses. Oracle is an information reference rather than an offline global optimum. Learned GRU/WOMD results are intentionally excluded from Paper 1 because their complete frozen evidence belongs to Paper 2.

## 12. Conclusion

Predictive communication-aware scheduling can improve modeled PC-FMCW/DPSK packet performance, but only conditionally. A prospectively selected current-service guard yields statistically supported goodput gains over Reactive Greedy in three of four predeclared synthetic holdout regimes. Under high load, the goodput effect remains uncertain and tail latency worsens. The evidence therefore rejects universal predictive superiority and supports a more precise conclusion: **prediction helps when future link information is actionable and its service-order opportunity cost is controlled**.

## 13. Reproducibility and Claim Boundary

The repository freezes Part-A provenance, causal simulation logic, selection/holdout protocols, seeds, paired statistical procedures, and experiment manifests. Publication-facing numerical claims must be generated from or traceable to frozen artifacts; missing external-data evidence is never substituted with synthetic numbers. The present Paper-1 claim is limited to model-based/synthetic evidence and must not be described as measured optical or real-world vehicular validation.
