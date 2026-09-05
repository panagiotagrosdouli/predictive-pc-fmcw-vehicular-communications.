#!/usr/bin/env python3
"""Run freeze-gated paired synthetic scheduling evaluation."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.config import load_config
from predictive_pc_fmcw.synthetic.scheduling_evaluation import (
    run_synthetic_scheduling_evaluation,
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
        "--selection-manifest",
        default=(
            "artifacts/synthetic_dataset_v1/"
            "development_checkpoint_selection.json"
        ),
    )
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument(
        "--split",
        choices=("held_out_test", "ood_test"),
        default="held_out_test",
    )
    parser.add_argument("--vehicles-per-episode", type=int, default=5)
    parser.add_argument("--history-steps", type=int, default=20)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    output = args.output or (
        f"artifacts/synthetic_dataset_v1/scheduling_{args.split}.json"
    )
    config = load_config(args.config)
    report = run_synthetic_scheduling_evaluation(
        args.dataset,
        split=args.split,
        ablation_dir=args.ablation,
        training_npz=args.training_npz,
        selection_manifest=args.selection_manifest,
        config=config,
        output_path=output,
        vehicles_per_episode=args.vehicles_per_episode,
        history_steps=args.history_steps,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "split": report["split"],
                "planned_runs": report["plan"]["planned_runs"],
                "output": output,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
