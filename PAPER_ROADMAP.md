# Paper Roadmap — Predictive PC-FMCW/DPSK Vehicular Communications

> **Purpose.** This document separates what the repository has actually demonstrated from what is only implemented or planned, and defines two defensible publication paths. It is intentionally fail-closed: code existence, CI success, a development run, or a plausible hypothesis is not a paper result.

## 1. Central scientific question

The project should be organized around one cross-layer question:

> **When does causal trajectory prediction have real packet-level communication value in PC-FMCW/DPSK vehicular optical scheduling, why, and when does it fail?**

The scientific chain is

```text
causal vehicle history
  -> future trajectory prediction
  -> future relative range / bearing
  -> predicted optical-link state
  -> SNR -> BER -> PER -> outage / link lifetime
  -> queue- and deadline-aware scheduling
  -> packet outcome on the ground-truth-derived realized link
```

The predictor is therefore an information source, not automatically the novelty. The main systems question is whether geometric forecasting accuracy survives translation through the optical channel and ultimately changes packet utility.

### Primary research questions

**RQ1 — Trajectory accuracy -> link fidelity.** Does lower ADE/FDE imply more accurate future range, bearing, SNR, outage state and link lifetime? Do predictor rankings change after the geometry-to-link transformation?

**RQ2 — Link fidelity -> packet utility.** Does better future-link prediction imply better goodput, PDR, latency, deadline satisfaction, availability, queue behavior and fairness? Can a geometrically worse predictor produce equal or better packet utility?

**RQ3 — Operating region.** Under which combinations of prediction horizon, offered load, deadline tightness, mobility, FoV, SNR/channel difficulty, sensing uncertainty and model mismatch does predictive scheduling help, become neutral, or hurt relative to reactive scheduling?

A secondary learned-model question is:

> **Can communication-aware GRU objectives improve the prediction-to-communication translation beyond classical predictors?**

This is an extension, not a prerequisite for the core mechanism question unless the final evidence shows that the learned component is essential to the scientific claim.

## 2. Candidate paper thesis

The strongest candidate thesis is not “trajectory prediction improves vehicular communications.” That is too broad and is not safe as a novelty claim.

The candidate thesis to test is:

> **Trajectory accuracy is not necessarily communication value: in a mobility-sensitive optical link, the benefit of causal motion prediction depends on how trajectory error translates into future link-state error and how that information interacts with packet deadlines, queues and link transitions.**

Two particularly valuable outcomes are possible if supported by frozen evidence:

1. **metric decoupling:** lower ADE/FDE is not sufficient to guarantee better outage/link-lifetime prediction or packet utility;
2. **conditional value:** prediction has identifiable helpful, neutral and harmful operating regions rather than a universal gain.

A useful mechanism to test is **link urgency != packet urgency**. A receiver whose link is about to disappear may be urgent from a channel perspective while another packet has a tighter deadline. A link-lifetime policy can therefore make a locally sensible link decision that is globally poor for packet utility.

These are hypotheses until the required experiments are complete.

---

# 3. What has actually been completed

The repository already contains substantial research infrastructure. The following items can be described as implemented/tested infrastructure, subject to the repository's individual stage gates.

## 3.1 End-to-end simulation architecture — IMPLEMENTED / TESTED

The code connects causal motion histories to trajectory predictors, maps predicted and ground-truth geometry through a PC-FMCW/DPSK optical-link model, simulates queues/arrivals/deadlines/retries, and supports packet scheduling. The realized packet outcome is evaluated using the ground-truth-derived link rather than letting the prediction declare its own success.

This is important because it permits a genuine causal comparison between information available to a scheduler and the physical/link outcome used for evaluation.

## 3.2 Synthetic mobility and data controls — IMPLEMENTED

The dataset-free protocol includes deterministic seeded synthetic mobility with multiple scenario families, scenario-level train/development/held-out/OOD partitions, zero-overlap checks, causal noisy observations, and ground-truth kinematic/link geometry. The minimum-separation correction remains a controlled simulation assumption and must not be presented as real traffic behavior.

## 3.3 PC-FMCW/DPSK link — EXECUTED CANONICAL EVIDENCE EXISTS

