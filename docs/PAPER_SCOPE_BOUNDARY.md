# Paper 1 / Paper 2 Scope Boundary

> **Repository rule:** this repository contains infrastructure for two scientifically distinct publication scopes. Files, experiments, and claims must be labelled by scope so that Paper 1 evidence is not confused with the incomplete learned study for Paper 2.

## Paper 1 — Mechanism and Operating-Region Study

**Working title:** *When Does Trajectory Prediction Help PC-FMCW/DPSK Vehicular Optical Scheduling?*

**Primary question:** When does causal future-motion information have packet-level value for PC-FMCW/DPSK vehicular optical scheduling, when does it become neutral or harmful, and why?

### In scope for Paper 1

- causal mobility -> future geometry -> optical-link -> packet-scheduling pipeline;
- classical trajectory predictors: Last Position, CV, CA, Kalman CV, IMM;
- perfect-future/oracle information only as an evaluator/reference, never as a deployable method or global optimum;
- trajectory metrics (ADE/FDE) and their translation to range/bearing, SNR, outage and link-lifetime fidelity;
- packet traffic, queues, deadlines, expiration, delivery, latency, PDR, goodput and fairness;
- reactive and predictive scheduling mechanisms;
- link-lifetime versus packet-deadline urgency;
- deadline-aware predictive scheduling;
- utility-term and fairness diagnostics;
- HELP / NEUTRAL / HURT operating-region characterization;
- decision-disagreement and service-order mechanism analysis;
- current-service guarded predictive scheduling;
- frozen prospective DEV/HOLDOUT scheduler selection and evaluation;
- scenario/episode-level paired statistics, effect sizes, confidence intervals and multiplicity control;
- robustness checks needed to support the mechanism/operating-region claims.

### Not required for Paper 1

- a learned GRU predictor;
- the 4-objective x 5-seed learned archive;
- WOMD-based learned-model superiority;
- communication-aware neural-loss claims;
- official learned held-out/OOD conclusions.

Paper 1 must not be blocked merely because Paper 2 learning experiments are incomplete. Conversely, diagnostic/non-canonical Paper-1 evidence must not be promoted to final publication evidence without its own frozen publication gate.

### Paper 1 candidate conclusion

The intended claim is conditional, not universal: trajectory/link prediction can have packet-level value, but that value depends on the operating regime and scheduling objective. Better geometric or future-link information does not by itself guarantee better packet scheduling. Congestion, packet urgency, fairness pressure and immediate service opportunity can change the sign of predictive value.

This conclusion remains limited to the evidence actually frozen for Paper 1.

---

## Paper 2 — Communication-Aware Learned Trajectory Prediction

**Working title:** *From Trajectory Accuracy to Communication Utility: Communication-Aware Learning for Predictive Vehicular Optical Scheduling*

**Primary question:** How should a learned causal trajectory predictor be trained when the downstream objective is communication usefulness rather than geometric trajectory accuracy alone?

### In scope for Paper 2

- causal GRU trajectory prediction;
- canonical WOMD data/provenance pipeline with scenario-level split controls;
- four frozen learning objectives:
  1. trajectory-only;
  2. trajectory + link;
  3. trajectory + outage;
  4. full communication-aware;
- exactly five canonical training seeds per objective (20 verified checkpoints total);
- development-only hyperparameter/checkpoint selection;
- untouched held-out and OOD predictor evaluation;
- trajectory-level metrics (ADE/FDE and geometry errors);
- communication-state metrics (SNR, outage and link-lifetime fidelity);
- downstream packet-level evaluation using the frozen communication/scheduling system;
- robustness to mobility, sensing and channel mismatch where required by the frozen protocol;
- objective-level statistics across training seeds and independent held-out scenario/episode units.

### Current Paper 2 blocker

The complete canonical WOMD corpus/checkpoint evidence is not currently available. Therefore the full 4 x 5 learned experiment, official held-out/OOD learned evaluation, and learned downstream conclusions are **not complete**. Paper 2 must not claim communication-aware GRU superiority until those gates pass.

### Paper 2 publication gate

Paper 2 should be a separate publication only if the learned study provides a distinct scientific answer, for example showing that geometric accuracy and communication usefulness diverge, or that communication-aware objectives systematically change held-out link/packet utility. If it only adds a GRU row to Paper 1 without a distinct conclusion, it should be merged as an extension rather than submitted as a separate paper.

---

## Shared Infrastructure

The following implementation may be shared by both papers without implying shared scientific claims:

- PC-FMCW/DPSK physical/link model;
- causal geometry utilities;
- packet/queue simulator;
- common metric definitions;
- reproducibility/provenance utilities;
- statistical utilities;
- ground-truth realization rule: predictions may inform decisions, but packet outcomes are realized from ground-truth-derived link state.

Shared code is not duplicate scientific evidence. Each paper must have its own frozen experiment manifest and result boundary.

---

## Repository Labelling Convention

From this point forward, new publication-facing material should use one of these labels:

- `PAPER1` — evidence/analysis used by the mechanism and operating-region paper;
- `PAPER2` — evidence/analysis used by the communication-aware learned paper;
- `SHARED` — reusable implementation or assumptions used by both;
- `HISTORICAL_DIAGNOSTIC` — exploratory evidence that is not a final paper result.

When an artifact could be relevant to both papers, the publication manifest must explicitly state which paper consumes it. A result must never become Paper 1 or Paper 2 evidence merely because its code exists or a CI workflow succeeded.

## Recommended Publication-Facing Layout

```text
paper/
├── paper1/
│   ├── README.md
│   ├── manuscript/
│   ├── figures/
│   └── tables/
├── paper2/
│   ├── README.md
│   ├── manuscript/
│   ├── figures/
│   └── tables/
└── shared/

artifacts/
├── paper1_final/
├── paper2_final/
├── shared/
└── diagnostics/
```

This is a publication-facing separation. Reusable scientific code should remain under `src/predictive_pc_fmcw/` rather than being duplicated between paper folders.

## One-Sentence Boundary

**Paper 1 asks when and why prediction has packet-level scheduling value; Paper 2 asks how a learned predictor should be trained for downstream communication usefulness.**
