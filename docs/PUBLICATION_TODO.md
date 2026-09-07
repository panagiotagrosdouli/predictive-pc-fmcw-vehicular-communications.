# Publication TODO — Paper 1 and Paper 2

Status vocabulary:

- `[x]` completed at the stated evidence tier;
- `[ ]` still required;
- `DIAGNOSTIC` is not automatically final publication evidence;
- `CANONICAL` means frozen publication evidence with provenance.

## Paper 1 — Mechanism / Operating-Region Study

**Question:** When and why does causal trajectory/link prediction have packet-level scheduling value?

### Scope and scientific story

- [x] Separate Paper 1 from Paper 2 in the repository.
- [x] Freeze the Paper-1 research question around trajectory -> link -> packet utility.
- [x] Avoid universal "prediction always helps" claims.
- [x] Define HELP / NEUTRAL / HURT operating-region framing.
- [x] Keep learned GRU/WOMD work outside the minimum Paper-1 scope.

### Core implementation

- [x] Causal mobility -> relative geometry pipeline.
- [x] Model-based PC-FMCW/DPSK optical link.
- [x] Ground-truth-derived realized link for packet outcomes.
- [x] Packet arrivals, queues, deadlines, expiration and delivery simulation.
- [x] Classical predictors: Last/CV/CA/Kalman/IMM.
- [x] Reactive and predictive scheduler infrastructure.
- [x] Packet-aware link-lifetime urgency correction.
- [x] Deadline-aware predictive scheduler.
- [x] Current-service guarded predictive scheduler family.
- [x] Unit/regression tests for corrected scheduler mechanisms.

### Existing mechanism evidence — DIAGNOSTIC

- [x] Classical trajectory -> link diagnostic evaluation.
- [x] Corrected scheduler benchmark diagnostics.
- [x] Corrected staged operating-region sweep.
- [x] Decision-disagreement audit.
- [x] Utility-term ablation.
- [x] Fairness-weight Pareto sweep.
- [x] Prospective fairness selection with fail-closed negative result.
- [x] High-load service-order audit.
- [x] Fresh prospective current-service-guard DEV/HOLDOUT execution.

### Paper-1 statistical closure — REQUIRED

- [ ] Parse/freeze the prospective current-service-guard result as a Paper-1 result artifact.
- [ ] Apply the precommitted holdout analysis protocol exactly: paired 100k bootstrap, 95% CI, practical margin, paired Wilcoxon, Holm correction, paired Cohen dz and win fraction.
- [ ] Report all predeclared regimes, including neutral/uncertain or harmful outcomes.
- [ ] Report secondary PDR, P95 latency and demand-normalized fairness descriptively without turning them into undeclared primary endpoints.
- [ ] Confirm independent unit and pairing at scenario/episode/seed level; do not treat packets/windows as independent samples.
- [ ] Create a frozen Paper-1 statistics manifest with code commit, workflow run, artifact digest, seeds and analysis protocol.

### Mechanism closure — REQUIRED

- [ ] Run/freeze disagreement-conditioned analysis for the prospectively selected current-service guard versus Reactive on the appropriate publication population.
- [ ] Quantify immediate-service preservation, HOL urgency, queue pressure, actual SNR/PER and delivered-packet consequences at disagreement slots.
- [ ] Test whether the guard changes the high-load failure mechanism without inventing a post-hoc causal claim.
- [ ] Separate mechanism evidence from performance evidence in the manuscript.

### Scientific anomaly audits — REQUIRED BEFORE FINAL FIGURES

- [ ] Audit the large Part-A BER-LUT versus analytical-link performance difference.
- [ ] Determine whether the BER-LUT difference is an implementation mismatch, expected model-regime effect or unsupported configuration.
- [ ] Audit counter-intuitive forecast-error/history-noise improvements in old diagnostics.
- [ ] Check for clipping, nonlinear threshold effects, changed decision ordering, randomization artifacts or implementation bugs.
- [ ] Preserve genuine negative/counter-intuitive findings if no bug is found.
- [ ] Do not include unexplained anomaly plots as headline evidence.

