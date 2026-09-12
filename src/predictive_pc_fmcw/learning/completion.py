from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any

from ..data.manifest import sha256_file
from .ablation import CANONICAL_SEEDS, OBJECTIVES


def _checkpoint_run_keys(paths: list[Path]) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for path in paths:
        seed_dir = path.parent.name
        objective = path.parent.parent.name
        if not seed_dir.startswith("seed_"):
            continue
        try:
            seed = int(seed_dir.removeprefix("seed_"))
        except ValueError:
            continue
        keys.add((objective, seed))
    return keys


def verify_completion_manifest(
    manifest_path: str | Path,
    *,
    training_npz: str | Path,
    checkpoints: list[str | Path],
) -> dict[str, Any]:
    manifest_source = Path(manifest_path)
    payload = json.loads(manifest_source.read_text(encoding="utf-8"))
    expected_runs = len(OBJECTIVES) * len(CANONICAL_SEEDS)
    expected_keys = set(product(OBJECTIVES, CANONICAL_SEEDS))
    supplied = [Path(path) for path in checkpoints]
    declared = [Path(path) for path in payload.get("checkpoints", [])]

    supplied_paths = sorted(str(path.resolve()) for path in supplied)
    declared_paths = sorted(str(path.resolve()) for path in declared)
    checks = {
        "manifest_complete": payload.get("complete") is True,
        "expected_runs_20": payload.get("expected_runs") == expected_runs,
        "completed_runs_20": payload.get("completed_runs") == expected_runs,
        "objectives_frozen": tuple(payload.get("objectives", ())) == OBJECTIVES,
        "seeds_frozen": tuple(payload.get("seeds", ())) == CANONICAL_SEEDS,
        "training_dataset_hash_matches": (
            payload.get("dataset_sha256") == sha256_file(training_npz)
        ),
        "twenty_checkpoints_declared": len(declared) == expected_runs,
        "twenty_checkpoints_supplied": len(supplied) == expected_runs,
        "declared_checkpoint_paths_unique": len(set(declared_paths)) == expected_runs,
        "supplied_checkpoint_paths_unique": len(set(supplied_paths)) == expected_runs,
        "checkpoint_paths_match_manifest": supplied_paths == declared_paths,
        "declared_run_grid_complete": _checkpoint_run_keys(declared) == expected_keys,
        "supplied_run_grid_complete": _checkpoint_run_keys(supplied) == expected_keys,
        "supplied_checkpoints_exist": all(path.is_file() for path in supplied),
        "link_config_hash_recorded": bool(payload.get("link_config_sha256")),
    }
    passed = all(checks.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "manifest": str(manifest_source),
        "training_npz": str(training_npz),
        "checkpoints": [str(path) for path in supplied],
        "checks": checks,
        "manifest_payload": payload,
    }
