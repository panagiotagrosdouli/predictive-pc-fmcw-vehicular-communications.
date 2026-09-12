from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np

from ..geometry import wrap_angle_rad
from ..link import LinkModel
from .calibration import ResidualGaussianCalibration, gaussian_nll_and_coverage


class BatchTrajectoryPredictor(Protocol):
    def predict(
        self, history_xy: np.ndarray, horizon_steps: int, dt_s: float
    ) -> np.ndarray: ...


@dataclass(frozen=True)
class HeldoutScenarioMetrics:
    checkpoint: str
    objective: str
    seed: int
    scenario_id: str
    samples: int
    ade_m: float
    fde_m: float
    range_mae_m: float
    bearing_mae_deg: float
    snr_mae_db: float
    goodput_mae_mbps: float
    outage_f1: float
    outage_auroc: float
    link_lifetime_mae_s: float
    gaussian_nll: float = float("nan")
    coverage_50: float = float("nan")
    coverage_90: float = float("nan")
    coverage_95: float = float("nan")


def _binary_f1(labels: np.ndarray, predictions: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=bool).ravel()
    predictions = np.asarray(predictions, dtype=bool).ravel()
    tp = int(np.count_nonzero(labels & predictions))
    fp = int(np.count_nonzero(~labels & predictions))
    fn = int(np.count_nonzero(labels & ~predictions))
    denominator = 2 * tp + fp + fn
    return 1.0 if denominator == 0 else 2 * tp / denominator


def _binary_auroc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=bool).ravel()
    scores = np.asarray(scores, dtype=np.float64).ravel()
    positives = scores[labels]
    negatives = scores[~labels]
    if positives.size == 0 or negatives.size == 0:
        return float("nan")
    # Rank-sum AUROC handles ties and avoids a quadratic pair matrix.
    from scipy.stats import rankdata

    ranks = rankdata(np.concatenate([positives, negatives]), method="average")
    positive_rank_sum = ranks[: positives.size].sum()
    return float(
        (positive_rank_sum - positives.size * (positives.size + 1) / 2)
        / (positives.size * negatives.size)
    )


