from __future__ import annotations

from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.dataset import DatasetBuildConfig, build_dataset
from predictive_pc_fmcw.synthetic.official_export import (
    build_official_evaluation_npz,
)
from predictive_pc_fmcw.synthetic.training_export import build_synthetic_training_npz


def test_official_export_requires_completed_20_run_freeze(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    build_dataset(
        dataset,
        config=DatasetBuildConfig(
            scenarios_per_family=2,
            ood_scenarios_per_family=1,
        ),
    )
    training = dataset / "training_dev.npz"
    build_synthetic_training_npz(
        dataset,
        training,
        history_steps=8,
        horizon_steps=4,
    )
    with pytest.raises(PermissionError, match="20-run completion manifest"):
        build_official_evaluation_npz(
            dataset,
            dataset / "learned_ablation",
            training,
            dataset / "held_out_test.npz",
            split="held_out_test",
            history_steps=8,
            horizon_steps=4,
        )
    assert not (dataset / "held_out_test.npz").exists()


def test_official_export_rejects_development_split(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="official export split"):
        build_official_evaluation_npz(
            tmp_path,
            tmp_path / "ablation",
            tmp_path / "training.npz",
            tmp_path / "development.npz",
            split="development",
        )
