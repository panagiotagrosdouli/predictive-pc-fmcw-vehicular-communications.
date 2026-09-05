import numpy as np

from predictive_pc_fmcw.config import ExperimentConfig, LinkConfig
from predictive_pc_fmcw.data.scenario import MotionScenario
from predictive_pc_fmcw.link import LinkModel
from predictive_pc_fmcw.simulation.engine import run_simulation
from predictive_pc_fmcw.traffic import generate_traffic_trace


def test_forecast_link_mismatch_does_not_change_actual_channel_trace() -> None:
    timestamps = np.arange(10, dtype=np.float64) * 0.1
    ego = np.zeros((10, 2), dtype=np.float64)
    vehicles = np.zeros((10, 2, 2), dtype=np.float64)
    vehicles[:, 0, 0] = np.linspace(50.0, 59.0, 10)
    vehicles[:, 1, 0] = np.linspace(80.0, 71.0, 10)
    vehicles[:, 1, 1] = 3.0
    scenario = MotionScenario(
        scenario_id="mismatch-test",
        timestamps_s=timestamps,
        ego_positions_xy=ego,
        vehicle_positions_xy=vehicles,
        actor_ids=("a", "b"),
        start_index=3,
    )
    config = ExperimentConfig()
    capacity = LinkModel(config.link).capacity_packets(config.slot_duration_s)
    traffic = generate_traffic_trace(
        seed=123,
        slots=scenario.evaluation_slots,
        vehicles=scenario.vehicle_count,
        nominal_capacity_packets=capacity,
        config=config.traffic,
        slot_duration_s=config.slot_duration_s,
    )
    matched = run_simulation(
        scenario,
        "reactive_greedy",
        traffic,
        config,
        seed=456,
    )
    mismatched = run_simulation(
        scenario,
        "reactive_greedy",
        traffic,
        config,
        seed=456,
        forecast_link_config=LinkConfig(reference_snr_db=3.0),
    )
    np.testing.assert_allclose(matched.actual_snr_db, mismatched.actual_snr_db)
    np.testing.assert_array_equal(matched.actual_outage, mismatched.actual_outage)
    np.testing.assert_array_equal(matched.selected_vehicle, mismatched.selected_vehicle)
