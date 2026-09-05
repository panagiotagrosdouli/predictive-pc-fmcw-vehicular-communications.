"""Predictor-to-link evaluation on Synthetic Dataset v1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from ..config import LinkConfig
from ..link import LinkModel
from ..predictors import (
    ConstantAccelerationPredictor,
    ConstantVelocityPredictor,
    InteractingMultipleModelPredictor,
    KalmanConstantVelocityPredictor,
    LastPositionPredictor,
    TrajectoryPredictor,
)


@dataclass(frozen=True)
class LinkPredictionMetrics:
    predictor: str
    split: str
    scenarios: int
    windows: int
    snr_mae_db: float
    ber_mae: float
    per_mae: float
    goodput_mae_bps: float
    outage_disagreement_rate: float


def _predictors() -> tuple[TrajectoryPredictor, ...]:
    return (
        LastPositionPredictor(),
        ConstantVelocityPredictor(),
        ConstantAccelerationPredictor(),
        KalmanConstantVelocityPredictor(),
        InteractingMultipleModelPredictor(),
    )


def _observed_xy(range_m: np.ndarray, bearing_rad: np.ndarray) -> np.ndarray:
    return np.stack(
        (range_m * np.cos(bearing_rad), range_m * np.sin(bearing_rad)), axis=-1
    )


def _mean_absolute(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.abs(left - right)))


def evaluate_synthetic_link_prediction(
    dataset_dir: str | Path,
    *,
    split: str = "development",
    history_steps: int = 20,
    horizon_steps: int = 10,
    stride: int = 5,
    allow_official_test: bool = False,
) -> list[LinkPredictionMetrics]:
    """Evaluate B0-B4 future-link fidelity through the frozen link mapping."""
    if split not in {"training", "development", "held_out_test", "ood_test"}:
        raise ValueError(f"unsupported split: {split}")
    if split in {"held_out_test", "ood_test"} and not allow_official_test:
        raise PermissionError(
            "held-out/OOD link evaluation requires explicit allow_official_test=True"
        )
    if history_steps < 2 or horizon_steps < 1 or stride < 1:
        raise ValueError("invalid history/horizon/stride")

    root = Path(dataset_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    link_model = LinkModel(LinkConfig(**manifest["link_config"]))
    manifest_key = "train" if split == "training" else split
    scenario_ids = tuple(manifest["split"][manifest_key])
    if not scenario_ids:
        raise ValueError(f"synthetic split is empty: {split}")
    predictors = _predictors()
    rows = {
        predictor.name: {
            "snr": [],
            "ber": [],
            "per": [],
            "goodput": [],
            "outage": [],
            "windows": 0,
        }
        for predictor in predictors
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
                true_link = link_model.evaluate_arrays(target_range, target_bearing)
                for predictor in predictors:
                    predicted = predictor.predict(history, horizon_steps, dt_s)
                    predicted_range = np.linalg.norm(predicted, axis=-1)
                    predicted_bearing = np.arctan2(predicted[:, 1], predicted[:, 0])
                    predicted_link = link_model.evaluate_arrays(
                        predicted_range, predicted_bearing
                    )
                    bucket = rows[predictor.name]
                    bucket["snr"].append(
                        _mean_absolute(
                            predicted_link["snr_db"], true_link["snr_db"]
                        )
                    )
                    bucket["ber"].append(
                        _mean_absolute(predicted_link["ber"], true_link["ber"])
                    )
                    bucket["per"].append(
                        _mean_absolute(predicted_link["per"], true_link["per"])
                    )
                    bucket["goodput"].append(
                        _mean_absolute(
                            predicted_link["goodput_bps"],
                            true_link["goodput_bps"],
                        )
                    )
                    bucket["outage"].append(
                        float(
                            np.mean(
                                predicted_link["outage"] != true_link["outage"]
                            )
                        )
                    )
                    bucket["windows"] = int(bucket["windows"]) + 1

    results: list[LinkPredictionMetrics] = []
    for predictor in predictors:
        bucket = rows[predictor.name]
        results.append(
            LinkPredictionMetrics(
                predictor=predictor.name,
                split=split,
                scenarios=len(scenario_ids),
                windows=int(bucket["windows"]),
                snr_mae_db=float(np.mean(bucket["snr"])),
                ber_mae=float(np.mean(bucket["ber"])),
                per_mae=float(np.mean(bucket["per"])),
                goodput_mae_bps=float(np.mean(bucket["goodput"])),
                outage_disagreement_rate=float(np.mean(bucket["outage"])),
            )
        )
    return results


def save_link_prediction_results(
    results: list[LinkPredictionMetrics], output_path: str | Path
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        [asdict(row) for row in results], indent=2, sort_keys=True
    )
    destination.write_text(payload + "\n", encoding="utf-8")
    return destination