### Final Paper-1 experimental freeze — REQUIRED

- [ ] Create `configs/paper1_final_protocol.json` with the exact predictor set, scheduler set, regimes, seeds, traffic model, physical assumptions, primary/secondary endpoints and statistical unit.
- [ ] Freeze which existing diagnostics are background only and which experiments must be rerun canonically.
- [ ] Execute the final Paper-1 protocol from a clean commit.
- [ ] Store final evidence only under `artifacts/paper1_final/`.
- [ ] Record hashes/provenance for every final table and figure input.
- [ ] Run a clean reproduction check from the documented command path.

### Paper-1 figures/tables — REQUIRED

- [ ] Figure: system / causal trajectory -> link -> packet pipeline.
- [ ] Figure/table: classical trajectory accuracy -> link-state fidelity translation.
- [ ] Figure: HELP / NEUTRAL / HURT operating-region map.
- [ ] Figure/table: prospective current-service-guard held-out comparison.
- [ ] Figure: disagreement/service-order mechanism.
- [ ] Figure/table: robustness/sensitivity sufficient for the final claim.
- [ ] Table: exact system/channel/traffic/scheduler assumptions.
- [ ] Table: primary paired statistics and effect sizes.
- [ ] Generate all publication numbers from saved artifacts; no manual result entry.

### Paper-1 manuscript — REQUIRED

- [ ] Final title.
- [ ] Abstract with conditional, evidence-matched claims.
- [ ] Introduction and explicit contributions.
- [ ] Related work / novelty boundary; no unsupported "first" claims.
- [ ] System model and PC-FMCW/DPSK assumptions.
- [ ] Causal predictor and scheduler methodology.
- [ ] Experimental protocol and statistical methodology.
- [ ] RQ1 results: trajectory -> link.
- [ ] RQ2 results: link information -> packet utility.
- [ ] RQ3 results: operating regions.
- [ ] Mechanism analysis: urgency/service-order/current-service guard.
- [ ] Limitations: synthetic mobility evidence where applicable, model-based optical channel, no measured optical-channel validation, oracle not globally optimal.
- [ ] Discussion and negative results.
- [ ] Conclusion.
- [ ] Reproducibility/data/code statement.
- [ ] Final claim-to-artifact audit.

### Paper-1 submission gate

Paper 1 is submission-ready only when the final protocol, statistics, anomaly audits, final artifacts, figures/tables and manuscript all pass. The existing prospective diagnostics make the paper scientifically promising, but they are not by themselves the complete publication release.

---

## Paper 2 — Communication-Aware Learned Trajectory Prediction

**Question:** How should a learned causal trajectory predictor be trained for downstream communication usefulness rather than geometric accuracy alone?

### Scope/design already available

- [x] Separate Paper 2 from Paper 1 in the repository.
- [x] Define communication-aware learned research question.
- [x] GRU infrastructure/design exists.
- [x] Freeze four objective families: trajectory-only, trajectory+link, trajectory+outage, full communication-aware.
- [x] Freeze five training seeds per objective: 20 checkpoints required.
- [x] Define development-only model/loss selection principle.
- [x] Define trajectory-, link- and packet-level evaluation layers.
- [x] Define held-out/OOD intent and fail-closed publication gates.

### Data/provenance blocker — FIRST PRIORITY FOR PAPER 2

- [ ] Recover or rebuild the canonical WOMD source corpus.
- [ ] Materialize canonical training and official-validation arrays from real source data.
- [ ] Record source hashes and processing provenance.
- [ ] Verify causal history/future construction.
- [ ] Verify scenario-level split and zero overlap/leakage.
- [ ] Freeze the Paper-2 dataset manifest.
- [ ] Do not manufacture historical counts merely to reproduce an old fingerprint.

### Learned training — REQUIRED

