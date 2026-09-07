# Legacy Umbrella Draft — Superseded for Paper 1

> **Status notice (2026-09-07):** This file is retained only as historical/diagnostic context. It is **not** the authoritative Paper-1 manuscript and its older numerical narrative must not be used as the current Paper-1 conclusion.
>
> The authoritative Paper-1 manuscript is `paper/paper1/manuscript/PAPER1_FINAL_DRAFT.md`.
> The frozen Paper-1 protocol is `configs/paper1_final_protocol.json`.
> The publication-facing evidence package is `artifacts/paper1_final/`.
> The completion audit is `paper/paper1/PAPER1_COMPLETION_AUDIT.md`.
>
> Paper 2 is a separate learned communication-aware prediction study and remains incomplete. Do not interpret references below to missing learned/WOMD evidence as blockers for the closed university Part-B Paper-1 scope.

## Historical manuscript snapshot

The content that previously occupied this path described an earlier combined Paper-1/Paper-2 research draft, including controlled diagnostics, a compact WOMD proxy, the five-seed staged study, urgent/bulk failure modes, and pending learned/WOMD work. That combined framing became stale after the repository adopted an explicit Paper-1/Paper-2 split and completed the prospective current-service-guard holdout for Paper 1.

For reproducibility, the historical version remains recoverable from Git history (for example, from the parent of the Paper-1 final-status reconciliation commit). It is intentionally not duplicated here because maintaining two active manuscript narratives risks stale or contradictory scientific claims.

## Current Paper-1 conclusion

The current Paper-1 evidence supports a conditional conclusion rather than universal predictive superiority. A prospectively selected current-service guard with ratio 0.8 was evaluated against Reactive Greedy on 20 disjoint paired synthetic holdout seeds in four predeclared regimes. The frozen analysis classifies deadline 0.05 s, deadline 0.5 s, and SNR offset +3 dB as HELP, while offered load 1.1 remains NEUTRAL_OR_UNCERTAIN and has a descriptive P95-latency penalty.

This is model-based synthetic evidence. It is not measured optical-channel evidence, real-road validation, or WOMD validation. Exact statistics and provenance are frozen in `artifacts/paper1_final/primary_statistics.json` and `artifacts/paper1_final/publication_manifest.json`.

## Current Paper-2 boundary

Learned GRU objectives, the complete 20-checkpoint archive, untouched held-out/OOD learned evaluation, learned scheduling, and associated communication-aware objective claims belong to Paper 2. They remain outside the completed Paper-1 claim.
