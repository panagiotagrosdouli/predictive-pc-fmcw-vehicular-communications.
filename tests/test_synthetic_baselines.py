from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.baselines import evaluate_synthetic_baselines
from predictive_pc_fmcw.synthetic.dataset import DatasetBuildConfig, build_dataset


def _dataset(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    build_dataset(
        root,
        config=DatasetBuildConfig(
            scenarios_per_family=2,
            ood_scenarios_per_family=1,
        ),
    )
    return root


def test_development_baselines_cover_b0_to_b4(tmp_path: Path) -> None:
    results = evaluate_synthetic_baselines(
        _dataset(tmp_path),
        split="development",
        history_steps=8,
        horizon_steps=4,
        stride=10,
    )
    names = {row.predictor for row in results}
    assert names == {
        "last_position",
        "constant_velocity",
        "constant_acceleration",
        "kalman_cv",
        "imm",
    }
    assert all(row.windows > 0 for row in results)
    assert all(row.ade_m >= 0.0 for row in results)


def test_heldout_requires_explicit_opt_in(tmp_path: Path) -> None:
    root = _dataset(tmp_path)
    with pytest.raises(PermissionError, match="explicit"):
        evaluate_synthetic_baselines(
            root,
            split="held_out_test",
            history_steps=8,
            horizon_steps=4,
        )


def test_heldout_can_be_run_only_with_explicit_opt_in(tmp_path: Path) -> None:
    results = evaluate_synthetic_baselines(
        _dataset(tmp_path),
        split="held_out_test",
        history_steps=8,
        horizon_steps=4,
        stride=20,
        allow_official_test=True,
    )
    assert len(results) == 5
    assert all(row.split == "held_out_test" for row in results)
