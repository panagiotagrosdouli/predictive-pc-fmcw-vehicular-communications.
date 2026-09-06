import unittest

import numpy as np

from predictive_pc_fmcw.config import SchedulerConfig
from predictive_pc_fmcw.scheduling.base import SchedulerContext
from predictive_pc_fmcw.scheduling.policies import (
    DeadlineAwareLifetimeScheduler,
    ServiceGuardedPredictiveScheduler,
    build_scheduler,
)


def context():
    horizon = 10
    return SchedulerContext(
        slot=5,
        queue_lengths=np.asarray([10, 10], dtype=np.int64),
        time_to_deadline=np.asarray([10.0, 10.0]),
        current_goodput_bps=np.asarray([0.2e6, 1.0e6]),
        current_outage=np.zeros(2, dtype=bool),
        predicted_goodput_bps=np.asarray(
            [
                np.full(horizon, 1.2e6),
                np.full(horizon, 0.2e6),
            ]
        ),
        predicted_outage=np.zeros((2, horizon), dtype=bool),
        predicted_lifetime_steps=np.full(2, horizon, dtype=np.int64),
        delivered_bits=np.ones(2),
        previous_vehicle=None,
        data_rate_bps=1e6,
        discount=0.95,
    )


class ServiceGuardedPredictiveSchedulerTest(unittest.TestCase):
    def test_zero_guard_keeps_predictive_choice(self):
        cfg = SchedulerConfig(fairness_weight=0.0)
        ctx = context()
        base = DeadlineAwareLifetimeScheduler(cfg).select(ctx)
        guarded = ServiceGuardedPredictiveScheduler(
            cfg, guard_ratio=0.0
        ).select(ctx)
        self.assertEqual(base.vehicle, 0)
        self.assertEqual(guarded.vehicle, base.vehicle)

    def test_full_guard_falls_back_to_best_current_service(self):
        cfg = SchedulerConfig(fairness_weight=0.0)
        decision = ServiceGuardedPredictiveScheduler(
            cfg, guard_ratio=1.0
        ).select(context())
        self.assertEqual(decision.vehicle, 1)

    def test_registered_guard_variants_use_declared_ratios(self):
        cfg = SchedulerConfig()
        expected = {
            "service_guarded_00": 0.0,
            "service_guarded_80": 0.8,
            "service_guarded_90": 0.9,
            "service_guarded_95": 0.95,
            "service_guarded_100": 1.0,
        }
        for name, ratio in expected.items():
            scheduler = build_scheduler(name, cfg, seed=7)
            self.assertAlmostEqual(scheduler.guard_ratio, ratio)
            self.assertEqual(scheduler.name, name)


if __name__ == "__main__":
    unittest.main()
