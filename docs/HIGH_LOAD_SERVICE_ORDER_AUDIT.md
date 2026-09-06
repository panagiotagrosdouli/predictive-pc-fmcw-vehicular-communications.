# High-Load Service-Order Mechanism Audit

Status: **EXECUTED / DIAGNOSTIC / DEVELOPMENT-ONLY**

This note records a mechanism audit performed only on the already-used development population. No holdout seed from the failed prospective fairness-selection protocol was inspected.

## Provenance

- Workflow: `High-load service-order audit`
- Workflow run: `34054732357`
- Head SHA: `9849c0aca52cf4704f1f6feb27ed30bc3ab5dfd3`
- Conclusion: `success`
- Artifact: `high-load-service-order-audit`
- Artifact ID: `9995613936`
- Artifact digest: `sha256:a90b374175f5f3a3eb5a2e4edc50d80489d6d7837946da6d79cc519086560f16`
- Development seeds: `20260901`–`20260910`
- Predictive policy: `deadline_aware_lifetime`
- Fairness weight: `0.0`
- Comparator: `reactive_greedy`
- Holdout inspected: **false**

The audit reproduces the prospective development outcomes for the zero-fairness candidate: mean predictive-minus-reactive goodput is `-0.0409 Mbps` at offered load `1.1`, while it is `+0.1419 Mbps` at deadline `0.5 s`.

## Disagreement-conditioned evidence

The audit replays the matched synthetic scenario and traffic trace and records scheduler state only on slots where Reactive and the zero-fairness predictive policy both act but choose different receivers.

| quantity, predictive minus reactive | load 1.1 | deadline 0.5 s |
|---|---:|---:|
| disagreement slots | 699 | 733 |
| mean queue packets at chosen receiver | +10.906 | +0.464 |
| mean HOL deadline slack, steps | -1.319 | -0.920 |
| mean actual SNR, dB | -0.135 | -0.042 |
| mean current link goodput, Mbps | -5.732 | -3.699 |
| mean expected immediate successful packets | -0.725 | -0.170 |
| mean realized successful packets in the slot | -0.783 | -0.160 |

At high load, the predictive scheduler therefore tends to choose a receiver with a substantially larger backlog and a more urgent head-of-line packet, while sacrificing immediate service opportunity on average. In the subset where the predictive choice has more urgent HOL slack than the Reactive choice, the mean expected immediate-service difference is about `-2.47 packets/slot` at load `1.1`. When the predictive choice is less urgent, the corresponding mean is about `+1.43 packets/slot`.

The same urgency-versus-immediate-service tension exists at deadline `0.5 s`, but packet-level goodput is positive there. This is important: urgency-driven service reordering is not intrinsically wrong. Its value depends on whether saved deadline utility compensates for the immediate capacity sacrificed. Under congestion, the current scheduler crosses that balance in the harmful direction.

## Mechanism interpretation

The prospective failure cannot be explained by fairness pressure, because the audited candidate uses fairness weight zero. It also cannot be reduced to selecting unusable links: prior diagnostics showed chosen realized outage near zero. The present evidence instead supports a narrower mechanism hypothesis:

> Under congestion, the predictive utility over-prioritizes backlog/HOL urgency relative to immediate service efficiency. It can spend scarce service opportunities on more urgent or larger queues even when those choices deliver fewer packets immediately; when the system is already capacity-limited, the lost instantaneous service is not recovered later.

This interpretation remains diagnostic. It is not a proof of causality and is not canonical publication evidence.

## Next hypothesis

The next scheduler family should add an explicit **current-service guardrail** rather than another fairness retuning. Predictive reordering should be allowed only when the selected receiver's current service opportunity is not too far below the best current-service alternative. The guardrail strength must be selected on a new development population and evaluated once on a fresh holdout population; the untouched holdout from the failed fairness family must not be repurposed for tuning.
