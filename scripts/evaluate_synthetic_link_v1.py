#!/usr/bin/env python3
"""Evaluate B0-B4 future-link prediction on Synthetic Dataset v1."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from predictive_pc_fmcw.synthetic.link_evaluation import (
    evaluate_synthetic_link_prediction,
    save_link_prediction_results,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", default="artifacts/synthetic_dataset_v1"
    )
    parser.add_argument("--split", default="development")
    parser.add_argument("--history-steps", type=int, default=20)
    parser.add_argument("--horizon-steps", type=int, default=10)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--allow-official-test", action="store_true")
    parser.add_argument(
        "--output",
        default="artifacts/synthetic_dataset_v1/development_link_metrics.json",
    )
    args = parser.parse_args()
    results = evaluate_synthetic_link_prediction(
        args.dataset,
        split=args.split,
        history_steps=args.history_steps,
        horizon_steps=args.horizon_steps,
        stride=args.stride,
        allow_official_test=args.allow_official_test,
    )
    save_link_prediction_results(results, args.output)
    print(json.dumps([asdict(row) for row in results], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
