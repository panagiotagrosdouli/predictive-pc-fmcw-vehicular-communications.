import numpy as np
import pytest

from predictive_pc_fmcw.synthetic.mobility import (
    SyntheticMobilityConfig,
    generate_scenario,
)

FAMILIES = (
    "constant_velocity",
    "constant_acceleration",
    "approaching",
    "receding",
    "lateral_crossing",
    "lane_change",
    "curved",
    "stop_and_go",
    "accelerate_then_brake",
    "mixed_nonlinear",
    "high_relative_speed",
)


@pytest.mark.parametrize("family", FAMILIES)
def test_all_families_are_finite_and_well_shaped(family: str) -> None:
    scenario = generate_scenario(family, seed=20260905)
    arrays = (
        scenario.t_s,
        scenario.x_m,
        scenario.y_m,
        scenario.vx_mps,
        scenario.vy_mps,
        scenario.ax_mps2,
        scenario.ay_mps2,
        scenario.speed_mps,
        scenario.heading_rad,
        scenario.range_m,
        scenario.radial_velocity_mps,
        scenario.bearing_rad,
    )
    assert len({array.shape for array in arrays}) == 1
    assert all(np.all(np.isfinite(array)) for array in arrays)
    assert np.all(scenario.range_m >= 0.0)
    assert np.all(scenario.speed_mps >= 0.0)


def test_generation_is_deterministic_for_seed() -> None:
    first = generate_scenario("lane_change", seed=42)
    second = generate_scenario("lane_change", seed=42)
    np.testing.assert_array_equal(first.x_m, second.x_m)
    np.testing.assert_array_equal(first.y_m, second.y_m)
    assert first.scenario_id == second.scenario_id


def test_seed_changes_scenario() -> None:
    first = generate_scenario("constant_velocity", seed=1)
    second = generate_scenario("constant_velocity", seed=2)
    assert not np.array_equal(first.x_m, second.x_m)


def test_approaching_has_negative_initial_radial_velocity() -> None:
    scenario = generate_scenario("approaching", seed=7)
    assert scenario.radial_velocity_mps[0] < 0.0


def test_invalid_family_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported synthetic mobility family"):
        generate_scenario("not_a_family", seed=1)


def test_sampling_contract() -> None:
    cfg = SyntheticMobilityConfig(duration_s=2.0, sampling_hz=5.0)
    scenario = generate_scenario("constant_velocity", seed=9, config=cfg)
    assert scenario.t_s.size == 11
    np.testing.assert_allclose(np.diff(scenario.t_s), 0.2)


@pytest.mark.parametrize("family", ("stop_and_go", "accelerate_then_brake"))
def test_integrated_maneuvers_preserve_initial_position(family: str) -> None:
    scenario = generate_scenario(family, seed=123)
    rng = np.random.default_rng(123)
    expected_x0 = rng.uniform(30.0, 180.0)
    assert scenario.x_m[0] == pytest.approx(expected_x0)


def test_speed_and_heading_match_velocity_components() -> None:
    scenario = generate_scenario("curved", seed=55)
    np.testing.assert_allclose(
        scenario.speed_mps,
        np.hypot(scenario.vx_mps, scenario.vy_mps),
    )
    np.testing.assert_allclose(
        np.sin(scenario.heading_rad),
        np.sin(np.arctan2(scenario.vy_mps, scenario.vx_mps)),
    )
