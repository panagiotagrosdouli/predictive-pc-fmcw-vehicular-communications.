import json
import tempfile
import unittest
from pathlib import Path

from predictive_pc_fmcw.config import LinkConfig, config_from_dict, load_config


class ConfigTest(unittest.TestCase):
    def test_nested_config_and_tuple_conversion(self):
        config = config_from_dict(
            {"benchmark": {"episodes": 2, "schedulers": ["random", "oracle"]}}
        )
        self.assertEqual(config.benchmark.episodes, 2)
        self.assertEqual(config.benchmark.schedulers, ("random", "oracle"))

    def test_round_trip_file(self):
        config = config_from_dict({})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
            loaded = load_config(path)
        self.assertEqual(loaded, config)

    def test_link_geometry_parameters_reject_nonphysical_values(self):
        invalid_cases = (
            {"reference_distance_m": 0.0},
            {"beam_divergence_half_angle_deg": 0.0},
            {"pointing_sigma_deg": 0.0},
            {"atmospheric_attenuation_per_m": -1e-3},
            {"min_received_power_w": -1e-15},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                LinkConfig(**overrides)

    def test_link_geometry_parameters_accept_physical_boundaries(self):
        config = LinkConfig(
            atmospheric_attenuation_per_m=0.0,
            min_received_power_w=0.0,
        )
        self.assertEqual(config.atmospheric_attenuation_per_m, 0.0)
        self.assertEqual(config.min_received_power_w, 0.0)


if __name__ == "__main__":
    unittest.main()
