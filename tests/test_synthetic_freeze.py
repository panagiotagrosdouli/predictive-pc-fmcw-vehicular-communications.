from __future__ import annotations

from pathlib import Path

import pytest

from predictive_pc_fmcw.synthetic.dataset import DatasetBuildConfig, build_dataset
from predictive_pc_fmcw.synthetic.freeze import verify_publication_training_freeze
from predictive_pc_fmcw.synthetic.training_export import build_synthetic_training_npz


def test_freeze_rejects_missing_20_run_completion(tmp_path: Path) -> None:
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
        dataset, training, history_steps=8, horizon_steps=4
    )
    with pytest.raises(PermissionError, match="20-run completion manifest"):
        verify_publication_training_freeze(
            dataset, dataset / "learned_ablation", training
        )
