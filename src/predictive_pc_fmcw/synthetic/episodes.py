"""Deterministic multi-vehicle episode composition for synthetic scheduling."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..data.scenario import MotionScenario


@dataclass(frozen=True)
class SyntheticEpisode:
    scenario: MotionScenario
    member_scenario_ids: tuple[str, ...]
    member_seeds: tuple[int, ...]


def _episode_id(split: str, members: tuple[str, ...]) -> str:
    payload = "|".join((split, *members)).encode("utf-8")
    return f"{split}-episode-{hashlib.sha256(payload).hexdigest()[:12]}"


def compose_synthetic_episodes(
    dataset_dir: str | Path,
    *,
    split: str,
    vehicles_per_episode: int = 5,
    history_steps: int = 20,
) -> tuple[SyntheticEpisode, ...]:
    """Group split members into disjoint multi-vehicle scheduling episodes.

    Every source trajectory is used at most once. This keeps the composed
    episode, rather than an individual timestep, as the independent unit.
    """
    if split not in {"development", "held_out_test", "ood_test"}:
        raise ValueError("episode split must be development, held_out_test, or ood_test")
    if vehicles_per_episode < 2:
        raise ValueError("scheduling episodes require at least two vehicles")
    if history_steps < 2:
        raise ValueError("history_steps must be at least two")

    root = Path(dataset_dir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    scenario_ids = list(manifest["split"][split])
    if len(scenario_ids) < vehicles_per_episode:
        raise ValueError(f"not enough {split} scenarios for one scheduling episode")

    seed_offset = {"development": 11, "held_out_test": 23, "ood_test": 37}[split]
    rng = np.random.default_rng(int(manifest["master_seed"]) + seed_offset)
    order = rng.permutation(len(scenario_ids))
    ordered = [scenario_ids[int(index)] for index in order]
    complete = len(ordered) // vehicles_per_episode
    episodes: list[SyntheticEpisode] = []

    for episode_index in range(complete):
        start = episode_index * vehicles_per_episode
        members = tuple(ordered[start : start + vehicles_per_episode])
        tracks: list[np.ndarray] = []
        seeds: list[int] = []
        timestamps: np.ndarray | None = None
        for scenario_id in members:
            with np.load(
                root / "scenarios" / f"{scenario_id}.npz", allow_pickle=False
            ) as data:
                current_t = np.asarray(data["t_s"], dtype=np.float64)
                current_xy = np.stack(
                    (
                        np.asarray(data["x_m"], dtype=np.float64),
                        np.asarray(data["y_m"], dtype=np.float64),
                    ),
                    axis=-1,
                )
                if timestamps is None:
                    timestamps = current_t
                elif current_t.shape != timestamps.shape or not np.allclose(
                    current_t, timestamps
                ):
                    raise ValueError("episode members have incompatible time grids")
                tracks.append(current_xy)
                seeds.append(int(np.asarray(data["seed"]).item()))

        assert timestamps is not None
        if history_steps >= timestamps.size:
            raise ValueError("history_steps must leave evaluation samples")
        vehicle_positions = np.stack(tracks, axis=1)
        ego_positions = np.zeros((timestamps.size, 2), dtype=np.float64)
        scenario = MotionScenario(
            scenario_id=_episode_id(split, members),
            timestamps_s=timestamps,
            ego_positions_xy=ego_positions,
            vehicle_positions_xy=vehicle_positions,
            actor_ids=members,
            start_index=history_steps - 1,
            source=f"synthetic_dataset_v1:{split}",
        )
        episodes.append(
            SyntheticEpisode(
                scenario=scenario,
                member_scenario_ids=members,
                member_seeds=tuple(seeds),
            )
        )

    used = [member for episode in episodes for member in episode.member_scenario_ids]
    if len(used) != len(set(used)):
        raise RuntimeError("source scenario reused across independent scheduling episodes")
    return tuple(episodes)
