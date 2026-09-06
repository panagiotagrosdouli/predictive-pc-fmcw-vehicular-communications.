from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config


def apply_regime(base, regime, seed, policy, protocol):
    benchmark = replace(base.benchmark, episodes=1, schedulers=(policy,))
    scheduler = replace(
        base.scheduler,
        fairness_weight=float(protocol["scheduler_overrides"]["fairness_weight"]),
    )
    cfg = replace(base, seed=seed, benchmark=benchmark, scheduler=scheduler)
    kind, value = regime["kind"], float(regime["value"])
    if kind == "deadline":
        return replace(
            cfg,
            traffic=replace(cfg.traffic, deadline_s=value, deadline_jitter_s=0.0),
        )
    if kind == "load":
        return replace(cfg, traffic=replace(cfg.traffic, offered_load=value))
    if kind == "snr_offset":
        return replace(
            cfg,
            link=replace(cfg.link, reference_snr_db=cfg.link.reference_snr_db + value),
        )
    raise ValueError(kind)


def metrics(output):
    return {
        "goodput_mbps": output.metrics.goodput_mbps,
        "fairness": output.metrics.demand_normalized_jain_fairness,
        "p95_latency_ms": output.metrics.p95_latency_ms,
        "pdr": output.metrics.packet_delivery_ratio,
    }


def run_pair(base, regime, seed, candidate, protocol):
    reactive = run_synthetic_benchmark(
        apply_regime(
            base,
            regime,
            seed,
            protocol["reactive_policy"],
            protocol,
        )
    )[0]
    predictive = run_synthetic_benchmark(
        apply_regime(base, regime, seed, candidate["name"], protocol)
    )[0]
    r, p = metrics(reactive), metrics(predictive)
    return {
        "regime": regime["name"],
        "seed": seed,
        "candidate_policy": candidate["name"],
        "guard_ratio": float(candidate["guard_ratio"]),
        **{f"reactive_{key}": value for key, value in r.items()},
        **{f"candidate_{key}": value for key, value in p.items()},
        **{f"delta_{key}": p[key] - r[key] for key in r},
    }


def select_candidate(rows, protocol):
    margin = float(protocol["selection_rule"]["noninferiority_margin_mbps"])
    candidates = []
    for candidate in protocol["candidate_policies"]:
        selected = [
            row
            for row in rows
            if row["candidate_policy"] == candidate["name"]
        ]
        by_regime = {}
        for regime in protocol["regimes"]:
            current = [row for row in selected if row["regime"] == regime["name"]]
            by_regime[regime["name"]] = {
                "mean_delta_goodput_mbps": float(
                    np.mean([row["delta_goodput_mbps"] for row in current])
                ),
                "mean_delta_fairness": float(
                    np.mean([row["delta_fairness"] for row in current])
                ),
                "mean_delta_p95_latency_ms": float(
                    np.mean([row["delta_p95_latency_ms"] for row in current])
                ),
            }
        eligible = all(
            value["mean_delta_goodput_mbps"] >= -margin
            for value in by_regime.values()
        )
        latency_deltas = [
            value["mean_delta_p95_latency_ms"] for value in by_regime.values()
        ]
        candidates.append(
            {
                "candidate_policy": candidate["name"],
                "guard_ratio": float(candidate["guard_ratio"]),
                "eligible": eligible,
                "worst_regime_goodput_gain_mbps": min(
                    value["mean_delta_goodput_mbps"]
                    for value in by_regime.values()
                ),
                "mean_delta_p95_latency_ms": float(np.mean(latency_deltas)),
                "regimes": by_regime,
            }
        )
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible:
        return None, candidates
    eligible.sort(
        key=lambda item: (
            -item["worst_regime_goodput_gain_mbps"],
            item["mean_delta_p95_latency_ms"],
            item["guard_ratio"],
        )
    )
    return eligible[0], candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument(
        "--protocol", default="configs/service_guard_selection_protocol.json"
    )
    parser.add_argument(
        "--output", default="artifacts/prospective_service_guard_selection"
    )
    args = parser.parse_args()

    base = load_config(args.config)
    protocol = json.loads(Path(args.protocol).read_text(encoding="utf-8"))
    dev_rows = [
        run_pair(base, regime, seed, candidate, protocol)
        for regime in protocol["regimes"]
        for seed in protocol["development_seeds"]
        for candidate in protocol["candidate_policies"]
    ]
    selected, candidates = select_candidate(dev_rows, protocol)

    holdout_rows = []
    if selected is not None:
        candidate = next(
            item
            for item in protocol["candidate_policies"]
            if item["name"] == selected["candidate_policy"]
        )
        holdout_rows = [
            run_pair(base, regime, seed, candidate, protocol)
            for regime in protocol["regimes"]
            for seed in protocol["holdout_seeds"]
        ]

    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "protocol": protocol,
        "selected_candidate": selected,
        "development_candidates": candidates,
        "development_rows": dev_rows,
        "holdout_rows": holdout_rows,
    }
    (destination / "prospective_service_guard_selection.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "development_rows": len(dev_rows),
                "selected_candidate": selected,
                "holdout_rows": len(holdout_rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
