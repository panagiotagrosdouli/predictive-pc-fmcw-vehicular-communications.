from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config
from predictive_pc_fmcw.data.synthetic import generate_synthetic_scenario
from predictive_pc_fmcw.geometry import range_and_bearing
from predictive_pc_fmcw.link import LinkModel
from predictive_pc_fmcw.scheduling.base import SchedulerContext
from predictive_pc_fmcw.scheduling.policies import build_scheduler
from predictive_pc_fmcw.simulation.engine import _current_heading, _link_forecast
from predictive_pc_fmcw.traffic import PacketQueues, generate_traffic_trace

DEV_SEEDS = tuple(range(20260901, 20260911))
POLICIES = ("reactive_greedy", "deadline_aware_lifetime")
REGIMES = (
    ("load_1p1", "load", 1.1),
    ("deadline_0p5", "deadline", 0.5),
)


def regime_config(base, kind: str, value: float, seed: int):
    benchmark = replace(base.benchmark, episodes=1, schedulers=POLICIES)
    scheduler = replace(base.scheduler, fairness_weight=0.0)
    cfg = replace(base, seed=seed, benchmark=benchmark, scheduler=scheduler)
    if kind == "load":
        return replace(cfg, traffic=replace(cfg.traffic, offered_load=value))
    if kind == "deadline":
        return replace(
            cfg,
            traffic=replace(
                cfg.traffic,
                deadline_s=value,
                deadline_jitter_s=0.0,
            ),
        )
    raise ValueError(kind)


def build_scenario_and_traffic(config):
    slots = (
        max(2, int(round(config.benchmark.duration_s / config.slot_duration_s)))
        if config.benchmark.duration_s is not None
        else config.benchmark.slots
    )
    scenario = generate_synthetic_scenario(
        seed=config.seed,
        slots=slots,
        vehicles=config.benchmark.vehicles,
        dt_s=config.slot_duration_s,
    )
    model = LinkModel(config.link)
    capacity = model.capacity_packets(config.slot_duration_s)
    eval_slots = min(config.benchmark.slots, scenario.evaluation_slots)
    traffic = generate_traffic_trace(
        seed=config.seed + 100_000,
        slots=eval_slots,
        vehicles=scenario.vehicle_count,
        nominal_capacity_packets=capacity,
        config=config.traffic,
        slot_duration_s=config.slot_duration_s,
    )
    return scenario, traffic


