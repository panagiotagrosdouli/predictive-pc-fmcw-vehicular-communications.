"""Causal noisy observations for synthetic PC-FMCW sensing studies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .mobility import Scenario


@dataclass(frozen=True)
class ObservationNoiseConfig:
    range_std_m: float = 0.05
    radial_velocity_std_mps: float = 0.10
    bearing_std_rad: float = np.deg2rad(0.10)


@dataclass(frozen=True)
class CausalObservations:
    scenario_id: str
    seed: int
    t_s: np.ndarray
    range_m: np.ndarray
    radial_velocity_mps: np.ndarray
    bearing_rad: np.ndarray

    def history_through(self, index: int) -> CausalObservations:
        """Return only measurements available at or before ``index``."""
        if index < 0 or index >= self.t_s.size:
            raise IndexError("observation history index out of bounds")
        stop = index + 1
        return CausalObservations(
            scenario_id=self.scenario_id,
            seed=self.seed,
            t_s=self.t_s[:stop].copy(),
            range_m=self.range_m[:stop].copy(),
            radial_velocity_mps=self.radial_velocity_mps[:stop].copy(),
            bearing_rad=self.bearing_rad[:stop].copy(),
        )


def observe_scenario(
    scenario: Scenario,
    seed: int,
    config: ObservationNoiseConfig | None = None,
) -> CausalObservations:
    """Generate deterministic noisy measurements from ground truth.

    Noise is generated solely from the supplied observation seed. The returned
    object contains no future-derived features; consumers must request causal
    histories with :meth:`CausalObservations.history_through` at prediction time.
    """
    cfg = config or ObservationNoiseConfig()
    if min(cfg.range_std_m, cfg.radial_velocity_std_mps, cfg.bearing_std_rad) < 0.0:
        raise ValueError("observation standard deviations must be non-negative")
    rng = np.random.default_rng(seed)
    measured_range = scenario.range_m + rng.normal(
        0.0,
        cfg.range_std_m,
        scenario.t_s.size,
    )
    measured_range = np.maximum(measured_range, 0.0)
    measured_radial = scenario.radial_velocity_mps + rng.normal(
        0.0, cfg.radial_velocity_std_mps, scenario.t_s.size
    )
    measured_bearing = scenario.bearing_rad + rng.normal(
        0.0, cfg.bearing_std_rad, scenario.t_s.size
    )
    measured_bearing = np.arctan2(
        np.sin(measured_bearing),
        np.cos(measured_bearing),
    )
    return CausalObservations(
        scenario_id=scenario.scenario_id,
        seed=seed,
        t_s=scenario.t_s.copy(),
        range_m=measured_range,
        radial_velocity_mps=measured_radial,
        bearing_rad=measured_bearing,
    )
