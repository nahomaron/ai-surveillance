"""T-08 part A: the substrate pieces that E-1.2.5 defines. Expected values from Appendix T CT-T rows,
the committed Appendix N2 fixtures and hand calculations noted inline. CR-005 covers the rest."""
import json
import math
import random
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rq1.decode import stage
from rq1.decode.timestamps import DecodeConfig
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.schema import vr_rules
from rq1.substrate import activity, durations, geometry, oracle

TOL = 1e-9
FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
CAM = core.anchor_id("cam", "camera", ["c"])


def s1(clip_dir, name, f_untimed=0.05):
    r = core.anchor_id("rec", "recording", [name])
    tl = {"tl_id": core.anchor_id("tl", "timeline", ["recording_local", r]), "kind": "recording_local", "extent_start_tl_s": None, "extent_end_tl_s": None}
    item = stage.S1Input(r, CAM, clip_dir / f"{name}.mkv", clip_dir / f"{name}.faults.json")
    config = DecodeConfig(1.5, f_untimed, 0.10, "rv1", {r: 0.033}, "delta_nom")
    return stage.run_s1(tl, [item], config, Spec("S1", "E-1.2.5", "f", "f", ("dcf_" + "a" * 26,), (), {}))


def all_detected(frames):
    return {f["frame_index"]: "tracked" for f in frames if f["eligible"]}


# CT-T-14 to 17, duration assertions: person and forklift detected on every eligible frame.
@pytest.mark.determinism
@pytest.mark.parametrize("name,f_untimed,detected,insufficient", [
    ("fx_clip_a", 0.05, 0.100, 0.033), ("fx_clip_b", 0.5, 0.067, 0.033), ("fx_clip_c", 0.5, 0.033, 0.067), ("fx_clip_d", 0.05, 0.133, 0.0)])
def test_ct_t_14_to_17_pair_durations(clip_dir, name, f_untimed, detected, insufficient):
    frames = s1(clip_dir, name, f_untimed).tables["frame"]
    states = all_detected(frames)
    n = len(states)
    a, b = durations.interval_extent(frames, 0, n)
    pair = durations.pair_class(lambda i: durations.object_class(states.get(i)), lambda i: durations.object_class(states.get(i)))
    result = durations.class_durations(frames, a, b, pair)
    assert result["detected"] == pytest.approx(detected, abs=TOL)
    assert result["inferred"] == pytest.approx(0.0, abs=TOL)
    assert result["insufficient"] == pytest.approx(insufficient, abs=TOL)
    assert result["detected"] + result["inferred"] + result["insufficient"] == pytest.approx(result["total"], abs=TOL)  # EC-01


@pytest.mark.determinism
def test_ct_t_15_nothing_in_uncertainty_region_counts(clip_dir):
    frames = s1(clip_dir, "fx_clip_b", 0.5).tables["frame"]
    states = all_detected(frames)
    cls = lambda i: durations.object_class(states.get(i))
    assert durations.class_durations(frames, 0.0, 0.066, durations.pair_class(cls, cls))["detected"] == 0.0


def test_section_3_4_pair_class_rules():
    c = durations.combine
    assert (c("detected", "detected"), c("detected", "inferred"), c("inferred", "inferred")) == ("detected", "inferred", "inferred")
    assert c("insufficient", "detected") == c("inferred", "insufficient") == "insufficient"
    assert [durations.object_class(s) for s in ("tracked", "predicted", "lost", None)] == ["detected", "inferred", "insufficient", "insufficient"]


@pytest.mark.determinism
def test_ti_10_interval_ending_mid_support(clip_dir):
    frames = s1(clip_dir, "fx_clip_d").tables["frame"]
    states = all_detected(frames)
    cls = lambda i: durations.object_class(states.get(i))
    assert durations.class_durations(frames, 0.0, 0.050, durations.pair_class(cls, cls))["detected"] == pytest.approx(0.050, abs=TOL)


