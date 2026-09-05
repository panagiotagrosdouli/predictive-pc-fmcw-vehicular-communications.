from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..config import ExperimentConfig, LinkConfig, SensingConfig
from ..data.scenario import MotionScenario
from ..geometry import heading_from_positions, range_and_bearing
from ..link import LinkModel
from ..metrics import SimulationMetrics, jains_fairness
from ..predictors import (
    ConstantAccelerationPredictor,
    ConstantVelocityPredictor,
    InteractingMultipleModelPredictor,
    KalmanConstantVelocityPredictor,
    TrajectoryPredictor,
    forecast_scenario,
)
from ..scheduling.base import SchedulerContext
from ..scheduling.policies import build_scheduler
from ..sensing import observe_combined_history
from ..traffic import PacketQueues, TrafficTrace


@dataclass(frozen=True)
class SimulationOutput:
    metrics: SimulationMetrics
    selected_vehicle: NDArray[np.int64]
    queue_packets: NDArray[np.int64]
    actual_snr_db: NDArray[np.float64]
    actual_outage: NDArray[np.bool_]
    delivered_packets_by_vehicle: NDArray[np.int64]
    forecast_mode: str


def _current_heading(ego_history: NDArray[np.float64]) -> float:
    if ego_history.shape[0] < 2:
        return 0.0
    return float(heading_from_positions(ego_history)[-1])


def _link_forecast(
    scenario: MotionScenario,
    time_index: int,
    horizon: int,
    mode: str,
    model: LinkModel,
    learned_predictor: TrajectoryPredictor | None = None,
    history_noise_std_m: float = 0.0,
    forecast_noise_std_m: float = 0.0,
    noise_seed: int = 0,
    sensing_config: SensingConfig | None = None,
) -> tuple[dict[str, NDArray], NDArray[np.int64], bool]:
    combined = scenario.combined_positions()
    measurement_std_m = 0.75
    if (
        sensing_config is not None
        and sensing_config.model != "perfect"
        and mode not in {"reactive", "oracle"}
    ):
        observation = observe_combined_history(
            combined[: time_index + 1], sensing_config, noise_seed
        )
        combined = combined.copy()
        combined[: time_index + 1] = observation.positions_xy
        if sensing_config.covariance_aware:
            target_std = observation.position_std_m[:, 1:]
            positive = target_std[target_std > 0]
            if positive.size:
                measurement_std_m = float(np.sqrt(np.mean(positive**2)))
    predictors = {
        "constant_velocity": ConstantVelocityPredictor(),
        "constant_acceleration": ConstantAccelerationPredictor(),
        "kalman_cv": KalmanConstantVelocityPredictor(
            measurement_std_m=measurement_std_m
        ),
        "imm": InteractingMultipleModelPredictor(
            measurement_std_m=measurement_std_m
        ),
        "reactive": None,
        "oracle": None,
        "learned": learned_predictor,
    }
    if mode not in predictors:
        raise ValueError(f"Unknown forecast mode: {mode}")
    available_future = combined.shape[0] - time_index - 1
    if available_future <= 0:
        heading = _current_heading(combined[: time_index + 1, 0])
        distances, bearings = range_and_bearing(
            combined[time_index, 1:],
            combined[time_index, 0],
            heading,
        )
        distances = distances[:, None]
        bearings = bearings[:, None]
        values = model.evaluate_arrays(distances, bearings)
        lifetime = model.link_lifetime_steps(distances, bearings)
        return values, lifetime, mode == "oracle"
    effective_horizon = min(horizon, available_future)
    rng = np.random.default_rng(noise_seed)
    if history_noise_std_m > 0 and mode not in {"reactive", "oracle"}:
        combined = combined.copy()
        combined[: time_index + 1] += rng.normal(
            0.0,
            history_noise_std_m,
            size=combined[: time_index + 1].shape,
        )
    if mode == "learned":
        if learned_predictor is None:
            raise ValueError("learned forecast mode requires a checkpoint predictor.")
        relative_history = (
            combined[: time_index + 1, 1:]
            - combined[: time_index + 1, :1]
        ).transpose(1, 0, 2)
        feature_schema = getattr(learned_predictor, "feature_schema", {})
        expected_history = int(
            feature_schema.get("history_steps", relative_history.shape[1])
        )
        if relative_history.shape[1] < expected_history:
            raise ValueError(
                "Learned checkpoint requires more causal history than is available."
            )
        relative_history = relative_history[:, -expected_history:]
        relative_prediction = learned_predictor.predict(
            relative_history, horizon, scenario.dt_s
        )[:, :effective_horizon]
        ego_history = combined[: time_index + 1, 0][None, :, :]
        ego_prediction = ConstantVelocityPredictor().predict(
            ego_history, effective_horizon, scenario.dt_s
        )[0]
        vehicle_prediction = relative_prediction + ego_prediction[None, :, :]
        oracle_forecast = False
    else:
        bundle = forecast_scenario(
            combined,
            time_index,
            effective_horizon,
            scenario.dt_s,
            predictors[mode],
            oracle=mode == "oracle",
        )
        ego_prediction = bundle.ego_xy
        vehicle_prediction = bundle.vehicle_xy
        oracle_forecast = bundle.oracle
    if forecast_noise_std_m > 0 and mode not in {"reactive", "oracle"}:
        vehicle_prediction = vehicle_prediction + rng.normal(
            0.0, forecast_noise_std_m, size=vehicle_prediction.shape
        )
    current_ego = scenario.ego_positions_xy[time_index]
    heading_path = np.concatenate([current_ego[None, :], ego_prediction], axis=0)
    headings = heading_from_positions(heading_path)[1:]
    distances, bearings = range_and_bearing(
        vehicle_prediction,
        ego_prediction[None, :, :],
        headings[None, :],
    )
    values = model.evaluate_arrays(distances, bearings)
    lifetime = model.link_lifetime_steps(distances, bearings)
    return values, lifetime, oracle_forecast


