from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray


class TrajectoryPredictor(Protocol):
    name: str

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]: ...


def _validate_history(history_xy: ArrayLike) -> NDArray[np.float64]:
    history = np.asarray(history_xy, dtype=np.float64)
    if history.ndim < 2 or history.shape[-1] != 2 or history.shape[-2] < 2:
        raise ValueError("history_xy must have shape (..., history, 2), history >= 2.")
    if not np.all(np.isfinite(history)):
        raise ValueError("history_xy must contain only finite values.")
    return history


def _validate_prediction_request(horizon_steps: int, dt_s: float) -> None:
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be positive.")
    if not np.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("dt_s must be a finite positive value.")


@dataclass(frozen=True)
class LastPositionPredictor:
    """No-motion lower bound used by the paper ablations."""

    name: str = "last_position"

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]:
        _validate_prediction_request(horizon_steps, dt_s)
        history = _validate_history(history_xy)
        return np.repeat(history[..., -1, None, :], horizon_steps, axis=-2)


@dataclass(frozen=True)
class ConstantVelocityPredictor:
    name: str = "constant_velocity"

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]:
        _validate_prediction_request(horizon_steps, dt_s)
        history = _validate_history(history_xy)
        velocity = (history[..., -1, :] - history[..., -2, :]) / dt_s
        steps = np.arange(1, horizon_steps + 1, dtype=np.float64)
        return history[..., -1, None, :] + velocity[..., None, :] * (
            steps * dt_s
        )[..., None]


@dataclass(frozen=True)
class ConstantAccelerationPredictor:
    acceleration_clip_mps2: float = 6.0
    name: str = "constant_acceleration"

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]:
        _validate_prediction_request(horizon_steps, dt_s)
        history = _validate_history(history_xy)
        if history.shape[-2] < 3:
            return ConstantVelocityPredictor().predict(history, horizon_steps, dt_s)
        velocity_now = (history[..., -1, :] - history[..., -2, :]) / dt_s
        velocity_before = (history[..., -2, :] - history[..., -3, :]) / dt_s
        acceleration = (velocity_now - velocity_before) / dt_s
        norm = np.linalg.norm(acceleration, axis=-1, keepdims=True)
        acceleration = acceleration * np.minimum(
            1.0, self.acceleration_clip_mps2 / np.maximum(norm, 1e-12)
        )
        tau = np.arange(1, horizon_steps + 1, dtype=np.float64) * dt_s
        return (
            history[..., -1, None, :]
            + velocity_now[..., None, :] * tau[..., None]
            + 0.5 * acceleration[..., None, :] * tau[..., None] ** 2
        )


