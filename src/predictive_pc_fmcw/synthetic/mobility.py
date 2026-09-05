"""Deterministic, physics-constrained synthetic vehicular mobility."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticMobilityConfig:
    duration_s: float = 12.0
    sampling_hz: float = 10.0
    initial_range_m: tuple[float, float] = (30.0, 180.0)
    speed_mps: tuple[float, float] = (5.0, 35.0)
    acceleration_mps2: tuple[float, float] = (-4.0, 3.0)
    lateral_speed_mps: tuple[float, float] = (-3.0, 3.0)
    maneuver_duration_s: tuple[float, float] = (2.0, 6.0)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    family: str
    seed: int
    t_s: np.ndarray
    x_m: np.ndarray
    y_m: np.ndarray
    vx_mps: np.ndarray
    vy_mps: np.ndarray
    ax_mps2: np.ndarray
    ay_mps2: np.ndarray
    speed_mps: np.ndarray
    heading_rad: np.ndarray
    range_m: np.ndarray
    radial_velocity_mps: np.ndarray
    bearing_rad: np.ndarray


def _integrate_velocity(velocity: np.ndarray, dt: float, x0: float) -> np.ndarray:
    """Integrate velocity while preserving the exact initial position."""
    displacement = np.zeros_like(velocity, dtype=np.float64)
    if velocity.size > 1:
        increments = 0.5 * (velocity[:-1] + velocity[1:]) * dt
        displacement[1:] = np.cumsum(increments)
    return x0 + displacement


def _kinematics(x: np.ndarray, y: np.ndarray, dt: float) -> tuple[np.ndarray, ...]:
    vx = np.gradient(x, dt)
    vy = np.gradient(y, dt)
    ax = np.gradient(vx, dt)
    ay = np.gradient(vy, dt)
    speed = np.hypot(vx, vy)
    heading = np.arctan2(vy, vx)
    radius = np.hypot(x, y)
    bearing = np.arctan2(y, x)
    radial = np.divide(
        x * vx + y * vy,
        radius,
        out=np.zeros_like(radius),
        where=radius > 0.0,
    )
    return vx, vy, ax, ay, speed, heading, radius, radial, bearing


def generate_scenario(
    family: str,
    seed: int,
    config: SyntheticMobilityConfig | None = None,
) -> Scenario:
    """Generate one deterministic scenario from a family and explicit seed."""
    cfg = config or SyntheticMobilityConfig()
    if cfg.duration_s <= 0.0 or cfg.sampling_hz <= 0.0:
        raise ValueError("duration_s and sampling_hz must be positive")
    if cfg.maneuver_duration_s[0] <= 0.0:
        raise ValueError("maneuver duration must be positive")
    rng = np.random.default_rng(seed)
    dt = 1.0 / cfg.sampling_hz
    t = np.arange(0.0, cfg.duration_s + 0.5 * dt, dt)
    r0 = rng.uniform(*cfg.initial_range_m)
    speed = rng.uniform(*cfg.speed_mps)
    accel = rng.uniform(*cfg.acceleration_mps2)
    lateral = rng.uniform(*cfg.lateral_speed_mps)
    maneuver_duration = rng.uniform(*cfg.maneuver_duration_s)
    x0, y0 = r0, rng.uniform(-3.5, 3.5)

    if family == "constant_velocity":
        x = x0 + speed * t
        y = y0 + lateral * t
    elif family == "constant_acceleration":
        x = x0 + speed * t + 0.5 * accel * t**2
        y = y0 + lateral * t
    elif family == "approaching":
        x = x0 - speed * t
        y = y0 + 0.25 * lateral * t
    elif family == "receding":
        x = x0 + speed * t
        y = y0 + 0.25 * lateral * t
    elif family == "lateral_crossing":
        x = np.full_like(t, x0)
        direction = 1.0 if lateral >= 0.0 else -1.0
        y = y0 + direction * max(abs(lateral), 1.0) * t
    elif family == "lane_change":
        x = x0 + speed * t
        center = 0.45 * cfg.duration_s
        width = max(0.4, 0.25 * maneuver_duration)
        y = y0 + 1.75 * (1.0 + np.tanh((t - center) / width))
    elif family == "curved":
        omega = rng.uniform(0.015, 0.06)
        radius = max(speed / omega, 20.0)
        angle = omega * t
        x = x0 + radius * np.sin(angle)
        y = y0 + radius * (1.0 - np.cos(angle))
    elif family == "stop_and_go":
        period = max(maneuver_duration, 1.0)
        velocity = np.clip(
            speed + 0.45 * speed * np.sin(2.0 * np.pi * t / period),
            0.0,
            None,
        )
        x = _integrate_velocity(velocity, dt, x0)
        y = np.full_like(t, y0)
    elif family == "accelerate_then_brake":
        midpoint = min(0.5 * cfg.duration_s, maneuver_duration)
        a = max(abs(accel), 1.0)
        velocity = np.where(
            t <= midpoint,
            speed + a * t,
            speed + a * midpoint - a * (t - midpoint),
        )
        velocity = np.clip(velocity, 0.0, None)
        x = _integrate_velocity(velocity, dt, x0)
        y = y0 + 0.2 * lateral * t
    elif family == "mixed_nonlinear":
        x = x0 + speed * t + 0.25 * accel * t**2
        period = max(maneuver_duration, 1.0)
        y = y0 + 2.0 * np.sin(2.0 * np.pi * t / period) + 0.15 * lateral * t
    elif family == "high_relative_speed":
        x = x0 - max(speed, 25.0) * t
        y = y0 + 0.5 * lateral * t
    else:
        raise ValueError(f"unsupported synthetic mobility family: {family}")

    values = _kinematics(x, y, dt)
    vx, vy, ax, ay, speed_mps, heading, range_m, radial, bearing = values
    scenario_id = f"{family}-seed-{seed}"
    return Scenario(
        scenario_id=scenario_id,
        family=family,
        seed=seed,
        t_s=t,
        x_m=x,
        y_m=y,
        vx_mps=vx,
        vy_mps=vy,
        ax_mps2=ax,
        ay_mps2=ay,
        speed_mps=speed_mps,
        heading_rad=heading,
        range_m=range_m,
        radial_velocity_mps=radial,
        bearing_rad=bearing,
    )
