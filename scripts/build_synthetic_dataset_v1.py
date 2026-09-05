#!/usr/bin/env python3
"""Build or validate the parallel Synthetic Dataset v1 protocol."""

from __future__ import annotations

import argparse
import json

from predictive_pc_fmcw.synthetic.dataset import (
    DatasetBuildConfig,
    build_dataset,
    validate_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/synthetic_dataset_v1")
    parser.add_argument("--scenarios-per-family", type=int, default=20)
    parser.add_argument("--ood-scenarios-per-family", type=int, default=5)
    parser.add_argument("--master-seed", type=int, default=20260905)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        report = validate_dataset(args.output)
    else:
        config = DatasetBuildConfig(
            master_seed=args.master_seed,
            scenarios_per_family=args.scenarios_per_family,
            ood_scenarios_per_family=args.ood_scenarios_per_family,
        )
        manifest = build_dataset(args.output, config=config)
        report = validate_dataset(args.output)
        report["built_scenario_count"] = manifest["scenario_count"]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
