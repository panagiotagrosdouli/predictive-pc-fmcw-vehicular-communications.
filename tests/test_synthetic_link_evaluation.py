from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.dataset import DatasetBuildConfig, build_dataset
from predictive_pc_fmcw.synthetic.link_evaluation import (
    evaluate_synthetic_link_prediction,
)


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


def test_development_link_metrics_cover_b0_to_b4(tmp_path: Path) -> None:
    results = evaluate_synthetic_link_prediction(
        _dataset(tmp_path),
        split="development",
        history_steps=8,
        horizon_steps=4,
        stride=20,
    )
    assert {row.predictor for row in results} == {
        "last_position",
        "constant_velocity",
        "constant_acceleration",
        "kalman_cv",
        "imm",
    }
    assert all(row.windows > 0 for row in results)
    assert all(row.snr_mae_db >= 0.0 for row in results)
    assert all(0.0 <= row.outage_disagreement_rate <= 1.0 for row in results)


def test_heldout_link_evaluation_requires_explicit_opt_in(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="explicit"):
        evaluate_synthetic_link_prediction(
            _dataset(tmp_path),
            split="held_out_test",
            history_steps=8,
            horizon_steps=4,
        )
