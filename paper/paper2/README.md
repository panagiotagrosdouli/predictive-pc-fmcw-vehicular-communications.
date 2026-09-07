# Paper 2 — Communication-Aware Learned Trajectory Prediction

**Scope label:** `PAPER2`

**Working title:** *From Trajectory Accuracy to Communication Utility: Communication-Aware Learning for Predictive Vehicular Optical Scheduling*

This directory is the publication-facing workspace for Paper 2. Reusable implementation stays under `src/predictive_pc_fmcw/`.

## Research question

How should a learned causal trajectory predictor be trained when the downstream objective is communication usefulness rather than geometric trajectory accuracy alone?

## Frozen learned design

Paper 2 requires four training objectives, each with five independent canonical seeds:

1. trajectory-only;
2. trajectory + link;
3. trajectory + outage;
4. full communication-aware.

The complete publication archive therefore requires exactly 20 verified checkpoints before official held-out/OOD learned conclusions are allowed.

## Current blocker

The complete canonical WOMD corpus/checkpoint evidence is not currently available. Paper 2 is therefore incomplete. No communication-aware GRU superiority claim is permitted until the data/provenance gate, 20-checkpoint training gate, untouched held-out/OOD evaluation, downstream packet evaluation and statistics all pass.

## Split-publication gate

Paper 2 should remain a separate paper only if its learned study provides a distinct scientific conclusion from Paper 1. If it merely adds another predictor row without a distinct trajectory-accuracy-versus-communication-utility result, it should be merged into the stronger Paper-1 study rather than published separately.
