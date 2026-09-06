from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from ..config import SchedulerConfig
from .base import (
    SchedulerContext,
    SchedulerDecision,
    choose_best,
    eligible_mask,
)


@dataclass
class RandomScheduler:
    seed: int
    name: str = "random"
    forecast_mode: str = "reactive"
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        eligible = np.flatnonzero(eligible_mask(context))
        scores = np.full(context.vehicles, -np.inf)
        if eligible.size == 0:
            return SchedulerDecision(None, scores, self.name)
        scores[eligible] = self._rng.random(eligible.size)
        vehicle = int(eligible[np.argmax(scores[eligible])])
        return SchedulerDecision(vehicle, scores, self.name)


@dataclass
class RoundRobinScheduler:
    name: str = "round_robin"
    forecast_mode: str = "reactive"
    _next: int = 0

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        scores = np.full(context.vehicles, -np.inf)
        for offset in range(context.vehicles):
            vehicle = (self._next + offset) % context.vehicles
            if context.queue_lengths[vehicle] > 0:
                self._next = (vehicle + 1) % context.vehicles
                scores[vehicle] = 1.0
                return SchedulerDecision(vehicle, scores, self.name)
        return SchedulerDecision(None, scores, self.name)


@dataclass(frozen=True)
class ReactiveGreedyScheduler:
    name: str = "reactive_greedy"
    forecast_mode: str = "reactive"

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        queue_scale = context.queue_lengths / max(1, int(context.queue_lengths.max()))
        scores = (
            context.current_goodput_bps / context.data_rate_bps
        ) * (0.25 + 0.75 * queue_scale)
        scores -= context.current_outage.astype(float)
        return choose_best(scores, eligible_mask(context), self.name)


@dataclass(frozen=True)
class ProportionalFairScheduler:
    """Current rate divided by historical normalized service per slot."""

    name: str = "proportional_fair"
    forecast_mode: str = "reactive"

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        elapsed_slots = max(1, context.slot)
        normalized_service = (
            context.delivered_bits / context.data_rate_bps / elapsed_slots
        )
        scores = (context.current_goodput_bps / context.data_rate_bps) / (
            1e-3 + normalized_service
        )
        scores -= context.current_outage.astype(float)
        return choose_best(scores, eligible_mask(context), self.name)


@dataclass(frozen=True)
class PredictiveUtilityScheduler:
    config: SchedulerConfig
    name: str = "predictive_utility"
    forecast_mode: str = "constant_acceleration"

    def _score(self, context: SchedulerContext) -> NDArray[np.float64]:
        horizon = context.predicted_goodput_bps.shape[1]
        discount = context.discount ** np.arange(horizon, dtype=np.float64)
        discount /= discount.sum()
        normalized_goodput = context.predicted_goodput_bps / context.data_rate_bps
        expected_goodput = normalized_goodput @ discount
        outage_risk = context.predicted_outage.astype(float) @ discount
        queue = context.queue_lengths / max(1, int(context.queue_lengths.max()))
        current_goodput = context.current_goodput_bps / context.data_rate_bps
        opportunity_loss = np.maximum(
            0.0, current_goodput - normalized_goodput[:, -1]
        ) * queue
        deadline = np.where(
            np.isfinite(context.time_to_deadline),
            1.0 / (1.0 + context.time_to_deadline),
            0.0,
        )
        mean_delivered = max(float(context.delivered_bits.mean()), 1.0)
        fairness = 1.0 / (0.25 + context.delivered_bits / mean_delivered)
        scores = (
            self.config.goodput_weight * expected_goodput
            - self.config.outage_weight * outage_risk
            - self.config.outage_weight * context.current_outage.astype(float)
            + self.config.opportunity_weight * opportunity_loss
            + self.config.queue_weight * queue
            + self.config.deadline_weight * deadline
            + self.config.fairness_weight * fairness
        )
        if context.previous_vehicle is not None:
            switching = np.ones(context.vehicles, dtype=np.float64)
            switching[context.previous_vehicle] = 0.0
            scores -= self.config.switching_weight * switching
        return scores

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        return choose_best(self._score(context), eligible_mask(context), self.name)