def run_trace(config, scheduler_name: str):
    scenario, traffic = build_scenario_and_traffic(config)
    model = LinkModel(config.link)
    scheduler = build_scheduler(scheduler_name, config.scheduler, config.seed)
    queues = PacketQueues(scenario.vehicle_count, config.traffic.max_queue_packets)
    slots = min(scenario.evaluation_slots, traffic.arrivals.shape[0])
    capacity = model.capacity_packets(config.slot_duration_s)
    delivered_bits = np.zeros(scenario.vehicle_count, dtype=np.float64)
    previous = None
    rows = []

    for slot in range(slots):
        time_index = scenario.start_index + slot
        queues.add_arrivals(slot, traffic.deadlines[slot], traffic.classes[slot])
        queues.expire(slot)
        heading = _current_heading(scenario.ego_positions_xy[: time_index + 1])
        distance, bearing = range_and_bearing(
            scenario.vehicle_positions_xy[time_index],
            scenario.ego_positions_xy[time_index],
            heading,
        )
        current = model.evaluate_arrays(distance, bearing)
        predicted, lifetime, is_oracle = _link_forecast(
            scenario,
            time_index,
            config.prediction_horizon_steps,
            scheduler.forecast_mode,
            model,
            history_noise_std_m=config.history_measurement_noise_std_m,
            forecast_noise_std_m=config.forecast_position_noise_std_m,
            noise_seed=config.seed + 10_000 * slot,
            sensing_config=config.sensing,
        )
        context = SchedulerContext(
            slot=slot,
            queue_lengths=queues.lengths(),
            time_to_deadline=queues.oldest_time_to_deadline(slot),
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
        vehicle = decision.vehicle
        if vehicle is None:
            rows.append({"slot": slot, "vehicle": -1})
            continue

        queue_before = int(context.queue_lengths[vehicle])
        deadline_before = float(context.time_to_deadline[vehicle])
        per = float(current["per"][vehicle])
        expected_immediate = min(queue_before, capacity) * (1.0 - per)
        attempted = queues.pop_attempts(vehicle, capacity)
        uniforms = traffic.success_uniforms[slot, vehicle, : len(attempted)]
        success = uniforms >= per
        failed = [
            packet
            for packet, ok in zip(attempted, success, strict=True)
            if not ok
        ]
        queues.requeue_failed(vehicle, failed)
        successful = int(np.sum(success))
        delivered_bits[vehicle] += successful * config.link.packet_bits
        previous = vehicle
        rows.append(
            {
                "slot": slot,
                "vehicle": int(vehicle),
                "queue": queue_before,
                "hol_deadline_steps": deadline_before,
                "actual_snr_db": float(current["snr_db"][vehicle]),
                "actual_per": per,
                "current_goodput_mbps": float(current["goodput_bps"][vehicle] / 1e6),
                "expected_immediate_packets": float(expected_immediate),
                "attempted_packets": len(attempted),
                "successful_packets": successful,
                "score": float(decision.scores[vehicle]),
            }
        )
    return rows


def paired_disagreements(reactive, predictive):
    by_slot_r = {row["slot"]: row for row in reactive}
    by_slot_p = {row["slot"]: row for row in predictive}
    rows = []
    for slot in sorted(set(by_slot_r) & set(by_slot_p)):
        r = by_slot_r[slot]
        p = by_slot_p[slot]
        if r["vehicle"] < 0 or p["vehicle"] < 0 or r["vehicle"] == p["vehicle"]:
            continue
        rows.append(
            {
                "slot": slot,
                "reactive_vehicle": r["vehicle"],
                "predictive_vehicle": p["vehicle"],
                "delta_queue": p["queue"] - r["queue"],
                "delta_hol_deadline_steps": (
                    p["hol_deadline_steps"] - r["hol_deadline_steps"]
                ),
                "delta_actual_snr_db": p["actual_snr_db"] - r["actual_snr_db"],
                "delta_current_goodput_mbps": (
                    p["current_goodput_mbps"] - r["current_goodput_mbps"]
                ),
                "delta_expected_immediate_packets": (
                    p["expected_immediate_packets"] - r["expected_immediate_packets"]
                ),
                "delta_successful_packets": (
                    p["successful_packets"] - r["successful_packets"]
                ),
                "predictive_lower_snr": p["actual_snr_db"] < r["actual_snr_db"],
                "predictive_larger_queue": p["queue"] > r["queue"],
                "predictive_less_urgent_hol": (
                    p["hol_deadline_steps"] > r["hol_deadline_steps"]
                ),
                "predictive_lower_immediate_service": (
                    p["expected_immediate_packets"]
                    < r["expected_immediate_packets"]
                ),
            }
        )
    return rows


def summarize(rows):
    if not rows:
        return {"disagreement_slots": 0}
    numeric = (
        "delta_queue",
        "delta_hol_deadline_steps",
        "delta_actual_snr_db",
        "delta_current_goodput_mbps",
        "delta_expected_immediate_packets",
        "delta_successful_packets",
    )
    flags = (
        "predictive_lower_snr",
        "predictive_larger_queue",
        "predictive_less_urgent_hol",
        "predictive_lower_immediate_service",
    )
    result = {"disagreement_slots": len(rows)}
    for name in numeric:
        values = np.asarray([float(row[name]) for row in rows], dtype=float)
        result[f"mean_{name}"] = float(np.nanmean(values))
        result[f"median_{name}"] = float(np.nanmedian(values))
    for name in flags:
        result[f"fraction_{name}"] = float(
            np.mean([bool(row[name]) for row in rows])
        )
    return result


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Development-only audit of predictive high-load service ordering."
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--output", default="artifacts/high_load_service_order_audit")
    args = parser.parse_args()

    base = load_config(args.config)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    disagreement_rows = []
    outcome_rows = []
    summary = {}

    for label, kind, value in REGIMES:
        summary[label] = {}
        regime_rows = []
        for seed in DEV_SEEDS:
            config = regime_config(base, kind, value, seed)
            benchmark_outputs = run_synthetic_benchmark(config)
            by_scheduler = {
                item.metrics.scheduler: item for item in benchmark_outputs
            }
            for name in POLICIES:
                metrics = by_scheduler[name].metrics
                outcome_rows.append(
                    {
                        "regime": label,
                        "seed": seed,
                        "scheduler": name,
                        "goodput_mbps": metrics.goodput_mbps,
                        "pdr": metrics.packet_delivery_ratio,
                        "p95_latency_ms": metrics.p95_latency_ms,
                        "fairness": metrics.demand_normalized_jain_fairness,
                    }
                )
            reactive = run_trace(config, "reactive_greedy")
            predictive = run_trace(config, "deadline_aware_lifetime")
            paired = paired_disagreements(reactive, predictive)
            for row in paired:
                row.update({"regime": label, "seed": seed})
            disagreement_rows.extend(paired)
            regime_rows.extend(paired)
        summary[label] = summarize(regime_rows)

    payload = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC_DEVELOPMENT_ONLY",
        "development_seeds": list(DEV_SEEDS),
        "fairness_weight": 0.0,
        "policies": list(POLICIES),
        "holdout_inspected": False,
        "regimes": summary,
    }
    write_csv(output / "disagreement_slots.csv", disagreement_rows)
    write_csv(output / "outcomes.csv", outcome_rows)
    (output / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