def evaluate_checkpoint_arrays(
    *,
    predictor: BatchTrajectoryPredictor,
    history_xy: np.ndarray,
    future_xy: np.ndarray,
    future_ego_heading_rad: np.ndarray,
    scenario_ids: np.ndarray,
    link_model: LinkModel,
    checkpoint: str,
    objective: str,
    seed: int,
    batch_size: int = 1024,
    dt_s: float = 0.1,
    calibration: ResidualGaussianCalibration | None = None,
) -> list[HeldoutScenarioMetrics]:
    history = np.asarray(history_xy, dtype=np.float32)
    future = np.asarray(future_xy, dtype=np.float32)
    heading = np.asarray(future_ego_heading_rad, dtype=np.float64)
    scenarios = np.asarray(scenario_ids).astype(str)
    if (
        history.ndim != 3
        or future.ndim != 3
        or history.shape[-1] != 2
        or future.shape[-1] != 2
    ):
        raise ValueError("Expected history/future arrays shaped (samples, time, 2).")
    if history.shape[0] < 1 or history.shape[1] < 1 or future.shape[1] < 1:
        raise ValueError("Held-out evaluation requires non-empty samples and horizons.")
    if not (history.shape[0] == future.shape[0] == scenarios.size):
        raise ValueError("Held-out arrays have inconsistent sample counts.")
    if heading.shape != future.shape[:2]:
        raise ValueError("future_ego_heading_rad must have shape (samples, horizon).")
    if not (
        np.all(np.isfinite(history))
        and np.all(np.isfinite(future))
        and np.all(np.isfinite(heading))
    ):
        raise ValueError("Held-out arrays must contain only finite values.")
    if batch_size < 1 or not np.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("batch_size must be positive and dt_s finite and positive.")

    predicted_chunks = []
    for start in range(0, history.shape[0], batch_size):
        stop = min(start + batch_size, history.shape[0])
        predicted_chunks.append(
            predictor.predict(history[start:stop], future.shape[1], dt_s)
        )
    predicted = np.concatenate(predicted_chunks).astype(np.float64)
    target = future.astype(np.float64)
    if predicted.shape != target.shape:
        raise ValueError("Checkpoint prediction shape does not match held-out targets.")
    if not np.all(np.isfinite(predicted)):
        raise ValueError("Checkpoint prediction contains non-finite values.")

    trajectory_error = np.linalg.norm(predicted - target, axis=-1)
    predicted_range = np.linalg.norm(predicted, axis=-1)
    target_range = np.linalg.norm(target, axis=-1)
    predicted_bearing = wrap_angle_rad(
        np.arctan2(predicted[..., 1], predicted[..., 0]) - heading
    )
    target_bearing = wrap_angle_rad(
        np.arctan2(target[..., 1], target[..., 0]) - heading
    )
    predicted_link = link_model.evaluate_arrays(predicted_range, predicted_bearing)
    target_link = link_model.evaluate_arrays(target_range, target_bearing)
    predicted_lifetime = link_model.link_lifetime_seconds(
        predicted_range, predicted_bearing, dt_s
    )
    target_lifetime = link_model.link_lifetime_seconds(
        target_range, target_bearing, dt_s
    )
    probabilistic = (
        gaussian_nll_and_coverage(predicted, target, calibration)
        if calibration is not None
        else None
    )

    grouped: dict[str, list[int]] = defaultdict(list)
    for index, scenario in enumerate(scenarios):
        grouped[scenario].append(index)
    rows: list[HeldoutScenarioMetrics] = []
    for scenario, indices_list in sorted(grouped.items()):
        indices = np.asarray(indices_list, dtype=int)
        true_outage = target_link["outage"][indices]
        predicted_outage = predicted_link["outage"][indices]
        rows.append(
            HeldoutScenarioMetrics(
                checkpoint=checkpoint,
                objective=objective,
                seed=seed,
                scenario_id=scenario,
                samples=int(indices.size),
                ade_m=float(trajectory_error[indices].mean()),
                fde_m=float(trajectory_error[indices, -1].mean()),
                range_mae_m=float(
                    np.abs(predicted_range[indices] - target_range[indices]).mean()
                ),
                bearing_mae_deg=float(
                    np.rad2deg(
                        np.abs(
                            wrap_angle_rad(
                                predicted_bearing[indices] - target_bearing[indices]
                            )
                        )
                    ).mean()
                ),
                snr_mae_db=float(
                    np.abs(
                        predicted_link["snr_db"][indices]
                        - target_link["snr_db"][indices]
                    ).mean()
                ),
                goodput_mae_mbps=float(
                    np.abs(
                        predicted_link["goodput_bps"][indices]
                        - target_link["goodput_bps"][indices]
                    ).mean()
                    / 1e6
                ),
                outage_f1=_binary_f1(true_outage, predicted_outage),
                outage_auroc=_binary_auroc(
                    true_outage, -predicted_link["snr_db"][indices]
                ),
                link_lifetime_mae_s=float(
                    np.abs(
                        predicted_lifetime[indices] - target_lifetime[indices]
                    ).mean()
                ),
                gaussian_nll=(
                    float(probabilistic["nll"][indices].mean())
                    if probabilistic is not None
                    else float("nan")
                ),
                coverage_50=(
                    float(probabilistic["coverage_50"][indices].mean())
                    if probabilistic is not None
                    else float("nan")
                ),
                coverage_90=(
                    float(probabilistic["coverage_90"][indices].mean())
                    if probabilistic is not None
                    else float("nan")
                ),
                coverage_95=(
                    float(probabilistic["coverage_95"][indices].mean())
                    if probabilistic is not None
                    else float("nan")
                ),
            )
        )
    return rows


def rows_as_dicts(rows: list[HeldoutScenarioMetrics]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]
