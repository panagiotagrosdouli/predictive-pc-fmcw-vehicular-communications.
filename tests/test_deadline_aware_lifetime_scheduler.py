import unittest

import numpy as np

from predictive_pc_fmcw.config import SchedulerConfig
from predictive_pc_fmcw.scheduling.base import SchedulerContext
from predictive_pc_fmcw.scheduling.policies import (
    DeadlineAwareLifetimeScheduler,
    LinkLifetimeScheduler,
)


def context(*, deadline, horizon=10):
    deadline = np.asarray(deadline, dtype=np.float64)
    vehicles = deadline.size
    return SchedulerContext(
        slot=5,
        queue_lengths=np.full(vehicles, 10, dtype=np.int64),
        time_to_deadline=deadline,
        current_goodput_bps=np.linspace(0.5e6, 1.0e6, vehicles),
        current_outage=np.zeros(vehicles, dtype=bool),
        predicted_goodput_bps=np.tile(
            np.linspace(0.2e6, 1.2e6, horizon),
            (vehicles, 1),
        ),
        predicted_outage=np.zeros((vehicles, horizon), dtype=bool),
        predicted_lifetime_steps=np.full(vehicles, horizon, dtype=np.int64),
        delivered_bits=np.ones(vehicles),
        previous_vehicle=None,
        data_rate_bps=1e6,
        discount=0.95,
    )


class DeadlineAwareLifetimeSchedulerTest(unittest.TestCase):
    def test_one_slot_deadline_disables_future_weight(self):
        ctx = context(deadline=[1.0, 1.0])
        weight = DeadlineAwareLifetimeScheduler._prediction_weight(ctx)
        np.testing.assert_allclose(weight, [0.0, 0.0])

    def test_deadline_at_horizon_uses_full_predictive_weight(self):
        ctx = context(deadline=[10.0, 10.0], horizon=10)
        weight = DeadlineAwareLifetimeScheduler._prediction_weight(ctx)
        np.testing.assert_allclose(weight, [1.0, 1.0])

    def test_infinite_deadline_uses_full_predictive_weight(self):
        ctx = context(deadline=[np.inf, np.inf])
        weight = DeadlineAwareLifetimeScheduler._prediction_weight(ctx)
        np.testing.assert_allclose(weight, [1.0, 1.0])

    def test_intermediate_deadline_blends_monotonically(self):
        ctx = context(deadline=[1.0, 5.0, 10.0], horizon=10)
        weight = DeadlineAwareLifetimeScheduler._prediction_weight(ctx)
        self.assertLess(weight[0], weight[1])
        self.assertLess(weight[1], weight[2])

    def test_tight_deadline_score_equals_current_packet_score(self):
        ctx = context(deadline=[1.0, 1.0])
        scheduler = DeadlineAwareLifetimeScheduler(SchedulerConfig())
        score = scheduler._score(ctx)
        current = scheduler._current_packet_score(ctx)
        np.testing.assert_allclose(score, current)

    def test_long_deadline_score_equals_link_lifetime_score(self):
        ctx = context(deadline=[10.0, 10.0], horizon=10)
        scheduler = DeadlineAwareLifetimeScheduler(SchedulerConfig())
        score = scheduler._score(ctx)
        predictive = LinkLifetimeScheduler._score(scheduler, ctx)
        np.testing.assert_allclose(score, predictive)


if __name__ == "__main__":
    unittest.main()
