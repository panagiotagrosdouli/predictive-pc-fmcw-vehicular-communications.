# Publication Status — Dataset-Free Synthetic Study

## Overall status

**NOT PAPER READY**

This repository contains the dataset-free simulation protocol and execution infrastructure, but publication readiness still requires quantitative completion of the frozen experiments. Code existence or CI success is not scientific evidence.

## Completed infrastructure

- Deterministic, seeded synthetic mobility generator with 11 scenario families.
- Configured minimum-separation safeguard using one constant lateral translation when a generated trajectory violates the controlled clearance assumption; this preserves velocity/acceleration smoothness but remains a simulation assumption rather than a real-traffic claim.
- Scenario-level train/development/held-out/OOD partitions with zero-overlap validation and explicit harder-than-training OOD mobility checks.
- Causal noisy range/radial-velocity/bearing observations; predictor histories are truncated at the current step and cannot contain future truth.
- Ground-truth x/y, velocity, acceleration, speed, heading, range, radial velocity, and bearing.
- Frozen link-model mapping from motion state to SNR, BER, PER, outage, effective rate/goodput, and link lifetime.
- Separate actual-channel and forecast-channel configurations for controlled channel-mismatch experiments; robustness perturbations do not rewrite the realized channel trace.
- Deterministic packet traffic with arrivals, deadlines, expiration, retransmissions, delivery, latency, queue state, and goodput accounting.
- B0–B4 classical predictor evaluation and development future-link evaluation through the same link model.
- Leakage-safe train/development export for learned models.
- Frozen learned-objective plan: 4 objectives × 5 canonical seeds = exactly 20 runs.
- Resume/checkpoint validation and a fail-closed publication freeze gate requiring all 20 verified checkpoints.
- Development-only checkpoint selection for the trajectory-only and full communication-aware scheduler models; held-out/OOD data are excluded from selection.
- Frozen packet-scheduling protocol S0–S7 with exactly five paired traffic seeds. S7 Oracle is evaluator-only.
- Multi-vehicle scenario/episode construction with disjoint source trajectories and paired traffic traces reused across schedulers.
- Freeze-gated held-out/OOD scheduling evaluation with S0–S7, including the selected learned checkpoints and evaluator-only oracle.
- Scenario/episode-level scheduling statistics with traffic-seed averaging within episode, bootstrap confidence intervals, paired tests/effect sizes, and Holm multiplicity correction for predeclared primary comparisons.
- Robustness protocol covering observation-noise scaling, forecast-channel mismatch, forecast-SNR bias, atmospheric-attenuation mismatch, and separate OOD evaluation.
- Operating-region sweep infrastructure over forecast horizon, channel difficulty, offered load/deadline tightness, and mobility-difficulty axes.
- Official held-out/OOD learned-model evaluator that evaluates all 4 objectives × 5 seeds after the publication freeze and performs no official-split model selection.
- Freeze-gated held-out and OOD official window exporters with no-silent-overwrite behavior and embedded freeze provenance hashes.
- Publication-artifact contract for exactly Figures 1–10 and Tables I–VIII. Each artifact is READY/BLOCKED based only on saved inputs, with SHA-256 provenance; missing official evidence cannot be replaced by placeholders or manual values.

## Experiments not yet completed

- 20 verified learned-model checkpoints: **NOT YET EXECUTED/VERIFIED AS A COMPLETE SET**.
- Frozen held-out trajectory and communication-aware learned evaluation: **BLOCKED BY TRAINING FREEZE**.
- OOD learned evaluation: **BLOCKED BY TRAINING FREEZE**.
- Packet-level scheduler comparison S0–S7 across the frozen five paired traffic seeds: **NOT YET COMPLETED**.
- Operating-region sweeps and heatmap analysis: **NOT YET COMPLETED**.
- Observation/channel-model robustness sweeps: **NOT YET COMPLETED**.
- Objective A/B/C/D quantitative ablation on official splits: **BLOCKED BY TRAINING**.
- Scenario/episode-level paired statistical report on official scheduling outputs: **NOT YET COMPLETED**.
- Publication Figures 1–10 and Tables I–VIII from frozen saved artifacts: **BLOCKED UNTIL THEIR REQUIRED INPUT ARTIFACTS EXIST**.

