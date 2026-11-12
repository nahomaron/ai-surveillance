"""Appendix T T10 tests at the substrate (contract E-1.2.8): CT-T10-02, CT-T10-03, CT-T10-10.
Expected values are T10 checks or hand calculations written here."""
import math

import pytest

from rq1.fixtures import synthetic_s1
from rq1.substrate import builder, evidence, kinematics

from test_part_b import build_s4, by_frame, n2_positions, tracks

TOL = 1e-9


def person_rows(built):
    return {r["frame_index"]: r for r in built.tables["object_state"] if r["track_id"] == builder.track_ids(built)[1]}


# CT-T10-02 (T10.2): at 10 fps with w_v = 0.5 s, 4 frames span 0.3 s >= 0.25 s and give a velocity; 3 frames span 0.2 s and give null.
def test_ct_t10_02_four_frames_give_velocity_three_do_not():
    assert kinematics.window_ok([0.0, 0.1, 0.2, 0.3], 0.5) and not kinematics.window_ok([0.0, 0.1, 0.2], 0.5)
    # Person lost on frame 4: run 0-3 has 4 frames (whole run used, T9.1), so every frame of it has speed 0.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={4: "lost"}), n2_positions("N2-G3", 10))
    person = person_rows(built)
    assert all(person[i]["speed_mps"] == pytest.approx(0.0, abs=TOL) for i in range(4))
    # Person lost on frames 3 and 7: runs 0-2 and 4-6 have 3 frames each, so speed is null (not_observable) on them.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={3: "lost", 7: "lost"}), n2_positions("N2-G3", 10))
    person = person_rows(built)
    assert all(person[i]["speed_mps"] is None and person[i]["speed_mps_null_reason"] == "not_observable" for i in (0, 1, 2, 4, 5, 6))


# CT-T10-03 (T10.3(a)): closing rate with the T9.1 window.
def test_ct_t10_03_g3_closing_rate_on_every_frame():
    built, _ = build_s4(synthetic_s1.build(10), tracks(10), n2_positions("N2-G3", 10))
    rows = by_frame(built)
    assert [rows[i]["closing_rate_mps"] for i in range(10)] == pytest.approx([1.5] * 10, abs=TOL)  # T10.3 check


def test_ct_t10_03_unmeasured_frame_gets_a_rate_when_the_window_has_three_measured_frames():
    # Person lost on frame 5 only (bridged). Frame 5's clearance is not measured, but its window [0.25, 0.75] holds frames
    # 3-7, of which 3, 4, 6, 7 are measured (span 0.4 s >= 0.25 s): rate = -slope of 3.70 - 1.5 t = 1.5.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={5: "lost"}), n2_positions("N2-G3", 10))
    row = by_frame(built)[5]
    assert row["clearance_state"] != "measured" and row["closing_rate_mps"] == pytest.approx(1.5, abs=TOL)


def test_ct_t10_03_null_with_fewer_than_three_measured_frames():
    # Person lost on frames 4-6. Frame 5's window [0.25, 0.75] holds frames 3-7; only 3 and 7 are measured -> null.
    # Frame 0's shifted window [0, 0.5] holds frames 0-5; measured 0-3 (4 frames, 0.3 s) -> 1.5.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={4: "lost", 5: "lost", 6: "lost"}), n2_positions("N2-G3", 10))
    rows = by_frame(built)
    assert rows[5]["closing_rate_mps"] is None and rows[5]["closing_rate_mps_null_reason"] == "not_observable"
    assert rows[0]["closing_rate_mps"] == pytest.approx(1.5, abs=TOL)


def test_ct_t10_03_zero_is_stored_as_positive_zero():
    # G1: person and forklift static, identical clearance on every frame, so the slope is exactly zero and -0.0 would arise.
    built, _ = build_s4(synthetic_s1.build(20), tracks(20), n2_positions("N2-G1", 20))
    rates = [r["closing_rate_mps"] for r in built.tables["pair_series"]]
    assert all(r == 0.0 and math.copysign(1.0, r) == 1.0 for r in rates)


# CT-T10-10 (T10.9): q_reasons for lost objects.
def test_ct_t10_10_lost_objects_are_reported_as_lost():
    assert evidence.q_state("insufficient", "lost", "visible", "measured") == ("insufficient", ["person_lost"])
    assert evidence.q_state("insufficient", "visible", "lost", "measured") == ("insufficient", ["forklift_lost"])
    assert evidence.q_state("inferred", "occluded_predicted", "visible", "measured") == ("insufficient", ["person_occluded"])  # T8.7 unchanged
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={5: "lost"}), n2_positions("N2-G3", 10))
    row = by_frame(built)[5]
    assert "person_lost" in row["q_reasons"] and "person_occluded" not in row["q_reasons"]
    assert row["q_state"] == "insufficient"  # q_state follows T8.7: the pair class is insufficient
