# Paper 1 Final Scientific Protocol

**Scope:** PAPER1

## Research question

When, why, and under which operating regimes does causal trajectory/link prediction improve packet-level scheduling for the model-based PC-FMCW/DPSK vehicular optical link relative to reactive scheduling?

## Contribution

The proposed method is predictive communication-aware scheduling. A causal motion predictor maps observed vehicle history to future relative geometry; the PC-FMCW/DPSK-informed link model maps that geometry to future link utility; queues, deadlines, current service opportunity, and predicted link lifetime determine the scheduling decision. The publication method includes the prospectively selected current-service guard, which limits future-urgency actions when they sacrifice too much immediate service opportunity.

## Causality and fairness

Deployable methods may use observations available at or before the decision slot only. Future ground truth is reserved for realization/evaluation and the explicitly labeled Oracle information reference. All paired scheduler comparisons must share scenario, traffic realization, packet deadlines, and transmission random numbers. The independent experimental unit is a scenario/episode seed, never an individual time sample.

## Primary confirmatory comparison

The frozen prospectively selected `service_guarded_80` policy is compared with Reactive Greedy on the four predeclared synthetic holdout regimes documented in `docs/PROSPECTIVE_SERVICE_GUARD_RESULT.md`: deadline 0.05 s, deadline 0.5 s, offered load 1.1, and reference SNR +3 dB. Holdout seeds are 20261201--20261220 and were not used for selection.

Primary endpoint: paired candidate-minus-Reactive goodput difference in each regime.

Inference: 100,000 paired percentile bootstrap replicates, 95% CI for the mean paired difference, two-sided paired Wilcoxon signed-rank test, Holm correction across the four primary comparisons, paired Cohen dz, and win/loss/tie fractions. Practical margin is +/-0.001 Mbps. HELP requires the lower CI bound > +0.001 Mbps; HURT requires the upper CI bound < -0.001 Mbps; otherwise the result is NEUTRAL_OR_UNCERTAIN.

## Secondary outcomes

PDR, deadline/censoring outcomes, P50/P95/P99 latency, queue at disconnect, urgent/bulk PDR, demand-normalized Jain fairness, scheduled SNR/BER/PER, outage, and link-lifetime diagnostics are secondary unless separately preregistered. They are interpreted as mechanism/trade-off evidence and are not promoted to undeclared primary hypotheses.

## Mechanism and robustness evidence

The publication may report the existing one-axis-at-a-time diagnostics over offered load, forecast horizon, slot duration, receiver count, traffic model/class, packet size, deadline, reference SNR, field of view, outage definition, and sensing assumptions. These analyses identify operating regions and failure modes; unless covered by a frozen confirmatory protocol, they remain diagnostic/exploratory.

Required ablations distinguish: future prediction, link prediction/forecast use, link-lifetime urgency, current-service guard, fairness term, horizon, sensing/predictor degradation, and Oracle information. Negative and null results must be retained.

## Claim boundary

The optical link is a PC-FMCW/DPSK-informed analytical/simulation model. The Part-A physical-layer parameters and upstream notebook provenance are frozen in `configs/part_a_physical_layer.json`. Geometry-to-gain, reference-SNR normalization, pointing/FoV, packetization, traffic, and scheduling assumptions introduced in this repository are modeling assumptions unless independently calibrated. No simulated optical-channel quantity is a physical measurement. No real-world autonomous or vehicular deployment validation is claimed.

## Paper-1 / Paper-2 boundary

Paper 1 does not depend on incomplete GRU/WOMD learned-model claims. Learned communication-aware training and its 20-checkpoint study belong to Paper 2. Paper 1 may mention learned prediction only as future/parallel work, not as evidence for its primary claim.

## Canonical evidence rule

No numerical claim may be promoted to final publication evidence unless it is traceable to a frozen artifact/manifest or an explicitly labeled executed diagnostic. Existing prospectively selected synthetic holdout evidence is admissible with that exact label. Missing external-data experiments must be reported as missing rather than imputed or invented.
