import pytest

from predictive_pc_fmcw.config import ExperimentConfig
from predictive_pc_fmcw.synthetic.operating_region import (
    OPERATING_CONDITIONS,
    _condition_config,
    operating_region_protocol_manifest,
    validate_nominal_operating_config,
    validate_operating_region_protocol,
)


def test_operating_region_conditions_are_one_factor_at_a_time() -> None:
    validate_operating_region_protocol()
    names = [condition.name for condition in OPERATING_CONDITIONS]
    assert names[0] == "nominal"
    assert len(names) == len(set(names))
    manifest = operating_region_protocol_manifest()
    assert manifest["mobility_axes_analyzed_at_episode_level"] is True
    assert manifest["nominal_prediction_horizon_steps"] == 10


def test_operating_condition_changes_only_requested_factor() -> None:
    base = ExperimentConfig()
    condition = next(
        item for item in OPERATING_CONDITIONS if item.name == "load_1_1"
    )
    changed = _condition_config(base, condition)
    assert changed.traffic.offered_load == 1.1
    assert changed.link == base.link
    assert changed.prediction_horizon_steps == base.prediction_horizon_steps


def test_horizon_sweep_never_exceeds_checkpoint_horizon() -> None:
    horizons = [
        item.prediction_horizon_steps
        for item in OPERATING_CONDITIONS
        if item.prediction_horizon_steps is not None
    ]
    assert horizons
    assert max(horizons) <= 10


def test_nominal_operating_config_requires_horizon_ten() -> None:
    validate_nominal_operating_config(ExperimentConfig(prediction_horizon_steps=10))
    with pytest.raises(ValueError, match="prediction horizon 10"):
        validate_nominal_operating_config(
            ExperimentConfig(prediction_horizon_steps=5)
        )
