from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .benchmark import run_synthetic_benchmark
from .config import ExperimentConfig
from .metrics import holm_adjusted_pvalues, paired_metric_statistics

STAGED_SCHEDULERS = (
    "reactive_greedy",
    "proportional_fair",
    "kalman_predictive",
    "predictive_utility",
    "link_lifetime",
    "oracle",
)

METRIC_DIRECTIONS = {
    "goodput_mbps": True,
    "packet_delivery_ratio": True,
    "scheduled_outage_fraction": False,
    "p95_latency_ms": False,
    "deadline_or_censored_ratio": False,
    "delivered_before_expiry_ratio": True,
    "demand_normalized_jain_fairness": True,
}


def _reference(config: ExperimentConfig, *, seed: int) -> ExperimentConfig:
    return replace(
        config,
        seed=seed,
        benchmark=replace(
            config.benchmark,
            episodes=1,
            schedulers=STAGED_SCHEDULERS,
        ),
    )


def _staged_settings(
    config: ExperimentConfig, *, seed: int
) -> list[tuple[str, str, ExperimentConfig]]:
    base = _reference(config, seed=seed)
    settings: list[tuple[str, str, ExperimentConfig]] = []

    for load in (0.3, 0.5, 0.7, 0.9, 1.1):
        settings.append(
            (
                "offered_load",
                f"load={load:g}",
                replace(base, traffic=replace(base.traffic, offered_load=load)),
            )
        )
    for horizon_s in (0.1, 0.3, 0.5, 1.0, 2.0):
        steps = max(1, int(round(horizon_s / base.slot_duration_s)))
        settings.append(
            (
                "prediction_horizon",
                f"horizon_s={horizon_s:g}",
                replace(base, prediction_horizon_steps=steps),
            )
        )
    for slot_s in (0.05, 0.1, 0.2):
        horizon_s = config.prediction_horizon_steps * config.slot_duration_s
        steps = max(1, int(round(horizon_s / slot_s)))
        settings.append(
            (
                "slot_duration",
                f"slot_s={slot_s:g}",
                replace(base, slot_duration_s=slot_s, prediction_horizon_steps=steps),
            )
        )
    for vehicles in (3, 5, 10):
        settings.append(
            (
                "vehicle_count",
                f"vehicles={vehicles}",
                replace(base, benchmark=replace(base.benchmark, vehicles=vehicles)),
            )
        )
    for model in ("poisson", "periodic", "markov_modulated", "saturated"):
        settings.append(
            (
                "traffic_model",
                f"traffic={model}",
                replace(base, traffic=replace(base.traffic, model=model)),
            )
        )
    for class_mode in ("single", "urgent_bulk"):
        settings.append(
            (
                "traffic_class",
                f"classes={class_mode}",
                replace(
                    base,
                    traffic=replace(
                        base.traffic, traffic_class_mode=class_mode
                    ),
                ),
            )
        )
    for packet_bits in (2_400, 9_600, 12_000):
        settings.append(
            (
                "packet_size",
                f"packet_bits={packet_bits}",
                replace(base, link=replace(base.link, packet_bits=packet_bits)),
            )
        )
    for deadline_s in (0.05, 0.1, 0.25, 0.5, 1.0):
        settings.append(
            (
                "deadline",
                f"deadline_s={deadline_s:g}",
                replace(
                    base,
                    traffic=replace(
                        base.traffic, deadline_s=deadline_s, deadline_jitter_s=0.0
                    ),
                ),
            )
        )
    for offset_db in (-6.0, -3.0, 0.0, 3.0, 6.0):
        settings.append(
            (
                "reference_snr",
                f"snr_offset_db={offset_db:g}",
                replace(
                    base,
                    link=replace(
                        base.link,
                        reference_snr_db=base.link.reference_snr_db + offset_db,
                    ),
                ),
            )
        )
    for fov_deg in (50.0, 70.0, 90.0):
        settings.append(
            (
                "field_of_view",
                f"fov_deg={fov_deg:g}",
                replace(base, link=replace(base.link, field_of_view_deg=fov_deg)),
            )
        )
    for outage_mode in ("ber", "per", "goodput"):
        settings.append(
            (
                "outage_definition",
                f"outage={outage_mode}",
                replace(base, link=replace(base.link, outage_mode=outage_mode)),
            )
        )
    sensing_settings = (
        ("perfect", "perfect", True, 0.0),
        ("cartesian_iid", "cartesian_0.75m", False, 0.0),
        ("range_bearing_assumed", "range_bearing_exact_R", False, 0.4),
        ("range_bearing_assumed", "range_bearing_covariance_R", True, 0.4),
    )
    for model, label, covariance_aware, correlation in sensing_settings:
        settings.append(
            (
                "sensing_uncertainty",
                label,
                replace(
                    base,
                    sensing=replace(
                        base.sensing,
                        model=model,
                        covariance_aware=covariance_aware,
                        temporal_correlation=correlation,
                    ),
                ),
            )
        )
    return settings


