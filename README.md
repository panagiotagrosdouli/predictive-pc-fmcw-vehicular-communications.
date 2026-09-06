# Predictive PC-FMCW/DPSK Vehicular Communications

**Causal trajectory forecasting for deadline-aware optical vehicle scheduling**

**English** | [Ελληνικά](README_GR.md) · [Executable stages](stages) · [Repository architecture](docs/REPOSITORY_ARCHITECTURE.md) · [Paper draft](paper/PAPER_DRAFT.md)

![Predictive PC-FMCW/DPSK system overview](docs/assets/readme-hero.webp)

> Can motion forecasts help a vehicle scheduler deliver packets before a
> directional optical link disappears - and does lower trajectory error
> actually imply better communication performance?

This repository connects real Waymo Open Motion Dataset (WOMD) trajectories to
a model-based PC-FMCW/DPSK optical link and a packet simulator with queues,
deadlines, retries and fairness. It extends the supplied Part-A physical layer;
it is **not** the separate joint beam/ADB project.

## Research questions

The project is organized around a primary systems thesis:

> **Determine when causal trajectory prediction has real packet-level
> communication value in PC-FMCW/DPSK vehicular optical scheduling, and whether
> geometric forecasting accuracy is a reliable proxy for downstream
> communication performance.**

The core research questions are:

1. **RQ1 — From trajectory accuracy to link accuracy:** Does lower ADE/FDE imply better prediction of the future optical link, including range/bearing, SNR, outage and link lifetime?
2. **RQ2 — From link accuracy to packet utility:** Does better future-link prediction actually improve packet-level outcomes such as goodput, PDR, latency, deadline satisfaction, queue behavior and fairness?
3. **RQ3 — Operating regions:** Under which mobility, prediction-horizon, traffic-load, deadline, FoV, sensing-noise and channel conditions does predictive scheduling help, become neutral or hurt relative to reactive scheduling?

A secondary extension asks whether communication-aware GRU objectives improve the
prediction-to-communication translation compared with classical predictors. The
GRU is therefore treated as a learned extension and ablation tool, not as the
central scientific novelty.

The central mechanism under test is:

```text
trajectory accuracy
        -> future-link fidelity
        -> packet-level communication utility
```

The project explicitly does **not** assume that improvement propagates through
all three layers. In particular, it tests whether

```text
better ADE/FDE != better link prediction != better scheduling performance
```

and whether predictive schedulers exhibit identifiable
**helpful / neutral / harmful operating regions**. One specific failure
mechanism of interest is that **link urgency is not necessarily packet urgency**:
a receiver whose optical link is about to disappear may not own the packet with
the tightest deadline.

```mermaid
flowchart LR
    A["Stage 0-1: frozen WOMD provenance"] --> B["Stage 3-5: causal prediction"]
    A --> C["Stage 2: frozen PC-FMCW/DPSK link"]
    B --> D["Stage 6: packet scheduling"]
    C --> D
    D --> E["Stage 7: scenario-level statistics"]
    E --> F["Stage 8: reproducibility release"]
```

Ground-truth future motion is used only to realize and evaluate the link. A
deployable predictor or scheduler never sees it.

## Canonical Stage 0-8 workflow

The project is organized as nine gated folders under [`stages/`](stages).
Every folder owns its `stage.json`, direct `run.py`, stage README, dependencies,
commands, expected evidence and acceptance criteria. Reusable implementation
remains under `src/predictive_pc_fmcw/`; stage folders do not duplicate science.

| Stage | Folder | Purpose | Completion gate |
|---:|---|---|---|
| 0 | [`00_freeze_and_provenance`](stages/00_freeze_and_provenance) | Freeze protocol and split policy | Dataset hashes and zero scenario overlap |
| 1 | [`01_womd_data_pipeline`](stages/01_womd_data_pipeline) | Materialize/audit the frozen WOMD corpora | Source hashes, causal arrays, split/provenance gates |
| 2 | [`02_pc_fmcw_dpsk_link`](stages/02_pc_fmcw_dpsk_link) | Freeze the Part-A link mapping | Confidence-aware verified BER LUT |
| 3 | [`03_classical_baselines`](stages/03_classical_baselines) | Evaluate Last/CV/CA/Kalman/IMM | Reproducible development trajectory/link metrics |
| 4 | [`04_communication_aware_gru`](stages/04_communication_aware_gru) | Select loss weights and train GRUs | Four objectives × five seeds = 20 verified checkpoints |
| 5 | [`05_official_predictor_evaluation`](stages/05_official_predictor_evaluation) | Evaluate untouched validation | Frozen predictors evaluated once on official validation |
| 6 | [`06_packet_scheduling`](stages/06_packet_scheduling) | Run paired packet experiments | Eight schedulers × five paired traffic seeds |
| 7 | [`07_statistics_and_figures`](stages/07_statistics_and_figures) | Analyze operating regions | Scenario/episode inference, multiplicity-aware statistics |
| 8 | [`08_final_paper`](stages/08_final_paper) | Build the release | Final evidence, paper and reproducibility manifest |

Canonical generated evidence mirrors stage ownership:

```text
artifacts/paper_final/
├── 00_freeze/
├── 01_data/
├── 02_link/
├── 03_baselines/
├── 04_learning/
├── 05_heldout/
├── 06_scheduling/
├── 07_statistics/
└── 08_release/
```

`artifacts/paper_final/execution_state.json` and Stage-4-local execution-state
files are operational restart reports only. They never replace scientific
completion manifests, provenance reports or acceptance gates.