- [ ] Run trajectory-only objective for 5 frozen seeds.
- [ ] Run trajectory+link objective for 5 frozen seeds.
- [ ] Run trajectory+outage objective for 5 frozen seeds.
- [ ] Run full communication-aware objective for 5 frozen seeds.
- [ ] Verify exactly 20 valid checkpoints and result manifests.
- [ ] Preserve failed/interrupted seeds rather than silently replacing them.
- [ ] Select hyperparameters/checkpoints using development data only.
- [ ] Freeze selected learned models before official validation is opened.

### Official predictor evaluation — REQUIRED

- [ ] Evaluate all frozen learned objectives/seeds on untouched official held-out data.
- [ ] Evaluate ADE/FDE and geometry errors.
- [ ] Evaluate SNR/link-state fidelity.
- [ ] Evaluate outage metrics.
- [ ] Evaluate link-lifetime error.
- [ ] Evaluate uncertainty/calibration metrics if retained in the final method.
- [ ] Evaluate OOD mobility.
- [ ] Quantify whether predictor rankings change from trajectory metrics to communication metrics.

### Downstream communication evaluation — REQUIRED

- [ ] Feed frozen learned forecasts into the frozen packet-scheduling system.
- [ ] Compare trajectory-only versus communication-aware objectives under identical scenarios/traffic/channel randomness.
- [ ] Report goodput, PDR, latency/deadlines, queues and fairness.
- [ ] Determine whether learned communication-aware training changes packet utility, not merely ADE/FDE.
- [ ] Run the required robustness axes for sensing/channel mismatch.
- [ ] Use independent scenario/episode units and training-seed variability correctly in inference.

### Paper-2 decision gate — REQUIRED BEFORE SPLIT PUBLICATION

- [ ] Test whether Paper 2 provides a distinct scientific conclusion from Paper 1.
- [ ] Strong split case: communication-aware objectives change held-out link/packet utility even when ADE/FDE alone would not select them.
- [ ] Valid negative case: learned complexity does not improve downstream communication over simple predictors/objectives.
- [ ] If Paper 2 merely adds a GRU row with no distinct conclusion, merge it into Paper 1 instead of creating a separate publication.

### Paper-2 final release — REQUIRED IF THE SPLIT SURVIVES

- [ ] Create `configs/paper2_final_protocol.json`.
- [ ] Store final evidence under `artifacts/paper2_final/` only.
- [ ] Generate Paper-2-specific figures/tables from frozen artifacts.
- [ ] Write Paper-2-specific manuscript with no duplicated Paper-1 contribution claims.
- [ ] Complete statistics, provenance and clean reproduction gate.
- [ ] Final claim-to-artifact audit.

---

## Repository migration / housekeeping

Do this without duplicating reusable science code or breaking provenance.

- [x] Add authoritative Paper 1 / Paper 2 scope boundary document.
- [x] Update root README with the two scopes.
- [x] Define labels: `PAPER1`, `PAPER2`, `SHARED`, `HISTORICAL_DIAGNOSTIC`.
- [ ] Create publication-facing `paper/paper1/`, `paper/paper2/`, `paper/shared/` directories.
- [ ] Create `artifacts/paper1_final/`, `artifacts/paper2_final/`, `artifacts/shared/`, `artifacts/diagnostics/` contracts without silently moving/relabeling legacy evidence.
- [ ] Add per-paper README/manifests listing exact inputs and outputs.
- [ ] Update publication workflows so each run declares `PAPER1` or `PAPER2` scope.
- [ ] Keep reusable implementation in `src/predictive_pc_fmcw/`.
- [ ] Keep legacy paths readable until dependent scripts/workflows are migrated and tested.
- [ ] Run repository-wide tests/lint after migration.

## Execution order

1. **Finish Paper 1 evidence and manuscript first.**
2. **Perform controlled publication-facing repository migration.**
3. **Recover/freeze WOMD and execute Paper 2.**
4. **Decide whether Paper 2 genuinely survives as a separate publication only after its held-out results exist.**
