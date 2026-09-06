from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config


def apply_regime(base, regime, seed, policy):
    benchmark = replace(base.benchmark, episodes=1, schedulers=(policy,))
    cfg = replace(base, seed=seed, benchmark=benchmark)
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


def run_pair(base, regime, seed, weight, protocol):
    reactive = run_synthetic_benchmark(
        apply_regime(base, regime, seed, protocol["reactive_policy"])
    )[0]
    predictive_cfg = apply_regime(
        base, regime, seed, protocol["predictive_policy"]
    )
    predictive_cfg = replace(
        predictive_cfg,
        scheduler=replace(predictive_cfg.scheduler, fairness_weight=float(weight)),
    )
    predictive = run_synthetic_benchmark(predictive_cfg)[0]
    r, p = metrics(reactive), metrics(predictive)
    return {
        "regime": regime["name"],
        "seed": seed,
        "fairness_weight": float(weight),
        **{f"reactive_{key}": value for key, value in r.items()},
        **{f"predictive_{key}": value for key, value in p.items()},
        **{f"delta_{key}": p[key] - r[key] for key in r},
    }


def select_weight(rows, protocol):
    margin = float(protocol["selection_rule"]["noninferiority_margin_mbps"])
    candidates = []
    for weight in protocol["candidate_fairness_weights"]:
        selected = [row for row in rows if row["fairness_weight"] == float(weight)]
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
        candidates.append(
            {
                "fairness_weight": float(weight),
                "eligible": eligible,
                "worst_regime_fairness_gain": min(
                    value["mean_delta_fairness"] for value in by_regime.values()
                ),
                "mean_delta_p95_latency_ms": float(
                    np.mean(
                        [value["mean_delta_p95_latency_ms"] for value in by_regime.values()]
                    )
                ),
                "regimes": by_regime,
            }
        )
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible:
        return None, candidates
    eligible.sort(
        key=lambda item: (
            -item["worst_regime_fairness_gain"],
            item["mean_delta_p95_latency_ms"],
            item["fairness_weight"],
        )
    )
    return eligible[0]["fairness_weight"], candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument(
        "--protocol", default="configs/fairness_selection_protocol.json"
    )
    parser.add_argument("--output", default="artifacts/prospective_fairness_selection")
    args = parser.parse_args()

    base = load_config(args.config)
    protocol = json.loads(Path(args.protocol).read_text(encoding="utf-8"))
    dev_rows = [
        run_pair(base, regime, seed, weight, protocol)
        for regime in protocol["regimes"]
        for seed in protocol["development_seeds"]
        for weight in protocol["candidate_fairness_weights"]
    ]
    selected_weight, candidates = select_weight(dev_rows, protocol)

    holdout_rows = []
    if selected_weight is not None:
        holdout_rows = [
            run_pair(base, regime, seed, selected_weight, protocol)
            for regime in protocol["regimes"]
            for seed in protocol["holdout_seeds"]
        ]

    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "evidence_tier": "EXECUTED_DIAGNOSTIC",
        "protocol": protocol,
        "selected_fairness_weight": selected_weight,
        "development_candidates": candidates,
        "development_rows": dev_rows,
        "holdout_rows": holdout_rows,
    }
    (destination / "prospective_fairness_selection.json").write_text(
        json.dumps(payload, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "development_rows": len(dev_rows),
                "selected_fairness_weight": selected_weight,
                "holdout_rows": len(holdout_rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
