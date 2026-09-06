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
VARIANTS = (
    ("full", None),
    ("no_fairness", "fairness_weight"),
    ("no_queue", "queue_weight"),
    ("no_deadline", "deadline_weight"),
    ("no_opportunity", "opportunity_weight"),
)
POLICY = "deadline_aware_lifetime"


def regime_config(base, kind: str, value: float, seed: int):
    benchmark = replace(base.benchmark, episodes=1, schedulers=(POLICY,))
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


def variant_config(cfg, field_name: str | None):
    if field_name is None:
        return cfg
    return replace(cfg, scheduler=replace(cfg.scheduler, **{field_name: 0.0}))


def chosen_state(output):
    selected = output.selected_vehicle
    active = selected >= 0
    slots = np.flatnonzero(active)
    vehicles = selected[active]
    if not slots.size:
        return float("nan"), float("nan"), float("nan")
    return (
        float(np.mean(output.actual_snr_db[slots, vehicles])),
        float(np.mean(output.actual_outage[slots, vehicles])),
        float(np.mean(output.queue_packets[slots, vehicles])),
    )


def disagreement(reference, candidate):
    a = reference.selected_vehicle
    b = candidate.selected_vehicle
    if a.shape != b.shape:
        raise ValueError("paired traces have different lengths")
    both_active = (a >= 0) & (b >= 0)
    if not np.any(both_active):
        return float("nan")
    return float(np.mean(a[both_active] != b[both_active]))


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Paired utility-term ablation for predictive scheduling."
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--output", default="artifacts/utility_term_ablation")
    args = parser.parse_args()

    base = load_config(args.config)
    rows = []
    for regime, kind, value in REGIMES:
        for seed in SEEDS:
            cfg = regime_config(base, kind, value, seed)
            outputs = {}
            for variant, field_name in VARIANTS:
                run_cfg = variant_config(cfg, field_name)
                outputs[variant] = run_synthetic_benchmark(run_cfg)[0]
            reference = outputs["full"]
            for variant, field_name in VARIANTS:
                output = outputs[variant]
                snr, outage, queue = chosen_state(output)
                rows.append(
                    {
                        "regime": regime,
                        "seed": seed,
                        "variant": variant,
                        "removed_term": field_name or "none",
                        "decision_disagreement_vs_full": (
                            0.0
                            if variant == "full"
                            else disagreement(reference, output)
                        ),
                        "goodput_mbps": output.metrics.goodput_mbps,
                        "pdr": output.metrics.packet_delivery_ratio,
                        "p95_latency_ms": output.metrics.p95_latency_ms,
                        "fairness": output.metrics.demand_normalized_jain_fairness,
                        "chosen_actual_snr_db": snr,
                        "chosen_actual_outage_fraction": outage,
                        "mean_queue_at_choice": queue,
                    }
                )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "utility_term_ablation.csv", rows)

    summary = {}
    for regime, _, _ in REGIMES:
        summary[regime] = {}
        regime_rows = [row for row in rows if row["regime"] == regime]
        full_rows = [row for row in regime_rows if row["variant"] == "full"]
        full_by_seed = {row["seed"]: row for row in full_rows}
        for variant, _ in VARIANTS:
            selected = [row for row in regime_rows if row["variant"] == variant]
            delta = [
                row["goodput_mbps"] - full_by_seed[row["seed"]]["goodput_mbps"]
                for row in selected
            ]
            summary[regime][variant] = {
                "mean_goodput_mbps": float(
                    np.mean([row["goodput_mbps"] for row in selected])
                ),
                "mean_delta_goodput_vs_full_mbps": float(np.mean(delta)),
                "mean_pdr": float(np.mean([row["pdr"] for row in selected])),
                "mean_p95_latency_ms": float(
                    np.mean([row["p95_latency_ms"] for row in selected])
                ),
                "mean_fairness": float(
                    np.mean([row["fairness"] for row in selected])
                ),
                "mean_decision_disagreement_vs_full": float(
                    np.mean(
                        [row["decision_disagreement_vs_full"] for row in selected]
                    )
                ),
            }

    payload = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "policy": POLICY,
        "seeds": list(SEEDS),
        "variants": [name for name, _ in VARIANTS],
        "regimes": summary,
    }
    (output_dir / "utility_term_ablation_summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(rows), "output": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
