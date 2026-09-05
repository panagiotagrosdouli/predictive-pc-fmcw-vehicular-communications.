"""Development-only representative checkpoint selection for learned schedulers."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ..config import LinkConfig
from ..learning.ablation import CANONICAL_SEEDS, validate_training_resume
from ..learning.heldout import evaluate_checkpoint_arrays
from ..learning.inference import TorchCheckpointPredictor
from ..link import LinkModel
from .freeze import verify_publication_training_freeze


def _mean_metric(rows: list[object], name: str) -> float:
    values = np.asarray([float(getattr(row, name)) for row in rows], dtype=np.float64)
    return float(np.nanmean(values))


def select_representative_seed(
    objective: str,
    summaries: list[dict[str, float | int]],
) -> int:
    """Select using a frozen development-only rule, never held-out data."""
    if objective not in {"trajectory_only", "full"}:
        raise ValueError("scheduler checkpoint selection supports trajectory_only/full")
    if {int(item["seed"]) for item in summaries} != set(CANONICAL_SEEDS):
        raise ValueError("selection requires all five canonical seeds")
    if objective == "trajectory_only":
        ordered = sorted(
            summaries,
            key=lambda item: (
                float(item["ade_m"]),
                float(item["fde_m"]),
                int(item["seed"]),
            ),
        )
    else:
        ordered = sorted(
            summaries,
            key=lambda item: (
                float(item["goodput_mae_mbps"]),
                -float(item["outage_f1"]),
                float(item["snr_mae_db"]),
                float(item["ade_m"]),
                int(item["seed"]),
            ),
        )
    return int(ordered[0]["seed"])


def build_development_checkpoint_selection(
    training_npz: str | Path,
    ablation_dir: str | Path,
    dataset_dir: str | Path,
    output_path: str | Path,
    *,
    link_config: LinkConfig,
    batch_size: int = 1024,
    dt_s: float = 0.1,
) -> dict[str, object]:
    """Evaluate all five seeds for S5/S6 on development and freeze the choice."""
    freeze = verify_publication_training_freeze(dataset_dir, ablation_dir, training_npz)
    training_sha = str(freeze["training_npz_sha256"])
    with np.load(training_npz, allow_pickle=False) as data:
        split = np.asarray(data["split"]).astype(str)
        mask = split == "development"
        if not np.any(mask):
            raise ValueError("training artifact has no development samples")
        history = np.asarray(data["history_xy"])[mask]
        future = np.asarray(data["future_xy"])[mask]
        heading = np.asarray(data["future_ego_heading_rad"])[mask]
        scenario_ids = np.asarray(data["scenario_id"])[mask]

    link_model = LinkModel(link_config)
    selected: dict[str, dict[str, object]] = {}
    all_summaries: dict[str, list[dict[str, float | int | str]]] = {}
    root = Path(ablation_dir)
    for objective in ("trajectory_only", "full"):
        summaries: list[dict[str, float | int | str]] = []
        for seed in CANONICAL_SEEDS:
            run_dir = root / objective / f"seed_{seed}"
            result_path = run_dir / "training_result.json"
            validation = validate_training_resume(
                result_path,
                expected_objective=objective,
                expected_seed=seed,
                expected_dataset_sha256=training_sha,
                expected_run_dir=run_dir,
            )
            if not validation.valid or validation.result is None:
                raise PermissionError(
                    f"cannot select unverified {objective}/{seed}: {validation.reason}"
                )
            predictor = TorchCheckpointPredictor(validation.result.checkpoint)
            rows = evaluate_checkpoint_arrays(
                predictor=predictor,
                history_xy=history,
                future_xy=future,
                future_ego_heading_rad=heading,
                scenario_ids=scenario_ids,
                link_model=link_model,
                checkpoint=validation.result.checkpoint,
                objective=objective,
                seed=seed,
                batch_size=batch_size,
                dt_s=dt_s,
            )
            summaries.append(
                {
                    "seed": seed,
                    "checkpoint": validation.result.checkpoint,
                    "ade_m": _mean_metric(rows, "ade_m"),
                    "fde_m": _mean_metric(rows, "fde_m"),
                    "snr_mae_db": _mean_metric(rows, "snr_mae_db"),
                    "goodput_mae_mbps": _mean_metric(rows, "goodput_mae_mbps"),
                    "outage_f1": _mean_metric(rows, "outage_f1"),
                }
            )
        representative = select_representative_seed(objective, summaries)
        chosen = next(item for item in summaries if int(item["seed"]) == representative)
        selected[objective] = {
            "seed": representative,
            "checkpoint": str(chosen["checkpoint"]),
        }
        all_summaries[objective] = summaries

    report = {
        "status": "FROZEN_DEVELOPMENT_SELECTION",
        "selection_split": "development",
        "training_npz_sha256": training_sha,
        "rules": {
            "trajectory_only": "min ADE, tie-break FDE then seed",
            "full": (
                "min goodput MAE, tie-break max outage F1, min SNR MAE, "
                "min ADE, then seed"
            ),
        },
        "all_seed_summaries": all_summaries,
        "selected": selected,
        "held_out_used_for_selection": False,
        "ood_used_for_selection": False,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite selection artifact: {destination}")
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
