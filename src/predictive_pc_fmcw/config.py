from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LinkConfig:
    carrier_frequency_hz: float = 193.4e12
    chirp_bandwidth_hz: float = 10e9
    chirp_duration_s: float = 10e-6
    data_rate_bps: float = 1e9
    packet_bits: int = 12_000
    resource_fraction: float = 0.005
    reference_distance_m: float = 40.0
    reference_snr_db: float = 18.0
    beam_divergence_half_angle_deg: float = 5.0
    field_of_view_deg: float = 70.0
    pointing_sigma_deg: float = 18.0
    atmospheric_attenuation_per_m: float = 0.004
    outage_ber_threshold: float = 1e-3
    min_received_power_w: float = 1e-15
    reference_received_power_w: float = 1e-6
    received_power_calibrated: bool = False
    channel_mode: str = "full"
    ber_source: str = "analytical"
    ber_lut_path: str | None = None
    outage_mode: str = "ber"
    outage_per_threshold: float = 0.1
    outage_goodput_fraction_threshold: float = 0.1
    physical_layer_source: str = "supplied Part-A PC-FMCW/DPSK notebook"

    def __post_init__(self) -> None:
        physical = (
            self.carrier_frequency_hz,
            self.chirp_bandwidth_hz,
            self.chirp_duration_s,
            self.data_rate_bps,
            self.reference_received_power_w,
        )
        if any(value <= 0 for value in physical) or self.packet_bits <= 0:
            raise ValueError("Physical parameters and packet length must be positive.")
        if self.reference_distance_m <= 0:
            raise ValueError("reference_distance_m must be positive.")
        if self.beam_divergence_half_angle_deg <= 0:
            raise ValueError("beam_divergence_half_angle_deg must be positive.")
        if self.pointing_sigma_deg <= 0:
            raise ValueError("pointing_sigma_deg must be positive.")
        if self.atmospheric_attenuation_per_m < 0:
            raise ValueError("atmospheric_attenuation_per_m must be non-negative.")
        if self.min_received_power_w < 0:
            raise ValueError("min_received_power_w must be non-negative.")
        if not 0 < self.resource_fraction <= 1:
            raise ValueError("resource_fraction must be in (0, 1].")
        if not 0 < self.field_of_view_deg <= 180:
            raise ValueError("field_of_view_deg must be in (0, 180].")
        if not 0 < self.outage_ber_threshold < 0.5:
            raise ValueError("outage_ber_threshold must be in (0, 0.5).")
        if self.channel_mode not in {"range_only", "range_pointing", "full"}:
            raise ValueError(
                "channel_mode must be range_only, range_pointing, or full."
            )
        if self.ber_source not in {"analytical", "lut"}:
            raise ValueError("ber_source must be analytical or lut.")
        if self.ber_source == "lut" and not self.ber_lut_path:
            raise ValueError("ber_lut_path is required when ber_source is lut.")
        if self.outage_mode not in {"ber", "per", "goodput"}:
            raise ValueError("outage_mode must be ber, per, or goodput.")
        if not 0 < self.outage_per_threshold < 1:
            raise ValueError("outage_per_threshold must be in (0, 1).")
        if not 0 < self.outage_goodput_fraction_threshold < 1:
            raise ValueError(
                "outage_goodput_fraction_threshold must be in (0, 1)."
            )


@dataclass(frozen=True)
class TrafficConfig:
    offered_load: float = 0.72
    deadline_slots: int = 12
    deadline_jitter_slots: int = 4
    deadline_s: float | None = 1.2
    deadline_jitter_s: float | None = 0.4
    max_queue_packets: int = 2_000
    model: str = "poisson"
    periodic_interval_slots: int = 5
    markov_low_rate_scale: float = 0.25
    markov_high_rate_scale: float = 2.5
    markov_low_to_high: float = 0.08
    markov_high_to_low: float = 0.20
    traffic_class_mode: str = "single"
    urgent_fraction: float = 0.35
    urgent_deadline_s: float = 0.1
    bulk_deadline_s: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.offered_load <= 2:
            raise ValueError("offered_load must be in [0, 2].")
        if self.deadline_slots < 1 or self.max_queue_packets < 1:
            raise ValueError("Deadlines and queue capacity must be positive.")
        if self.model not in {
            "poisson",
            "periodic",
            "markov_modulated",
            "saturated",
        }:
            raise ValueError("Unsupported traffic model.")
        if self.deadline_s is not None and self.deadline_s <= 0:
            raise ValueError("deadline_s must be positive when provided.")
        if self.deadline_jitter_s is not None and self.deadline_jitter_s < 0:
            raise ValueError("deadline_jitter_s must be non-negative when provided.")
        if self.periodic_interval_slots < 1:
            raise ValueError("periodic_interval_slots must be positive.")
        probabilities = (self.markov_low_to_high, self.markov_high_to_low)
        if any(not 0 <= value <= 1 for value in probabilities):
            raise ValueError("Markov transition probabilities must be in [0, 1].")
        if self.markov_low_rate_scale < 0 or self.markov_high_rate_scale < 0:
            raise ValueError("Markov traffic-rate scales must be non-negative.")
        if self.traffic_class_mode not in {"single", "urgent_bulk"}:
            raise ValueError(
                "traffic_class_mode must be single or urgent_bulk."
            )
        if not 0 <= self.urgent_fraction <= 1:
            raise ValueError("urgent_fraction must be in [0, 1].")
        if self.urgent_deadline_s <= 0 or self.bulk_deadline_s <= 0:
            raise ValueError("Class-specific deadlines must be positive.")