@dataclass(frozen=True)
class KalmanConstantVelocityPredictor:
    """Causal 2-D constant-velocity Kalman baseline.

    The filter consumes positions only. Dataset-provided future velocity is
    never used, which keeps the comparison deployable and leakage-free.
    """

    process_acceleration_std_mps2: float = 2.0
    measurement_std_m: float = 0.75
    name: str = "kalman_cv"

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]:
        _validate_prediction_request(horizon_steps, dt_s)
        history = _validate_history(history_xy)
        leading = history.shape[:-2]
        flattened = history.reshape(-1, history.shape[-2], 2)
        output = np.empty((flattened.shape[0], horizon_steps, 2))
        transition = np.asarray(
            [
                [1.0, 0.0, dt_s, 0.0],
                [0.0, 1.0, 0.0, dt_s],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        observation = np.asarray(
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]
        )
        dt2 = dt_s**2
        dt3 = dt_s**3
        dt4 = dt_s**4
        process = self.process_acceleration_std_mps2**2 * np.asarray(
            [
                [dt4 / 4, 0.0, dt3 / 2, 0.0],
                [0.0, dt4 / 4, 0.0, dt3 / 2],
                [dt3 / 2, 0.0, dt2, 0.0],
                [0.0, dt3 / 2, 0.0, dt2],
            ]
        )
        measurement = np.eye(2) * self.measurement_std_m**2
        identity = np.eye(4)
        for row_index, positions in enumerate(flattened):
            velocity = (positions[1] - positions[0]) / dt_s
            state = np.concatenate([positions[0], velocity])
            covariance = np.diag([1.0, 1.0, 25.0, 25.0])
            for measured in positions[1:]:
                state = transition @ state
                covariance = transition @ covariance @ transition.T + process
                innovation = measured - observation @ state
                innovation_covariance = (
                    observation @ covariance @ observation.T + measurement
                )
                gain = (
                    covariance
                    @ observation.T
                    @ np.linalg.inv(innovation_covariance)
                )
                state = state + gain @ innovation
                covariance = (identity - gain @ observation) @ covariance
            future_state = state.copy()
            for step in range(horizon_steps):
                future_state = transition @ future_state
                output[row_index, step] = future_state[:2]
        return output.reshape(*leading, horizon_steps, 2)


@dataclass(frozen=True)
class InteractingMultipleModelPredictor:
    """Lightweight causal CV/CA multiple-model baseline.

    The last-step innovation assigns probabilities to a filtered CV model and
    a bounded-acceleration model. This provides an interpretable maneuver-aware
    baseline without importing annotated future velocity.
    """

    innovation_std_m: float = 1.5
    measurement_std_m: float = 0.75
    name: str = "imm"

    def predict(
        self, history_xy: ArrayLike, horizon_steps: int, dt_s: float
    ) -> NDArray[np.float64]:
        _validate_prediction_request(horizon_steps, dt_s)
        history = _validate_history(history_xy)
        cv = KalmanConstantVelocityPredictor(
            measurement_std_m=self.measurement_std_m
        ).predict(
            history, horizon_steps, dt_s
        )
        ca = ConstantAccelerationPredictor().predict(
            history, horizon_steps, dt_s
        )
        if history.shape[-2] < 4:
            return 0.5 * (cv + ca)
        previous_velocity = (
            history[..., -2, :] - history[..., -3, :]
        ) / dt_s
        cv_last = history[..., -2, :] + previous_velocity * dt_s
        older_velocity = (
            history[..., -3, :] - history[..., -4, :]
        ) / dt_s
        acceleration = (previous_velocity - older_velocity) / dt_s
        ca_last = (
            history[..., -2, :]
            + previous_velocity * dt_s
            + 0.5 * acceleration * dt_s**2
        )
        cv_error = np.sum((history[..., -1, :] - cv_last) ** 2, axis=-1)
        ca_error = np.sum((history[..., -1, :] - ca_last) ** 2, axis=-1)
        variance = max(self.innovation_std_m**2, 1e-12)
        cv_likelihood = np.exp(-0.5 * cv_error / variance)
        ca_likelihood = np.exp(-0.5 * ca_error / variance)
        ca_probability = ca_likelihood / np.maximum(
            cv_likelihood + ca_likelihood, 1e-12
        )
        weight = ca_probability[..., None, None]
        return (1.0 - weight) * cv + weight * ca


@dataclass(frozen=True)
class ForecastBundle:
    ego_xy: NDArray[np.float64]
    vehicle_xy: NDArray[np.float64]
    future_indices: NDArray[np.int64]
    oracle: bool


def forecast_scenario(
    combined_positions: NDArray[np.float64],
    time_index: int,
    horizon_steps: int,
    dt_s: float,
    predictor: TrajectoryPredictor | None,
    oracle: bool = False,
) -> ForecastBundle:
    _validate_prediction_request(horizon_steps, dt_s)
    positions = np.asarray(combined_positions, dtype=np.float64)
    if positions.ndim != 3 or positions.shape[-1] != 2 or positions.shape[1] < 2:
        raise ValueError(
            "combined_positions must have shape (time, actors, 2), actors >= 2."
        )
    if positions.shape[0] < 1:
        raise ValueError("combined_positions must contain at least one time step.")
    if not np.all(np.isfinite(positions)):
        raise ValueError("combined_positions must contain only finite values.")
    if not 0 <= time_index < positions.shape[0]:
        raise IndexError("time_index must reference an available time step.")

    total = positions.shape[0]
    indices = np.minimum(
        np.arange(time_index + 1, time_index + horizon_steps + 1), total - 1
    ).astype(np.int64)
    if oracle:
        prediction = positions[indices].transpose(1, 0, 2)
    else:
        if predictor is None:
            current = positions[time_index].transpose(0, 1)
            prediction = np.repeat(current[:, None, :], horizon_steps, axis=1)
        else:
            causal_history = positions[: time_index + 1].transpose(1, 0, 2)
            prediction = predictor.predict(causal_history, horizon_steps, dt_s)
    return ForecastBundle(
        ego_xy=prediction[0],
        vehicle_xy=prediction[1:],
        future_indices=indices,
        oracle=oracle,
    )
