#!/usr/bin/env python3
"""Export train/development windows from Synthetic Dataset v1."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.synthetic.training_export import (
    build_synthetic_training_npz,
    validate_synthetic_training_npz,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", default="artifacts/synthetic_dataset_v1"
    )
    parser.add_argument(
        "--output", default="artifacts/synthetic_dataset_v1/training_dev.npz"
    )
    parser.add_argument("--history-steps", type=int, default=20)
    parser.add_argument("--horizon-steps", type=int, default=10)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only:
        build_synthetic_training_npz(
            args.dataset,
            args.output,
            history_steps=args.history_steps,
            horizon_steps=args.horizon_steps,
            stride=args.stride,
        )
    report = validate_synthetic_training_npz(args.dataset, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
