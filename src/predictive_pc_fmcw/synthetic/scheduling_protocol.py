"""Frozen eight-family scheduling protocol for synthetic evaluation."""

from __future__ import annotations

from dataclasses import dataclass

PAIRED_TRAFFIC_SEEDS = (20260901, 20260902, 20260903, 20260904, 20260905)


@dataclass(frozen=True)
class SchedulerFamily:
    protocol_id: str
    scheduler_name: str
    forecast_source: str
    learned_objective: str | None = None
    deployable: bool = True


SCHEDULER_FAMILIES = (
    SchedulerFamily("S0", "reactive_greedy", "current_link"),
    SchedulerFamily("S1", "proportional_fair", "current_link"),
    SchedulerFamily("S2", "cv_predictive", "constant_velocity"),
    SchedulerFamily("S3", "kalman_predictive", "kalman_cv"),
    SchedulerFamily("S4", "imm_predictive", "imm"),
    SchedulerFamily(
        "S5",
        "learned_predictive",
        "trajectory_gru",
        learned_objective="trajectory_only",
    ),
    SchedulerFamily(
        "S6",
        "learned_predictive",
        "communication_aware_gru",
        learned_objective="full",
    ),
    SchedulerFamily("S7", "oracle", "oracle_future", deployable=False),
)


def validate_scheduler_protocol() -> None:
    """Fail closed if the publication scheduler protocol drifts."""
    expected_ids = tuple(f"S{index}" for index in range(8))
    if tuple(item.protocol_id for item in SCHEDULER_FAMILIES) != expected_ids:
        raise ValueError("publication scheduler IDs must remain S0-S7")
    if len(PAIRED_TRAFFIC_SEEDS) != 5:
        raise ValueError("publication scheduling requires exactly five traffic seeds")
    if SCHEDULER_FAMILIES[-1].deployable:
        raise ValueError("oracle scheduler must remain evaluator-only")
    learned = [item for item in SCHEDULER_FAMILIES if item.learned_objective]
    if {item.learned_objective for item in learned} != {"trajectory_only", "full"}:
        raise ValueError("learned scheduler objectives drifted from frozen protocol")


def scheduler_protocol_manifest() -> dict[str, object]:
    validate_scheduler_protocol()
    return {
        "paired_inputs": (
            "mobility_scenario",
            "channel_realization",
            "packet_arrivals",
            "packet_deadlines",
            "traffic_seed",
        ),
        "traffic_seeds": PAIRED_TRAFFIC_SEEDS,
        "inferential_unit": "scenario_episode",
        "families": [
            {
                "protocol_id": item.protocol_id,
                "scheduler_name": item.scheduler_name,
                "forecast_source": item.forecast_source,
                "learned_objective": item.learned_objective,
                "deployable": item.deployable,
            }
            for item in SCHEDULER_FAMILIES
        ],
    }
