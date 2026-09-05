# Publication Status — Dataset-Free Synthetic Study

## Overall status

**NOT PAPER READY**

This repository contains the dataset-free simulation protocol and execution infrastructure, but publication readiness requires quantitative completion of the frozen experiments. Code existence or CI success is not scientific evidence.

## Completed infrastructure

- Deterministic, seeded synthetic mobility generator with 11 scenario families.
- Scenario-level train/development/held-out/OOD partitions with zero-overlap validation.
- Explicit harder-than-training OOD mobility regime validation.
- Causal noisy range/radial-velocity/bearing observation model.
- Ground-truth x/y, velocity, acceleration, speed, heading, range, radial velocity, and bearing.
- Frozen link-model mapping to SNR, BER, PER, outage, goodput, and link lifetime.
- Deterministic traffic traces with packet arrivals and deadlines.
- B0–B4 classical predictor evaluation on development data.
- Development future-link prediction evaluation through the same link model.
- Leakage-safe train/development export for learned models.
- Frozen learned-objective plan: 4 objectives × 5 seeds = 20 runs.
- Resume/checkpoint validation and a fail-closed publication freeze gate.
- Freeze-gated held-out and OOD window exporters; neither can materialize before all 20 checkpoints verify.
- Official exports refuse silent overwrite and retain freeze provenance hashes.

## Experiments not yet completed

- 20 verified learned-model checkpoints: **NOT YET EXECUTED/VERIFIED AS A COMPLETE SET**.
- Frozen held-out trajectory evaluation: **BLOCKED BY TRAINING FREEZE**.
- Frozen held-out link evaluation: **BLOCKED BY TRAINING FREEZE**.
- OOD evaluation: **BLOCKED BY TRAINING FREEZE**.
- Packet-level scheduler comparison S0–S4: **NOT YET COMPLETED**.
- Operating-region sweeps and heatmaps: **NOT YET COMPLETED**.
- Observation/channel-model uncertainty sweeps: **NOT YET COMPLETED**.
- Objective A/B/C/D quantitative ablation: **BLOCKED BY TRAINING**.
- Scenario-level paired statistical inference and multiplicity correction: **NOT YET COMPLETED**.
- Publication Figures 1–10 and Tables I–VIII from frozen artifacts: **NOT YET COMPLETED**.

## Primary numerical results

None are claimed yet. Development artifacts are diagnostic/model-selection outputs and must not be presented as final held-out evidence.

## Hypothesis status

**UNEVALUATED.** No PASS/FAIL/MIXED conclusion is permitted until the frozen held-out, OOD, scheduling, and statistical pipeline has completed. Negative or mixed results must remain visible.

## Limitations

The study is a controlled synthetic simulation. It is not real-world deployment validation. Observation-noise values are controlled assumptions and must be evaluated with robustness sweeps; they are not inferred from the Part 1 ranging result. Oracle information is evaluator-only and must never enter deployable decisions.

## Exact execution path

```bash
make synthetic-pipeline
make synthetic-ablation
make synthetic-freeze
make synthetic-heldout
make synthetic-ood
```

`synthetic-pipeline` prepares and validates the synthetic protocol plus development artifacts. `synthetic-ablation` performs the frozen 20-run learned ablation and requires an ML-capable environment. `synthetic-freeze` refuses publication evaluation unless all 20 objective/seed checkpoints validate against the frozen training artifact. Only after that gate passes can `synthetic-heldout` and `synthetic-ood` materialize official evaluation windows.

## Completion rule

Do not change this status to paper-ready merely because scripts execute or CI is green. Paper readiness requires frozen quantitative outputs, confidence intervals/effect sizes, all required figures/tables generated from saved artifacts, preserved failed/negative experiments, and a clean reproduction run.