@st.composite
def frame_sets(draw):
    n = draw(st.integers(2, 25))
    t, frames, index = 0.0, [], 0
    for seq in range(n):
        s = draw(st.sampled_from([0.033, 0.034, 0.05]))
        eligible = draw(st.booleans()) or seq == 0
        status = draw(st.sampled_from(["measured", "timing_uncertain"])) if eligible else "excluded_own_support"
        frames.append({"decode_seq": seq, "eligible": eligible, "frame_index": index if eligible else None, "support_start_tl_s": t, "support_s": s,
                       "support_status": status})
        index += eligible
        t += s + draw(st.sampled_from([0.0, 0.0, 0.2]))
    states = {f["frame_index"]: draw(st.sampled_from(["tracked", "predicted", "lost"])) for f in frames if f["eligible"]}
    return frames, states


@pytest.mark.determinism
@settings(max_examples=300, deadline=None)
@given(frame_sets(), st.floats(0, 0.5), st.floats(0, 2.0))
def test_ct_t_20_c_d_and_ec_01_property(data, a, length):
    frames, states = data
    b = a + length
    cls = lambda i: durations.object_class(states.get(i))
    result = durations.class_durations(frames, a, b, durations.pair_class(cls, cls))
    observable = sum(max(0.0, min(f["support_start_tl_s"] + f["support_s"], b) - max(f["support_start_tl_s"], a))
                     for f in frames if f["eligible"] and f["support_status"] != "timing_uncertain")
    assert result["detected"] <= observable + TOL  # (c)
    tracked = lambda i: "detected"  # (d): with every object detected, system time equals reference-observable time
    assert durations.class_durations(frames, a, b, durations.pair_class(tracked, tracked))["detected"] == pytest.approx(observable, abs=1e-9)
    assert result["detected"] + result["inferred"] + result["insufficient"] == pytest.approx(result["total"], abs=1e-9)  # EC-01


# Oracle S3 source
@pytest.mark.determinism
def test_oracle_s3_tracks_and_evidence_classes(clip_dir):
    s1_art = s1(clip_dir, "fx_clip_a")
    frames = s1_art.tables["frame"]
    rec = frames[0]["recording_id"]
    truth = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [10.0, 10.0, 20.0, 40.0], "state": st} for i, st in enumerate(["tracked", "predicted", "tracked"])]},
             {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [30.0, 10.0, 60.0, 40.0], "state": "tracked"} for i in range(3)]}]
    built = oracle.OracleTrackSource().tracks(rec, truth, frames, Spec("S3", "E-1.2.5", "f", "f", ("orc_" + "a" * 26,), (s1_art.artifact_id,), {}))
    person = next(t for t in built.tables["track"] if t["track_local_id"] == 1)
    # Frame index 1 is f2 [0.066, 0.100): predicted, so inferred 0.034. Frames f0 and f3 detected 0.033 + 0.033.
    # f1 (corrupt, ineligible) lies inside the track extent and counts as insufficient (ST-6).
    assert (person["t_detected_s"], person["t_inferred_s"], person["t_insufficient_s"]) == pytest.approx((0.066, 0.034, 0.033), abs=TOL)
    assert person["span_s"] == pytest.approx(0.133, abs=TOL) and person["n_gaps"] == 1 and person["max_gap_frames"] == 1
    points = {(p["track_nk"][1], p["frame_index"]): p for p in built.tables["track_point"]}
    assert points[(1, 1)]["evidence_class"] == "inferred" and points[(1, 1)]["detection_id"] is None
    assert points[(1, 0)]["foot_point_px"] == [15.0, 40.0]  # bottom centre of [10, 10, 20, 40] in CF-IMG
    for table, rows in built.tables.items():
        assert vr_rules.check_ids(table, rows, built.artifact_id) == []


# Activity segments (section 3.5, CD-01 to 03, FX-D1/D2, CT-E-11)
@pytest.mark.determinism
def test_activity_segments_tile_coverage(clip_dir):
    s1_art = s1(clip_dir, "fx_clip_a")
    frames, coverage = s1_art.tables["frame"], s1_art.tables["coverage_segment"]
    detections = {0: {"person", "forklift"}, 1: {"person"}, 2: set()}
    rows = activity.build(coverage, frames, detections, pair_classes={"forklift"}, perception_artifact_id="art_" + "a" * 26)
    shape = [(round(r["t_start_tl_s"], 9), round(r["t_end_tl_s"], 9), r["coverage_state"], r["ai_activity_state"]) for r in rows]
    assert shape == [(0.0, 0.033, "usable", "pair_detected"), (0.033, 0.066, "unusable", "not_evaluated"),
                     (0.066, 0.1, "usable", "objects_detected_no_pair"), (0.1, 0.133, "usable", "observed_no_detection")]
    extent = (min(c["t_start_tl_s"] for c in coverage), max(c["t_end_tl_s"] for c in coverage))
    assert vr_rules.check_activity(rows, extent) == []
    assert all((r["perception_artifact_id"] is None) == (r["ai_activity_state"] == "not_evaluated") for r in rows)
    assert vr_rules.check_no_reference_states("activity_segment", rows) == []  # CT-E-11, store part