Stage 2 is the clearest completed canonical scientific artifact at present. The repository contains the receiver-derived BER LUT and link verification evidence under `artifacts/paper_final/02_link/`. The LUT was executed on a 31-point SNR grid. The optical power/channel remains model-based; measured end-to-end optical-channel validation is not available and must not be claimed.

## 3.4 Classical predictors — IMPLEMENTED; DEVELOPMENT EVIDENCE EXISTS

The repository supports Last Position, CV, CA, position-only Kalman CV and causal CV/CA IMM baselines, with development trajectory and future-link evaluation. These are valuable for the mechanism study because the central question does not require a neural predictor to be meaningful.

However, development results are not automatically official held-out publication evidence.

## 3.5 Packet traffic and scheduling — IMPLEMENTED; OFFICIAL COMPARISON NOT COMPLETE

The simulator accounts for arrivals, deadlines, expiration, retransmissions, delivery, latency, queue state and goodput. A frozen scheduling protocol S0-S7 exists, including an evaluator-only oracle, multi-vehicle episodes, paired traffic traces and five paired traffic seeds.

Historical/non-canonical scheduling studies exist and are useful for debugging hypotheses and identifying candidate mechanisms. They must remain labeled exploratory until the frozen official protocol is executed.

## 3.6 Statistics and robustness infrastructure — IMPLEMENTED

The repository already defines scenario/episode-level inference, traffic-seed averaging within episode, bootstrap confidence intervals, paired tests/effect sizes and Holm correction for predeclared primary comparisons. It also implements robustness axes for observation noise, forecast-channel mismatch, forecast-SNR bias, atmospheric attenuation mismatch and OOD evaluation.

Operating-region sweep infrastructure exists over forecast horizon, channel difficulty, load/deadline tightness and mobility difficulty.

The infrastructure is not equivalent to completed statistical evidence.

## 3.7 Learned communication-aware GRU protocol — DESIGNED / IMPLEMENTED, NOT COMPLETE

The frozen plan contains four objectives and five canonical seeds, requiring exactly **20 verified checkpoints**. Selection is development-only and official held-out/OOD data are excluded from selection. The publication freeze is designed to fail closed unless the complete checkpoint set exists.

At present the complete 20-checkpoint canonical archive has not been executed and verified. Consequently the official learned-model evaluation and learned scheduling claims remain blocked.

## 3.8 Publication artifact contract — IMPLEMENTED, FINAL ARTIFACTS BLOCKED

The repository defines a provenance-aware contract for Figures 1-10 and Tables I-VIII. Missing official evidence may not be replaced by placeholders or manually entered results. This is good research hygiene, but the final publication figures/tables remain blocked until their required upstream evidence exists.

---

# 4. What has NOT yet been completed

As of the current repository status, the following must not be described as finished results:

- the complete 4-objective x 5-seed = **20-checkpoint** learned archive;
- frozen official held-out learned trajectory/link evaluation;
- frozen OOD learned evaluation;
- the official S0-S7 packet-scheduler comparison over five paired traffic seeds;
- the final operating-region sweeps/heatmaps;
- observation/channel robustness sweeps;
- official objective A/B/C/D learned ablation;
- the final scenario/episode-level paired statistical report;
- the final publication Figures 1-10 and Tables I-VIII;
- measured optical-channel validation;
- a final PASS/FAIL/MIXED verdict for the central hypothesis.

Therefore the repository is **not currently submission-ready as the full planned paper**. Existing diagnostic results can guide experiment design, but they cannot be silently promoted to final evidence.

---

# 5. Paper A — Mechanism / Operating-Region Study

## 5.1 Proposed scope

**Working title:**

> **When Does Trajectory Prediction Help PC-FMCW/DPSK Vehicular Optical Scheduling?**

Paper A asks a narrower but potentially strong systems question: when is future-motion information actually useful to packet scheduling, and why?

The paper does **not** need to claim a new trajectory predictor. Classical predictors are scientifically useful because they provide different error structures with which to test the trajectory -> link -> packet translation.

### Candidate contributions, only if supported by final evidence

1. A causal cross-layer evaluation framework connecting trajectory forecasts to future optical-link state and then to packet-level scheduling outcomes.
2. A quantitative analysis of whether ADE/FDE ranking predicts SNR/outage/link-lifetime ranking and packet-level utility ranking.
3. A systematic map of prediction-helpful, prediction-neutral and prediction-harmful operating regions.
4. A mechanism analysis of failures such as link urgency versus packet urgency and sensitivity near FoV/outage/link-transition boundaries.

