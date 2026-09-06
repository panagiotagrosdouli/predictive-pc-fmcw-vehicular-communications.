from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path

from .benchmark import run_synthetic_benchmark
from .config import ExperimentConfig


@dataclass(frozen=True)
class AblationSpec:
    name: str
    scheduler: str
    channel_mode: str = "full"
    traffic_model: str = "poisson"
    fairness_weight: float | None = None
    lifetime_weight: float | None = None
    history_noise_std_m: float = 0.0
    forecast_noise_std_m: float = 0.0
    use_ber_lut: bool = False


def paper_ablation_specs() -> tuple[AblationSpec, ...]:
    """Return the paper-ablation design without duplicate scientific conditions.

    ``trajectory_predictive`` is the zero-lifetime-urgency reference: the
    predictive-utility and link-lifetime schedulers use the same
    constant-acceleration forecast and base utility, so setting
    ``lifetime_weight=0`` on the link-lifetime scheduler is behaviorally
    equivalent to ``trajectory_predictive``.

    ``full_channel`` is retained only as the explicitly named reference point
    for the channel-model ablation plot. It is intentionally equivalent to the
    default ``link_lifetime`` condition and must not be counted as an
    independent scheduler ablation or statistical comparison.
    """

    return (
        AblationSpec("no_prediction", "reactive_greedy"),
        AblationSpec("cv_predictor", "cv_predictive"),
        AblationSpec("kalman_predictor", "kalman_predictive"),
        AblationSpec("imm_predictor", "imm_predictive"),
        AblationSpec("trajectory_predictive", "predictive_utility"),
        AblationSpec("link_lifetime", "link_lifetime"),
        AblationSpec("perfect_future", "oracle"),
        AblationSpec(
            "no_fairness_term", "predictive_utility", fairness_weight=0.0
        ),
        AblationSpec(
            "range_only_channel", "link_lifetime", channel_mode="range_only"
        ),
        AblationSpec(
            "range_pointing_channel",
            "link_lifetime",
            channel_mode="range_pointing",
        ),
        # Intentional reference alias for the channel-model ablation only.
        AblationSpec("full_channel", "link_lifetime"),
        AblationSpec(
            "part_a_ber_lut", "link_lifetime", use_ber_lut=True
        ),
        AblationSpec(
            "history_noise_0_5m",
            "link_lifetime",
            history_noise_std_m=0.5,
        ),
        AblationSpec(
            "history_noise_1m", "link_lifetime", history_noise_std_m=1.0
        ),
        AblationSpec(
            "history_noise_2m", "link_lifetime", history_noise_std_m=2.0
        ),
        AblationSpec(
            "forecast_error_0_5m",
            "link_lifetime",
            forecast_noise_std_m=0.5,
        ),
        AblationSpec(
            "forecast_error_1m", "link_lifetime", forecast_noise_std_m=1.0
        ),
        AblationSpec(
            "forecast_error_2m", "link_lifetime", forecast_noise_std_m=2.0
        ),
        AblationSpec(
            "periodic_traffic", "link_lifetime", traffic_model="periodic"
        ),
        AblationSpec(
            "markov_traffic",
            "link_lifetime",
            traffic_model="markov_modulated",
        ),
    )


def run_paper_ablations(
    config: ExperimentConfig,
    ber_lut_path: str | Path,
    quick: bool = False,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    lut_path = Path(ber_lut_path)
    for spec in paper_ablation_specs():
        if spec.use_ber_lut and not lut_path.exists():
            raise FileNotFoundError(f"BER LUT not found: {lut_path}")
        link = replace(
            config.link,
            channel_mode=spec.channel_mode,
            ber_source="lut" if spec.use_ber_lut else "analytical",
            ber_lut_path=str(lut_path) if spec.use_ber_lut else None,
        )
        scheduler = replace(
            config.scheduler,
            fairness_weight=(
                config.scheduler.fairness_weight
                if spec.fairness_weight is None
                else spec.fairness_weight
            ),
            lifetime_weight=(
                config.scheduler.lifetime_weight
                if spec.lifetime_weight is None
                else spec.lifetime_weight
            ),
        )
        traffic = replace(config.traffic, model=spec.traffic_model)
        benchmark = replace(
            config.benchmark,
            episodes=(
                min(config.benchmark.episodes, 2)
                if quick
                else config.benchmark.episodes
            ),
            schedulers=(spec.scheduler,),
        )
        current = replace(
            config,
            link=link,
            scheduler=scheduler,
            traffic=traffic,
            benchmark=benchmark,
            history_measurement_noise_std_m=spec.history_noise_std_m,
            forecast_position_noise_std_m=spec.forecast_noise_std_m,
        )
        for output in run_synthetic_benchmark(current):
            row = output.metrics.to_dict()
            row.update(
                {
                    "ablation": spec.name,
                    "channel_mode": spec.channel_mode,
                    "traffic_model": spec.traffic_model,
                    "history_noise_std_m": spec.history_noise_std_m,
                    "forecast_noise_std_m": spec.forecast_noise_std_m,
                    "ber_source": link.ber_source,
                }
            )
            rows.append(row)
    return rows


def write_ablation_artifacts(
    rows: list[dict[str, object]], output_dir: str | Path
) -> dict[str, Path]:
    if not rows:
        raise ValueError("No ablation rows were produced.")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "paper_ablation_rows.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    csv_path = destination / "paper_ablation_rows.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    summary = _summarize(rows)
    summary_path = destination / "paper_ablation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "summary": summary_path}


def _summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    metrics = (
        "goodput_mbps",
        "packet_delivery_ratio",
        "deadline_miss_ratio",
        "p95_latency_ms",
        "jain_fairness",
        "delivered_before_expiry_ratio",
        "undelivered_packets_at_disconnect",
    )
    result: dict[str, object] = {}
    for name in sorted({str(row["ablation"]) for row in rows}):
        selected = [row for row in rows if row["ablation"] == name]
        result[name] = {
            "samples": len(selected),
            **{
                metric: sum(float(row[metric]) for row in selected) / len(selected)
                for metric in metrics
            },
        }
    return result
