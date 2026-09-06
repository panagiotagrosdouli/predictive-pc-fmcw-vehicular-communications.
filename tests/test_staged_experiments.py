import unittest

from predictive_pc_fmcw.config import ExperimentConfig
from predictive_pc_fmcw.staged_experiments import (
    STAGED_SCHEDULERS,
    _staged_settings,
)


class StagedExperimentTest(unittest.TestCase):
    def test_slot_study_preserves_physical_horizon_and_duration(self):
        config = ExperimentConfig()
        expected_horizon = (
            config.prediction_horizon_steps * config.slot_duration_s
        )
        settings = [
            current
            for study, _, current in _staged_settings(config, seed=1)
            if study == "slot_duration"
        ]
        self.assertEqual(len(settings), 3)
        for current in settings:
            self.assertAlmostEqual(
                current.prediction_horizon_steps * current.slot_duration_s,
                expected_horizon,
            )
            self.assertEqual(
                current.benchmark.duration_s, config.benchmark.duration_s
            )
            self.assertEqual(current.traffic.deadline_s, config.traffic.deadline_s)

    def test_corrected_staged_design_has_45_settings_and_six_policies(self):
        settings = _staged_settings(ExperimentConfig(), seed=1)
        self.assertEqual(len(settings), 45)
        self.assertEqual(
            STAGED_SCHEDULERS,
            (
                "reactive_greedy",
                "proportional_fair",
                "kalman_predictive",
                "predictive_utility",
                "link_lifetime",
                "oracle",
            ),
        )
        for _, _, current in settings:
            self.assertEqual(current.benchmark.schedulers, STAGED_SCHEDULERS)


if __name__ == "__main__":
    unittest.main()
