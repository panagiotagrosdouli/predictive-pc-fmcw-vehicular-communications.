import pytest

from predictive_pc_fmcw.learning.ablation import CANONICAL_SEEDS
from predictive_pc_fmcw.synthetic.checkpoint_selection import (
    select_representative_seed,
)


def _rows() -> list[dict[str, float | int]]:
    return [
        {
            "seed": seed,
            "ade_m": 1.0 + index,
            "fde_m": 2.0 + index,
            "goodput_mae_mbps": 5.0 - index,
            "outage_f1": 0.5 + 0.01 * index,
            "snr_mae_db": 3.0 - 0.1 * index,
        }
        for index, seed in enumerate(CANONICAL_SEEDS)
    ]


def test_trajectory_selection_uses_development_ade_rule() -> None:
    assert select_representative_seed("trajectory_only", _rows()) == CANONICAL_SEEDS[0]


def test_full_selection_uses_communication_rule() -> None:
    assert select_representative_seed("full", _rows()) == CANONICAL_SEEDS[-1]


def test_selection_requires_all_canonical_seeds() -> None:
    with pytest.raises(ValueError, match="all five canonical"):
        select_representative_seed("full", _rows()[:-1])