None of these should be written as a confirmed result before the experiments support them.

## 5.2 Minimum evidence required for Paper A

Paper A should not be submitted using only the old exploratory matrix. At minimum it needs:

### A1. Freeze a Paper-A predictor set

Use a small, interpretable set such as Last/CV/CA/Kalman/IMM, with no post-held-out tuning. Perfect future may appear only as an evaluator/reference bound.

### A2. RQ1 translation experiment

On held-out scenarios, compute on common support:

- ADE/FDE;
- range and bearing error;
- future-SNR error;
- outage classification metrics;
- link-lifetime error;
- predictor rank correlation and explicit rank reversals across layers.

The important output is not merely a table of ADE. It is a **translation map** showing whether geometric ranking survives the optical-link transformation.

### A3. RQ2 paired packet experiment

Run the frozen deployable reactive/predictive scheduler families needed to answer the mechanism question using identical scenarios, arrivals, deadlines and random seeds across policies. Report at least:

- goodput;
- PDR;
- latency distribution/P95 where appropriate;
- deadline success/misses;
- expiration/censoring;
- fairness;
- scheduled-link quality and switching behavior when relevant.

Packet success must be realized from the ground-truth-derived actual link, never from the forecast used to choose the packet.

### A4. RQ3 operating-region experiment

Produce a prediction-value map such as

`Delta G = G_predictive - G_reactive`

across predeclared axes. Prioritize scientifically interpretable dimensions rather than a combinatorial sweep for its own sake:

- horizon;
- offered load;
- deadline tightness;
- FoV/channel difficulty;
- mobility/link-transition difficulty;
- sensing uncertainty.

Channel mismatch can be a robustness extension if resources permit.

The paper should explicitly retain helpful, neutral and harmful regions.

### A5. Link-urgency versus packet-urgency mechanism test

Instrument scheduling decisions so that the analysis can identify cases where predicted remaining link lifetime and packet deadline pressure disagree. Compare the downstream consequences. This should be treated as a mechanism analysis, not asserted from anecdotes.

### A6. Statistical closure

Use scenario/episode as the independent unit, preserve pairing, report confidence intervals and effect sizes, and apply the declared multiplicity correction to primary comparisons. Do not inflate sample size by treating packets/windows from one episode as independent observations.

### A7. Robustness sufficient for the claim

At minimum show that the main conclusion is not an artifact of one observation-noise value or one optical-channel setting. The full robustness grid planned for Paper B is not automatically necessary if a smaller preregistered sensitivity set is enough to test Paper A's claim.

## 5.3 Paper-A decision gate

Paper A is viable if the frozen evidence reveals a reproducible scientific structure, for example:

- predictor rankings change between ADE and communication metrics;
- prediction gain concentrates near link transitions or particular load/deadline regimes;
- a predictive scheduler has clear beneficial and harmful regions;
- link urgency versus packet urgency explains a meaningful subset of failures.

Paper A can also survive if prediction is mostly unhelpful, provided the negative result is robust and the study explains **when and why**. It should not be forced into a universal-improvement narrative.

If the experiments produce only tiny noisy differences with no stable mechanism or operating-region structure, Paper A should be reconsidered rather than rescued by selective plots.

---

# 6. Paper B — Full Learned Predictive Scheduling Study

## 6.1 Proposed scope

Paper B is the stronger and more expensive study. It retains RQ1-RQ3 but adds the learned question:

> Can communication-aware training produce forecasts that are more useful to the communication system, even when geometric ADE/FDE alone would not select them?

The key learned ablation is the frozen four-objective design:

1. trajectory-only;
2. trajectory + link;
3. trajectory + outage;
4. full communication-aware objective;

with five canonical seeds per objective.

## 6.2 Required work for Paper B

### B1. Recover/rebuild the canonical WOMD corpus

The canonical WOMD data/provenance gate must pass before the learned pipeline can be called complete. Preserve source hashes, true causal histories/futures, split labels and zero scenario overlap. Do not manufacture historical sample counts merely to match an old fingerprint.

