from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import ExperimentConfig, load_config

POLICIES = ("predictive_utility", "link_lifetime", "oracle")
METRICS = (
    "goodput_mbps",
    "packet_delivery_ratio",
    "p95_latency_ms",
    "deadline_miss_ratio",
    "delivered_before_expiry_ratio",
    "jain_fairness",
    "demand_normalized_jain_fairness",
)


def _run_condition(
    config: ExperimentConfig,
    *,
    label: str,
) -> dict[str, object]:
    outputs = run_synthetic_benchmark(config, scheduler_names=POLICIES)
    by_key = {
        (output.metrics.scenario_id, int(output.metrics.seed), output.metrics.scheduler): output
        for output in outputs
    }
    episode_keys = sorted(
        {
            (scenario_id, seed)
            for scenario_id, seed, policy in by_key
            if policy == "predictive_utility"
        }
    )
    rows: list[dict[str, object]] = []
    for scenario_id, seed in episode_keys:
        predictive = by_key[(scenario_id, seed, "predictive_utility")]
        lifetime = by_key[(scenario_id, seed, "link_lifetime")]
        oracle = by_key[(scenario_id, seed, "oracle")]
        slots = predictive.selected_vehicle.size
        pu_ll_diff = predictive.selected_vehicle != lifetime.selected_vehicle
        ll_oracle_diff = lifetime.selected_vehicle != oracle.selected_vehicle
        row: dict[str, object] = {
            "condition": label,
            "scenario_id": scenario_id,
            "seed": seed,
            "slots": int(slots),
            "pu_vs_ll_changed_slots": int(pu_ll_diff.sum()),
            "pu_vs_ll_changed_fraction": float(pu_ll_diff.mean()),
            "ll_vs_oracle_changed_slots": int(ll_oracle_diff.sum()),
            "ll_vs_oracle_changed_fraction": float(ll_oracle_diff.mean()),
        }
        for metric in METRICS:
            pu = float(getattr(predictive.metrics, metric))
            ll = float(getattr(lifetime.metrics, metric))
            oracle_value = float(getattr(oracle.metrics, metric))
            row[f"pu_{metric}"] = pu
            row[f"ll_{metric}"] = ll
            row[f"oracle_{metric}"] = oracle_value
            row[f"ll_minus_pu_{metric}"] = ll - pu
            row[f"oracle_minus_ll_{metric}"] = oracle_value - ll
        rows.append(row)

    def summarize_difference(field: str) -> dict[str, float]:
        values = np.asarray([float(row[field]) for row in rows], dtype=np.float64)
        return {
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "min": float(values.min()),
            "max": float(values.max()),
            "nonzero_fraction": float(np.mean(~np.isclose(values, 0.0))),
        }

    summary: dict[str, object] = {
        "condition": label,
        "episodes": len(rows),
        "prediction_horizon_steps": config.prediction_horizon_steps,
        "slot_duration_s": config.slot_duration_s,
        "offered_load": config.traffic.offered_load,
        "deadline_s": config.traffic.deadline_s,
        "pu_vs_ll": {
            "episodes_with_any_decision_change": sum(
                int(row["pu_vs_ll_changed_slots"]) > 0 for row in rows
            ),
            "mean_changed_slot_fraction": float(
                np.mean([row["pu_vs_ll_changed_fraction"] for row in rows])
            ),
            "max_changed_slot_fraction": float(
                np.max([row["pu_vs_ll_changed_fraction"] for row in rows])
            ),
            "metric_differences": {
                metric: summarize_difference(f"ll_minus_pu_{metric}")
                for metric in METRICS
            },
        },
        "ll_vs_oracle": {
            "episodes_with_any_decision_change": sum(
                int(row["ll_vs_oracle_changed_slots"]) > 0 for row in rows
            ),
            "mean_changed_slot_fraction": float(
                np.mean([row["ll_vs_oracle_changed_fraction"] for row in rows])
            ),
            "max_changed_slot_fraction": float(
                np.max([row["ll_vs_oracle_changed_fraction"] for row in rows])
            ),
            "metric_differences": {
                metric: summarize_difference(f"oracle_minus_ll_{metric}")
                for metric in METRICS
            },
        },
    }
    return {"summary": summary, "episodes": rows}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure when lifetime/oracle information changes scheduling decisions."
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument(
        "--output",
        default="results/corrected_scheduler_mechanism.json",
    )
    parser.add_argument(
        "--with-stress-cases",
        action="store_true",
        help="Also run high-load, short-deadline, and long-horizon diagnostics.",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    conditions = [("reference", config)]
    if args.with_stress_cases:
        conditions.extend(
            [
                (
                    "high_load_0_9",
                    replace(config, traffic=replace(config.traffic, offered_load=0.9)),
                ),
                (
                    "short_deadline_0_05s",
                    replace(
                        config,
                        traffic=replace(
                            config.traffic,
                            deadline_s=0.05,
                            deadline_jitter_s=0.0,
                        ),
                    ),
                ),
                (
                    "long_horizon_20_steps",
                    replace(config, prediction_horizon_steps=20),
                ),
            ]
        )
    result = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "purpose": (
            "Decision-level mechanism diagnostic; not canonical publication evidence."
        ),
        "conditions": [
            _run_condition(current, label=label) for label, current in conditions
        ],
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
