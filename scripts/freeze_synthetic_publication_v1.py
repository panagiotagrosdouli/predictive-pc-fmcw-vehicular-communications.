#!/usr/bin/env python3
"""Verify the 20-checkpoint freeze before any official synthetic evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from predictive_pc_fmcw.synthetic.freeze import verify_publication_training_freeze


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
        "--output", default="artifacts/synthetic_dataset_v1/publication_freeze.json"
    )
    args = parser.parse_args()
    report = verify_publication_training_freeze(
        args.dataset, args.ablation, args.training_npz
    )
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite frozen artifact: {destination}")
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
