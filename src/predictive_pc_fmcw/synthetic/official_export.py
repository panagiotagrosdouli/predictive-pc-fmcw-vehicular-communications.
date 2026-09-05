"""Freeze-gated held-out/OOD window export for Synthetic Dataset v1."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .freeze import verify_publication_training_freeze


def _observed_xy(range_m: np.ndarray, bearing_rad: np.ndarray) -> np.ndarray:
    return np.stack(
        (range_m * np.cos(bearing_rad), range_m * np.sin(bearing_rad)), axis=-1
    )


def build_official_evaluation_npz(
    dataset_dir: str | Path,
    ablation_dir: str | Path,
    training_npz: str | Path,
    output_path: str | Path,
    *,
    split: str,
    history_steps: int = 20,
    horizon_steps: int = 10,
    stride: int = 5,
) -> Path:
    """Export held-out or OOD windows only after the publication freeze passes."""
    if split not in {"held_out_test", "ood_test"}:
        raise ValueError("official export split must be held_out_test or ood_test")
    if history_steps < 2 or horizon_steps < 1 or stride < 1:
        raise ValueError("invalid history/horizon/stride")

    freeze = verify_publication_training_freeze(
        dataset_dir, ablation_dir, training_npz
    )
    root = Path(dataset_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    scenario_ids = tuple(manifest["split"][split])
    if not scenario_ids:
        raise ValueError(f"official split is empty: {split}")

    histories: list[np.ndarray] = []
    futures: list[np.ndarray] = []
    sample_scenarios: list[str] = []
    end_indices: list[int] = []
    for scenario_id in scenario_ids:
        path = root / "scenarios" / f"{scenario_id}.npz"
        with np.load(path, allow_pickle=False) as data:
            observed = _observed_xy(
                np.asarray(data["observed_range_m"], dtype=np.float64),
                np.asarray(data["observed_bearing_rad"], dtype=np.float64),
            )
            truth = np.stack(
                (
                    np.asarray(data["x_m"], dtype=np.float64),
                    np.asarray(data["y_m"], dtype=np.float64),
                ),
                axis=-1,
            )
            first_end = history_steps - 1
            last_end = truth.shape[0] - horizon_steps - 1
            for end_index in range(first_end, last_end + 1, stride):
                history_start = end_index - history_steps + 1
                future_start = end_index + 1
                future_stop = future_start + horizon_steps
                histories.append(observed[history_start : end_index + 1])
                futures.append(truth[future_start:future_stop])
                sample_scenarios.append(scenario_id)
                end_indices.append(end_index)

    if not histories:
        raise ValueError(f"no official evaluation windows produced for {split}")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite official artifact: {destination}")
    sample_count = len(histories)
    np.savez_compressed(
        destination,
        history_xy=np.stack(histories).astype(np.float32),
        future_xy=np.stack(futures).astype(np.float32),
        future_ego_heading_rad=np.zeros(
            (sample_count, horizon_steps), dtype=np.float32
        ),
        scenario_id=np.asarray(sample_scenarios),
        split=np.asarray([split] * sample_count),
        sample_history_end_index=np.asarray(end_indices, dtype=np.int64),
        source=np.asarray("synthetic_dataset_v1_official_freeze_gated"),
        coordinate_frame=np.asarray("ego_fixed_relative_world_xy"),
        freeze_training_npz_sha256=np.asarray(freeze["training_npz_sha256"]),
        freeze_dataset_manifest_sha256=np.asarray(
            freeze["dataset_manifest_sha256"]
        ),
        freeze_completion_manifest_sha256=np.asarray(
            freeze["completion_manifest_sha256"]
        ),
        history_steps=np.asarray(history_steps, dtype=np.int64),
        horizon_steps=np.asarray(horizon_steps, dtype=np.int64),
        stride=np.asarray(stride, dtype=np.int64),
    )
    return destination