### B2. Complete all 20 learned runs

Train exactly four objectives x five seeds and validate every checkpoint/result pair. Failed or interrupted seeds remain visible. No official split may be used for model selection.

### B3. Freeze learned-model selection

Use development data only to select required checkpoints/hyperparameters. Pass the fail-closed publication freeze before opening official evaluation.

### B4. Official held-out and OOD predictor evaluation

Evaluate all four objectives x five seeds on untouched official validation and OOD evidence. Report trajectory metrics, communication-state fidelity, uncertainty/calibration metrics where applicable, and objective-level paired/clustered comparisons.

### B5. Official packet scheduling

Run the frozen Stage-6 protocol: exactly eight scheduler families over exactly five paired traffic seeds, with the required learned checkpoints and evaluator-only oracle. Preserve common scenarios/traffic/channel randomness across scheduler comparisons.

### B6. Full operating-region and robustness study

Complete the predeclared horizon/channel/load/deadline/mobility sweeps plus observation-noise, channel mismatch, forecast-SNR bias, atmospheric attenuation and OOD analyses required by the frozen protocol.

### B7. Statistical closure

Generate scenario/episode-level confidence intervals, paired effect sizes/tests and Holm-adjusted primary comparisons. Report seed variability rather than selecting a favorable learned seed.

### B8. Publication artifacts and reproducibility

Generate final Figures 1-10 and Tables I-VIII only from frozen saved artifacts with provenance hashes. Complete the clean reproduction/release manifest and manuscript gate.

## 6.3 Paper-B decision gate

Paper B is scientifically valuable if the learned ablation answers more than “GRU has lower ADE.” Useful outcomes include:

- communication-aware objectives improve link/outage/lifetime fidelity even with similar trajectory ADE;
- communication-aware objectives improve packet utility on held-out/OOD scenarios;
- gains occur only in particular operating regions;
- learned models do **not** beat simple baselines downstream, establishing that additional forecasting complexity is unnecessary under some regimes.

The last outcome is still a legitimate result. The learned study must not be optimized to make the GRU win.

---

# 7. Relationship between Paper A and Paper B

Paper A and Paper B should be treated as **two possible publication scopes**, not automatically as two papers that must both be submitted.

Paper A is the minimum scientifically coherent mechanism study. It asks whether prediction has communication value and characterizes the conditions/mechanisms.

Paper B extends that story by asking whether communication-aware learning changes the answer under official held-out/OOD evaluation.

To avoid salami slicing, if both eventually become separate submissions they must have genuinely different research questions, experiments and conclusions. If Paper B merely repeats Paper A with a GRU row added to the same tables, it should instead become the stronger version of one paper.

A sensible decision sequence is:

```text
complete rigorous Paper-A evidence
        |
        +-- no stable mechanism/value map -> reconsider publication scope
        |
        +-- strong mechanism/value map
                |
                +-- learned component adds a distinct scientific answer -> Paper B may be justified
                |
                +-- learned component only adds another predictor -> combine into one stronger paper
```

---

# 8. Related Work and Novelty Boundary

This section records the literature boundary found during the current red-team review. It is deliberately conservative. The project should not use “first” language unless a later systematic review justifies it.

## 8.1 Trajectory prediction in dynamic / vehicular VLC already exists

Jiang et al., **“Trajectory Prediction of Target Light Source for Dynamic Visible Light Communication Systems with A Narrow Field of View,”** IEEE ICC Workshops, 2020, applies Kalman-based trajectory prediction to dynamic VLC beam alignment/tracking under narrow FoV. This means the project must **not** claim that trajectory prediction has never been applied to vehicular VLC.

What remains different here is the downstream question: packet/receiver service decisions under queues and deadlines, rather than optical alignment as the principal control variable.

## 8.2 Vehicular VLC resource optimization and lifetime-aware decisions already exist

Msongaleli and Kucuk, **“Optimal resource utilisation algorithm for visible light communication-based vehicular ad-hoc networks,”** IET Intelligent Transport Systems, 2020, studies VLC-VANET resource allocation with network lifetime, connectivity and load balancing objectives.

