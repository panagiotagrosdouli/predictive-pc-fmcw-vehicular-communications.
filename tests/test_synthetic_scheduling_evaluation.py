from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.scheduling_evaluation import (
    _load_selected_predictors,
    build_scheduling_plan,
)


def test_scheduling_plan_is_exact_eight_by_five_per_episode() -> None:
    plan = build_scheduling_plan(episode_count=3)
    assert plan["scheduler_families"] == 8
    assert plan["traffic_seeds"] == 5
    assert plan["runs_per_episode"] == 40
    assert plan["planned_runs"] == 120


def test_scheduling_plan_requires_episode() -> None:
    with pytest.raises(ValueError, match="positive"):
        build_scheduling_plan(episode_count=0)


def test_learned_scheduling_requires_development_selection_manifest(
    tmp_path: Path,
) -> None:
    with pytest.raises(PermissionError, match="selection manifest"):
        _load_selected_predictors(
            tmp_path / "missing.json",
            ablation_dir=tmp_path / "ablation",
            training_sha256="deadbeef",
        )
