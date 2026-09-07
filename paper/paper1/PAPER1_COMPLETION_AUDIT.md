# Paper 1 Completion Audit

**Scope:** PAPER1 — mechanism / operating-region study  
**Repository:** `panagiotagrosdouli/predictive-pc-fmcw-vehicular-communications.`  
**Evidence boundary:** model-based PC-FMCW/DPSK-informed simulation; no measured optical-link or real-world vehicular validation claim.

## 1. What existed before final closure

The repository already contained the scientific implementation needed for a strong Part-B mechanism study: a causal trajectory-to-link-to-packet pipeline; classical predictors; reactive and predictive scheduling policies; an evaluator-only Oracle; packet queues, deadlines, retries and packet-level KPIs; operating-region and robustness infrastructure; paired statistical analysis; Part-A provenance; extensive scientific tests; and a manuscript/roadmap that explicitly preserved negative and null findings.

The strongest already executed Paper-1 evidence was the prospectively selected current-service-guard study on a disjoint synthetic holdout. Its policy-selection and holdout protocol were frozen before holdout evaluation.

## 2. What was changed during Paper-1 closure

Paper 1 was separated cleanly from incomplete Paper-2 learned-model claims. A frozen Paper-1 scientific protocol was added, together with a publication-facing final draft and an updated Paper-1 README. The proposed method is now stated precisely as predictive communication-aware scheduling with a prospectively selected current-service guard that limits predictive reordering when it sacrifices excessive immediate service opportunity.

No numerical result, external-data result, learned checkpoint, or optical measurement was invented.

## 3. What was actually executed

The confirmatory evidence used in Paper 1 was already executed and provenance documented. The frozen `service_guarded_80` policy was selected using development seeds `20261101`--`20261110`, then evaluated once on disjoint holdout seeds `20261201`--`20261220` in four predeclared regimes. The primary endpoint was paired candidate-minus-Reactive goodput. Analysis used 100,000 paired bootstrap replicates, a 95% CI, paired Wilcoxon signed-rank tests, Holm correction across the four primary comparisons, paired Cohen dz and win/loss/tie fractions.

After the Paper-1 protocol/manuscript merge, repository CI also executed successfully on `main` at commit `e89c3df56f73e876ecbc8a2a4c5322903aacc6d9` (workflow run `34118112069`). The CI workflow covers editable installation, Ruff, pytest, stage-entrypoint checks and `pcfmcw validate`.

## 4. Strongest positive result

The strongest confirmatory gain is the 0.5 s deadline regime:

- mean paired goodput gain: **+0.05680 Mbps**;
- 95% paired bootstrap CI: **[+0.04015, +0.07530] Mbps**;
- Holm-adjusted p: **0.000527**;
- paired Cohen dz: **1.384**;
- classification: **HELP**.

Two additional predeclared regimes are also classified HELP: deadline 0.05 s and reference SNR +3 dB.

## 5. Strongest negative/null result

Under offered load 1.1, the primary goodput effect is **NEUTRAL_OR_UNCERTAIN**:

- mean paired goodput gain: **+0.00860 Mbps**;
- 95% paired bootstrap CI: **[-0.00230, +0.02050] Mbps**;
- Holm-adjusted p: **0.295869**;
- paired Cohen dz: **0.322**.

The same high-load regime has a descriptive P95-latency penalty of about **+50 ms**, with bootstrap interval **[+20, +85] ms**. This prevents a universal superiority claim and is retained as a central limitation/failure regime.

Earlier unconstrained predictive diagnostics also showed that prediction can become harmful under congestion and urgent/bulk traffic. Those diagnostics are mechanism evidence, not silently promoted confirmatory hypotheses.

## 6. Statistical significance and effect sizes

Three of four predeclared confirmatory holdout regimes satisfy the frozen practical HELP rule and survive Holm-adjusted paired testing. The high-load regime does not. The independent statistical unit is the paired episode/seed, not packet or time samples. Secondary endpoints remain secondary/descriptive unless separately preregistered.

## 7. Why prediction helps — and why it can fail

The evidence supports a conditional mechanism. Future geometry/link information is useful when it changes service order before a communication-relevant boundary and when the cost of that reordering is controlled. Prediction can fail when future link urgency conflicts with packet urgency or with a strong current service opportunity. The current-service guard targets that service-order failure mode; it does not solve congestion universally and is not claimed optimal.

## 8. Remaining limitations

The optical channel is model-based and uses declared geometry/reference-SNR/pointing/FoV assumptions. The Part-A waveform parameters and receiver provenance provide physical-layer context but do not constitute measured end-to-end vehicular optical calibration. The confirmatory Paper-1 holdout is synthetic. There is no real-road deployment, hardware-in-the-loop experiment, or measured vehicular optical-channel validation. The 0.8 guard is selected for the frozen study, not claimed globally optimal. Learned GRU/WOMD evidence is excluded and remains Paper 2 work.

## 9. Readiness for university Part B

**READY, with an explicit simulation/model claim boundary.**

Paper 1 satisfies the Part-B requirement to propose and evaluate a technique intended to improve system performance. The contribution goes beyond an idea or simple plot: it includes an implemented predictive scheduling method, causal/fair baseline comparisons, a prospectively selected refinement, paired holdout evaluation, confidence intervals, hypothesis tests, effect sizes, multiple-comparison correction, negative/null findings, mechanism analysis, robustness infrastructure, provenance and reproducibility controls.

The defensible Part-B conclusion is not that prediction always improves the system. It is:

> Predictive communication-aware scheduling can improve modeled packet-level performance in specific operating regimes when future link information is actionable and immediate service opportunity is protected; under high load the benefit is uncertain and latency can worsen.

## 10. Readiness for actual publication

**STRONG MINI-PAPER / PRE-PUBLICATION QUALITY, but not equivalent to externally validated publication evidence.**

The methodology, causality, statistics, negative-result handling and provenance are publication-style. A stronger journal/conference claim would benefit from independent real-motion external validation and/or measured/calibrated optical-channel evidence. Paper 2 would additionally require the complete frozen learned-model pipeline and its 20 verified checkpoints.

## Final status

Paper 1 is scientifically closed for the university Part-B scope using the evidence that has actually been executed. Any future extension must preserve the existing evidence labels and must not retroactively convert diagnostic or synthetic outputs into physical measurements.
