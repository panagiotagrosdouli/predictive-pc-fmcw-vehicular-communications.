import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from predictive_pc_fmcw.data.synthetic import generate_synthetic_scenario
from predictive_pc_fmcw.data.womd_export import load_womd_motion_scenarios
from predictive_pc_fmcw.predictors import (
    ConstantAccelerationPredictor,
    ConstantVelocityPredictor,
    InteractingMultipleModelPredictor,
    KalmanConstantVelocityPredictor,
    LastPositionPredictor,
    forecast_scenario,
)


class DataAndPredictorTest(unittest.TestCase):
    def test_synthetic_shapes(self):
        scenario = generate_synthetic_scenario(1, slots=12, vehicles=3)
        self.assertEqual(scenario.vehicle_positions_xy.shape, (22, 3, 2))
        self.assertEqual(scenario.evaluation_slots, 12)

    def test_future_mutation_does_not_change_causal_prediction(self):
        scenario = generate_synthetic_scenario(2, slots=12, vehicles=2)
        combined = scenario.combined_positions()
        changed = combined.copy()
        changed[scenario.start_index + 1 :] += 1e5
        first = forecast_scenario(
            combined,
            scenario.start_index,
            5,
            scenario.dt_s,
            ConstantVelocityPredictor(),
        )
        second = forecast_scenario(
            changed,
            scenario.start_index,
            5,
            scenario.dt_s,
            ConstantVelocityPredictor(),
        )
        np.testing.assert_array_equal(first.vehicle_xy, second.vehicle_xy)

    def test_paper_motion_baselines_follow_linear_motion(self):
        history = np.asarray(
            [[0.0, 1.0], [1.0, 1.0], [2.0, 1.0], [3.0, 1.0]]
        )
        last = LastPositionPredictor().predict(history, 3, 1.0)
        cv = ConstantVelocityPredictor().predict(history, 3, 1.0)
        kalman = KalmanConstantVelocityPredictor().predict(history, 3, 1.0)
        imm = InteractingMultipleModelPredictor().predict(history, 3, 1.0)
        np.testing.assert_allclose(last, [[3.0, 1.0]] * 3)
        np.testing.assert_allclose(cv, [[4.0, 1.0], [5.0, 1.0], [6.0, 1.0]])
        np.testing.assert_allclose(kalman, cv, atol=0.25)
        np.testing.assert_allclose(imm, cv, atol=0.25)

    def test_all_deployable_baselines_are_future_leakage_free(self):
        scenario = generate_synthetic_scenario(12, slots=10, vehicles=2)
        combined = scenario.combined_positions()
        changed = combined.copy()
        changed[scenario.start_index + 1 :] -= 9e4
        predictors = (
            LastPositionPredictor(),
            ConstantVelocityPredictor(),
            KalmanConstantVelocityPredictor(),
            InteractingMultipleModelPredictor(),
        )
        for predictor in predictors:
            first = forecast_scenario(
                combined, scenario.start_index, 4, scenario.dt_s, predictor
            )
            second = forecast_scenario(
                changed, scenario.start_index, 4, scenario.dt_s, predictor
            )
            np.testing.assert_array_equal(first.vehicle_xy, second.vehicle_xy)

    def test_predictors_reject_invalid_prediction_requests(self):
        history = np.asarray([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
        predictors = (
            LastPositionPredictor(),
            ConstantVelocityPredictor(),
            ConstantAccelerationPredictor(),
            KalmanConstantVelocityPredictor(),
            InteractingMultipleModelPredictor(),
        )
        for predictor in predictors:
            with self.subTest(predictor=predictor.name, case="zero_horizon"):
                with self.assertRaises(ValueError):
                    predictor.predict(history, 0, 0.1)
            with self.subTest(predictor=predictor.name, case="zero_dt"):
                with self.assertRaises(ValueError):
                    predictor.predict(history, 2, 0.0)
            with self.subTest(predictor=predictor.name, case="nonfinite_dt"):
                with self.assertRaises(ValueError):
                    predictor.predict(history, 2, np.nan)

    def test_predictors_reject_nonfinite_history(self):
        history = np.asarray([[0.0, 0.0], [np.nan, 1.0]])
        with self.assertRaises(ValueError):
            ConstantVelocityPredictor().predict(history, 2, 0.1)

    def test_forecast_scenario_rejects_invalid_inputs(self):
        positions = np.zeros((4, 3, 2), dtype=float)
        with self.assertRaises(ValueError):
            forecast_scenario(positions, 1, 0, 0.1, ConstantVelocityPredictor())
        with self.assertRaises(ValueError):
            forecast_scenario(positions, 1, 2, 0.0, ConstantVelocityPredictor())
        with self.assertRaises(IndexError):
            forecast_scenario(positions, -1, 2, 0.1, ConstantVelocityPredictor())
        with self.assertRaises(IndexError):
            forecast_scenario(positions, 4, 2, 0.1, ConstantVelocityPredictor())
        with self.assertRaises(ValueError):
            forecast_scenario(np.zeros((4, 2)), 1, 2, 0.1, None)
        invalid = positions.copy()
        invalid[1, 1, 0] = np.inf
        with self.assertRaises(ValueError):
            forecast_scenario(invalid, 1, 2, 0.1, None)

    def test_womd_proxy_adapter(self):
        records = []
        for actor in range(3):
            records.append(
                {
                    "scenario_id": "scene",
                    "track_index": actor,
                    "past": [[float(t + actor * 4), 0.0] for t in range(3)],
                    "future": [[float(t + 3 + actor * 4), 0.0] for t in range(2)],
                }
            )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps(records), encoding="utf-8")
            scenarios = load_womd_motion_scenarios(path)
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].vehicle_count, 2)
        self.assertIn("proxy", scenarios[0].source)


if __name__ == "__main__":
    unittest.main()
