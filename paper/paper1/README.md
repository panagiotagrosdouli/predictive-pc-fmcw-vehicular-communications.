# Paper 1 — Mechanism / Operating-Region Study

**Scope label:** `PAPER1`

**Title:** *When Does Trajectory Prediction Help PC-FMCW/DPSK Vehicular Optical Scheduling?*

Paper 1 is the self-contained classical/mechanism Part-B study. Reusable implementation remains under `src/predictive_pc_fmcw/`; this directory contains publication-facing protocol and manuscript material.

## Research question

When does causal future-motion/link information have real packet-level scheduling value, when does it become neutral or harmful, and why?

## Proposed method

The Paper-1 method is predictive communication-aware scheduling with a prospectively selected **current-service guard**. Future link urgency may reorder service only while preserving a specified fraction of the current modeled service opportunity. The frozen selected guard ratio is 0.8.

This design directly addresses the diagnosed failure mode in which unconstrained future-link urgency sacrifices too much immediate service efficiency under congestion.

## Evidence boundary

The strongest confirmatory evidence currently available is a prospectively selected synthetic holdout with 20 disjoint seeds per predeclared regime. It is documented in `docs/PROSPECTIVE_SERVICE_GUARD_RESULT.md` and summarized in `manuscript/PAPER1_FINAL_DRAFT.md`.

The result is conditional rather than universal: the guarded predictive policy is classified HELP in three of four predeclared regimes; the high-load regime is NEUTRAL_OR_UNCERTAIN and retains a descriptive P95-latency cost.

The optical channel is model-based. No measured optical-link or real-world vehicular validation is claimed.

## Frozen protocol

`manifests/PAPER1_FINAL_PROTOCOL.md` defines the final research question, causal/fairness constraints, independent experimental unit, confirmatory comparison, statistical procedure, robustness interpretation, claim boundary, and Paper-1/Paper-2 separation.

## Manuscript

`manuscript/PAPER1_FINAL_DRAFT.md` is the publication-facing Paper-1 draft. Numerical claims are limited to already executed, provenance-documented evidence. Missing external-data evidence is not invented.

## Paper-2 boundary

Incomplete GRU/WOMD learned-model claims are excluded from Paper 1. The four-objective, five-seed learned study belongs to Paper 2 and is not required for the university Part-B Paper-1 contribution.

## Reproducibility rule

Canonical publication artifacts, when promoted, belong under `artifacts/paper1_final/`. Diagnostic evidence must retain its diagnostic/holdout label and provenance. Individual time samples must never be treated as independent statistical observations when the independent unit is an episode/scenario seed.

## Completion status

The **Paper-1 scientific narrative and frozen protocol are complete on the `complete-paper1` branch using the currently executed evidence**. A stronger external-data publication claim remains contingent on additional canonical datasets/runs. Therefore this branch is suitable for a defensible university Part B based on model-based synthetic evidence, but it must not be represented as measured-channel or real-world validation.