@pytest.mark.determinism
def test_fx_d1_and_d2():
    d1 = json.loads((FIX / "FX-D1.json").read_text())["record"]
    d2 = json.loads((FIX / "FX-D2.json").read_text())["record"]
    row = lambda r: {"t_start_tl_s": r["t_start_session_s"], "t_end_tl_s": r["t_end_session_s"], "coverage_state": r["coverage_state"], "ai_activity_state": r["ai_activity_state"]}
    assert vr_rules.check_activity([row(d1)], (0.0, 20.0)) == []
    assert [i.rule for i in vr_rules.check_activity([row(d2)], (0.0, 20.0))] == ["VR-E-013"]


# Geometry: signed footprint distance and constant-velocity prediction (Appendix N2)
PERSON_R, FORK = 0.30, (2.0, 1.0)


def n2(name):
    return json.loads((FIX / f"{name}.json").read_text())


def _forklift_x(name, t):
    return {"N2-G1": 0.0, "N2-G2": -2.5 + 1.0 * t, "N2-G3": 1.5 * t}[name]


@pytest.mark.determinism
@pytest.mark.parametrize("name", ["N2-G1", "N2-G2", "N2-G3"])
def test_n2_clearances(name):
    fixture = n2(name)
    person = fixture["inputs"]["person_xy"]
    for k, expected in enumerate(fixture["expected"]["clearance_m"]):
        got = geometry.clearance(person, PERSON_R, (_forklift_x(name, k / 10), 0.0), 0.0, *FORK)
        assert got == pytest.approx(expected, abs=1e-6), (name, k)


@pytest.mark.determinism
@pytest.mark.parametrize("name", ["N2-G1", "N2-G3"])
def test_n2_constant_velocity_predicted_minimum(name):
    fixture = n2(name)
    person = fixture["inputs"]["person_xy"]
    speed = fixture["inputs"]["forklift_speed_mps"]
    for k, expected in enumerate(fixture["expected"]["pred_min_clearance_m"]):
        got, t_min = geometry.predict_min_clearance(person, (0.0, 0.0), PERSON_R, (_forklift_x(name, k / 10), 0.0), (speed, 0.0), 0.0, *FORK, horizon_s=2.0)
        assert got == pytest.approx(expected, abs=1e-6), (name, k)
        assert 0.0 <= t_min <= 2.0


def test_n2_g2_predicted_minimum_never_below_d_pc():
    for k in range(50):
        got, _ = geometry.predict_min_clearance((0.0, 1.9), (0.0, 0.0), PERSON_R, (-2.5 + k / 10, 0.0), (1.0, 0.0), 0.0, *FORK, horizon_s=2.0)
        assert got >= 1.0 - 1e-9  # N2 G2: C_by_R3 = 0 with d_pc = 1.0


@pytest.mark.determinism
@settings(max_examples=300, deadline=None)
@given(st.floats(-4, 4), st.floats(-4, 4), st.floats(-math.pi, math.pi))
def test_ct_e_06_overlap_iff_clearance_not_positive(x, y, yaw):
    c = geometry.clearance((x, y), PERSON_R, (0.0, 0.0), yaw, *FORK)
    assert (geometry.footprint_overlap(c) == 1) == (c <= 0)


def test_signed_distance_inside_rectangle():
    # Hand calculation: centre inside, 0.35 m from the nearest edge, so signed distance -0.35 and clearance -0.65.
    assert geometry.clearance((5.0, 0.0), PERSON_R, (4.35, 0.0), 0.0, *FORK) == pytest.approx(-0.65, abs=1e-12)
