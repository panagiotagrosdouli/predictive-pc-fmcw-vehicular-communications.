import unittest

import numpy as np

from predictive_pc_fmcw.config import LinkConfig
from predictive_pc_fmcw.learning.heldout import evaluate_checkpoint_arrays
from predictive_pc_fmcw.link import LinkModel


class _ExactPredictor:
    def __init__(self, future):
        self.future = future
        self.offset = 0

    def predict(self, history_xy, horizon_steps, dt_s):
        del horizon_steps, dt_s
        start = self.offset
        self.offset += len(history_xy)
        return self.future[start : self.offset]


class HeldoutEvaluationTest(unittest.TestCase):
    def setUp(self):
        self.history = np.zeros((3, 11, 2), dtype=np.float32)
        self.future = np.zeros((3, 80, 2), dtype=np.float32)
        self.future[..., 0] = np.linspace(10, 20, 80)
        self.headings = np.zeros((3, 80), dtype=np.float32)
        self.scenarios = np.asarray(["a", "a", "b"])
        self.link_model = LinkModel(LinkConfig())

    def _evaluate(self, **overrides):
        values = {
            "predictor": _ExactPredictor(self.future),
            "history_xy": self.history,
            "future_xy": self.future,
            "future_ego_heading_rad": self.headings,
            "scenario_ids": self.scenarios,
            "link_model": self.link_model,
            "checkpoint": "exact.pt",
            "objective": "trajectory_only",
            "seed": 1,
            "batch_size": 2,
        }
        values.update(overrides)
        return evaluate_checkpoint_arrays(**values)

    def test_exact_prediction_has_zero_heldout_errors(self):
        rows = self._evaluate()
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row.ade_m, 0.0)
            self.assertEqual(row.fde_m, 0.0)
            self.assertEqual(row.snr_mae_db, 0.0)
            self.assertEqual(row.goodput_mae_mbps, 0.0)
            self.assertEqual(row.link_lifetime_mae_s, 0.0)

    def test_rejects_heading_horizon_mismatch(self):
        with self.assertRaises(ValueError):
            self._evaluate(future_ego_heading_rad=np.zeros((3, 79)))

    def test_rejects_nonfinite_inputs(self):
        future = self.future.copy()
        future[0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            self._evaluate(future_xy=future)

    def test_rejects_empty_heldout_sample_set(self):
        with self.assertRaises(ValueError):
            evaluate_checkpoint_arrays(
                predictor=_ExactPredictor(np.zeros((0, 80, 2))),
                history_xy=np.zeros((0, 11, 2)),
                future_xy=np.zeros((0, 80, 2)),
                future_ego_heading_rad=np.zeros((0, 80)),
                scenario_ids=np.asarray([], dtype=str),
                link_model=self.link_model,
                checkpoint="empty.pt",
                objective="trajectory_only",
                seed=1,
            )

    def test_rejects_nonfinite_checkpoint_predictions(self):
        predicted = self.future.copy()
        predicted[0, 0, 0] = np.inf
        with self.assertRaises(ValueError):
            self._evaluate(predictor=_ExactPredictor(predicted))


if __name__ == "__main__":
    unittest.main()