@dataclass(frozen=True)
class SensingConfig:
    """Assumed observation model used only for controlled robustness studies.

    These parameters do not describe measured PC-FMCW sensor performance.  The
    default is perfect state knowledge so legacy experiments remain unchanged.
    """

    model: str = "perfect"
    cartesian_std_m: float = 0.75
    range_std_base_m: float = 0.20
    range_std_per_m: float = 0.005
    bearing_std_deg: float = 0.25
    temporal_correlation: float = 0.0
    covariance_aware: bool = True
    assumption_source: str = "declared synthetic robustness model"

    def __post_init__(self) -> None:
        if self.model not in {"perfect", "cartesian_iid", "range_bearing_assumed"}:
            raise ValueError(
                "sensing.model must be perfect, cartesian_iid, or "
                "range_bearing_assumed."
            )
        non_negative = (
            self.cartesian_std_m,
            self.range_std_base_m,
            self.range_std_per_m,
            self.bearing_std_deg,
        )
        if any(value < 0 for value in non_negative):
            raise ValueError("Sensing uncertainty parameters must be non-negative.")
        if not 0 <= self.temporal_correlation < 1:
            raise ValueError("temporal_correlation must be in [0, 1).")


@dataclass(frozen=True)
class SchedulerConfig:
    goodput_weight: float = 1.0
    outage_weight: float = 1.5
    queue_weight: float = 0.35
    deadline_weight: float = 0.5
    fairness_weight: float = 0.2
    switching_weight: float = 0.02
    opportunity_weight: float = 0.6
    lifetime_weight: float = 2.0


@dataclass(frozen=True)
class BenchmarkConfig:
    episodes: int = 12
    slots: int = 120
    duration_s: float | None = 12.0
    vehicles: int = 5
    bootstrap_samples: int = 2_000
    schedulers: tuple[str, ...] = (
        "random",
        "round_robin",
        "reactive_greedy",
        "proportional_fair",
        "cv_predictive",
        "kalman_predictive",
        "imm_predictive",
        "predictive_utility",
        "link_lifetime",
        "oracle",
    )

    def __post_init__(self) -> None:
        if self.episodes < 1 or self.slots < 1 or self.vehicles < 1:
            raise ValueError("Benchmark sizes must be positive.")
        if self.duration_s is not None and self.duration_s <= 0:
            raise ValueError("duration_s must be positive when provided.")


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 20260827
    slot_duration_s: float = 0.1
    prediction_horizon_steps: int = 10
    discount: float = 0.93
    history_measurement_noise_std_m: float = 0.0
    forecast_position_noise_std_m: float = 0.0
    link: LinkConfig = field(default_factory=LinkConfig)
    traffic: TrafficConfig = field(default_factory=TrafficConfig)
    sensing: SensingConfig = field(default_factory=SensingConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)

    def __post_init__(self) -> None:
        if self.slot_duration_s <= 0:
            raise ValueError("slot_duration_s must be positive.")
        if self.prediction_horizon_steps < 1:
            raise ValueError("prediction_horizon_steps must be positive.")
        if not 0 < self.discount <= 1:
            raise ValueError("discount must be in (0, 1].")
        if self.history_measurement_noise_std_m < 0:
            raise ValueError("history_measurement_noise_std_m must be non-negative.")
        if self.forecast_position_noise_std_m < 0:
            raise ValueError("forecast_position_noise_std_m must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tuple_schedulers(raw: dict[str, Any]) -> dict[str, Any]:
    value = dict(raw)
    if "schedulers" in value:
        value["schedulers"] = tuple(value["schedulers"])
    return value


def config_from_dict(raw: dict[str, Any]) -> ExperimentConfig:
    return ExperimentConfig(
        seed=int(raw.get("seed", 20260827)),
        slot_duration_s=float(raw.get("slot_duration_s", 0.1)),
        prediction_horizon_steps=int(raw.get("prediction_horizon_steps", 10)),
        discount=float(raw.get("discount", 0.93)),
        history_measurement_noise_std_m=float(
            raw.get("history_measurement_noise_std_m", 0.0)
        ),
        forecast_position_noise_std_m=float(
            raw.get("forecast_position_noise_std_m", 0.0)
        ),
        link=LinkConfig(**raw.get("link", {})),
        traffic=TrafficConfig(**raw.get("traffic", {})),
        sensing=SensingConfig(**raw.get("sensing", {})),
        scheduler=SchedulerConfig(**raw.get("scheduler", {})),
        benchmark=BenchmarkConfig(**_tuple_schedulers(raw.get("benchmark", {}))),
    )


def load_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        return config_from_dict(json.load(handle))
