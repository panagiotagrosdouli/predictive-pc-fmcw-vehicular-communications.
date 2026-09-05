"""Freeze-gated paired packet-level scheduling evaluation for Synthetic Dataset v1."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from ..config import ExperimentConfig, SensingConfig
from ..data.manifest import sha256_file
from ..learning.ablation import CANONICAL_SEEDS, validate_training_resume
from ..learning.inference import TorchCheckpointPredictor
from ..link import LinkModel
from ..simulation.engine import run_simulation
from ..traffic import generate_traffic_trace
from .episodes import compose_synthetic_episodes
from .freeze import verify_publication_training_freeze
from .scheduling_protocol import (
    PAIRED_TRAFFIC_SEEDS,
    SCHEDULER_FAMILIES,
    scheduler_protocol_manifest,
    validate_scheduler_protocol,
)


def build_scheduling_plan(
    *,
    episode_count: int,
) -> dict[str, object]:
    """Return the frozen Stage-6 execution cardinality without running models."""
    validate_scheduler_protocol()
    if episode_count < 1:
        raise ValueError("episode_count must be positive")
    per_episode = len(SCHEDULER_FAMILIES) * len(PAIRED_TRAFFIC_SEEDS)
    return {
        "scheduler_families": len(SCHEDULER_FAMILIES),
        "traffic_seeds": len(PAIRED_TRAFFIC_SEEDS),
        "runs_per_episode": per_episode,
        "episode_count": episode_count,
        "planned_runs": episode_count * per_episode,
        "protocol": scheduler_protocol_manifest(),
    }


def _load_selected_predictors(
    selection_manifest_path: str | Path,
    *,
    ablation_dir: str | Path,
    training_sha256: str,
) -> dict[str, TorchCheckpointPredictor]:
    path = Path(selection_manifest_path)
    if not path.is_file():
        raise PermissionError("development checkpoint-selection manifest is required")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("selection_split") != "development":
        raise PermissionError("learned scheduler checkpoints must be selected on development")
    if raw.get("training_npz_sha256") != training_sha256:
        raise PermissionError("checkpoint-selection manifest training hash mismatch")
    selected = raw.get("selected")
    if not isinstance(selected, dict):
        raise PermissionError("checkpoint-selection manifest lacks selected models")

    predictors: dict[str, TorchCheckpointPredictor] = {}
    root = Path(ablation_dir)
    for objective in ("trajectory_only", "full"):
        item = selected.get(objective)
        if not isinstance(item, dict):
            raise PermissionError(f"missing development selection for {objective}")
        seed = int(item.get("seed", -1))
        if seed not in CANONICAL_SEEDS:
            raise PermissionError(f"selected seed is not canonical for {objective}")
        run_dir = root / objective / f"seed_{seed}"
        result_path = run_dir / "training_result.json"
        validation = validate_training_resume(
            result_path,
            expected_objective=objective,
            expected_seed=seed,
            expected_dataset_sha256=training_sha256,
            expected_run_dir=run_dir,
        )
        if not validation.valid or validation.result is None:
            raise PermissionError(
                f"selected {objective} checkpoint is not verified: {validation.reason}"
            )
        predictors[objective] = TorchCheckpointPredictor(validation.result.checkpoint)
    return predictors


def _sensing_from_dataset_manifest(manifest: dict[str, object]) -> SensingConfig:
    raw = manifest["observation_config"]
    if not isinstance(raw, dict):
        raise ValueError("dataset observation_config is invalid")
    return SensingConfig(
        model="range_bearing_assumed",
        range_std_base_m=float(raw["range_std_m"]),
        range_std_per_m=0.0,
        bearing_std_deg=float(np.rad2deg(float(raw["bearing_std_rad"]))),
        temporal_correlation=0.0,
        covariance_aware=True,
        assumption_source="synthetic_dataset_v1 frozen observation configuration",
    )


def run_synthetic_scheduling_evaluation(
    dataset_dir: str | Path,
    *,
    split: str,
    ablation_dir: str | Path,
    training_npz: str | Path,
    selection_manifest: str | Path,
    config: ExperimentConfig,
    output_path: str | Path,
    vehicles_per_episode: int = 5,
    history_steps: int = 20,
) -> dict[str, object]:
    """Run the exact 8-family x 5-seed paired scheduling protocol.

    Held-out and OOD scheduling are inaccessible until all 20 training runs
    pass the publication freeze and the learned checkpoints were selected using
    development data only.
    """
    if split not in {"held_out_test", "ood_test"}:
        raise ValueError("official scheduling split must be held_out_test or ood_test")
    destination = Path(output_path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite official artifact: {destination}")

    freeze = verify_publication_training_freeze(dataset_dir, ablation_dir, training_npz)
    training_sha = str(freeze["training_npz_sha256"])
    predictors = _load_selected_predictors(
        selection_manifest,
        ablation_dir=ablation_dir,
        training_sha256=training_sha,
    )

    root = Path(dataset_dir)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    episodes = compose_synthetic_episodes(
        root,
        split=split,
        vehicles_per_episode=vehicles_per_episode,
        history_steps=history_steps,
    )
    plan = build_scheduling_plan(episode_count=len(episodes))
    sensing = _sensing_from_dataset_manifest(manifest)
    rows: list[dict[str, object]] = []

    for episode in episodes:
        scenario = episode.scenario
        dt_s = scenario.dt_s
        current_config = replace(
            config,
            slot_duration_s=dt_s,
            sensing=sensing,
        )
        capacity = LinkModel(current_config.link).capacity_packets(dt_s)
        for traffic_seed in PAIRED_TRAFFIC_SEEDS:
            effective_seed = int(
                (sum(episode.member_seeds) + traffic_seed) % (2**31 - 1)
            )
            traffic = generate_traffic_trace(
                seed=effective_seed,
                slots=scenario.evaluation_slots,
                vehicles=scenario.vehicle_count,
                nominal_capacity_packets=capacity,
                config=current_config.traffic,
                slot_duration_s=dt_s,
            )
            for family in SCHEDULER_FAMILIES:
                learned_predictor = (
                    predictors[family.learned_objective]
                    if family.learned_objective is not None
                    else None
                )
                output = run_simulation(
                    scenario=scenario,
                    scheduler_name=family.scheduler_name,
                    traffic=traffic,
                    config=current_config,
                    seed=effective_seed,
                    learned_predictor=learned_predictor,
                )
                row = output.metrics.to_dict()
                row.update(
                    {
                        "protocol_id": family.protocol_id,
                        "forecast_source": family.forecast_source,
                        "learned_objective": family.learned_objective,
                        "traffic_seed": traffic_seed,
                        "effective_traffic_seed": effective_seed,
                        "member_scenario_ids": list(episode.member_scenario_ids),
                        "mean_queue_packets": float(output.queue_packets.mean()),
                        "p95_queue_packets": float(
                            np.quantile(output.queue_packets, 0.95)
                        ),
                        "retransmission_attempts": int(output.metrics.failed_attempts),
                    }
                )
                rows.append(row)

    if len(rows) != int(plan["planned_runs"]):
        raise RuntimeError("scheduling execution cardinality does not match frozen plan")
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "COMPLETED",
        "protocol": "synthetic_dataset_v1_stage6",
        "split": split,
        "plan": plan,
        "freeze": freeze,
        "dataset_manifest_sha256": sha256_file(manifest_path),
        "selection_manifest_sha256": sha256_file(selection_manifest),
        "rows": rows,
        "scientific_guards": {
            "paired_traffic_trace_within_episode_seed": True,
            "scenario_episode_inferential_unit": True,
            "oracle_evaluation_only": True,
            "development_only_checkpoint_selection": True,
            "source_tracks_disjoint_across_episodes": True,
        },
        "known_limitation": (
            "radial-velocity observations are generated and retained by the dataset, "
            "but the current scheduler predictor interface consumes causal position "
            "histories reconstructed from range/bearing sensing"
        ),
    }
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
