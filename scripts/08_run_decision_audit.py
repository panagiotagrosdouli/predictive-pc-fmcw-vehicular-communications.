from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config

POLICIES = (
    "reactive_greedy",
    "predictive_utility",
    "link_lifetime",
    "deadline_aware_lifetime",
    "oracle",
)
REGIMES = (
    ("deadline_0p05", "deadline", 0.05),
    ("deadline_0p5", "deadline", 0.5),
    ("load_1p1", "load", 1.1),
    ("snr_plus3", "snr_offset", 3.0),
)
SEEDS = (20260827, 20260828, 20260829, 20260830, 20260831)
PAIRS = (
    ("reactive_greedy", "predictive_utility"),
    ("predictive_utility", "link_lifetime"),
    ("link_lifetime", "deadline_aware_lifetime"),
    ("reactive_greedy", "deadline_aware_lifetime"),
    ("deadline_aware_lifetime", "oracle"),
    ("reactive_greedy", "link_lifetime"),
)
AGREEMENT_METRICS = (
    "all_slot_agreement",
    "both_active_fraction",
    "both_active_agreement",
    "both_active_disagreement_fraction",
    "a_only_active_fraction",
    "b_only_active_fraction",
)


def regime_config(base, kind: str, value: float, seed: int):
    benchmark = replace(
        base.benchmark,
        episodes=1,
        schedulers=POLICIES,
    )
    cfg = replace(base, seed=seed, benchmark=benchmark)
    if kind == "deadline":
        traffic = replace(
            cfg.traffic,
            deadline_s=value,
            deadline_jitter_s=0.0,
        )
        return replace(cfg, traffic=traffic)
    if kind == "load":
        return replace(
            cfg,
            traffic=replace(cfg.traffic, offered_load=value),
        )
    if kind == "snr_offset":
        link = replace(
            cfg.link,
            reference_snr_db=cfg.link.reference_snr_db + value,
        )
        return replace(cfg, link=link)
    raise ValueError(kind)


def pair_stats(a, b):
    selected_a = a.selected_vehicle
    selected_b = b.selected_vehicle
    if selected_a.shape != selected_b.shape:
        raise ValueError("paired traces have different lengths")

    active_a = selected_a >= 0
    active_b = selected_b >= 0
    both_active = active_a & active_b
    agreement = selected_a == selected_b
    disagreement = both_active & ~agreement
    slots = len(selected_a)

    def fraction(mask):
        return float(np.mean(mask)) if slots else float("nan")

    if np.any(both_active):
        active_agreement = float(np.mean(agreement[both_active]))
    else:
        active_agreement = float("nan")

    return {
        "slots": slots,
        "all_slot_agreement": fraction(agreement),
        "both_active_fraction": fraction(both_active),
        "both_active_agreement": active_agreement,
        "both_active_disagreement_fraction": fraction(disagreement),
        "a_only_active_fraction": fraction(active_a & ~active_b),
        "b_only_active_fraction": fraction(active_b & ~active_a),
    }


def chosen_state(output):
    selected = output.selected_vehicle
    active = selected >= 0
    slots = np.flatnonzero(active)
    vehicles = selected[active]
    if not slots.size:
        return {
            "chosen_actual_outage_fraction": float("nan"),
            "chosen_actual_snr_db": float("nan"),
            "mean_queue_at_choice": float("nan"),
        }
    return {
        "chosen_actual_outage_fraction": float(
            np.mean(output.actual_outage[slots, vehicles])
        ),
        "chosen_actual_snr_db": float(
            np.mean(output.actual_snr_db[slots, vehicles])
        ),
        "mean_queue_at_choice": float(
            np.mean(output.queue_packets[slots, vehicles])
        ),
    }


def state_row(label, seed, name, output):
    return {
        "regime": label,
        "seed": seed,
        "scheduler": name,
        **chosen_state(output),
        "goodput_mbps": output.metrics.goodput_mbps,
        "pdr": output.metrics.packet_delivery_ratio,
        "p95_latency_ms": output.metrics.p95_latency_ms,
        "fairness": output.metrics.demand_normalized_jain_fairness,
    }


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Decision-level mechanism audit for corrected predictive schedulers."
        )
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--output", default="artifacts/decision_audit")
    args = parser.parse_args()

    base = load_config(args.config)
    rows = []
    state_rows = []

    for label, kind, value in REGIMES:
        for seed in SEEDS:
            config = regime_config(base, kind, value, seed)
            outputs = run_synthetic_benchmark(config)
            by_scheduler = {output.metrics.scheduler: output for output in outputs}

            for name in POLICIES:
                state_rows.append(
                    state_row(label, seed, name, by_scheduler[name])
                )

            for policy_a, policy_b in PAIRS:
                rows.append(
                    {
                        "regime": label,
                        "seed": seed,
                        "policy_a": policy_a,
                        "policy_b": policy_b,
                        **pair_stats(
                            by_scheduler[policy_a],
                            by_scheduler[policy_b],
                        ),
                    }
                )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "decision_agreement.csv", rows)
    write_csv(output_dir / "chosen_state.csv", state_rows)

    summary = {}
    for label, _, _ in REGIMES:
        summary[label] = {}
        for policy_a, policy_b in PAIRS:
            selected_rows = [
                row
                for row in rows
                if row["regime"] == label
                and row["policy_a"] == policy_a
                and row["policy_b"] == policy_b
            ]
            summary[label][f"{policy_a}__vs__{policy_b}"] = {
                metric: float(
                    np.nanmean([row[metric] for row in selected_rows])
                )
                for metric in AGREEMENT_METRICS
            }

    payload = {
        "schema_version": 2,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "seeds": list(SEEDS),
        "policies": list(POLICIES),
        "regimes": summary,
    }
    (output_dir / "decision_audit_summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "rows": len(rows),
                "state_rows": len(state_rows),
                "output": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
