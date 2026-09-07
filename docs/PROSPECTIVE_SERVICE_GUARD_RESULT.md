# Prospective Current-Service Guard Result

**Scope:** PAPER1  
**Evidence tier:** EXECUTED_DIAGNOSTIC / prospectively selected synthetic holdout  
**Workflow run:** `34055071988`  
**Head SHA:** `769d461aa09d4a9d7af8d47c9536d6e2d5c08b30`  
**Artifact ID:** `9995724323`  
**Artifact name:** `prospective-current-service-guard`  
**Artifact digest:** `sha256:041e93b097a21924fe3d7b37e4eeb6aaf8d54e1e2ff55f97f419bd81dac758df`

## Frozen protocol

The prospective protocol selected a current-service guard using fresh development seeds `20261101`-`20261110` and evaluated the frozen selected policy once on disjoint holdout seeds `20261201`-`20261220`.

The candidate family was `service_guarded_00`, `service_guarded_80`, `service_guarded_90`, `service_guarded_95`, and `service_guarded_100`, all with fairness weight fixed to zero. Eligibility required mean paired candidate-minus-Reactive goodput >= -0.001 Mbps in every development regime. Among eligible candidates, the frozen objective maximized the worst development-regime mean goodput gain, with P95 latency and then smaller guard ratio as tie-breaks.

The four predeclared regimes were:

- deadline = 0.05 s;
- deadline = 0.5 s;
- offered load = 1.1;
- SNR offset = +3 dB.

No holdout value was used in policy selection.

## Development selection

The frozen development rule selected `service_guarded_80` (`guard_ratio = 0.8`). Its mean paired goodput gains on development were:

| Regime | Candidate - Reactive goodput (Mbps) |
|---|---:|
| deadline 0.05 s | +0.0428 |
| deadline 0.5 s | +0.0598 |
| load 1.1 | +0.0107 |
| SNR +3 dB | +0.0190 |

The selected candidate's worst development-regime gain was +0.0107 Mbps. The candidate was then frozen before the holdout evaluation.

## Precommitted holdout analysis

Primary endpoint: paired candidate-minus-Reactive goodput difference within each predeclared regime, using 20 paired holdout seeds per regime.

The analysis protocol is:

- 100,000 paired percentile bootstrap replicates;
- 95% confidence interval for the mean paired difference;
- bootstrap RNG seed `20260906`;
- practical margin +/-0.001 Mbps;
- HELP if the CI lower bound is > +0.001 Mbps;
- HURT if the CI upper bound is < -0.001 Mbps;
- otherwise NEUTRAL_OR_UNCERTAIN;
- two-sided paired Wilcoxon signed-rank test;
- Holm adjustment across the four predeclared primary regime comparisons;
- paired Cohen dz and win/loss/tie fractions.

The reproducible analysis implementation is `scripts/14_analyze_service_guard_holdout.py`.

## Holdout primary results

| Regime | Mean delta goodput (Mbps) | 95% paired bootstrap CI | Classification | Wilcoxon p | Holm p | Cohen dz | Win / Loss / Tie |
|---|---:|---:|---|---:|---:|---:|---:|
| deadline 0.05 s | +0.03730 | [0.02195, 0.05365] | HELP | 0.000625 | 0.001875 | 1.000 | 0.80 / 0.15 / 0.05 |
| deadline 0.5 s | +0.05680 | [0.04015, 0.07530] | HELP | 0.000132 | 0.000527 | 1.384 | 0.95 / 0.00 / 0.05 |
| load 1.1 | +0.00860 | [-0.00230, 0.02050] | NEUTRAL_OR_UNCERTAIN | 0.295869 | 0.295869 | 0.322 | 0.50 / 0.40 / 0.10 |
| SNR +3 dB | +0.01915 | [0.00790, 0.03120] | HELP | 0.009977 | 0.019954 | 0.706 | 0.75 / 0.25 / 0.00 |

The three HELP classifications survive the frozen practical-margin rule. The high-load regime does not: its confidence interval includes both a small negative effect and a positive effect, so it remains NEUTRAL_OR_UNCERTAIN.

## Secondary descriptive outcomes

These are secondary/descriptive and must not be promoted into undeclared primary hypotheses.

| Regime | Mean delta PDR [95% CI] | Mean delta fairness [95% CI] | Mean delta P95 latency ms [95% CI] |
|---|---:|---:|---:|
| deadline 0.05 s | +0.01058 [0.00626, 0.01521] | +0.01571 [0.00312, 0.02878] | 0 [0, 0] |
| deadline 0.5 s | +0.01599 [0.01134, 0.02108] | +0.04777 [0.02458, 0.07431] | +10 [-10, 30] |
| load 1.1 | +0.00159 [-0.00045, 0.00382] | +0.01526 [-0.00101, 0.03985] | +50 [20, 85] |
| SNR +3 dB | +0.00542 [0.00225, 0.00877] | +0.02288 [0.01023, 0.03787] | +14.5 [-10.5, 40] |

The high-load regime therefore remains an important limitation: the guard removed the earlier clear throughput harm, but the held-out goodput effect is uncertain and P95 latency is descriptively worse by about 50 ms with a bootstrap interval entirely above zero.

## Scientific interpretation

This prospective synthetic holdout supports a narrow mechanism claim:

> A current-service opportunity constraint can preserve predictive packet-level gains in several operating regimes while reducing the congestion-induced throughput harm observed in less constrained predictive scheduling.

It does **not** support universal superiority. In particular, the high-load regime is not classified as HELP and retains a latency cost. The result is consistent with the previously identified service-order mechanism: future urgency can become harmful when it causes a scheduler to sacrifice too much immediate service efficiency, especially under capacity pressure.

## What may be claimed

Permitted wording:

> In a prospectively selected synthetic holdout, a 0.8 current-service guard produced statistically supported goodput gains in three of four predeclared regimes. Under high load, the goodput effect remained uncertain and P95 latency worsened, so the method is not uniformly beneficial.

Not permitted:

- "predictive scheduling always improves performance";
- "the current-service guard solves congestion";
- "the guard is optimal";
- any real-world or measured-channel validation claim;
- treating the synthetic holdout as canonical WOMD evidence.

## Remaining publication work

This result closes the precommitted statistical analysis for this prospective diagnostic, but Paper 1 still requires final publication-level protocol freezing, anomaly resolution, mechanism closure on the publication population, final artifact generation, figures/tables, and manuscript/reproduction audit before submission.
