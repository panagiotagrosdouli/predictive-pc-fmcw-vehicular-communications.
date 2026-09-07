#!/usr/bin/env python3
"""Analyze the frozen prospective current-service-guard holdout.

This script performs the precommitted Paper-1 primary analysis on the saved
prospective service-guard JSON artifact. It does not tune or select policies.

Primary endpoint: paired candidate-minus-reactive goodput difference by regime.
Inference: 100,000 paired percentile bootstrap replicates, two-sided paired
Wilcoxon signed-rank test, Holm correction across the four predeclared regimes,
paired Cohen dz, and win/loss/tie fractions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

BOOTSTRAP_REPLICATES = 100_000
BOOTSTRAP_SEED = 20260906
PRACTICAL_MARGIN_MBPS = 0.001
EXPECTED_REGIMES = ["deadline_0p05", "deadline_0p5", "load_1p1", "snr_plus3"]


def percentile_ci(
    values: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, float]:
    n = len(values)
    indices = rng.integers(0, n, size=(BOOTSTRAP_REPLICATES, n))
    boot_means = values[indices].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def holm_adjust(p_values: list[float]) -> list[float]:
    m = len(p_values)
    order = np.argsort(np.asarray(p_values))
    adjusted = np.empty(m, dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = (m - rank) * p_values[index]
        running = max(running, candidate)
        adjusted[index] = min(running, 1.0)
    return adjusted.tolist()


def classify(ci_lo: float, ci_hi: float) -> str:
    if ci_lo > PRACTICAL_MARGIN_MBPS:
        return "HELP"
    if ci_hi < -PRACTICAL_MARGIN_MBPS:
        return "HURT"
    return "NEUTRAL_OR_UNCERTAIN"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    selected = payload.get("selected_candidate")
    if not selected:
        raise SystemExit(
            "Frozen development protocol selected no candidate; "
            "holdout analysis is invalid."
        )
    if selected.get("candidate_policy") != "service_guarded_80":
        candidate_policy = selected.get("candidate_policy")
        raise SystemExit(f"Unexpected frozen candidate: {candidate_policy}")

    rows = payload.get("holdout_rows", [])
    if len(rows) != 80:
        raise SystemExit(f"Expected exactly 80 holdout rows, found {len(rows)}")

    by_regime: dict[str, list[dict]] = {name: [] for name in EXPECTED_REGIMES}
    for row in rows:
        regime = row["regime"]
        if regime not in by_regime:
            raise SystemExit(f"Unexpected holdout regime: {regime}")
        by_regime[regime].append(row)

    for regime, regime_rows in by_regime.items():
        seeds = [int(row["seed"]) for row in regime_rows]
        if len(regime_rows) != 20 or len(set(seeds)) != 20:
            raise SystemExit(f"{regime}: expected 20 unique paired holdout seeds")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    results = []
    raw_p = []

    for regime in EXPECTED_REGIMES:
        regime_rows = sorted(
            by_regime[regime],
            key=lambda row: int(row["seed"]),
        )
        delta = np.asarray(
            [float(row["delta_goodput_mbps"]) for row in regime_rows]
        )
        ci_lo, ci_hi = percentile_ci(delta, rng)
        wilcoxon = stats.wilcoxon(
            delta,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        p_value = float(wilcoxon.pvalue)
        raw_p.append(p_value)
        sd = float(delta.std(ddof=1))
        dz = float(delta.mean() / sd) if sd > 0 else 0.0
        results.append(
            {
                "regime": regime,
                "n_pairs": len(delta),
                "mean_delta_goodput_mbps": float(delta.mean()),
                "ci95_low_mbps": ci_lo,
                "ci95_high_mbps": ci_hi,
                "classification": classify(ci_lo, ci_hi),
                "wilcoxon_statistic": float(wilcoxon.statistic),
                "wilcoxon_p_raw": p_value,
                "cohen_dz": dz,
                "win_fraction": float(np.mean(delta > 0)),
                "loss_fraction": float(np.mean(delta < 0)),
                "tie_fraction": float(np.mean(delta == 0)),
            }
        )

    adjusted = holm_adjust(raw_p)
    for result, p_holm in zip(results, adjusted, strict=True):
        result["wilcoxon_p_holm"] = p_holm

    output = {
        "schema_version": 1,
        "status": "FROZEN_HOLDOUT_ANALYSIS",
        "input_selected_candidate": selected,
        "analysis_protocol": {
            "primary_metric": "delta_goodput_mbps",
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_method": (
                "paired percentile bootstrap of mean paired difference"
            ),
            "confidence_level": 0.95,
            "practical_margin_mbps": PRACTICAL_MARGIN_MBPS,
            "classification_rule": (
                "HELP if CI lower > +margin; HURT if CI upper < -margin; "
                "otherwise NEUTRAL_OR_UNCERTAIN"
            ),
            "paired_test": "two-sided Wilcoxon signed-rank",
            "multiplicity": (
                "Holm across four predeclared primary regime comparisons"
            ),
            "effect_size": "paired Cohen dz",
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
