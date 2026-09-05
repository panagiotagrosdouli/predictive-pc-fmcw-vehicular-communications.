from predictive_pc_fmcw.synthetic.scheduling_protocol import (
    PAIRED_TRAFFIC_SEEDS,
    SCHEDULER_FAMILIES,
    scheduler_protocol_manifest,
    validate_scheduler_protocol,
)


def test_scheduler_protocol_is_exact_s0_through_s7() -> None:
    validate_scheduler_protocol()
    assert [item.protocol_id for item in SCHEDULER_FAMILIES] == [
        f"S{index}" for index in range(8)
    ]
    assert len(PAIRED_TRAFFIC_SEEDS) == 5


def test_scheduler_protocol_preserves_scientific_roles() -> None:
    by_id = {item.protocol_id: item for item in SCHEDULER_FAMILIES}
    assert by_id["S0"].scheduler_name == "reactive_greedy"
    assert by_id["S1"].scheduler_name == "proportional_fair"
    assert by_id["S2"].scheduler_name == "cv_predictive"
    assert by_id["S3"].scheduler_name == "kalman_predictive"
    assert by_id["S4"].scheduler_name == "imm_predictive"
    assert by_id["S5"].learned_objective == "trajectory_only"
    assert by_id["S6"].learned_objective == "full"
    assert by_id["S7"].scheduler_name == "oracle"
    assert by_id["S7"].deployable is False


def test_scheduler_protocol_declares_paired_scenario_unit() -> None:
    manifest = scheduler_protocol_manifest()
    assert manifest["inferential_unit"] == "scenario_episode"
    assert set(manifest["paired_inputs"]) == {
        "mobility_scenario",
        "channel_realization",
        "packet_arrivals",
        "packet_deadlines",
        "traffic_seed",
    }
    assert tuple(manifest["traffic_seeds"]) == PAIRED_TRAFFIC_SEEDS
