import copy

import pytest

from predictive_pc_fmcw.synthetic.scheduling_protocol import PAIRED_TRAFFIC_SEEDS
from predictive_pc_fmcw.synthetic.scheduling_statistics import (
    SCHEDULING_METRICS,
    aggregate_traffic_seeds,
    analyze_scheduling_rows,
)


def _rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for episode in range(3):
        for scheduler in range(8):
            for traffic_seed in PAIRED_TRAFFIC_SEEDS:
                base = float(episode + scheduler + traffic_seed % 3)
                row: dict[str, object] = {
                    "scenario_id": f"episode-{episode}",
                    "protocol_id": f"S{scheduler}",
                    "traffic_seed": traffic_seed,
                }
                for metric, higher_is_better in SCHEDULING_METRICS.items():
                    row[metric] = base if higher_is_better else 20.0 - base
                rows.append(row)
    return rows


def test_statistics_collapse_traffic_seeds_inside_episode() -> None:
    aggregated = aggregate_traffic_seeds(_rows())
    assert len(aggregated) == 24
    assert all(row["traffic_seed_replicates"] == 5 for row in aggregated)


def test_statistics_use_episode_as_independent_unit() -> None:
    report = analyze_scheduling_rows(_rows(), bootstrap_samples=50)
    assert report["inferential_unit"] == "scenario_episode"
    comparisons = report["primary_comparisons"]
    assert comparisons["communication_aware_vs_reactive"]["episodes"] == 3
    assert comparisons["communication_aware_vs_trajectory_gru"]["episodes"] == 3


def test_statistics_reject_duplicate_traffic_seed_rows() -> None:
    rows = _rows()
    duplicate = copy.deepcopy(rows[0])
    rows.append(duplicate)
    with pytest.raises(ValueError, match="exactly five unique"):
        aggregate_traffic_seeds(rows)


def test_statistics_reject_nonfinite_metric_values() -> None:
    rows = _rows()
    rows[0]["goodput_mbps"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        aggregate_traffic_seeds(rows)


def test_statistics_reject_unbalanced_paired_episodes() -> None:
    rows = [
        row
        for row in _rows()
        if not (
            row["scenario_id"] == "episode-2" and row["protocol_id"] == "S0"
        )
    ]
    with pytest.raises(ValueError, match="unbalanced paired episodes"):
        analyze_scheduling_rows(rows, bootstrap_samples=50)
