"""Scenario-level paired statistics for frozen synthetic scheduling results."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from ..metrics import (
    bootstrap_mean_ci,
    holm_adjusted_pvalues,
    paired_metric_statistics,
)

SCHEDULING_METRICS: dict[str, bool] = {
    "goodput_mbps": True,
    "packet_delivery_ratio": True,
    "deadline_miss_ratio": False,
    "scheduled_outage_fraction": False,
    "mean_latency_ms": False,
    "retransmission_attempts": False,
    "mean_queue_packets": False,
    "jain_fairness": True,
}
PRIMARY_COMPARISONS = (
    ("S6", "S0", "communication_aware_vs_reactive"),
    ("S6", "S5", "communication_aware_vs_trajectory_gru"),
    ("S6", "S2", "communication_aware_vs_cv_predictive"),
)


def aggregate_traffic_seeds(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Average repeated traffic seeds within each independent episode/scheduler."""
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["scenario_id"]), str(row["protocol_id"]))].append(row)
    aggregated: list[dict[str, object]] = []
    for (episode, protocol_id), selected in sorted(grouped.items()):
        seeds = {int(row["traffic_seed"]) for row in selected}
        if len(seeds) != 5:
            raise ValueError(
                f"{episode}/{protocol_id} must contain exactly five paired traffic seeds"
            )
        aggregated.append(
            {
                "scenario_id": episode,
                "protocol_id": protocol_id,
                "traffic_seed_replicates": len(selected),
                **{
                    metric: float(
                        np.mean([float(row[metric]) for row in selected])
                    )
                    for metric in SCHEDULING_METRICS
                },
            }
        )
    return aggregated


def _scheduler_summary(
    episode_rows: list[dict[str, object]],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in episode_rows:
        grouped[str(row["protocol_id"])].append(row)
    summary: dict[str, object] = {}
    for protocol_id, selected in sorted(grouped.items()):
        metrics: dict[str, object] = {}
        for metric in SCHEDULING_METRICS:
            values = np.asarray(
                [float(row[metric]) for row in selected], dtype=np.float64
            )
            interval = bootstrap_mean_ci(
                values,
                samples=bootstrap_samples,
                seed=seed,
            )
            metrics[metric] = {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
                "ci95_low": interval.low,
                "ci95_high": interval.high,
                "episodes": int(values.size),
            }
        summary[protocol_id] = metrics
    return summary


def analyze_scheduling_rows(
    rows: list[dict[str, object]],
    *,
    bootstrap_samples: int = 5000,
    seed: int = 20260905,
) -> dict[str, object]:
    """Compute paired inference after collapsing traffic-seed replication."""
    episode_rows = aggregate_traffic_seeds(rows)
    indexed = {
        (str(row["scenario_id"]), str(row["protocol_id"])): row
        for row in episode_rows
    }
    comparisons: dict[str, dict[str, object]] = {}
    test_keys: list[tuple[str, str]] = []
    t_values: list[float] = []
    w_values: list[float] = []

    for proposed, baseline, name in PRIMARY_COMPARISONS:
        episodes = sorted(
            episode
            for episode, protocol_id in indexed
            if protocol_id == proposed and (episode, baseline) in indexed
        )
        if not episodes:
            raise ValueError(f"no paired episodes for {name}")
        metric_results: dict[str, object] = {}
        for metric, higher_is_better in SCHEDULING_METRICS.items():
            proposed_values = np.asarray(
                [float(indexed[(episode, proposed)][metric]) for episode in episodes]
            )
            baseline_values = np.asarray(
                [float(indexed[(episode, baseline)][metric]) for episode in episodes]
            )
            result = paired_metric_statistics(
                proposed_values,
                baseline_values,
                higher_is_better=higher_is_better,
                samples=bootstrap_samples,
                seed=seed,
            )
            metric_results[metric] = result
            test_keys.append((name, metric))
            t_values.append(float(result["paired_t_test_p_value"]))
            w_values.append(float(result["wilcoxon_p_value"]))
        comparisons[name] = {
            "proposed": proposed,
            "baseline": baseline,
            "episodes": len(episodes),
            "metrics": metric_results,
        }

    adjusted_t = holm_adjusted_pvalues(t_values)
    adjusted_w = holm_adjusted_pvalues(w_values)
    for (name, metric), t_value, w_value in zip(
        test_keys, adjusted_t, adjusted_w, strict=True
    ):
        metric_result = comparisons[name]["metrics"][metric]
        assert isinstance(metric_result, dict)
        metric_result["paired_t_test_holm_p_value"] = t_value
        metric_result["wilcoxon_holm_p_value"] = w_value

    return {
        "inferential_unit": "scenario_episode",
        "traffic_seed_handling": (
            "five paired traffic-seed replicates averaged within episode before inference"
        ),
        "episode_rows": episode_rows,
        "scheduler_summary": _scheduler_summary(
            episode_rows,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        ),
        "primary_comparisons": comparisons,
        "multiplicity_correction": "Holm across all primary comparison-metric tests",
    }


def analyze_scheduling_file(
    scheduling_json: str | Path,
    output_json: str | Path,
    *,
    bootstrap_samples: int = 5000,
    seed: int = 20260905,
) -> dict[str, object]:
    source = json.loads(Path(scheduling_json).read_text(encoding="utf-8"))
    rows = source.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("scheduling artifact contains no result rows")
    report = analyze_scheduling_rows(
        rows,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    destination = Path(output_json)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite statistics artifact: {destination}")
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