@dataclass(frozen=True)
class CVPredictiveScheduler(PredictiveUtilityScheduler):
    name: str = "cv_predictive"
    forecast_mode: str = "constant_velocity"


@dataclass(frozen=True)
class KalmanPredictiveScheduler(PredictiveUtilityScheduler):
    name: str = "kalman_predictive"
    forecast_mode: str = "kalman_cv"


@dataclass(frozen=True)
class IMMPredictiveScheduler(PredictiveUtilityScheduler):
    name: str = "imm_predictive"
    forecast_mode: str = "imm"


@dataclass(frozen=True)
class LearnedPredictiveScheduler(PredictiveUtilityScheduler):
    name: str = "learned_predictive"
    forecast_mode: str = "learned"


@dataclass(frozen=True)
class LinkLifetimeScheduler(PredictiveUtilityScheduler):
    """Predictive utility with packet-aware link-expiry urgency.

    A closing link is urgent only when it is expected to disappear before the
    head-of-line packet's own deadline. If the packet deadline arrives first,
    the base deadline term already represents the relevant urgency and the
    lifetime term must not double-count it.
    """

    name: str = "link_lifetime"
    forecast_mode: str = "constant_acceleration"

    @staticmethod
    def _lifetime_urgency(context: SchedulerContext) -> NDArray[np.float64]:
        horizon = context.predicted_goodput_bps.shape[1]
        lifetime = context.predicted_lifetime_steps.astype(np.float64)
        closing_pressure = np.clip(
            (horizon - lifetime) / max(1, horizon), 0.0, 1.0
        )
        queue = context.queue_lengths / max(1, int(context.queue_lengths.max()))
        currently_usable = (~context.current_outage).astype(float)
        finite_deadline = np.isfinite(context.time_to_deadline)
        link_limited = finite_deadline & (lifetime < context.time_to_deadline)
        return (
            closing_pressure
            * queue
            * currently_usable
            * link_limited.astype(float)
        )

    def _score(self, context: SchedulerContext) -> NDArray[np.float64]:
        scores = super()._score(context)
        return scores + self.config.lifetime_weight * self._lifetime_urgency(context)


@dataclass(frozen=True)
class DeadlineAwareLifetimeScheduler(LinkLifetimeScheduler):
    """Blend current packet utility with predictive link utility by deadline slack.

    The predictive horizon should not dominate packets that expire before that
    horizon can matter. For an oldest-packet deadline of one slot or less, the
    score is purely current-state packet utility. As deadline slack grows toward
    the prediction horizon, the scheduler smoothly recovers the full
    LinkLifetimeScheduler score. Infinite deadlines use the full predictive
    score. This is a diagnostic mechanism, not a claim of optimality.
    """

    name: str = "deadline_aware_lifetime"
    forecast_mode: str = "constant_acceleration"

    @staticmethod
    def _prediction_weight(context: SchedulerContext) -> NDArray[np.float64]:
        horizon = context.predicted_goodput_bps.shape[1]
        deadline = context.time_to_deadline.astype(np.float64)
        weight = np.ones(context.vehicles, dtype=np.float64)
        finite = np.isfinite(deadline)
        scale = max(1, horizon - 1)
        weight[finite] = np.clip((deadline[finite] - 1.0) / scale, 0.0, 1.0)
        return weight

    def _current_packet_score(
        self, context: SchedulerContext
    ) -> NDArray[np.float64]:
        queue = context.queue_lengths / max(1, int(context.queue_lengths.max()))
        current_goodput = context.current_goodput_bps / context.data_rate_bps
        deadline = np.where(
            np.isfinite(context.time_to_deadline),
            1.0 / (1.0 + context.time_to_deadline),
            0.0,
        )
        mean_delivered = max(float(context.delivered_bits.mean()), 1.0)
        fairness = 1.0 / (0.25 + context.delivered_bits / mean_delivered)
        scores = (
            self.config.goodput_weight * current_goodput
            - self.config.outage_weight * context.current_outage.astype(float)
            + self.config.queue_weight * queue
            + self.config.deadline_weight * deadline
            + self.config.fairness_weight * fairness
        )
        if context.previous_vehicle is not None:
            switching = np.ones(context.vehicles, dtype=np.float64)
            switching[context.previous_vehicle] = 0.0
            scores -= self.config.switching_weight * switching
        return scores

    def _score(self, context: SchedulerContext) -> NDArray[np.float64]:
        current_score = self._current_packet_score(context)
        predictive_score = super()._score(context)
        weight = self._prediction_weight(context)
        return (1.0 - weight) * current_score + weight * predictive_score