def run_staged_experiments(
    config: ExperimentConfig,
    seeds: tuple[int, ...] = (
        20260827,
        20260828,
        20260829,
        20260830,
        20260831,
    ),
    *,
    quick: bool = False,
) -> list[dict[str, object]]:
    if not seeds:
        raise ValueError("At least one independent seed is required.")
    selected_seeds = seeds[:2] if quick else seeds
    rows: list[dict[str, object]] = []
    for seed in selected_seeds:
        for study, setting, current in _staged_settings(config, seed=seed):
            for output in run_synthetic_benchmark(current):
                row = output.metrics.to_dict()
                row.update(
                    {
                        "study": study,
                        "setting": setting,
                        "prediction_horizon_s": (
                            current.prediction_horizon_steps
                            * current.slot_duration_s
                        ),
                        "slot_duration_s": current.slot_duration_s,
                        "offered_load": current.traffic.offered_load,
                        "traffic_model": current.traffic.model,
                        "traffic_class_mode": (
                            current.traffic.traffic_class_mode
                        ),
                        "packet_bits": current.link.packet_bits,
                        "deadline_s": current.traffic.deadline_s,
                        "reference_snr_db": current.link.reference_snr_db,
                        "field_of_view_deg": current.link.field_of_view_deg,
                        "outage_mode": current.link.outage_mode,
                        "sensing_model": current.sensing.model,
                        "sensing_covariance_aware": (
                            current.sensing.covariance_aware
                        ),
                        "diagnostic_quick_run": quick,
                    }
                )
                rows.append(row)
    return rows


def _paired_comparison(
    selected: list[dict[str, object]],
    proposed_scheduler: str,
    reference_scheduler: str,
) -> dict[str, Any]:
    by_scheduler_seed = {
        (str(row["scheduler"]), int(row["seed"])): row for row in selected
    }
    proposed_rows = [
        row for row in selected if row["scheduler"] == proposed_scheduler
    ]
    metric_results: dict[str, Any] = {}
    for metric, higher_is_better in METRIC_DIRECTIONS.items():
        proposed = []
        reference = []
        clusters = []
        for row in proposed_rows:
            seed = int(row["seed"])
            reference_row = by_scheduler_seed[(reference_scheduler, seed)]
            proposed.append(float(row[metric]))
            reference.append(float(reference_row[metric]))
            clusters.append(seed)
        metric_results[metric] = paired_metric_statistics(
            proposed,
            reference,
            higher_is_better=higher_is_better,
            clusters=clusters,
        )
    raw_p = [
        metric_results[metric]["wilcoxon_p_value"] for metric in METRIC_DIRECTIONS
    ]
    adjusted = holm_adjusted_pvalues(raw_p)
    for metric, value in zip(METRIC_DIRECTIONS, adjusted, strict=True):
        metric_results[metric]["wilcoxon_holm_p_value"] = value
    return metric_results


def summarize_staged_experiments(
    rows: list[dict[str, object]],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["study"]), str(row["setting"]))
        grouped.setdefault(key, []).append(row)
    summary: dict[str, Any] = {}
    for (study, setting), selected in sorted(grouped.items()):
        scheduler_names = sorted({str(row["scheduler"]) for row in selected})
        comparisons: dict[str, Any] = {}
        for scheduler in scheduler_names:
            if scheduler == "reactive_greedy":
                continue
            comparisons[scheduler] = _paired_comparison(
                selected, scheduler, "reactive_greedy"
            )
        mechanism_comparisons: dict[str, Any] = {}
        if {"predictive_utility", "link_lifetime"}.issubset(scheduler_names):
            mechanism_comparisons["link_lifetime_vs_predictive_utility"] = (
                _paired_comparison(selected, "link_lifetime", "predictive_utility")
            )
        if {"link_lifetime", "oracle"}.issubset(scheduler_names):
            mechanism_comparisons["oracle_vs_link_lifetime"] = _paired_comparison(
                selected, "oracle", "link_lifetime"
            )
        summary.setdefault(study, {})[setting] = {
            "independent_seeds": sorted({int(row["seed"]) for row in selected}),
            "comparisons_vs_reactive": comparisons,
            "mechanism_comparisons": mechanism_comparisons,
        }
    return summary


def write_staged_artifacts(
    rows: list[dict[str, object]], output_dir: str | Path
) -> dict[str, Path]:
    if not rows:
        raise ValueError("No staged experiment rows were produced.")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "staged_experiment_rows.json"
    json_path.write_text(json.dumps(rows, indent=2, allow_nan=True), encoding="utf-8")
    csv_path = destination / "staged_experiment_rows.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary_path = destination / "staged_experiment_summary.json"
    summary_path.write_text(
        json.dumps(summarize_staged_experiments(rows), indent=2, allow_nan=True),
        encoding="utf-8",
    )
    manifest_path = destination / "staged_experiment_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "design": "one-axis-at-a-time around frozen reference",
                "rows": len(rows),
                "studies": sorted({str(row["study"]) for row in rows}),
                "schedulers": sorted({str(row["scheduler"]) for row in rows}),
                "seeds": sorted({int(row["seed"]) for row in rows}),
                "diagnostic_quick_run": all(
                    bool(row["diagnostic_quick_run"]) for row in rows
                ),
                "mechanism_pairs": [
                    "link_lifetime_vs_predictive_utility",
                    "oracle_vs_link_lifetime",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "json": json_path,
        "csv": csv_path,
        "summary": summary_path,
        "manifest": manifest_path,
    }
