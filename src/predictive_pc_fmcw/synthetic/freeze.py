"""Fail-closed freeze gate for Synthetic Dataset v1 publication evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..learning.ablation import CANONICAL_SEEDS, OBJECTIVES, validate_training_resume


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_publication_training_freeze(
    dataset_dir: str | Path,
    ablation_dir: str | Path,
    training_npz: str | Path,
) -> dict[str, object]:
    """Require exactly 20 verified runs before held-out/OOD materialization."""
    root = Path(dataset_dir)
    ablation = Path(ablation_dir)
    training = Path(training_npz)
    manifest_path = root / "manifest.json"
    completion_path = ablation / "completion_manifest.json"
    if not manifest_path.is_file() or not training.is_file():
        raise FileNotFoundError("dataset manifest and training NPZ are required")
    if not completion_path.is_file():
        raise PermissionError(
            "20-run completion manifest is required before test freeze"
        )

    dataset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    training_sha = _sha256_file(training)
    if completion.get("complete") is not True:
        raise PermissionError("training completion manifest is not complete")
    if int(completion.get("completed_runs", -1)) != 20:
        raise PermissionError("publication freeze requires exactly 20 completed runs")
    if int(completion.get("expected_runs", -1)) != 20:
        raise PermissionError("publication freeze expected-run count must be 20")
    if tuple(completion.get("objectives", ())) != OBJECTIVES:
        raise PermissionError("publication objectives differ from frozen protocol")
    if tuple(completion.get("seeds", ())) != CANONICAL_SEEDS:
        raise PermissionError("publication seeds differ from frozen protocol")
    if completion.get("dataset_sha256") != training_sha:
        raise PermissionError("completion manifest training dataset hash mismatch")

    verified: list[dict[str, object]] = []
    for objective in OBJECTIVES:
        for seed in CANONICAL_SEEDS:
            run_dir = ablation / objective / f"seed_{seed}"
            result_path = run_dir / "training_result.json"
            validation = validate_training_resume(
                result_path,
                expected_objective=objective,
                expected_seed=seed,
                expected_dataset_sha256=training_sha,
                expected_run_dir=run_dir,
            )
            if not validation.valid:
                raise PermissionError(
                    f"unverified checkpoint {objective}/{seed}: {validation.reason}"
                )
            verified.append({"objective": objective, "seed": seed})

    return {
        "status": "PASS",
        "protocol": dataset_manifest["protocol"],
        "training_npz_sha256": training_sha,
        "dataset_manifest_sha256": _sha256_file(manifest_path),
        "completion_manifest_sha256": _sha256_file(completion_path),
        "verified_runs": len(verified),
        "objectives": list(OBJECTIVES),
        "seeds": list(CANONICAL_SEEDS),
        "held_out_opened": False,
        "ood_opened": False,
    }
