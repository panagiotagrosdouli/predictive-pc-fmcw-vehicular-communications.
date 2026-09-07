# Publication Status — Paper 1 / Paper 2

## Overall status

This repository now contains two deliberately separated scientific scopes. A single global `NOT PAPER READY` label is no longer accurate.

### Paper 1 — classical predictive scheduling / university Part B

**STATUS: SCIENTIFICALLY CLOSED FOR UNIVERSITY PART B, WITH AN EXPLICIT MODEL-BASED SYNTHETIC CLAIM BOUNDARY.**

Paper 1 asks when causal future geometry/link information improves packet scheduling for the modeled PC-FMCW/DPSK vehicular optical link. Its final manuscript is `paper/paper1/manuscript/PAPER1_FINAL_DRAFT.md`; its frozen protocol is `configs/paper1_final_protocol.json`; its completion audit is `paper/paper1/PAPER1_COMPLETION_AUDIT.md`; and its publication-facing evidence package is `artifacts/paper1_final/`.

The proposed refinement is a predictive scheduler with a prospectively selected current-service guard. The frozen selected policy is `service_guarded_80` (`guard_ratio = 0.8`) versus Reactive Greedy. Selection used development seeds 20261101–20261110 only. Confirmatory evaluation used 20 disjoint paired holdout seeds 20261201–20261220 in four predeclared regimes, with 100,000 paired bootstrap replicates, two-sided paired Wilcoxon tests, Holm correction across the four primary comparisons, paired Cohen dz, and a practical HELP/HURT margin of ±0.001 Mbps.

The confirmatory synthetic holdout gives HELP in three regimes: deadline 0.05 s (+0.03730 Mbps, 95% CI [0.02195, 0.05365], Holm p=0.001875, dz=1.000), deadline 0.5 s (+0.05680 Mbps, [0.04015, 0.07530], Holm p=0.000527, dz=1.384), and SNR offset +3 dB (+0.01915 Mbps, [0.00790, 0.03120], Holm p=0.019954, dz=0.706). Offered load 1.1 remains NEUTRAL_OR_UNCERTAIN (+0.00860 Mbps, [-0.00230, 0.02050], Holm p=0.295869, dz=0.322) and has a descriptive +50 ms P95-latency difference with 95% CI [20, 85] ms.

Therefore the supported Paper-1 conclusion is conditional: predictive communication-aware scheduling can improve modeled packet-level performance when future link information is actionable and immediate service opportunity is protected, but it is not uniformly beneficial and latency can worsen under high load.

Paper 1 is suitable as a defensible university Part-B study. It is also a strong mini-paper/pre-publication package, but it is **not** equivalent to externally validated journal/conference evidence. The optical channel remains model-based; no measured end-to-end optical channel, real-road deployment, or real-world vehicular validation is claimed. The prospective holdout retains its original evidence label `EXECUTED_DIAGNOSTIC / prospectively selected synthetic holdout`; freezing its statistics does not relabel it as WOMD or measured evidence.

### Paper 2 — learned communication-aware prediction

**STATUS: INCOMPLETE / NOT PAPER READY.**

Paper 2 contains the heavier learned extension. Publication readiness still requires the complete frozen 4-objective × 5-independent-seed GRU archive (20 verified checkpoints), untouched held-out/OOD learned evaluation, learned-predictor scheduling evaluation, communication-aware objective ablations and predictor-to-communication joins, robustness/operating-region evidence as required by its protocol, final paired statistics, and its own publication figures/tables/manifests. Paper-1 evidence must not be used to imply that these learned claims have been executed.

## Shared completed infrastructure

The repository contains deterministic synthetic mobility generation, causal observation histories, leakage-safe scenario splits, classical Last-Position/CV/CA/Kalman/IMM prediction, future geometry/link translation, a PC-FMCW/DPSK-informed link abstraction, packet queues/deadlines/retransmissions, broad reactive and predictive scheduler families, evaluator-only Oracle information, paired traffic randomness, robustness/operating-region infrastructure, learned-objective/checkpoint validation machinery, and extensive regression/scientific-gate tests.

The Part-A physical-layer provenance is frozen in `configs/part_a_physical_layer.json`. The local communication study uses a reference-SNR/model abstraction rather than claiming a calibrated absolute optical power budget. The canonical Stage-2 receiver evidence is retained under `artifacts/paper_final/02_link/` and the resolved FFT alias-branch receiver verification is referenced by the Paper-1 manifest.

## Paper-1 evidence provenance

The prospectively selected service-guard result is traceable to workflow run 34055071988, head SHA `769d461aa09d4a9d7af8d47c9536d6e2d5c08b30`, artifact ID 9995724323, artifact name `prospective-current-service-guard`, and digest `sha256:041e93b097a21924fe3d7b37e4eeb6aaf8d54e1e2ff55f97f419bd81dac758df`. Its compact statistics and provenance are versioned in `artifacts/paper1_final/primary_statistics.json` and `artifacts/paper1_final/publication_manifest.json`.

The Paper-1 publication-evidence freeze was merged at commit `2a407c2a946661fb7e131b1e2ab052dbe0f5ab8e`. Post-merge CI run 34149666617 (#648) completed successfully on that exact `main` commit.

## Negative and null evidence that must remain visible

Paper 1 does not support a universal prediction-gain claim. Earlier controlled diagnostics showed only small aggregate-goodput differences and material tail-latency costs for unconstrained predictive policies. Urgent/bulk diagnostics showed that link-lifetime urgency can serve bulk traffic at the expense of urgent PDR when link urgency and packet urgency conflict. The prospectively selected service guard improves the confirmatory result in three predeclared regimes but does not establish HELP at offered load 1.1, where the goodput interval crosses the practical null region and P95 latency is descriptively worse.

These negative/null findings are part of the scientific result and must not be deleted or hidden in future manuscript revisions.

## Claim boundary

- Future ground truth is permitted only for realized outcomes/evaluation and explicitly labeled Oracle/reference information; deployable schedulers remain causal.
- Simulated/model-derived channel quantities are not measurements.
- The Part-A connection must remain explicit, including which physical-layer quantities are frozen upstream and which geometry/link assumptions are new in Part B.
- The independent inferential unit is the paired scenario/episode seed, not packets or time samples.
- No learned-model claim may be promoted until the Paper-2 freeze requirements are satisfied.
- No external/real-world validation claim may be made from the Paper-1 synthetic holdout.

## Current readiness summary

**University Part B:** READY, provided the report preserves the model/simulation boundary and the conditional conclusion above.

**Paper 1 as an externally validated publication:** PRE-PUBLICATION / LIMITED BY EXTERNAL VALIDATION. The scientific narrative, protocol, confirmatory statistics, provenance package, completion audit and CI are closed, but stronger venue claims would benefit from independent real-motion/external-data validation and/or measured/calibrated optical-channel evidence.

**Paper 2:** NOT PAPER READY. The complete learned experiment archive and official evaluations remain outstanding.

## Reproducibility rule

Code existence or green CI alone is never scientific evidence. Numerical claims must remain traceable to executed artifacts with preserved evidence labels. Future stronger claims require their own frozen protocol, clean execution, raw outputs, statistics, figures/tables and manifest. Negative or mixed results must remain visible.
