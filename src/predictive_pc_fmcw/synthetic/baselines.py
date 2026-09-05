"""Causal B0-B4 predictor evaluation for Synthetic Dataset v1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from ..predictors import (
    ConstantAccelerationPredictor,
    ConstantVelocityPredictor,
    InteractingMultipleModelPredictor,
    KalmanConstantVelocityPredictor,
    LastPositionPredictor,
    TrajectoryPredictor,
)


@dataclass(frozen=True)
class BaselineMetrics:
    predictor: str
    split: str
    scenarios: int
    windows: int
    ade_m: float
    fde_m: float
    range_mae_m: float
    bearing_mae_rad: float


def _observed_xy(range_m: np.ndarray, bearing_rad: np.ndarray) -> np.ndarray:
    return np.stack(
        (range_m * np.cos(bearing_rad), range_m * np.sin(bearing_rad)), axis=-1
    )


def _angle_error(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.arctan2(np.sin(left - right), np.cos(left - right))


def _predictors() -> tuple[TrajectoryPredictor, ...]:
    return (
        LastPositionPredictor(),
        ConstantVelocityPredictor(),
        ConstantAccelerationPredictor(),
        KalmanConstantVelocityPredictor(),
        InteractingMultipleModelPredictor(),
    )


def evaluate_synthetic_baselines(
    dataset_dir: str | Path,
    *,
    split: str = "development",
    history_steps: int = 20,
    horizon_steps: int = 10,
    stride: int = 5,
    allow_official_test: bool = False,
) -> list[BaselineMetrics]:
    """Evaluate B0-B4 from causal noisy histories against future truth."""
    if split not in {"training", "development", "held_out_test", "ood_test"}:
        raise ValueError(f"unsupported split: {split}")
    if split in {"held_out_test", "ood_test"} and not allow_official_test:
        raise PermissionError(
            "held-out/OOD evaluation requires explicit allow_official_test=True"
        )
    if history_steps < 2 or horizon_steps < 1 or stride < 1:
        raise ValueError("invalid history/horizon/stride")

    root = Path(dataset_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest_key = "train" if split == "training" else split
    scenario_ids = tuple(manifest["split"][manifest_key])
    if not scenario_ids:
        raise ValueError(f"synthetic split is empty: {split}")

    predictors = _predictors()
    rows: dict[str, dict[str, list[float] | int]] = {}
    for predictor in predictors:
        rows[predictor.name] = {
            "ade": [],
            "fde": [],
            "range": [],
            "bearing": [],
            "windows": 0,
        }

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
            t_s = np.asarray(data["t_s"], dtype=np.float64)
            dt_s = float(np.median(np.diff(t_s)))
            first_end = history_steps - 1
            last_end = truth.shape[0] - horizon_steps - 1
            for end_index in range(first_end, last_end + 1, stride):
                history = observed[end_index - history_steps + 1 : end_index + 1]
                target = truth[end_index + 1 : end_index + 1 + horizon_steps]
                target_range = np.linalg.norm(target, axis=-1)
                target_bearing = np.arctan2(target[:, 1], target[:, 0])
                for predictor in predictors:
                    predicted = predictor.predict(history, horizon_steps, dt_s)
                    error = np.linalg.norm(predicted - target, axis=-1)
                    predicted_range = np.linalg.norm(predicted, axis=-1)
                    predicted_bearing = np.arctan2(predicted[:, 1], predicted[:, 0])
                    bearing_error = _angle_error(predicted_bearing, target_bearing)
                    bucket = rows[predictor.name]
                    bucket["ade"].append(float(np.mean(error)))
                    bucket["fde"].append(float(error[-1]))
                    bucket["range"].append(
                        float(np.mean(np.abs(predicted_range - target_range)))
                    )
                    bucket["bearing"].append(
                        float(np.mean(np.abs(bearing_error)))
                    )
                    bucket["windows"] = int(bucket["windows"]) + 1

    results: list[BaselineMetrics] = []
    for predictor in predictors:
        bucket = rows[predictor.name]
        results.append(
            BaselineMetrics(
                predictor=predictor.name,
                split=split,
                scenarios=len(scenario_ids),
                windows=int(bucket["windows"]),
                ade_m=float(np.mean(bucket["ade"])),
                fde_m=float(np.mean(bucket["fde"])),
                range_mae_m=float(np.mean(bucket["range"])),
                bearing_mae_rad=float(np.mean(bucket["bearing"])),
            )
        )
    return results


def save_baseline_results(
    results: list[BaselineMetrics], output_path: str | Path
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        [asdict(row) for row in results], indent=2, sort_keys=True
    )
    destination.write_text(payload + "\n", encoding="utf-8")
    return destination