def run_simulation(
    scenario: MotionScenario,
    scheduler_name: str,
    traffic: TrafficTrace,
    config: ExperimentConfig,
    seed: int,
    learned_predictor: TrajectoryPredictor | None = None,
    forecast_link_config: LinkConfig | None = None,
) -> SimulationOutput:
    model = LinkModel(config.link)
    forecast_model = LinkModel(forecast_link_config or config.link)
    scheduler = build_scheduler(scheduler_name, config.scheduler, seed)
    slots = min(scenario.evaluation_slots, traffic.arrivals.shape[0])
    vehicles = scenario.vehicle_count
    if traffic.arrivals.shape[1] != vehicles:
        raise ValueError("Traffic trace vehicle count does not match scenario.")
    queues = PacketQueues(vehicles, config.traffic.max_queue_packets)
    selected = np.full(slots, -1, dtype=np.int64)
    queue_series = np.zeros((slots, vehicles), dtype=np.int64)
    actual_snr = np.empty((slots, vehicles), dtype=np.float64)
    actual_outage = np.empty((slots, vehicles), dtype=bool)
    delivered_by_vehicle = np.zeros(vehicles, dtype=np.int64)
    delivered_by_slot_vehicle = np.zeros((slots, vehicles), dtype=np.int64)
    delivered_bits = np.zeros(vehicles, dtype=np.float64)
    delivered_by_class = {"urgent": 0, "bulk": 0, "best_effort": 0}
    failed_attempts = 0
    scheduled_outages = 0
    scheduled_slots = 0
    scheduled_snr_sum = 0.0
    scheduled_ber_sum = 0.0
    scheduled_per_sum = 0.0
    scheduled_relative_power_sum = 0.0
    switch_count = 0
    previous: int | None = None
    latencies: list[float] = []
    capacity = model.capacity_packets(config.slot_duration_s)

    for relative_slot in range(slots):
        time_index = scenario.start_index + relative_slot
        queues.add_arrivals(
            relative_slot,
            traffic.deadlines[relative_slot],
            traffic.classes[relative_slot],
        )
        queues.expire(relative_slot)
        current_heading = _current_heading(scenario.ego_positions_xy[: time_index + 1])
        distance, bearing = range_and_bearing(
            scenario.vehicle_positions_xy[time_index],
            scenario.ego_positions_xy[time_index],
            current_heading,
        )
        current = model.evaluate_arrays(distance, bearing)
        actual_snr[relative_slot] = current["snr_db"]
        actual_outage[relative_slot] = current["outage"]
        predicted, lifetime, is_oracle = _link_forecast(
            scenario,
            time_index,
            config.prediction_horizon_steps,
            scheduler.forecast_mode,
            forecast_model,
            learned_predictor=learned_predictor,
            history_noise_std_m=config.history_measurement_noise_std_m,
            forecast_noise_std_m=config.forecast_position_noise_std_m,
            noise_seed=seed + 10_000 * relative_slot,
            sensing_config=config.sensing,
        )
        context = SchedulerContext(
            slot=relative_slot,
            queue_lengths=queues.lengths(),
            time_to_deadline=queues.oldest_time_to_deadline(relative_slot),
            current_goodput_bps=current["goodput_bps"],
            current_outage=current["outage"].astype(bool),
            predicted_goodput_bps=predicted["goodput_bps"],
            predicted_outage=predicted["outage"].astype(bool),
            predicted_lifetime_steps=lifetime,
            delivered_bits=delivered_bits.copy(),
            previous_vehicle=previous,
            data_rate_bps=config.link.data_rate_bps,
            discount=config.discount,
            oracle_forecast=is_oracle,
        )
        decision = scheduler.select(context)
        queue_series[relative_slot] = context.queue_lengths
        if decision.vehicle is None:
            continue
        vehicle = decision.vehicle
        selected[relative_slot] = vehicle
        scheduled_slots += 1
        scheduled_outages += int(current["outage"][vehicle])
        scheduled_snr_sum += float(current["snr_db"][vehicle])
        scheduled_ber_sum += float(current["ber"][vehicle])
        scheduled_per_sum += float(current["per"][vehicle])
        scheduled_relative_power_sum += float(
            current["relative_received_power"][vehicle]
        )
        if previous is not None and previous != vehicle:
            switch_count += 1
        previous = vehicle
        attempted = queues.pop_attempts(vehicle, capacity)
        uniforms = traffic.success_uniforms[
            relative_slot, vehicle, : len(attempted)
        ]
        success = uniforms >= float(current["per"][vehicle])
        failed = [
            packet
            for packet, ok in zip(attempted, success, strict=True)
            if not ok
        ]
        queues.requeue_failed(vehicle, failed)
        successful = [
            packet for packet, ok in zip(attempted, success, strict=True) if ok
        ]
        failed_attempts += len(failed)
        delivered_by_vehicle[vehicle] += len(successful)
        for packet in successful:
            delivered_by_class[packet.traffic_class] += 1
        delivered_by_slot_vehicle[relative_slot, vehicle] = len(successful)
        delivered_bits[vehicle] += len(successful) * config.link.packet_bits
        latencies.extend(
            (relative_slot - packet.arrival_slot + 1) * config.slot_duration_s
            for packet in successful
        )

    generated = int(queues.generated.sum())
    delivered = int(delivered_by_vehicle.sum())
    deadline_dropped = int(queues.deadline_dropped.sum())
    overflow_dropped = int(queues.overflow_dropped.sum())
    remaining = int(queues.remaining().sum())
    duration = slots * config.slot_duration_s
    latency_ms = np.asarray(latencies, dtype=np.float64) * 1e3
    demand_service_ratio = delivered_by_vehicle / np.maximum(queues.generated, 1)
    has_disconnect = np.any(actual_outage, axis=0)
    first_disconnect = np.argmax(actual_outage, axis=0)
    first_disconnect = np.where(has_disconnect, first_disconnect, slots)
    delivered_before_expiry = 0
    eligible_before_expiry = 0
    undelivered_at_disconnect = 0
    for vehicle, disconnect in enumerate(first_disconnect):
        delivered_before_expiry += int(
            delivered_by_slot_vehicle[:disconnect, vehicle].sum()
        )
        eligible_before_expiry += int(
            traffic.arrivals[:disconnect, vehicle].sum()
        )
        if disconnect < slots:
            undelivered_at_disconnect += int(queue_series[disconnect, vehicle])
    urgent_generated = int(queues.class_generated["urgent"].sum())
    urgent_dropped = int(
        queues.class_deadline_dropped["urgent"].sum()
        + queues.class_overflow_dropped["urgent"].sum()
    )
    bulk_generated = int(queues.class_generated["bulk"].sum())
    bulk_dropped = int(
        queues.class_deadline_dropped["bulk"].sum()
        + queues.class_overflow_dropped["bulk"].sum()
    )
    metrics = SimulationMetrics(
        scheduler=scheduler_name,
        scenario_id=scenario.scenario_id,
        source=scenario.source,
        seed=seed,
        vehicles=vehicles,
        duration_s=duration,
        generated_packets=generated,
        delivered_packets=delivered,
        failed_attempts=failed_attempts,
        deadline_dropped_packets=deadline_dropped,
        overflow_dropped_packets=overflow_dropped,
        remaining_packets=remaining,
        goodput_mbps=float(delivered * config.link.packet_bits / duration / 1e6),
        packet_delivery_ratio=delivered / max(1, generated),
        scheduled_outage_fraction=scheduled_outages / max(1, scheduled_slots),
        availability_outage_fraction=float(actual_outage.mean()),
        mean_latency_ms=float(latency_ms.mean()) if latency_ms.size else float("nan"),
        p50_latency_ms=float(np.quantile(latency_ms, 0.50))
        if latency_ms.size
        else float("nan"),
        p95_latency_ms=float(np.quantile(latency_ms, 0.95))
        if latency_ms.size
        else float("nan"),
        p99_latency_ms=float(np.quantile(latency_ms, 0.99))
        if latency_ms.size
        else float("nan"),
        deadline_miss_ratio=(deadline_dropped + overflow_dropped) / max(1, generated),
        censored_packet_ratio=remaining / max(1, generated),
        deadline_or_censored_ratio=(
            deadline_dropped + overflow_dropped + remaining
        )
        / max(1, generated),
        delivered_before_expiry_ratio=delivered_before_expiry
        / max(1, eligible_before_expiry),
        undelivered_packets_at_disconnect=undelivered_at_disconnect,
        urgent_generated_packets=urgent_generated,
        urgent_delivered_packets=delivered_by_class["urgent"],
        urgent_packet_delivery_ratio=(
            delivered_by_class["urgent"] / max(1, urgent_generated)
        ),
        urgent_deadline_miss_ratio=urgent_dropped / max(1, urgent_generated),
        bulk_generated_packets=bulk_generated,
        bulk_delivered_packets=delivered_by_class["bulk"],
        bulk_packet_delivery_ratio=(
            delivered_by_class["bulk"] / max(1, bulk_generated)
        ),
        bulk_deadline_miss_ratio=bulk_dropped / max(1, bulk_generated),
        jain_fairness=jains_fairness(delivered_by_vehicle),
        demand_normalized_jain_fairness=jains_fairness(demand_service_ratio),
        mean_scheduled_snr_db=scheduled_snr_sum / max(1, scheduled_slots),
        mean_scheduled_ber=scheduled_ber_sum / max(1, scheduled_slots),
        mean_scheduled_per=scheduled_per_sum / max(1, scheduled_slots),
        mean_scheduled_relative_power=(
            scheduled_relative_power_sum / max(1, scheduled_slots)
        ),
        switch_count=switch_count,
    )
    return SimulationOutput(
        metrics=metrics,
        selected_vehicle=selected,
        queue_packets=queue_series,
        actual_snr_db=actual_snr,
        actual_outage=actual_outage,
        delivered_packets_by_vehicle=delivered_by_vehicle,
        forecast_mode=scheduler.forecast_mode,
    )
