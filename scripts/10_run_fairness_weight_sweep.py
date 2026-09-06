from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config

SEEDS = (20260827, 20260828, 20260829, 20260830, 20260831)
REGIMES = (
    ("deadline_0p05", "deadline", 0.05),
    ("deadline_0p5", "deadline", 0.5),
    ("load_1p1", "load", 1.1),
    ("snr_plus3", "snr_offset", 3.0),
)
FAIRNESS_WEIGHTS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
PREDICTIVE_POLICY = "deadline_aware_lifetime"
REACTIVE_POLICY = "reactive_greedy"


def regime_config(base, kind: str, value: float, seed: int, policy: str):
    benchmark = replace(base.benchmark, episodes=1, schedulers=(policy,))
    cfg = replace(base, seed=seed, benchmark=benchmark)
    if kind == "deadline":
        return replace(
            cfg,
            traffic=replace(
                cfg.traffic,
                deadline_s=value,
                deadline_jitter_s=0.0,
            ),
        )
    if kind == "load":
        return replace(cfg, traffic=replace(cfg.traffic, offered_load=value))
    if kind == "snr_offset":
        return replace(
            cfg,
            link=replace(
                cfg.link,
                reference_snr_db=cfg.link.reference_snr_db + value,
            ),
        )
    raise ValueError(kind)


def state_metrics(output):
    selected = output.selected_vehicle
    active = selected >= 0
    slots = np.flatnonzero(active)
    vehicles = selected[active]
    if not slots.size:
        snr = outage = queue = float("nan")
    else:
        snr = float(np.mean(output.actual_snr_db[slots, vehicles]))
        outage = float(np.mean(output.actual_outage[slots, vehicles]))
        queue = float(np.mean(output.queue_packets[slots, vehicles]))
    return {
        "goodput_mbps": output.metrics.goodput_mbps,
        "pdr": output.metrics.packet_delivery_ratio,
        "p95_latency_ms": output.metrics.p95_latency_ms,
        "fairness": output.metrics.demand_normalized_jain_fairness,
        "chosen_actual_snr_db": snr,
        "chosen_actual_outage_fraction": outage,
        "mean_queue_at_choice": queue,
    }


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fairness-weight Pareto sweep for deadline-aware predictive "
            "scheduling."
        )
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--output", default="artifacts/fairness_weight_sweep")
    args = parser.parse_args()

    base = load_config(args.config)
    rows = []

    for regime, kind, value in REGIMES:
        for seed in SEEDS:
            reactive_cfg = regime_config(base, kind, value, seed, REACTIVE_POLICY)
            reactive_output = run_synthetic_benchmark(reactive_cfg)[0]
            rows.append(
                {
                    "regime": regime,
                    "seed": seed,
                    "policy": REACTIVE_POLICY,
                    "fairness_weight": "reactive",
                    **state_metrics(reactive_output),
                }
            )

            predictive_base = regime_config(
                base,
                kind,
                value,
                seed,
                PREDICTIVE_POLICY,
            )
            for weight in FAIRNESS_WEIGHTS:
                cfg = replace(
                    predictive_base,
                    scheduler=replace(
                        predictive_base.scheduler,
                        fairness_weight=weight,
                    ),
                )
                output = run_synthetic_benchmark(cfg)[0]
                rows.append(
                    {
                        "regime": regime,
                        "seed": seed,
                        "policy": PREDICTIVE_POLICY,
                        "fairness_weight": weight,
                        **state_metrics(output),
                    }
                )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "fairness_weight_sweep.csv", rows)

    summary = {}
    for regime, _, _ in REGIMES:
        summary[regime] = {}
        regime_rows = [row for row in rows if row["regime"] == regime]
        reactive = [row for row in regime_rows if row["policy"] == REACTIVE_POLICY]
        reactive_goodput = float(np.mean([row["goodput_mbps"] for row in reactive]))
        reactive_fairness = float(np.mean([row["fairness"] for row in reactive]))
        summary[regime][REACTIVE_POLICY] = {
            "mean_goodput_mbps": reactive_goodput,
            "mean_fairness": reactive_fairness,
            "mean_pdr": float(np.mean([row["pdr"] for row in reactive])),
            "mean_p95_latency_ms": float(
                np.mean([row["p95_latency_ms"] for row in reactive])
            ),
        }
        for weight in FAIRNESS_WEIGHTS:
            selected = [
                row
                for row in regime_rows
                if row["policy"] == PREDICTIVE_POLICY
                and float(row["fairness_weight"]) == weight
            ]
            mean_goodput = float(np.mean([row["goodput_mbps"] for row in selected]))
            mean_fairness = float(np.mean([row["fairness"] for row in selected]))
            summary[regime][f"fairness_{weight:.2f}"] = {
                "mean_goodput_mbps": mean_goodput,
                "delta_goodput_vs_reactive_mbps": mean_goodput - reactive_goodput,
                "mean_fairness": mean_fairness,
                "delta_fairness_vs_reactive": mean_fairness - reactive_fairness,
                "mean_pdr": float(np.mean([row["pdr"] for row in selected])),
                "mean_p95_latency_ms": float(
                    np.mean([row["p95_latency_ms"] for row in selected])
                ),
            }

    payload = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "predictive_policy": PREDICTIVE_POLICY,
        "reactive_policy": REACTIVE_POLICY,
        "seeds": list(SEEDS),
        "fairness_weights": list(FAIRNESS_WEIGHTS),
        "regimes": summary,
    }
    (output_dir / "fairness_weight_sweep_summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(rows), "output": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