Garai et al., **“Optimized vehicular connectivity and data exchange in a tree-structured VLC communication network based on optical codewords,”** Frontiers in Physics, 2025, studies mobility-aware vehicular VLC attachment/routing/QoS and relates mobility to SNR, delay, throughput/connectivity and link/network behavior.

Therefore claims such as “first lifetime-aware vehicular optical resource allocation” or “first vehicular VLC resource optimization” are unsafe.

## 8.3 Trajectory-prediction-assisted vehicular resource selection/scheduling already exists

Hajrasouliha and Shahgholi Ghahfarokhi, **“Dynamic geo-based resource selection in LTE-V2V communications using vehicle trajectory prediction,”** Computer Communications, 2021, predicts future vehicle locations and uses them in LTE-V2V resource selection.

Han et al., **“Online Scheduling With Trajectory Prediction for Collaborative DNN Inference in Vehicular Networks,”** IEEE Transactions on Networking, 2025, uses trajectory prediction before online scheduling decisions for collaborative vehicle-edge DNN inference.

Xu et al., **“Offloading elastic transfers to opportunistic vehicular networks based on imperfect trajectory prediction,”** IEEE/ACM Transactions on Networking, 2023, explicitly considers imperfect trajectory prediction in vehicular-network scheduling/offloading and throughput optimization.

Therefore “first prediction-based vehicular scheduling” and “first study of imperfect trajectory prediction affecting networking performance” are unsafe broad claims.

## 8.4 Link-lifetime prediction and prediction-supported routing already exist

Xu et al., **“PQR: Prediction-supported Quality-aware Routing for Uninterrupted Vehicle Communication,”** IEEE/ACM IWQoS, 2021, uses acceleration-based trajectory prediction to estimate link lifetime and combines it with predicted route quality for proactive routing.

Thus link-lifetime prediction itself is not the novelty.

## 8.5 Prediction-based vehicular VLC handover already exists

Abualhoul et al., **“A Proposal for VLC-Assisting IEEE802.11p Communication for Vehicular Environment Using a Prediction-based Handover,”** IEEE ITSC, 2018, predates this project. Prediction-assisted VLC/RF handover therefore cannot be claimed as new in the broad sense.

## 8.6 What novelty may still be defensible

The current literature review did **not** establish a safe broad “first.” Instead it suggests a narrower research gap worth testing:

### Candidate C1 — cross-layer causal chain

A framework in which causal trajectory forecasts are translated into future PC-FMCW/DPSK-informed optical link states and then used for **queue/deadline-aware packet scheduling**, while packet outcomes are realized/evaluated on the ground-truth-derived link.

This is a candidate differentiator, not a proven exhaustive first claim.

### Candidate C2 — trajectory metric -> link fidelity -> packet utility

A systematic analysis of whether lower ADE/FDE actually predicts better SNR/outage/link-lifetime fidelity and, in turn, better packet-level utility. This is stronger than presenting trajectory accuracy as an end metric.

### Candidate C3 — helpful / neutral / harmful operating regions

A systematic characterization of when prediction helps, when it has negligible value and when it harms packet scheduling across mobility, horizon, load, deadline, FoV/channel and sensing conditions. This is currently the strongest candidate research angle.

### Candidate C4 — link urgency versus packet urgency

A packet-level failure mechanism in which imminent link loss and imminent packet deadline impose different notions of urgency. If the frozen experiments support it, this can explain why better future-link knowledge need not yield better packet utility.

## 8.7 Claims to avoid

Until a deeper systematic review establishes otherwise, do **not** claim:

- first use of trajectory prediction in vehicular communications;
- first trajectory prediction in VLC;
- first mobility-to-optical-performance mapping;
- first link-lifetime prediction;
- first link-lifetime-aware networking decision;
- first vehicular VLC resource allocation/scheduling/routing;
- first prediction-based vehicular scheduling;
- first prediction-based VLC/802.11p handover;
- first study showing that prediction error affects network performance.

Prefer precise contribution language such as **“we study,” “we characterize,” “we evaluate,”** and **“we connect”** rather than unsupported priority claims.

---

# 9. Evidence matrix

