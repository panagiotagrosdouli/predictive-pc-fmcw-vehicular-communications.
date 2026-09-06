import unittest

import numpy as np

from predictive_pc_fmcw.config import SchedulerConfig
from predictive_pc_fmcw.scheduling.base import SchedulerContext
from predictive_pc_fmcw.scheduling.policies import LinkLifetimeScheduler


def context(*, lifetime, deadline, queue=None, outage=None):
    lifetime = np.asarray(lifetime, dtype=np.int64)
    vehicles = lifetime.size
    queue = np.asarray(
        queue if queue is not None else [10] * vehicles,
        dtype=np.int64,
    )
    outage = np.asarray(
        outage if outage is not None else [False] * vehicles,
        dtype=bool,
    )
    horizon = 10
    return SchedulerContext(
        slot=5,
        queue_lengths=queue,
        time_to_deadline=np.asarray(deadline, dtype=np.float64),
        current_goodput_bps=np.full(vehicles, 1e6),
        current_outage=outage,
        predicted_goodput_bps=np.full((vehicles, horizon), 1e6),
        predicted_outage=np.zeros((vehicles, horizon), dtype=bool),
        predicted_lifetime_steps=lifetime,
        delivered_bits=np.ones(vehicles),
        previous_vehicle=None,
        data_rate_bps=1e6,
        discount=0.95,
    )


class LinkLifetimeUrgencyTest(unittest.TestCase):
    def test_link_closure_before_packet_deadline_creates_urgency(self):
        ctx = context(lifetime=[2], deadline=[8])
        urgency = LinkLifetimeScheduler._lifetime_urgency(ctx)
        self.assertGreater(urgency[0], 0.0)

    def test_packet_deadline_before_link_closure_does_not_double_count(self):
        ctx = context(lifetime=[8], deadline=[2])
        urgency = LinkLifetimeScheduler._lifetime_urgency(ctx)
        self.assertEqual(urgency[0], 0.0)

    def test_current_outage_cannot_receive_lifetime_bonus(self):
        ctx = context(lifetime=[2], deadline=[8], outage=[True])
        urgency = LinkLifetimeScheduler._lifetime_urgency(ctx)
        self.assertEqual(urgency[0], 0.0)

    def test_empty_queue_cannot_receive_lifetime_bonus(self):
        ctx = context(lifetime=[2], deadline=[8], queue=[0])
        urgency = LinkLifetimeScheduler._lifetime_urgency(ctx)
        self.assertEqual(urgency[0], 0.0)

    def test_more_imminent_link_expiry_is_more_urgent_when_packet_limited(self):
        ctx = context(lifetime=[2, 6], deadline=[9, 9], queue=[10, 10])
        urgency = LinkLifetimeScheduler._lifetime_urgency(ctx)
        self.assertGreater(urgency[0], urgency[1])

    def test_scheduler_score_contains_exact_weighted_lifetime_bonus(self):
        ctx = context(lifetime=[2, 8], deadline=[9, 2], queue=[10, 10])
        scheduler = LinkLifetimeScheduler(SchedulerConfig(lifetime_weight=2.0))
        base = super(LinkLifetimeScheduler, scheduler)._score(ctx)
        score = scheduler._score(ctx)
        expected = 2.0 * scheduler._lifetime_urgency(ctx)
        np.testing.assert_allclose(score - base, expected)


if __name__ == "__main__":
    unittest.main()
