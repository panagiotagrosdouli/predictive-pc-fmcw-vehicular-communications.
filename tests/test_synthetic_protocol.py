from dataclasses import replace

import numpy as np
import pytest

from predictive_pc_fmcw.synthetic.mobility import generate_scenario
from predictive_pc_fmcw.synthetic.observations import (
    ObservationNoiseConfig,
    observe_scenario,
)
from predictive_pc_fmcw.synthetic.splits import (
    build_split_manifest,
    validate_split_manifest,
)


def test_observations_are_seed_deterministic() -> None:
    scenario = generate_scenario("curved", seed=10)
    first = observe_scenario(scenario, seed=20)
    second = observe_scenario(scenario, seed=20)
    np.testing.assert_array_equal(first.range_m, second.range_m)
    np.testing.assert_array_equal(
        first.radial_velocity_mps,
        second.radial_velocity_mps,
    )
    np.testing.assert_array_equal(first.bearing_rad, second.bearing_rad)


def test_zero_noise_recovers_observable_ground_truth() -> None:
    scenario = generate_scenario("constant_velocity", seed=3)
    noise = ObservationNoiseConfig(0.0, 0.0, 0.0)
    observations = observe_scenario(scenario, seed=4, config=noise)
    np.testing.assert_allclose(observations.range_m, scenario.range_m)
    np.testing.assert_allclose(
        observations.radial_velocity_mps,
        scenario.radial_velocity_mps,
    )
    np.testing.assert_allclose(observations.bearing_rad, scenario.bearing_rad)


def test_history_through_contains_no_future_samples() -> None:
    scenario = generate_scenario("lane_change", seed=30)
    observations = observe_scenario(scenario, seed=31)
    index = 17
    history = observations.history_through(index)
    assert history.t_s.size == index + 1
    assert history.t_s[-1] == observations.t_s[index]
    np.testing.assert_array_equal(
        history.range_m,
        observations.range_m[: index + 1],
    )


def test_negative_observation_noise_is_rejected() -> None:
    scenario = generate_scenario("receding", seed=1)
    with pytest.raises(ValueError, match="non-negative"):
        observe_scenario(
            scenario,
            seed=2,
            config=ObservationNoiseConfig(range_std_m=-1.0),
        )


def test_split_manifest_is_deterministic_disjoint_and_fingerprinted() -> None:
    ids = [f"scenario-{i:03d}" for i in range(40)]
    ood = [f"ood-{i:03d}" for i in range(8)]
    first = build_split_manifest(ids, ood, master_seed=20260905)
    second = build_split_manifest(ids, ood, master_seed=20260905)
    assert first == second
    validate_split_manifest(first)
    assert len(first.sha256) == 64
    assert set(first.train).isdisjoint(first.development)
    assert set(first.train).isdisjoint(first.held_out_test)
    assert set(first.development).isdisjoint(first.held_out_test)


def test_split_validator_detects_leakage() -> None:
    manifest = build_split_manifest(
        [f"scenario-{i}" for i in range(20)],
        [f"ood-{i}" for i in range(4)],
        master_seed=5,
    )
    leaked = replace(
        manifest,
        held_out_test=manifest.held_out_test + (manifest.train[0],),
    )
    with pytest.raises(ValueError, match="scenario leakage"):
        validate_split_manifest(leaked)


def test_split_validator_detects_fingerprint_drift() -> None:
    manifest = build_split_manifest(
        [f"scenario-{i}" for i in range(20)],
        [f"ood-{i}" for i in range(4)],
        master_seed=5,
    )
    corrupted = replace(manifest, sha256="0" * 64)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        validate_split_manifest(corrupted)
