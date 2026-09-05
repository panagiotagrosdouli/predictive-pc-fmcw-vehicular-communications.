"""Scenario-level partitions and reproducibility fingerprints."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class SplitManifest:
    master_seed: int
    train: tuple[str, ...]
    development: tuple[str, ...]
    held_out_test: tuple[str, ...]
    ood_test: tuple[str, ...]
    sha256: str


def _digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def build_split_manifest(
    scenario_ids: Iterable[str],
    ood_scenario_ids: Iterable[str],
    master_seed: int,
    train_fraction: float = 0.70,
    development_fraction: float = 0.15,
) -> SplitManifest:
    """Partition IDs deterministically; the inferential unit is a scenario."""
    ids = sorted(set(scenario_ids))
    ood = tuple(sorted(set(ood_scenario_ids)))
    if len(ids) < 3:
        raise ValueError("at least three in-distribution scenarios are required")
    if set(ids) & set(ood):
        raise ValueError("OOD scenarios must not overlap in-distribution scenarios")
    if not (0.0 < train_fraction < 1.0 and 0.0 < development_fraction < 1.0):
        raise ValueError("split fractions must be strictly between zero and one")
    if train_fraction + development_fraction >= 1.0:
        raise ValueError(
            "train + development fractions must leave held-out test scenarios"
        )

    import numpy as np

    rng = np.random.default_rng(master_seed)
    shuffled = list(ids)
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = max(1, int(n * train_fraction))
    n_dev = max(1, int(n * development_fraction))
    if n_train + n_dev >= n:
        n_dev = max(1, n - n_train - 1)
    train = tuple(sorted(shuffled[:n_train]))
    development = tuple(sorted(shuffled[n_train : n_train + n_dev]))
    held_out = tuple(sorted(shuffled[n_train + n_dev :]))
    payload = {
        "master_seed": master_seed,
        "train": train,
        "development": development,
        "held_out_test": held_out,
        "ood_test": ood,
    }
    return SplitManifest(
        master_seed=master_seed,
        train=train,
        development=development,
        held_out_test=held_out,
        ood_test=ood,
        sha256=_digest(payload),
    )


def validate_split_manifest(manifest: SplitManifest) -> None:
    """Fail closed on overlap, empty official partitions, or fingerprint drift."""
    groups = {
        "train": set(manifest.train),
        "development": set(manifest.development),
        "held_out_test": set(manifest.held_out_test),
        "ood_test": set(manifest.ood_test),
    }
    if any(not group for group in groups.values()):
        raise ValueError("all synthetic dataset partitions must be non-empty")
    names = list(groups)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            if groups[left] & groups[right]:
                raise ValueError(f"scenario leakage between {left} and {right}")
    payload = {
        "master_seed": manifest.master_seed,
        "train": manifest.train,
        "development": manifest.development,
        "held_out_test": manifest.held_out_test,
        "ood_test": manifest.ood_test,
    }
    if _digest(payload) != manifest.sha256:
        raise ValueError("split manifest SHA-256 fingerprint mismatch")
