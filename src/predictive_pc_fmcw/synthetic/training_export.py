"""Leakage-safe training export from Synthetic Dataset v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _observed_xy(range_m: np.ndarray, bearing_rad: np.ndarray) -> np.ndarray:
    return np.stack(
        (range_m * np.cos(bearing_rad), range_m * np.sin(bearing_rad)), axis=-1
    )


def build_synthetic_training_npz(
    dataset_dir: str | Path,
    output_path: str | Path,
    *,
    history_steps: int = 20,
    horizon_steps: int = 10,
    stride: int = 5,
) -> Path:
    """Export causal train/development windows; held-out and OOD are forbidden."""
    if history_steps < 2 or horizon_steps < 1 or stride < 1:
        raise ValueError("history_steps >= 2, horizon_steps >= 1, stride >= 1 required")
    root = Path(dataset_dir)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    split = manifest["split"]
    allowed = {
        **{scenario_id: "training" for scenario_id in split["train"]},
        **{scenario_id: "development" for scenario_id in split["development"]},
    }
    forbidden = set(split["held_out_test"]) | set(split["ood_test"])
    if set(allowed) & forbidden:
        raise ValueError(
            "synthetic manifest leaks held-out/OOD scenarios into training"
        )

    histories: list[np.ndarray] = []
    futures: list[np.ndarray] = []
    scenario_ids: list[str] = []
    splits: list[str] = []
    future_ego_headings: list[np.ndarray] = []
    sample_end_indices: list[int] = []
    source_hashes: dict[str, str] = {}

    for scenario_id, split_name in sorted(allowed.items()):
        path = root / "scenarios" / f"{scenario_id}.npz"
        if not path.is_file():
            raise FileNotFoundError(f"missing synthetic scenario: {scenario_id}")
        expected_hash = manifest["scenario_sha256"][scenario_id]
        actual_hash = _sha256_file(path)
        if actual_hash != expected_hash:
            raise ValueError(f"scenario fingerprint mismatch: {scenario_id}")
        source_hashes[scenario_id] = actual_hash
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
                future_ego_headings.append(
                    np.zeros(horizon_steps, dtype=np.float64)
                )
                scenario_ids.append(scenario_id)
                splits.append(split_name)
                sample_end_indices.append(end_index)

    if not histories:
        raise ValueError("no synthetic training samples were produced")
    split_array = np.asarray(splits)
    if not np.any(split_array == "training") or not np.any(
        split_array == "development"
    ):
        raise ValueError("training export requires non-empty training and development")
    if set(scenario_ids) & forbidden:
        raise ValueError("held-out/OOD scenario entered synthetic training export")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        destination,
        history_xy=np.stack(histories).astype(np.float32),
        future_xy=np.stack(futures).astype(np.float32),
        scenario_id=np.asarray(scenario_ids),
        actor_id=np.asarray(["synthetic_target"] * len(scenario_ids)),
        future_ego_heading_rad=np.stack(future_ego_headings).astype(np.float32),
        split=split_array,
        sample_history_end_index=np.asarray(sample_end_indices, dtype=np.int64),
        source=np.asarray("synthetic_dataset_v1_causal_noisy_observations"),
        coordinate_frame=np.asarray("ego_fixed_relative_world_xy"),
        dataset_manifest_sha256=np.asarray(_sha256_file(manifest_path)),
        source_scenario_hashes_json=np.asarray(
            json.dumps(source_hashes, sort_keys=True, separators=(",", ":"))
        ),
        history_steps=np.asarray(history_steps, dtype=np.int64),
        horizon_steps=np.asarray(horizon_steps, dtype=np.int64),
        stride=np.asarray(stride, dtype=np.int64),
    )
    return destination


def validate_synthetic_training_npz(
    dataset_dir: str | Path, training_npz: str | Path
) -> dict[str, object]:
    """Fail closed if held-out/OOD IDs or malformed causal windows are present."""
    root = Path(dataset_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    forbidden = set(manifest["split"]["held_out_test"]) | set(
        manifest["split"]["ood_test"]
    )
    with np.load(training_npz, allow_pickle=False) as data:
        scenario_ids = np.asarray(data["scenario_id"]).astype(str)
        splits = np.asarray(data["split"]).astype(str)
        history = np.asarray(data["history_xy"])
        future = np.asarray(data["future_xy"])
        future_ego_heading = np.asarray(data["future_ego_heading_rad"])
        if set(scenario_ids) & forbidden:
            raise ValueError("held-out/OOD contamination in synthetic training NPZ")
        if set(np.unique(splits)) != {"training", "development"}:
            raise ValueError(
                "synthetic training NPZ must contain only train/development"
            )
        if history.ndim != 3 or future.ndim != 3:
            raise ValueError("history_xy/future_xy must be rank-3 arrays")
        if history.shape[0] != future.shape[0] or history.shape[-1] != 2:
            raise ValueError("synthetic training sample arrays are misaligned")
        if future_ego_heading.shape != future.shape[:2]:
            raise ValueError("future ego heading must align with future trajectory")
        if not np.allclose(future_ego_heading, 0.0):
            raise ValueError("ego-fixed synthetic frame requires zero ego heading")
        if not np.all(np.isfinite(history)) or not np.all(np.isfinite(future)):
            raise ValueError("synthetic training NPZ contains non-finite values")
        return {
            "status": "PASS",
            "samples": int(history.shape[0]),
            "training_samples": int(np.sum(splits == "training")),
            "development_samples": int(np.sum(splits == "development")),
            "scenario_count": int(np.unique(scenario_ids).size),
            "held_out_or_ood_samples": 0,
            "sha256": _sha256_file(Path(training_npz)),
        }