@dataclass(frozen=True)
class ServiceGuardedPredictiveScheduler(DeadlineAwareLifetimeScheduler):
    """Permit predictive reordering only when current service stays competitive.

    The predictive candidate is retained when its current-service proxy is at
    least ``guard_ratio`` times the best currently available proxy. Otherwise
    the scheduler falls back to the current-service choice. This targets the
    congestion mechanism observed in the development-only service-order audit.
    """

    guard_ratio: float = 0.9
    name: str = "service_guarded_predictive"

    @staticmethod
    def _current_service_proxy(context: SchedulerContext) -> NDArray[np.float64]:
        queue_scale = context.queue_lengths / max(1, int(context.queue_lengths.max()))
        service = (
            context.current_goodput_bps / context.data_rate_bps
        ) * (0.25 + 0.75 * queue_scale)
        return np.where(context.current_outage, 0.0, service)

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        eligible = eligible_mask(context)
        predictive = choose_best(self._score(context), eligible, self.name)
        if predictive.vehicle is None:
            return predictive

        service = self._current_service_proxy(context)
        current = choose_best(service, eligible, self.name)
        if current.vehicle is None:
            return predictive

        best_service = float(service[current.vehicle])
        predicted_service = float(service[predictive.vehicle])
        if best_service <= 0.0 or predicted_service >= self.guard_ratio * best_service:
            return predictive
        return SchedulerDecision(current.vehicle, service, self.name)


@dataclass(frozen=True)
class OracleScheduler(LinkLifetimeScheduler):
    """Perfect-future information reference using the same heuristic utility."""

    name: str = "oracle"
    forecast_mode: str = "oracle"

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        if not context.oracle_forecast:
            raise ValueError("Oracle scheduler requires an oracle forecast context.")
        return super().select(context)


def build_scheduler(name: str, config: SchedulerConfig, seed: int):
    policies = {
        "random": lambda: RandomScheduler(seed),
        "round_robin": RoundRobinScheduler,
        "reactive_greedy": ReactiveGreedyScheduler,
        "proportional_fair": ProportionalFairScheduler,
        "cv_predictive": lambda: CVPredictiveScheduler(config),
        "kalman_predictive": lambda: KalmanPredictiveScheduler(config),
        "imm_predictive": lambda: IMMPredictiveScheduler(config),
        "learned_predictive": lambda: LearnedPredictiveScheduler(config),
        "predictive_utility": lambda: PredictiveUtilityScheduler(config),
        "link_lifetime": lambda: LinkLifetimeScheduler(config),
        "deadline_aware_lifetime": lambda: DeadlineAwareLifetimeScheduler(config),
        "service_guarded_00": lambda: ServiceGuardedPredictiveScheduler(
            config, guard_ratio=0.00, name="service_guarded_00"
        ),
        "service_guarded_80": lambda: ServiceGuardedPredictiveScheduler(
            config, guard_ratio=0.80, name="service_guarded_80"
        ),
        "service_guarded_90": lambda: ServiceGuardedPredictiveScheduler(
            config, guard_ratio=0.90, name="service_guarded_90"
        ),
        "service_guarded_95": lambda: ServiceGuardedPredictiveScheduler(
            config, guard_ratio=0.95, name="service_guarded_95"
        ),
        "service_guarded_100": lambda: ServiceGuardedPredictiveScheduler(
            config, guard_ratio=1.00, name="service_guarded_100"
        ),
        "oracle": lambda: OracleScheduler(config),
    }
    try:
        return policies[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown scheduler: {name}") from exc
