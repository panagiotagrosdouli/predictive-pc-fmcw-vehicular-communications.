#!/usr/bin/env python3
"""Run the frozen four-objective x five-seed synthetic GRU ablation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from predictive_pc_fmcw.config import load_config
from predictive_pc_fmcw.learning.ablation import (
    CANONICAL_SEEDS,
    build_training_ablation_plan,
    run_training_ablation,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="artifacts/synthetic_dataset_v1/training_dev.npz",
    )
    parser.add_argument(
        "--output",
        default="artifacts/synthetic_dataset_v1/learned_ablation",
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lambda-link", type=float, default=0.2)
    parser.add_argument("--lambda-outage", type=float, default=0.1)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()

    plan = build_training_ablation_plan(
        args.dataset,
        seeds=CANONICAL_SEEDS,
        epochs=args.epochs,
    )
    if plan.planned_runs != 20:
        raise RuntimeError("publication ablation must contain exactly 20 runs")
    if args.plan_only:
        print(json.dumps(asdict(plan), indent=2, sort_keys=True))
        return

    config = load_config(args.config)
    results = run_training_ablation(
        args.dataset,
        Path(args.output),
        link_config=config.link,
        seeds=CANONICAL_SEEDS,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lambda_link=args.lambda_link,
        lambda_outage=args.lambda_outage,
    )
    if len(results) != 20:
        raise RuntimeError("training returned fewer than 20 verified run results")
    print(
        json.dumps(
            {
                "status": "COMPLETED",
                "verified_runs": len(results),
                "completion_manifest": str(
                    Path(args.output) / "completion_manifest.json"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
