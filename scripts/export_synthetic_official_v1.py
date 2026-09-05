#!/usr/bin/env python3
"""Export freeze-gated held-out or OOD synthetic evaluation windows."""

from __future__ import annotations

import argparse

from predictive_pc_fmcw.synthetic.official_export import (
    build_official_evaluation_npz,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="artifacts/synthetic_dataset_v1")
    parser.add_argument(
        "--training-npz", default="artifacts/synthetic_dataset_v1/training_dev.npz"
    )
    parser.add_argument(
        "--ablation", default="artifacts/synthetic_dataset_v1/learned_ablation"
    )
    parser.add_argument(
        "--split", choices=("held_out_test", "ood_test"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--history-steps", type=int, default=20)
    parser.add_argument("--horizon-steps", type=int, default=10)
    parser.add_argument("--stride", type=int, default=5)
    args = parser.parse_args()
    path = build_official_evaluation_npz(
        args.dataset,
        args.ablation,
        args.training_npz,
        args.output,
        split=args.split,
        history_steps=args.history_steps,
        horizon_steps=args.horizon_steps,
        stride=args.stride,
    )
    print(path)


if __name__ == "__main__":
    main()
