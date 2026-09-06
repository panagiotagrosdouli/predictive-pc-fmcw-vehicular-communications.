"""Operating-region sweeps for the frozen dataset-free publication study."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from ..config import ExperimentConfig
from ..data.manifest import sha256_file
from .scheduling_evaluation import run_synthetic_scheduling_evaluation
from .scheduling_statistics import aggregate_traffic_seeds


@dataclass(frozen=True)
class OperatingCondition:
    name: str
    prediction_horizon_steps: int | None = None
    reference_snr_db: float | None = None
    offered_load: float | None = None
    deadline_s: float | None = None


OPERATING_CONDITIONS = (
    OperatingCondition("nominal"),
    OperatingCondition("horizon_3", prediction_horizon_steps=3),
    OperatingCondition("horizon_5", prediction_horizon_steps=5),
    OperatingCondition("snr_12db", reference_snr_db=12.0),
    OperatingCondition("snr_24db", reference_snr_db=24.0),
    OperatingCondition("load_0_4", offered_load=0.4),
    OperatingCondition("load_1_1", offered_load=1.1),
    OperatingCondition("deadline_0_4s", deadline_s=0.4),
    OperatingCondition("deadline_0_8s", deadline_s=0.8),
)


def validate_operating_region_protocol() -> None:
    names = [condition.name for condition in OPERATING_CONDITIONS]
    if names[0] != "nominal" or len(names) != len(set(names)):
        raise ValueError("operating-region conditions must be unique and start nominal")
    for condition in OPERATING_CONDITIONS:
        changed = sum(
            value is not None
            for value in (
                condition.prediction_horizon_steps,
                condition.reference_snr_db,
                condition.offered_load,
                condition.deadline_s,
            )
        )
        if condition.name == "nominal" and changed != 0:
            raise ValueError("nominal operating condition must not change a factor")
        if condition.name != "nominal" and changed != 1:
            raise ValueError("operating conditions must vary exactly one factor")
        if condition.prediction_horizon_steps is not None and not (
            1 <= condition.prediction_horizon_steps <= 10
        ):
            raise ValueError("frozen learned checkpoint supports horizons up to 10")
        if condition.offered_load is not None and not (
            0 <= condition.offered_load <= 2
        ):
            raise ValueError("offered-load sweep value is invalid")
        if condition.deadline_s is not None and condition.deadline_s <= 0:
            raise ValueError("deadline sweep values must be positive")


def validate_nominal_operating_config(config: ExperimentConfig) -> None:
    """Fail closed if the nominal horizon drifts from the frozen heatmap label."""
    if config.prediction_horizon_steps != 10:
        raise ValueError(
            "operating-region nominal configuration must use prediction horizon 10"
        )


def operating_region_protocol_manifest() -> dict[str, object]:
    validate_operating_region_protocol()
    return {
        "conditions": [asdict(condition) for condition in OPERATING_CONDITIONS],
        "design": "one_factor_at_a_time_around_frozen_nominal_configuration",
        "nominal_prediction_horizon_steps": 10,
        "mobility_axes": (
            "speed_mps",
            "absolute_radial_velocity_mps",
            "acceleration_mps2",
            "lateral_speed_mps",
        ),
        "mobility_axes_analyzed_at_episode_level": True,
        "observation_uncertainty_sweep": "handled_by_robustness_protocol",
        "ood_mobility": "handled_by_ood_test_split",
    }


def _condition_config(
    config: ExperimentConfig,
    condition: OperatingCondition,
) -> ExperimentConfig:
    current = config
    if condition.prediction_horizon_steps is not None:
        current = replace(
            current,
            prediction_horizon_steps=condition.prediction_horizon_steps,
        )
    if condition.reference_snr_db is not None:
        current = replace(
            current,
            link=replace(current.link, reference_snr_db=condition.reference_snr_db),
        )
    if condition.offered_load is not None:
        current = replace(
            current,
            traffic=replace(current.traffic, offered_load=condition.offered_load),
        )
    if condition.deadline_s is not None:
        current = replace(
            current,
            traffic=replace(current.traffic, deadline_s=condition.deadline_s),
        )
    return current


def run_operating_region_sweep(
    dataset_dir: str | Path,
    *,
    split: str,
    ablation_dir: str | Path,
    training_npz: str | Path,
    selection_manifest: str | Path,
    config: ExperimentConfig,
    output_dir: str | Path,
    vehicles_per_episode: int = 5,
    history_steps: int = 20,
) -> dict[str, object]:
    """Run one-factor communication operating conditions on identical episodes."""
    validate_operating_region_protocol()
    validate_nominal_operating_config(config)
    destination = Path(output_dir)
    manifest_path = destination / "operating_region_manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite operating sweep: {manifest_path}")
    destination.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, object]] = []
    expected_episode_count: int | None = None

    for condition in OPERATING_CONDITIONS:
        current_config = _condition_config(config, condition)
        output_path = destination / f"{condition.name}.json"
        report = run_synthetic_scheduling_evaluation(
            dataset_dir,
            split=split,
            ablation_dir=ablation_dir,
            training_npz=training_npz,
            selection_manifest=selection_manifest,
            config=current_config,
            output_path=output_path,
            vehicles_per_episode=vehicles_per_episode,
            history_steps=history_steps,
            forecast_link_config=current_config.link,
            condition_label=condition.name,
        )
        plan = report["plan"]
        if not isinstance(plan, dict):
            raise RuntimeError("operating condition returned invalid run plan")
        episode_count = int(plan["episode_count"])
        if expected_episode_count is None:
            expected_episode_count = episode_count
        elif episode_count != expected_episode_count:
            raise RuntimeError("operating conditions used different episode counts")
        artifacts.append(
            {
                "condition": condition.name,
                "path": str(output_path),
                "sha256": sha256_file(output_path),
                "planned_runs": int(plan["planned_runs"]),
            }
        )

    manifest = {
        "status": "COMPLETED",
        "split": split,
        "protocol": operating_region_protocol_manifest(),
        "episode_count": expected_episode_count,
        "artifacts": artifacts,
        "scientific_guards": {
            "same_split_and_episode_composition": True,
            "same_paired_traffic_seed_set": True,
            "one_factor_at_a_time": True,
            "nominal_horizon_verified_as_10_steps": True,
            "no_final_test_model_selection": True,
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def _episode_mobility_descriptors(
    dataset_dir: Path,
    member_ids: list[str],
) -> dict[str, float]:
    max_speed = 0.0
    max_radial = 0.0
    max_acceleration = 0.0
    max_lateral = 0.0
    for scenario_id in member_ids:
        with np.load(
            dataset_dir / "scenarios" / f"{scenario_id}.npz",
            allow_pickle=False,
        ) as data:
            speed = np.asarray(data["speed_mps"], dtype=np.float64)
            radial = np.asarray(data["radial_velocity_mps"], dtype=np.float64)
            ax = np.asarray(data["ax_mps2"], dtype=np.float64)
            ay = np.asarray(data["ay_mps2"], dtype=np.float64)
            vy = np.asarray(data["vy_mps"], dtype=np.float64)
            max_speed = max(max_speed, float(np.max(speed)))
            max_radial = max(max_radial, float(np.max(np.abs(radial))))
            max_acceleration = max(
                max_acceleration,
                float(np.max(np.sqrt(ax**2 + ay**2))),
            )
            max_lateral = max(max_lateral, float(np.max(np.abs(vy))))
    return {
        "speed_mps": max_speed,
        "absolute_radial_velocity_mps": max_radial,
        "acceleration_mps2": max_acceleration,
        "lateral_speed_mps": max_lateral,
    }


def _gain_rows(
    report: dict[str, object],
    dataset_dir: Path,
) -> list[dict[str, object]]:
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("operating artifact has no rows")
    averaged = aggregate_traffic_seeds(rows)
    source_rows: dict[tuple[str, str], dict[str, object]] = {
        (str(row["scenario_id"]), str(row["protocol_id"])): row for row in rows
    }
    by_episode = {
        (str(row["scenario_id"]), str(row["protocol_id"])): row for row in averaged
    }
    episodes = sorted(
        episode for episode, protocol in by_episode if protocol == "S6"
    )
    gains: list[dict[str, object]] = []
    for episode in episodes:
        proposed = by_episode[(episode, "S6")]
        baseline = by_episode[(episode, "S0")]
        source = source_rows[(episode, "S6")]
        members = source.get("member_scenario_ids")
        if not isinstance(members, list):
            raise ValueError("operating row lacks member_scenario_ids")
        descriptors = _episode_mobility_descriptors(
            dataset_dir,
            [str(item) for item in members],
        )
        gains.append(
            {
                "scenario_id": episode,
                "goodput_gain_mbps": (
                    float(proposed["goodput_mbps"])
                    - float(baseline["goodput_mbps"])
                ),
                "deadline_miss_reduction": (
                    float(baseline["deadline_miss_ratio"])
                    - float(proposed["deadline_miss_ratio"])
                ),
                **descriptors,
            }
        )
    return gains


def analyze_operating_region(
    dataset_dir: str | Path,
    sweep_dir: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    """Derive predictive-gain rows and mobility-difficulty heatmap inputs."""
    root = Path(sweep_dir)
    manifest = json.loads(
        (root / "operating_region_manifest.json").read_text(encoding="utf-8")
    )
    protocol = manifest.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("operating sweep manifest lacks protocol metadata")
    if int(protocol.get("nominal_prediction_horizon_steps", -1)) != 10:
        raise ValueError("operating sweep nominal horizon provenance is not 10 steps")
    dataset_root = Path(dataset_dir)
    condition_rows: list[dict[str, object]] = []
    for artifact in manifest["artifacts"]:
        condition = str(artifact["condition"])
        report = json.loads(Path(artifact["path"]).read_text(encoding="utf-8"))
        for row in _gain_rows(report, dataset_root):
            condition_rows.append({"condition": condition, **row})

    nominal = [row for row in condition_rows if row["condition"] == "nominal"]
    axes = (
        "speed_mps",
        "absolute_radial_velocity_mps",
        "acceleration_mps2",
        "lateral_speed_mps",
    )
    mobility_bins: dict[str, dict[str, float]] = {}
    for axis in axes:
        values = np.asarray([float(row[axis]) for row in nominal], dtype=np.float64)
        if values.size < 3:
            raise ValueError("at least three episodes are required for mobility bins")
        low, high = np.quantile(values, (1 / 3, 2 / 3))
        mobility_bins[axis] = {"low_medium": float(low), "medium_high": float(high)}

    heatmap_rows: list[dict[str, object]] = []
    horizon_names = ("horizon_3", "horizon_5", "nominal")
    horizon_values = {"horizon_3": 3, "horizon_5": 5, "nominal": 10}
    for axis in axes:
        thresholds = mobility_bins[axis]
        for condition in horizon_names:
            current = [row for row in condition_rows if row["condition"] == condition]
            for label in ("low", "medium", "high"):
                if label == "low":
                    selected = [
                        row
                        for row in current
                        if float(row[axis]) <= thresholds["low_medium"]
                    ]
                elif label == "medium":
                    selected = [
                        row
                        for row in current
                        if thresholds["low_medium"] < float(row[axis])
                        <= thresholds["medium_high"]
                    ]
                else:
                    selected = [
                        row
                        for row in current
                        if float(row[axis]) > thresholds["medium_high"]
                    ]
                if not selected:
                    continue
                goodput_gain = [
                    float(row["goodput_gain_mbps"]) for row in selected
                ]
                deadline_gain = [
                    float(row["deadline_miss_reduction"]) for row in selected
                ]
                heatmap_rows.append(
                    {
                        "mobility_axis": axis,
                        "difficulty_bin": label,
                        "horizon_steps": horizon_values[condition],
                        "episodes": len(selected),
                        "mean_goodput_gain_mbps": float(np.mean(goodput_gain)),
                        "mean_deadline_miss_reduction": float(
                            np.mean(deadline_gain)
                        ),
                    }
                )

    report = {
        "status": "COMPLETED",
        "condition_gain_rows": condition_rows,
        "mobility_bins": mobility_bins,
        "heatmap_rows": heatmap_rows,
        "gain_definition": {
            "goodput": "S6_minus_S0_Mbps",
            "deadline": "S0_minus_S6_deadline_miss_ratio",
        },
        "scientific_guard": (
            "mobility bins are episode-level descriptive strata, not independent "
            "timesteps"
        ),
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        message = f"refusing to overwrite operating analysis: {destination}"
        raise FileExistsError(message)
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
