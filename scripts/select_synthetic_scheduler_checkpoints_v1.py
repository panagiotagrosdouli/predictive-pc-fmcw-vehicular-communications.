#!/usr/bin/env python3
"""Freeze development-only representative checkpoints for S5/S6."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.config import load_config
from predictive_pc_fmcw.synthetic.checkpoint_selection import (
    build_development_checkpoint_selection,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="artifacts/synthetic_dataset_v1")
    parser.add_argument(
        "--training-npz",
        default="artifacts/synthetic_dataset_v1/training_dev.npz",
    )
    parser.add_argument(
        "--ablation",
        default="artifacts/synthetic_dataset_v1/learned_ablation",
    )
    parser.add_argument(
        "--output",
        default="artifacts/synthetic_dataset_v1/development_checkpoint_selection.json",
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--batch-size", type=int, default=1024)
    args = parser.parse_args()

    config = load_config(args.config)
    report = build_development_checkpoint_selection(
        args.training_npz,
        args.ablation,
        args.dataset,
        args.output,
        link_config=config.link,
        batch_size=args.batch_size,
        dt_s=config.slot_duration_s,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
