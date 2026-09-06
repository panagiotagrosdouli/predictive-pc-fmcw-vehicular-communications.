from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.benchmark import run_synthetic_benchmark
from predictive_pc_fmcw.config import load_config

POLICIES = ("reactive_greedy", "predictive_utility", "link_lifetime", "oracle")
REGIMES = (
    ("deadline_0p05", "deadline", 0.05),
    ("deadline_0p5", "deadline", 0.5),
    ("load_1p1", "load", 1.1),
    ("snr_plus3", "snr_offset", 3.0),
)
SEEDS = (20260827, 20260828, 20260829, 20260830, 20260831)


def regime_config(base, kind: str, value: float, seed: int):
    cfg = replace(base, seed=seed, benchmark=replace(base.benchmark, episodes=1, schedulers=POLICIES))
    if kind == "deadline":
        return replace(cfg, traffic=replace(cfg.traffic, deadline_s=value, deadline_jitter_s=0.0))
    if kind == "load":
        return replace(cfg, traffic=replace(cfg.traffic, offered_load=value))
    if kind == "snr_offset":
        return replace(cfg, link=replace(cfg.link, reference_snr_db=cfg.link.reference_snr_db + value))
    raise ValueError(kind)


def pair_stats(a, b):
    sa, sb = a.selected_vehicle, b.selected_vehicle
    if sa.shape != sb.shape:
        raise ValueError("paired traces have different lengths")
    active_a, active_b = sa >= 0, sb >= 0
    both = active_a & active_b
    agree = sa == sb
    disagreements = both & ~agree
    n = len(sa)
    def frac(mask): return float(np.mean(mask)) if n else float("nan")
    return {
        "slots": n,
        "all_slot_agreement": frac(agree),
        "both_active_fraction": frac(both),
        "both_active_agreement": float(np.mean(agree[both])) if np.any(both) else float("nan"),
        "both_active_disagreement_fraction": frac(disagreements),
        "a_only_active_fraction": frac(active_a & ~active_b),
        "b_only_active_fraction": frac(active_b & ~active_a),
    }


def chosen_state(output):
    selected = output.selected_vehicle
    active = selected >= 0
    slots = np.flatnonzero(active)
    vehicles = selected[active]
    if not slots.size:
        return {"chosen_actual_outage_fraction": float("nan"), "chosen_actual_snr_db": float("nan"), "mean_queue_at_choice": float("nan")}
    return {
        "chosen_actual_outage_fraction": float(np.mean(output.actual_outage[slots, vehicles])),
        "chosen_actual_snr_db": float(np.mean(output.actual_snr_db[slots, vehicles])),
        "mean_queue_at_choice": float(np.mean(output.queue_packets[slots, vehicles])),
    }


def main():
    p = argparse.ArgumentParser(description="Decision-level mechanism audit for corrected predictive schedulers.")
    p.add_argument("--config", default="configs/default.json")
    p.add_argument("--output", default="artifacts/decision_audit")
    args = p.parse_args()
    base = load_config(args.config)
    rows = []
    state_rows = []
    for label, kind, value in REGIMES:
        for seed in SEEDS:
            outputs = run_synthetic_benchmark(regime_config(base, kind, value, seed))
            by = {o.metrics.scheduler: o for o in outputs}
            for name in POLICIES:
                state_rows.append({"regime": label, "seed": seed, "scheduler": name, **chosen_state(by[name]), "goodput_mbps": by[name].metrics.goodput_mbps, "pdr": by[name].metrics.packet_delivery_ratio, "p95_latency_ms": by[name].metrics.p95_latency_ms, "fairness": by[name].metrics.demand_normalized_jain_fairness})
            for a, b in (("reactive_greedy", "predictive_utility"), ("predictive_utility", "link_lifetime"), ("link_lifetime", "oracle"), ("reactive_greedy", "link_lifetime")):
                rows.append({"regime": label, "seed": seed, "policy_a": a, "policy_b": b, **pair_stats(by[a], by[b])})
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    for filename, data in (("decision_agreement.csv", rows), ("chosen_state.csv", state_rows)):
        with (out / filename).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=data[0].keys()); w.writeheader(); w.writerows(data)
    summary = {}
    for label, _, _ in REGIMES:
        summary[label] = {}
        for a, b in (("reactive_greedy", "predictive_utility"), ("predictive_utility", "link_lifetime"), ("link_lifetime", "oracle"), ("reactive_greedy", "link_lifetime")):
            sel = [r for r in rows if r["regime"] == label and r["policy_a"] == a and r["policy_b"] == b]
            summary[label][f"{a}__vs__{b}"] = {k: float(np.nanmean([r[k] for r in sel])) for k in ("all_slot_agreement", "both_active_fraction", "both_active_agreement", "both_active_disagreement_fraction", "a_only_active_fraction", "b_only_active_fraction")}
    (out / "decision_audit_summary.json").write_text(json.dumps({"schema_version": 1, "evidence_tier": "EXECUTED_DIAGNOSTIC", "seeds": list(SEEDS), "regimes": summary}, indent=2, allow_nan=True), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "state_rows": len(state_rows), "output": str(out)}, indent=2))

if __name__ == "__main__":
    main()
