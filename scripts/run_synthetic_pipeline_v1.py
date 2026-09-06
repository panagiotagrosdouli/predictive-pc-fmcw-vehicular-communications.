#!/usr/bin/env python3
"""Run the reproducible Synthetic Dataset v1 research preparation pipeline."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

from predictive_pc_fmcw.config import load_config
from predictive_pc_fmcw.learning.ablation import (
    CANONICAL_SEEDS,
    build_training_ablation_plan,
    run_training_ablation,
)
from predictive_pc_fmcw.synthetic.baselines import (
    evaluate_synthetic_baselines,
    save_baseline_results,
)
from predictive_pc_fmcw.synthetic.configuration import load_synthetic_protocol_config
from predictive_pc_fmcw.synthetic.dataset import build_dataset, validate_dataset
from predictive_pc_fmcw.synthetic.link_evaluation import (
    evaluate_synthetic_link_prediction,
    save_link_prediction_results,
)
from predictive_pc_fmcw.synthetic.training_export import (
    build_synthetic_training_npz,
    validate_synthetic_training_npz,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/synthetic_dataset_v1")
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument(
        "--protocol-config",
        default="configs/synthetic_dataset_v1.json",
    )
    parser.add_argument("--scenarios-per-family", type=int, default=None)
    parser.add_argument("--ood-scenarios-per-family", type=int, default=None)
    parser.add_argument("--history-steps", type=int, default=20)
    parser.add_argument("--horizon-steps", type=int, default=10)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lambda-link", type=float, default=0.2)
    parser.add_argument("--lambda-outage", type=float, default=0.1)
    parser.add_argument("--execute-training", action="store_true")
    args = parser.parse_args()

    root = Path(args.output)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite synthetic pipeline directory: {root}"
        )
    root.mkdir(parents=True, exist_ok=True)
    experiment = load_config(args.config)
    loaded_protocol = load_synthetic_protocol_config(args.protocol_config)
    dataset_config = loaded_protocol.build_config
    overrides: dict[str, int] = {}
    if args.scenarios_per_family is not None:
        overrides["scenarios_per_family"] = args.scenarios_per_family
    if args.ood_scenarios_per_family is not None:
        overrides["ood_scenarios_per_family"] = args.ood_scenarios_per_family
    if overrides:
        dataset_config = replace(dataset_config, **overrides)

    manifest = build_dataset(
        root,
        config=dataset_config,
        link_config=experiment.link,
        traffic_config=experiment.traffic,
    )
    (root / "protocol_config.json").write_text(
        Path(args.protocol_config).read_text(encoding="utf-8"), encoding="utf-8"
    )
    (root / "protocol_config.sha256").write_text(
        loaded_protocol.sha256 + "\n", encoding="utf-8"
    )
    dataset_validation = validate_dataset(root)

    training_npz = root / "training_dev.npz"
    build_synthetic_training_npz(
        root,
        training_npz,
        history_steps=args.history_steps,
        horizon_steps=args.horizon_steps,
        stride=args.stride,
    )
    training_validation = validate_synthetic_training_npz(root, training_npz)

    baseline_results = evaluate_synthetic_baselines(
        root,
        split="development",
        history_steps=args.history_steps,
        horizon_steps=args.horizon_steps,
        stride=args.stride,
    )
    save_baseline_results(baseline_results, root / "development_baselines.json")

    link_results = evaluate_synthetic_link_prediction(
        root,
        split="development",
        history_steps=args.history_steps,
        horizon_steps=args.horizon_steps,
        stride=args.stride,
    )
    save_link_prediction_results(
        link_results, root / "development_link_metrics.json"
    )

    plan = build_training_ablation_plan(
        training_npz,
        CANONICAL_SEEDS,
        epochs=args.epochs,
    )
    if plan.planned_runs != 20:
        raise RuntimeError("publication training plan must contain exactly 20 runs")

    training_status = "NOT_EXECUTED"
    if args.execute_training:
        results = run_training_ablation(
            training_npz,
            root / "learned_ablation",
            link_config=experiment.link,
            seeds=CANONICAL_SEEDS,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lambda_link=args.lambda_link,
            lambda_outage=args.lambda_outage,
        )
        if len(results) != 20:
            raise RuntimeError("publication training did not verify all 20 runs")
        training_status = "COMPLETED_20_VERIFIED_RUNS"

    report = {
        "protocol": "synthetic_dataset_v1",
        "protocol_config_sha256": loaded_protocol.sha256,
        "dataset": dataset_validation,
        "training_export": training_validation,
        "development_baselines": [asdict(row) for row in baseline_results],
        "development_link_metrics": [asdict(row) for row in link_results],
        "training_plan": asdict(plan),
        "training_status": training_status,
        "held_out_evaluated": False,
        "ood_evaluated": False,
        "scenario_count": manifest["scenario_count"],
    }
    report_path = root / "pipeline_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
