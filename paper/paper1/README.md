# Paper 1 — Mechanism / Operating-Region Study

**Scope label:** `PAPER1`

**Working title:** *When Does Trajectory Prediction Help PC-FMCW/DPSK Vehicular Optical Scheduling?*

This directory is the publication-facing workspace for Paper 1. Reusable implementation stays under `src/predictive_pc_fmcw/`; this directory must contain only manuscript-facing material, figure/table build inputs, scope-specific manifests, and documentation.

## Research question

When does causal future-motion/link information have real packet-level scheduling value, when does it become neutral or harmful, and why?

## Current evidence boundary

The strongest current evidence is synthetic and includes operating-region diagnostics, decision/mechanism audits, and a prospectively selected current-service guard evaluated on a disjoint synthetic holdout. The current-service-guard holdout result is documented in `docs/PROSPECTIVE_SERVICE_GUARD_RESULT.md`.

This workspace must not import incomplete Paper-2 GRU/WOMD claims as Paper-1 evidence.

## Required subdirectories

Publication generators may create:

```text
paper/paper1/
├── manuscript/
├── figures/
├── tables/
└── manifests/
```

Generated scientific numbers must come from frozen artifacts under `artifacts/paper1_final/`; no manually entered result is considered canonical evidence.

## Submission gate

Paper 1 remains not submission-ready until the final protocol is frozen, anomaly audits close, final canonical runs/statistics are complete, figures/tables are generated from provenance-tracked artifacts, and the manuscript passes a claim-to-artifact audit.
