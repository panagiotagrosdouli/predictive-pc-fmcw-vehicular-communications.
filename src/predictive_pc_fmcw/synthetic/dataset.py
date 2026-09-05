"""Materialization and validation for Synthetic Dataset v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from ..config import LinkConfig, TrafficConfig
from ..link import LinkModel
from ..traffic import generate_traffic_trace
from .mobility import SyntheticMobilityConfig, generate_scenario
from .observations import ObservationNoiseConfig, observe_scenario
from .splits import SplitManifest, build_split_manifest, validate_split_manifest

FAMILIES = (
    "constant_velocity",
    "constant_acceleration",
    "approaching",
    "receding",
    "lateral_crossing",
    "lane_change",
    "curved",
    "stop_and_go",
    "accelerate_then_brake",
    "mixed_nonlinear",
    "high_relative_speed",
)


@dataclass(frozen=True)
class DatasetBuildConfig:
    master_seed: int = 20260905
    scenarios_per_family: int = 20
    ood_scenarios_per_family: int = 5
    mobility: SyntheticMobilityConfig = SyntheticMobilityConfig()
    ood_mobility: SyntheticMobilityConfig = SyntheticMobilityConfig(
        initial_range_m=(20.0, 220.0),
        speed_mps=(35.0, 45.0),
        acceleration_mps2=(-6.0, 4.5),
        lateral_speed_mps=(-5.0, 5.0),
    )
    observations: ObservationNoiseConfig = ObservationNoiseConfig()


def _scenario_seed(
    master_seed: int, family_index: int, replicate: int, ood: bool
) -> int:
    return master_seed + (1_000_000 if ood else 0) + 10_000 * family_index + replicate


def _fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_ood_regime(config: DatasetBuildConfig) -> None:
    train = config.mobility
    ood = config.ood_mobility
    if ood.speed_mps[0] < train.speed_mps[1]:
        raise ValueError(
            "OOD speed lower bound must be at least the training speed upper bound"
        )
    harder_acceleration = (
        ood.acceleration_mps2[0] < train.acceleration_mps2[0]
        or ood.acceleration_mps2[1] > train.acceleration_mps2[1]
    )
    harder_lateral = (
        ood.lateral_speed_mps[0] < train.lateral_speed_mps[0]
        or ood.lateral_speed_mps[1] > train.lateral_speed_mps[1]
    )
    if not harder_acceleration or not harder_lateral:
        raise ValueError(
            "OOD mobility must extend both acceleration and lateral-speed severity"
        )


def _link_lifetime_seconds(outage: np.ndarray, dt_s: float) -> float:
    indices = np.flatnonzero(outage)
    return float(indices[0] * dt_s) if indices.size else float(outage.size * dt_s)


def _write_scenario(
    output: Path,
    family: str,
    seed: int,
    mobility: SyntheticMobilityConfig,
    observation_seed: int,
    observation_config: ObservationNoiseConfig,
    link_model: LinkModel,
    traffic_config: TrafficConfig,
) -> tuple[str, str]:
    scenario = generate_scenario(family, seed=seed, config=mobility)
    observations = observe_scenario(
        scenario, seed=observation_seed, config=observation_config
    )
    link = link_model.evaluate_arrays(scenario.range_m, scenario.bearing_rad)
    dt_s = 1.0 / mobility.sampling_hz
    nominal_capacity = link_model.capacity_packets(dt_s)
    traffic = generate_traffic_trace(
        seed=observation_seed + 1,
        slots=scenario.t_s.size,
        vehicles=1,
        nominal_capacity_packets=nominal_capacity,
        config=traffic_config,
        slot_duration_s=dt_s,
    )
    deadline_json = json.dumps(
        [[int(value) for value in row[0]] for row in traffic.deadlines],
        separators=(",", ":"),
    )
    path = output / f"{scenario.scenario_id}.npz"
    np.savez_compressed(
        path,
        scenario_id=np.asarray(scenario.scenario_id),
        family=np.asarray(family),
        seed=np.asarray(seed, dtype=np.int64),
        t_s=scenario.t_s,
        x_m=scenario.x_m,
        y_m=scenario.y_m,
        vx_mps=scenario.vx_mps,
        vy_mps=scenario.vy_mps,
        ax_mps2=scenario.ax_mps2,
        ay_mps2=scenario.ay_mps2,
        speed_mps=scenario.speed_mps,
        heading_rad=scenario.heading_rad,
        range_m=scenario.range_m,
        radial_velocity_mps=scenario.radial_velocity_mps,
        bearing_rad=scenario.bearing_rad,
        observed_range_m=observations.range_m,
        observed_radial_velocity_mps=observations.radial_velocity_mps,
        observed_bearing_rad=observations.bearing_rad,
        snr_db=link["snr_db"],
        ber=link["ber"],
        per=link["per"],
        goodput_bps=link["goodput_bps"],
        outage=link["outage"].astype(np.uint8),
        link_lifetime_s=np.asarray(_link_lifetime_seconds(link["outage"], dt_s)),
        packet_arrivals=traffic.arrivals[:, 0],
        packet_deadlines_json=np.asarray(deadline_json),
    )
    return scenario.scenario_id, _fingerprint_file(path)


def build_dataset(
    output_dir: str | Path,
    config: DatasetBuildConfig | None = None,
    link_config: LinkConfig | None = None,
    traffic_config: TrafficConfig | None = None,
) -> dict[str, object]:
    """Materialize deterministic scenarios and a fail-closed provenance manifest."""
    cfg = config or DatasetBuildConfig()
    if cfg.scenarios_per_family < 1 or cfg.ood_scenarios_per_family < 1:
        raise ValueError("scenario counts must be positive")
    _validate_ood_regime(cfg)
    output = Path(output_dir)
    scenario_dir = output / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    link_cfg = link_config or LinkConfig()
    traffic_cfg = traffic_config or TrafficConfig()
    link_model = LinkModel(link_cfg)
    in_ids: list[str] = []
    ood_ids: list[str] = []
    hashes: dict[str, str] = {}
    for family_index, family in enumerate(FAMILIES):
        for replicate in range(cfg.scenarios_per_family):
            seed = _scenario_seed(cfg.master_seed, family_index, replicate, False)
            scenario_id, sha = _write_scenario(
                scenario_dir,
                family,
                seed,
                cfg.mobility,
                seed + 500_000,
                cfg.observations,
                link_model,
                traffic_cfg,
            )
            in_ids.append(scenario_id)
            hashes[scenario_id] = sha
        for replicate in range(cfg.ood_scenarios_per_family):
            seed = _scenario_seed(cfg.master_seed, family_index, replicate, True)
            scenario_id, sha = _write_scenario(
                scenario_dir,
                family,
                seed,
                cfg.ood_mobility,
                seed + 500_000,
                cfg.observations,
                link_model,
                traffic_cfg,
            )
            ood_ids.append(scenario_id)
            hashes[scenario_id] = sha
    split = build_split_manifest(in_ids, ood_ids, cfg.master_seed)
    validate_split_manifest(split)
    manifest = {
        "protocol": "synthetic_dataset_v1",
        "master_seed": cfg.master_seed,
        "scenario_count": len(in_ids) + len(ood_ids),
        "in_distribution_count": len(in_ids),
        "ood_count": len(ood_ids),
        "split": asdict(split),
        "scenario_sha256": dict(sorted(hashes.items())),
        "mobility_config": asdict(cfg.mobility),
        "ood_mobility_config": asdict(cfg.ood_mobility),
        "observation_config": asdict(cfg.observations),
        "link_config": asdict(link_cfg),
        "traffic_config": asdict(traffic_cfg),
        "scientific_guards": {
            "scenario_level_split": True,
            "held_out_for_selection": False,
            "oracle_evaluation_only": True,
            "external_trajectory_dataset": False,
            "ood_mobility_harder_than_training": True,
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest["manifest_sha256"] = _fingerprint_file(manifest_path)
    return manifest


def validate_dataset(output_dir: str | Path) -> dict[str, object]:
    """Verify split integrity and every materialized scenario fingerprint."""
    output = Path(output_dir)
    manifest_path = output / "manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    split_raw = raw["split"]
    split = SplitManifest(
        master_seed=int(split_raw["master_seed"]),
        train=tuple(split_raw["train"]),
        development=tuple(split_raw["development"]),
        held_out_test=tuple(split_raw["held_out_test"]),
        ood_test=tuple(split_raw["ood_test"]),
        sha256=str(split_raw["sha256"]),
    )
    validate_split_manifest(split)
    hashes = raw["scenario_sha256"]
    expected_ids = set(
        split.train + split.development + split.held_out_test + split.ood_test
    )
    if expected_ids != set(hashes):
        raise ValueError("manifest scenario IDs do not match split IDs")
    for scenario_id, expected in hashes.items():
        path = output / "scenarios" / f"{scenario_id}.npz"
        if not path.is_file():
            raise FileNotFoundError(f"missing synthetic scenario: {scenario_id}")
        if _fingerprint_file(path) != expected:
            raise ValueError(f"scenario fingerprint mismatch: {scenario_id}")
        with np.load(path, allow_pickle=False) as data:
            required = {
                "t_s",
                "x_m",
                "y_m",
                "vx_mps",
                "vy_mps",
                "ax_mps2",
                "ay_mps2",
                "speed_mps",
                "heading_rad",
                "range_m",
                "radial_velocity_mps",
                "bearing_rad",
                "observed_range_m",
                "observed_radial_velocity_mps",
                "observed_bearing_rad",
                "snr_db",
                "ber",
                "per",
                "goodput_bps",
                "outage",
                "link_lifetime_s",
                "packet_arrivals",
                "packet_deadlines_json",
            }
            if not required.issubset(data.files):
                raise ValueError(f"scenario schema incomplete: {scenario_id}")
            length = data["t_s"].size
            aligned = tuple(required - {"link_lifetime_s", "packet_deadlines_json"})
            if any(data[name].size != length for name in aligned):
                raise ValueError(f"scenario arrays misaligned: {scenario_id}")
            numeric = tuple(name for name in aligned if name != "outage")
            if any(not np.all(np.isfinite(data[name])) for name in numeric):
                raise ValueError(f"non-finite scenario values: {scenario_id}")
            json.loads(str(data["packet_deadlines_json"]))
    return {
        "status": "PASS",
        "protocol": raw["protocol"],
        "scenario_count": len(hashes),
        "split_sha256": split.sha256,
        "manifest_sha256": _fingerprint_file(manifest_path),
    }
