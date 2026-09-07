# Paper 1 Final Artifacts

**Scope:** `PAPER1`

This directory is the publication-facing evidence package for the mechanism/operating-region Paper 1.

## Frozen package contents

- `primary_statistics.json` — compact machine-readable record of the already executed prospectively selected synthetic holdout, including the original workflow run, head SHA, Actions artifact ID/digest, statistical unit, frozen analysis settings, all four primary regime outcomes, effect sizes, and secondary descriptive outcomes.
- `publication_manifest.json` — provenance map connecting the Paper-1 protocol/manuscript to the confirmatory holdout, canonical Part-A receiver evidence, diagnostic mechanism/background evidence, and latest pre-package green CI.
- `configs/paper1_final_protocol.json` — exact Paper-1 scope, claim boundary, reference system assumptions, predictor/scheduler context, confirmatory method, seeds, regimes, endpoints and evidence labels.

## Evidence semantics

The service-guard result retains its original evidence label: **EXECUTED_DIAGNOSTIC / prospectively selected synthetic holdout**. Versioning its compact statistics and provenance here does not retroactively convert it into WOMD, measured-channel, or real-world evidence.

The canonical Part-A BER receiver evidence remains under `artifacts/paper_final/02_link/`; this package references it rather than duplicating it. Legacy `corrected_v2` motion, staged-sweep and ablation outputs are background/mechanism evidence only unless explicitly identified otherwise.

## Scientific claim boundary

Paper 1 supports a university Part-B conclusion that predictive communication-aware scheduling with a current-service guard can improve modeled packet performance in specific regimes. It does not support universal predictive superiority. The high-load regime remains neutral/uncertain for goodput and carries a descriptive P95-latency penalty.

Absolute received power and the vehicular optical link remain model-based; no measured optical channel or real-world vehicular deployment is claimed. Learned GRU/WOMD evidence is excluded from Paper 1 and belongs to Paper 2.

## Reproducibility rule

No future update may silently relabel diagnostic evidence as canonical external validation. Any stronger publication claim requires a new frozen protocol, clean execution, preserved raw outputs, and an updated manifest. The independent inferential unit for the confirmatory holdout is the paired scenario/seed within regime, never packets or time samples.
