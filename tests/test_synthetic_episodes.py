from pathlib import Path

import numpy as np

from predictive_pc_fmcw.synthetic.dataset import DatasetBuildConfig, build_dataset
from predictive_pc_fmcw.synthetic.episodes import compose_synthetic_episodes


def test_composed_episodes_are_multi_vehicle_disjoint_and_deterministic(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dataset"
    build_dataset(
        root,
        config=DatasetBuildConfig(
            scenarios_per_family=4,
            ood_scenarios_per_family=1,
        ),
    )
    first = compose_synthetic_episodes(
        root,
        split="development",
        vehicles_per_episode=2,
        history_steps=3,
    )
    second = compose_synthetic_episodes(
        root,
        split="development",
        vehicles_per_episode=2,
        history_steps=3,
    )
    assert first
    assert [item.scenario.scenario_id for item in first] == [
        item.scenario.scenario_id for item in second
    ]
    used = [member for item in first for member in item.member_scenario_ids]
    assert len(used) == len(set(used))
    assert all(item.scenario.vehicle_count == 2 for item in first)
    assert all(item.scenario.start_index == 2 for item in first)
    assert all(np.all(item.scenario.ego_positions_xy == 0.0) for item in first)


def test_scheduling_episode_rejects_single_vehicle(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    build_dataset(
        root,
        config=DatasetBuildConfig(
            scenarios_per_family=1,
            ood_scenarios_per_family=1,
        ),
    )
    try:
        compose_synthetic_episodes(
            root,
            split="ood_test",
            vehicles_per_episode=1,
            history_steps=3,
        )
    except ValueError as exc:
        assert "at least two vehicles" in str(exc)
    else:
        raise AssertionError("single-vehicle scheduling episode must be rejected")