### One canonical operator path

```bash
# 1. Preflight: Stage 1 deliberately does not require Stage 2 or CUDA.
make canonical-preflight \
  WOMD_DATA_ROOT=/data/womd \
  TRAIN_NPZ=/data/womd/womd_training_paper.npz \
  VALIDATION_NPZ=/data/womd/womd_validation_paper.npz

# 2. Stage 1 provenance/corpus verification.
make canonical-stage1 \
  WOMD_DATA_ROOT=/data/womd \
  TRAIN_NPZ=/data/womd/womd_training_paper.npz \
  VALIDATION_NPZ=/data/womd/womd_validation_paper.npz

# 3. Full downstream canonical execution. This requires frozen Stage 2,
#    official-validation TFRecords and CUDA through the full preflight.
make canonical-full \
  WOMD_DATA_ROOT=/data/womd \
  TRAIN_NPZ=/data/womd/womd_training_paper.npz \
  VALIDATION_NPZ=/data/womd/womd_validation_paper.npz \
  VALIDATION_GLOB='/data/womd/validation/*.tfrecord'
```

For dependency-oriented inspection of individual research stages, use:

```bash
make stages
make stage STAGE=stage0
make stage STAGE=stage0 EXECUTE=--execute
```

## Current evidence - honestly separated

| Evidence | State |
|---|---|
| Trajectory → link → packet simulation | Implemented and tested |
| Part-A receiver-derived LUT | Executed on a 31-point SNR grid |
| Controlled scheduling study | Existing non-canonical development evidence retained |
| Historical WOMD training fingerprint | 249,137 samples / 24,182 scenarios; provenance fingerprint, not a target |
| Training/development leakage audit | Zero overlap required by the canonical gate |
| Earlier partial training attempt | Preserved as historical evidence; not canonical completion |
| Canonical learned archive | Pending until 20 verified checkpoints exist |
| Untouched official-validation corpus | Export supported; must remain outside model selection |
| Official learned scheduling evidence | Requires real validation data and checkpoints |
| Measured optical-channel validation | Not available and not claimed |

Historical training corpus SHA-256 recorded in prior evidence:
`b47faf427487a7405531e4944c5bfff9ca56d4fcb9ce3f8495df3cce534347ee`.
Historical counts and hashes are provenance fingerprints: the Stage-1 gate does
not force a new run to manufacture those counts.

## Why ADE is not enough

A small Cartesian error near the optical FoV boundary may cause a large
pointing-gain or outage error. The paper therefore evaluates the full chain:

\[
\mathrm{ADE/FDE}\rightarrow\{r,\theta\}\rightarrow
\{\mathrm{SNR},\mathrm{BER},\mathrm{PER},T_{link}\}\rightarrow
\{\mathrm{goodput},\mathrm{misses},\mathrm{latency}\}.
\]

The learned objective is

\[
\mathcal{L}=\lambda_{traj}\mathcal{L}_{traj}
+\lambda_{link}\mathcal{L}_{link}
+\lambda_{out}\mathcal{L}_{outage}.
\]

Stage 4 separately trains trajectory-only, trajectory+link,
trajectory+outage and full communication-aware GRUs. Lambda selection is
strictly development-only and is frozen before Stage 5.

## Included methods

Predictors:

- Last Position, Constant Velocity and Constant Acceleration;
- position-only Kalman CV and causal CV/CA IMM;
- deterministic GRU with four communication-loss objectives;
- development-fitted residual Gaussian calibration for held-out NLL and
  50/90/95% coverage;
- perfect-future information reference for evaluator-only bounds.

Schedulers:

- canonical Stage 6 uses exactly eight frozen scheduler families;
- every family is paired over exactly five frozen traffic seeds;
- information-oracle behavior remains evaluator-only and is not deployable.

## Installation and verification

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,ml,paper]"

make test
make lint
make validate
```

PyTorch is needed only for learned-model stages.

## External stage inputs

Copy [`stages/.env.example`](stages/.env.example) and set:

```bash
export WOMD_DATA_ROOT=/data/womd
export TRAIN_NPZ=/data/womd/womd_v131_training.npz
export VALIDATION_NPZ=/data/womd/womd_v131_official_validation.npz
export VALIDATION_TFRECORD='/data/womd/validation/*.tfrecord'
export CHECKPOINT_GLOB='artifacts/paper_final/04_learning/learned_ablation/*/seed_*/best_comm_aware_gru.pt'
export LAMBDA_LINK=0.2
export LAMBDA_OUTAGE=0.1
```

Loss weights are selected only on development data and frozen before official
validation is opened.

## Repository layout

```text
stages/                        canonical Stage 0-8 orchestration and contracts
├── 00_freeze_and_provenance/
├── 01_womd_data_pipeline/
├── 02_pc_fmcw_dpsk_link/
├── 03_classical_baselines/
├── 04_communication_aware_gru/
├── 05_official_predictor_evaluation/
├── 06_packet_scheduling/
├── 07_statistics_and_figures/
└── 08_final_paper/
src/predictive_pc_fmcw/        reusable scientific/software library
scripts/                       canonical and auxiliary executable entrypoints
configs/                       frozen physical/experimental assumptions
tests/                         regression and scientific gates
artifacts/paper_final/         canonical stage-aligned evidence
paper/                         manuscript source
notebooks/                     Colab GPU/data-acquisition operator workflow
```