| Question / claim | Required evidence | Current state | Needed next |
|---|---|---|---|
| End-to-end causal trajectory -> link -> packet simulator exists | tests + implementation | **Implemented/tested** | preserve regression gates |
| PC-FMCW/DPSK BER/link mapping | canonical LUT + verification | **Executed; Stage-2 evidence exists** | keep frozen; document model-based limitation |
| Lower ADE implies better link fidelity | common-support held-out predictor/link evaluation | **Not yet a final canonical conclusion** | run/freeze RQ1 analysis |
| Better link prediction implies better packet utility | paired held-out scheduling | **Not yet completed officially** | run RQ2 paired scheduler study |
| Prediction has helpful/neutral/harmful regions | operating-region sweeps + clustered inference | **Infrastructure exists; final evidence missing** | run RQ3 sweeps/statistics |
| Link urgency != packet urgency explains failures | decision-level instrumentation + paired analysis | **Candidate mechanism** | explicitly test and quantify |
| Classical mechanism paper is sufficient | RQ1-RQ3 closure + robustness + stats | **Possible, not yet proven** | complete Paper-A minimum set |
| Communication-aware GRU improves downstream utility | 20 checkpoints + held-out/OOD + scheduling | **Blocked / incomplete** | complete Stage 4-7 canonical path |
| Full learned paper is ready | all frozen evidence + final figures/tables | **No** | complete Paper-B path |
| Real-world optical validation | measured channel evidence | **Not available** | either obtain measurements or state model-based scope |

---

# 10. Recommended execution order

The research should minimize expensive work while preserving scientific rigor.

### Phase 1 — Close Paper A first

1. Freeze the classical predictor set and Paper-A primary comparisons.
2. Produce the held-out trajectory -> link translation analysis for RQ1.
3. Execute paired packet scheduling for RQ2.
4. Execute the smallest preregistered operating-region grid sufficient for RQ3.
5. Quantify link-urgency versus packet-urgency conflicts.
6. Run scenario/episode-level inference and sensitivity checks.
7. Decide whether a stable publishable mechanism exists.

### Phase 2 — Decide whether Paper B is scientifically necessary

Only after Phase 1:

1. recover/rebuild and freeze the canonical WOMD corpus;
2. execute/verify all 20 learned checkpoints;
3. freeze selection;
4. run official held-out/OOD learned evaluation;
5. run full learned scheduler protocol;
6. run full robustness/operating-region analysis;
7. generate final publication artifacts and reproducibility release.

This ordering prevents spending substantial GPU/data effort merely to discover that the core communication hypothesis has no stable signal.

---

# 11. Publication-readiness rules

A result may enter the manuscript as a primary numerical claim only when its declared evidence gate is satisfied.

Use these labels consistently:

- **IMPLEMENTED** — code/functionality exists; no scientific result implied.
- **EXECUTED / DIAGNOSTIC** — experiment ran, but is exploratory/development evidence.
- **FROZEN / CANONICAL** — evidence satisfies the declared scientific gate and may support the corresponding manuscript claim.
- **BLOCKED / MISSING** — required evidence does not yet exist.

Negative and mixed results must remain visible. Oracle information is evaluator-only. Future truth cannot enter deployable decisions. Model-based optical results must not be described as measured validation. Packets/windows from the same scenario must not be used to create artificial statistical sample size.

---

# 12. Current verdict

## Paper A

**Promising and scientifically coherent, but not yet submission-ready.** The repository already contains the essential simulator, physical/link mapping, classical predictor support, scheduler infrastructure, operating-region machinery and statistical design. What is missing is the frozen quantitative closure of RQ1-RQ3.

Paper A should be the immediate target because it tests the central scientific idea with the minimum necessary complexity.

## Paper B

**Potentially stronger, but materially incomplete.** It requires the canonical data gate, the complete 20-checkpoint learned archive, untouched held-out/OOD evaluation, official paired scheduling, robustness/operating-region experiments, statistical closure and final reproducibility artifacts.

Do not make Paper B mandatory merely because the code supports it. It is justified only if communication-aware learning adds a distinct scientific answer beyond the mechanism established by Paper A.

## Overall

There is a credible route to publication, but the paper must be earned by the frozen experiments rather than inferred from implementation. The strongest current strategy is:

> **first establish whether prediction has packet-level value and map where that value appears; then determine whether communication-aware learning materially changes that map.**

That strategy allows positive, mixed or negative outcomes to remain scientifically useful and keeps the publication story aligned with the evidence.