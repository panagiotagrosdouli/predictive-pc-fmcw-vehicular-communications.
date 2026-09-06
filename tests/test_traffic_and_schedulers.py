import unittest

import numpy as np

from predictive_pc_fmcw.config import SchedulerConfig, TrafficConfig
from predictive_pc_fmcw.scheduling.base import SchedulerContext
from predictive_pc_fmcw.scheduling.policies import build_scheduler
from predictive_pc_fmcw.traffic import generate_traffic_trace


class TrafficAndSchedulerTest(unittest.TestCase):
    def test_traffic_reproducibility(self):
        first = generate_traffic_trace(4, 8, 3, 20, TrafficConfig())
        second = generate_traffic_trace(4, 8, 3, 20, TrafficConfig())
        np.testing.assert_array_equal(first.arrivals, second.arrivals)
        np.testing.assert_array_equal(first.success_uniforms, second.success_uniforms)
        self.assertEqual(first.deadlines, second.deadlines)

    def test_periodic_and_markov_traffic_are_reproducible(self):
        for model in ("periodic", "markov_modulated"):
            config = TrafficConfig(model=model, periodic_interval_slots=4)
            first = generate_traffic_trace(14, 40, 3, 20, config)
            second = generate_traffic_trace(14, 40, 3, 20, config)
            np.testing.assert_array_equal(first.arrivals, second.arrivals)
            self.assertGreater(int(first.arrivals.sum()), 0)
            if model == "periodic":
                active_slots = np.flatnonzero(first.arrivals.sum(axis=1))
                self.assertTrue(np.all(active_slots % 4 == 0))

    def test_physical_deadline_is_invariant_to_slot_duration(self):
        config = TrafficConfig(
            model="saturated", deadline_s=1.2, deadline_jitter_s=0.0
        )
        slow = generate_traffic_trace(3, 3, 2, 20, config, slot_duration_s=0.1)
        fast = generate_traffic_trace(3, 3, 2, 20, config, slot_duration_s=0.05)
        slow_deadline = slow.deadlines[0][0][0] * 0.1
        fast_deadline = fast.deadlines[0][0][0] * 0.05
        self.assertAlmostEqual(slow_deadline, 1.2)
        self.assertAlmostEqual(fast_deadline, 1.2)
        self.assertTrue(np.all(slow.arrivals > 0))

    def test_urgent_and_bulk_classes_have_distinct_deadlines(self):
        config = TrafficConfig(
            model="saturated",
            traffic_class_mode="urgent_bulk",
            urgent_fraction=0.5,
            urgent_deadline_s=0.1,
            bulk_deadline_s=1.0,
        )
        trace = generate_traffic_trace(
            18, 4, 2, 100, config, slot_duration_s=0.1
        )
        observed = {
            traffic_class
            for row in trace.classes
            for vehicle in row
            for traffic_class in vehicle
        }
        self.assertEqual(observed, {"urgent", "bulk"})
        for slot, (deadline_row, class_row) in enumerate(
            zip(trace.deadlines, trace.classes, strict=True)
        ):
            for deadlines, classes in zip(deadline_row, class_row, strict=True):
                for deadline, traffic_class in zip(
                    deadlines, classes, strict=True
                ):
                    expected = 1 if traffic_class == "urgent" else 10
                    self.assertEqual(deadline - slot, expected)

    def test_all_policies_choose_at_most_one_eligible_vehicle(self):
        context = SchedulerContext(
            slot=0,
            queue_lengths=np.asarray([0, 3, 2]),
            time_to_deadline=np.asarray([np.inf, 2.0, 5.0]),
            current_goodput_bps=np.asarray([1e9, 8e8, 7e8]),
            current_outage=np.asarray([False, False, False]),
            predicted_goodput_bps=np.full((3, 4), 8e8),
            predicted_outage=np.zeros((3, 4), dtype=bool),
            predicted_lifetime_steps=np.asarray([4, 2, 4]),
            delivered_bits=np.asarray([0.0, 10.0, 4.0]),
            previous_vehicle=None,
            data_rate_bps=1e9,
            discount=0.9,
            oracle_forecast=True,
        )
        names = [
            "random",
            "round_robin",
            "reactive_greedy",
            "proportional_fair",
            "cv_predictive",
            "kalman_predictive",
            "imm_predictive",
            "predictive_utility",
            "link_lifetime",
            "oracle",
        ]
        for name in names:
            decision = build_scheduler(name, SchedulerConfig(), 9).select(context)
            self.assertIn(decision.vehicle, {1, 2})

    def test_lifetime_urgency_is_horizon_scale_invariant(self):
        def context(horizon, lifetime, deadline):
            return SchedulerContext(
                slot=3,
                queue_lengths=np.asarray([4, 4]),
                time_to_deadline=np.asarray(deadline, dtype=np.float64),
                current_goodput_bps=np.asarray([8e8, 8e8]),
                current_outage=np.asarray([False, False]),
                predicted_goodput_bps=np.full((2, horizon), 8e8),
                predicted_outage=np.zeros((2, horizon), dtype=bool),
                predicted_lifetime_steps=np.asarray(lifetime),
                delivered_bits=np.asarray([1e6, 1e6]),
                previous_vehicle=None,
                data_rate_bps=1e9,
                discount=1.0,
            )

        scheduler = build_scheduler("link_lifetime", SchedulerConfig(), 2)
        short = scheduler._lifetime_urgency(context(4, [2, 4], [4, 4]))
        long = scheduler._lifetime_urgency(context(8, [4, 8], [8, 8]))
        np.testing.assert_allclose(short, long)

    def test_reactive_is_horizon_zero_equivalent(self):
        """Future arrays cannot change the current-link (H=0) decision."""

        def context(predicted_goodput, predicted_outage):
            return SchedulerContext(
                slot=2,
                queue_lengths=np.asarray([4, 4]),
                time_to_deadline=np.asarray([3.0, 3.0]),
                current_goodput_bps=np.asarray([7e8, 9e8]),
                current_outage=np.asarray([False, False]),
                predicted_goodput_bps=np.asarray(predicted_goodput),
                predicted_outage=np.asarray(predicted_outage),
                predicted_lifetime_steps=np.asarray([1, 1]),
                delivered_bits=np.asarray([0.0, 0.0]),
                previous_vehicle=None,
                data_rate_bps=1e9,
                discount=0.9,
            )

        scheduler = build_scheduler("reactive_greedy", SchedulerConfig(), 5)
        favorable_first = scheduler.select(
            context([[1e9], [0.0]], [[False], [True]])
        )
        favorable_second = scheduler.select(
            context([[0.0], [1e9]], [[True], [False]])
        )
        self.assertEqual(favorable_first.vehicle, 1)
        self.assertEqual(favorable_second.vehicle, 1)


if __name__ == "__main__":
    unittest.main()