## Primary numerical results

None are claimed yet. Development artifacts are diagnostic/model-selection outputs and must not be presented as final held-out evidence.

## Executed corrected-scheduler diagnostics — noncanonical

The packet-aware lifetime-urgency correction has now passed repository CI and a dedicated diagnostic workflow. These executions are **EXECUTED/DIAGNOSTIC**, synthetic, and noncanonical; they do not satisfy Stage 6 or the publication freeze.

At the default 12-episode synthetic reference condition, corrected Link-Lifetime versus Reactive shows only a small aggregate-goodput difference (+0.0141 Mbps; paired bootstrap interval crosses zero), a small PDR increase, and a small reduction in deadline misses. In contrast, P95 latency is worse by about 266 ms and this tail-latency penalty is consistent across the paired episodes, while demand-normalized Jain fairness improves by about 0.028. Predictive Utility and Oracle show nearly the same latency/fairness trade-off, so the observed tail-latency cost is not attributable solely to the lifetime-urgency term.

The corrected paper-ablation diagnostic further shows that removing the fairness term raises aggregate goodput and materially reduces P95 latency relative to the predictive policies, while reducing fairness. This is mechanism evidence for an objective trade-off rather than evidence that prediction is intrinsically harmful. The same diagnostic also shows large sensitivity to the channel/BER modeling choice, so scheduler conclusions must not be inferred from cross-channel comparisons.

The quick operating-region matrix uses only two independent seeds and is therefore descriptive only. Its current Link-Lifetime aggregate goodput difference versus Reactive is approximately neutral at offered load 0.35 and negative on average at offered load 0.55. No inferential HELP/HURT claim is permitted from this quick matrix.

A decision-level diagnostic has also been added to measure how often Link-Lifetime actually changes the selected receiver relative to Predictive Utility, and how often Oracle information changes decisions relative to Link-Lifetime. Those outputs are mechanism diagnostics only and must remain separate from official publication evidence.

## Hypothesis status

**UNEVALUATED.** No PASS/FAIL/MIXED conclusion is permitted until the frozen held-out, OOD, scheduling, robustness/operating-region, and statistical pipeline has completed. Negative or mixed results must remain visible.

## Limitations

The study is a controlled synthetic simulation and is not real-world deployment validation. Observation-noise values and the minimum-separation correction policy are controlled assumptions that require sensitivity analysis; they are not inferred from Part 1 performance. Oracle information is evaluator-only and must never enter deployable decisions. The current learned/scheduler position interface reconstructs causal XY from observed range/bearing; radial-velocity observations are generated and retained but are not yet used directly by that learned position interface. Any paper claim must describe this limitation explicitly.

## Exact execution path

```bash
make synthetic-pipeline
make synthetic-ablation
make synthetic-freeze
make synthetic-select-checkpoints
make synthetic-heldout
make synthetic-ood
make synthetic-learned-heldout
make synthetic-learned-ood
make synthetic-scheduling-protocol
make synthetic-scheduling-heldout
make synthetic-scheduling-ood
make synthetic-stats-heldout
make synthetic-stats-ood
make synthetic-robustness-heldout
make synthetic-robustness-ood
make synthetic-operating-heldout
make synthetic-operating-ood
make synthetic-publication-manifest
```

`synthetic-pipeline` prepares and validates the canonical Synthetic Dataset v1 protocol plus development artifacts. `synthetic-ablation` performs the frozen 20-run learned ablation and requires an ML-capable environment. `synthetic-freeze` refuses publication evaluation unless all 20 objective/seed checkpoints validate against the frozen training artifact. Checkpoint selection is development-only. Only after the freeze passes can official held-out/OOD windows, learned evaluation, scheduling, robustness, operating-region outputs, statistics, and publication-artifact readiness be completed.

## Completion rule

Do not change this status to paper-ready merely because scripts execute or CI is green. Paper readiness requires the complete verified 20-checkpoint set, untouched frozen held-out/OOD quantitative outputs, paired scheduling evidence, robustness and operating-region results, confidence intervals/effect sizes with the declared inferential unit, all required figures/tables generated from saved artifacts, preserved failed/negative experiments, and a clean reproduction run. Hypothesis PASS requires quantitative evidence; absence of evidence is never PASS.
