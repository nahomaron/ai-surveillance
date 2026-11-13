"""Appendix T T15 (contract E-1.2.13; CR-018, D-27): R4 time-to-collision and predicted PET, the R4 Unknown rule, the T15.5
configuration constraint, and baseline configurations BL-1 to BL-6. Footprint priors as in the other S5 tests: person disc
r = 0.30 m; forklift rectangle 2.0 m x 1.0 m (length along yaw). tau = 2.0 s; TEST-ONLY ttc_max 1.5 s, pet_max 1.0 s
(Package F section 3; T15.6). Expected values are hand calculations written beside each assertion. The bisection tolerance is
1e-6 s (T15.2); pet_pred differences carry two bounds, so they are compared at 2e-6 s."""
import dataclasses
import math

import pytest

from rq1.events import baselines, engine, providers, s5
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema import validate
from rq1.schema.errors import ContractError
from rq1.substrate import builder, geometry, oracle, surrogate

from test_engine_part_a import FORK, PERSON
from test_t10 import BANDS, PARAMS, RULES, SUBSTRATE, build_s5, s5_config

R, L, W, TAU = 0.30, 2.0, 1.0, 2.0
TTC_TOL, PET_TOL = 1e-6, 2e-6
R4_RULES = dataclasses.replace(RULES, conflict=("R4",))


def predict(pc, pv, fc, fv, yaw=0.0):
    """ttc, pet_pred and both occupancy intervals of the T15 prediction from the frame (t = 0)."""
    args = (pc, pv, R, fc, fv, yaw, L, W)
    _, t_min = geometry.predict_min_clearance(*args, TAU)
    ttc = surrogate.ttc(lambda t: geometry.predicted_clearance(*args, t), t_min)
    person, fork = surrogate.person_shape(pc, R), surrogate.forklift_shape(fc, yaw, L, W)
    occ_p = surrogate.occupancy(person, pv, surrogate.swept(fork, fv, TAU), TAU)
    occ_f = surrogate.occupancy(fork, fv, surrogate.swept(person, pv, TAU), TAU)
    return ttc, surrogate.pet_pred(person, pv, fork, fv, TAU), occ_p, occ_f


# --- T15.2 / T15.3 geometry, one fixture per required case --------------------------------------------------------------

@pytest.mark.determinism
def test_head_on_approach_ttc_found():
    # Forklift centre (0,0), yaw 0, v (1,0): front at x = 1 + t. Person (3,0), v (-0.5,0): back of the disc at 2.7 - 0.5 t.
    # Clearance 1.7 - 1.5 t -> 0 at t = 1.7 / 1.5 = 1.1333333 s <= tau. TTC part: 1.1333 < 1.5 -> 1.
    ttc, pet, occ_p, occ_f = predict((3.0, 0.0), (-0.5, 0.0), (0.0, 0.0), (1.0, 0.0))
    assert ttc == pytest.approx(1.7 / 1.5, abs=TTC_TOL)
    # Swept forklift: x in [-1, 3]. Person disc spans [2.7 - 0.5 t, 3.3 - 0.5 t] -> meets it from t = 0 to tau: [0, 2].
    # Swept person: capsule (3,0)-(2,0), r 0.3, x >= 1.7. Forklift front 1 + t reaches 1.7 at t = 0.7; rear -1 + t < 3.3 to tau.
    assert occ_p == pytest.approx((0.0, 2.0), abs=TTC_TOL) and occ_f == pytest.approx((0.7, 2.0), abs=TTC_TOL)
    # First = person (starts at 0). pet_pred = max(0, 0.7 - 2.0) = 0.
    assert pet == 0.0


@pytest.mark.determinism
def test_approach_crossing_beyond_tau_ttc_null():
    # Person (5,0) static; forklift front 1 + t: clearance 3.7 - t > 0 on [0, 2] (1.7 at tau) -> ttc null.
    # Swept forklift x in [-1, 3]; person disc x in [4.7, 5.3]: gap 1.7 -> A empty -> pet_pred null.
    assert predict((5.0, 0.0), (0.0, 0.0), (0.0, 0.0), (1.0, 0.0))[:2] == (None, None)


@pytest.mark.determinism
def test_crossing_paths_with_time_gap_pet_positive_ttc_null():
    # Forklift centre (2,0), v (3,0): x in [1 + 3t, 3 + 3t], y in [-0.5, 0.5]. Person (4,-2.5), v (0,1).
    # Clearance = hypot(xg, yg) - 0.3 with xg = max(0, 1 - 3t, 3t - 3), yg = max(0, 2 - t). xg = 0 only on [1/3, 1], where
    # yg >= 1 -> clearance >= 0.7; elsewhere both terms keep it positive -> ttc null.
    # Forklift meets the person capsule (x = 4, y in [-2.5, -0.5], r 0.3): 4 - (3 + 3t) <= 0.3 -> t >= 0.2333333;
    # (1 + 3t) - 4 <= 0.3 -> t <= 1.1. Person meets the swept forklift (y >= -0.5): -0.5 - (-2.5 + t) <= 0.3 -> t >= 1.7, to tau.
    # First = forklift: pet_pred = 1.7 - 1.1 = 0.6 s. PET part: 0.6 < 1.0 -> 1.
    ttc, pet, occ_p, occ_f = predict((4.0, -2.5), (0.0, 1.0), (2.0, 0.0), (3.0, 0.0))
    assert ttc is None
    assert occ_f == pytest.approx((0.7 / 3, 1.1), abs=TTC_TOL) and occ_p == pytest.approx((1.7, 2.0), abs=TTC_TOL)
    assert pet == pytest.approx(0.6, abs=PET_TOL)


@pytest.mark.determinism
def test_simultaneous_occupancy_pet_zero():
    # As above, person from (4,-1): it meets the swept forklift from -0.5 - (-1 + t) <= 0.3 -> t >= 0.2 until its far edge
    # passes y = 0.5: -1 + t - 0.3 <= 0.5 -> t <= 1.8. Forklift interval [0.2333333, 1.1] (as above).
    # First = person (0.2): pet_pred = max(0, 0.2333 - 1.8) = 0.
    ttc, pet, occ_p, occ_f = predict((4.0, -1.0), (0.0, 1.0), (2.0, 0.0), (3.0, 0.0))
    assert occ_p == pytest.approx((0.2, 1.8), abs=TTC_TOL) and occ_f == pytest.approx((0.7 / 3, 1.1), abs=TTC_TOL)
    assert pet == 0.0
    # ttc: for t < 1/3 the nearest rectangle point is the corner (3 + 3t, -0.5): xg = 1 - 3t, yg = 0.5 - t;
    # (1 - 3t)^2 + (0.5 - t)^2 = 0.09 -> 10 t^2 - 7 t + 1.16 = 0 -> t = (7 - sqrt(2.6)) / 20 = 0.2693774 s.
    assert ttc == pytest.approx((7 - math.sqrt(2.6)) / 20, abs=TTC_TOL)


@pytest.mark.determinism
def test_parallel_paths_conflict_area_empty():
    # Person (0,3) and forklift (0,0), both v (1,0): clearance constant 3 - 0.5 - 0.3 = 2.2 -> ttc null.
    # Swept forklift y in [-0.5, 0.5], swept person y in [2.7, 3.3] -> A empty -> pet_pred null.
    assert predict((0.0, 3.0), (1.0, 0.0), (0.0, 0.0), (1.0, 0.0))[:2] == (None, None)


@pytest.mark.determinism
def test_overlap_at_the_frame_gives_ttc_zero():
    # Person at (1.2, 0): clearance 1.2 - 1.0 - 0.3 = -0.1 <= 0 at t = 0 -> ttc = 0 (T15.2).
    assert predict((1.2, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0))[0] == 0.0


@pytest.mark.determinism
def test_unknown_yaw_uses_the_circumscribed_disc():
    # T15.1 / T8.2: disc radius 0.5 sqrt(5) = 1.1180340. Person (3,0) static, forklift v (1,0):
    # clearance 3 - t - 1.1180340 - 0.3 -> ttc = 1.5819660 s.
    ttc = predict((3.0, 0.0), (0.0, 0.0), (0.0, 0.0), (1.0, 0.0), yaw=None)[0]
    assert ttc == pytest.approx(3 - 0.5 * math.sqrt(5) - 0.3, abs=TTC_TOL)


@pytest.mark.determinism
def test_hull_of_translated_rectangle():
    # Rectangle 2 x 1 at the origin, yaw 0, moved by (3, 0): hull = [-1, 4] x [-0.5, 0.5] (4 corners, CCW from the lowest-left).
    shape = surrogate.swept(surrogate.forklift_shape((0.0, 0.0), 0.0, L, W), (1.5, 0.0), 2.0)
    assert shape.verts == ((-1.0, -0.5), (4.0, -0.5), (4.0, 0.5), (-1.0, 0.5)) and shape.r == 0.0


# --- S4: pair_series.ttc_s and pet_pred_s (T15.7) ------------------------------------------------------------------------

def s4_moving(n, person_xy, fork_xy, person_positions=True):
    """Person and forklift on straight lines at 10 fps (t = i / 10); forklift yaw 0 supplied; covariance as in test_t10."""
    positions = {(2, i): {"xy": list(fork_xy(i / 10)), "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(n)}
    if person_positions:
        positions.update({(1, i): {"xy": list(person_xy(i / 10)), "cov": [0.0025, 0.0, 0.0025]} for i in range(n)})
    s1 = synthetic_s1.build(n)
    truth = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [100.0, 100.0, 140.0, 200.0], "state": "tracked"} for i in range(n)]},
             {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"} for i in range(n)]}]
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.13", "f", "f", ("orc_" + "a" * 26,), (), {}))
    cfg = builder.SubstrateConfig(15, 0.3, 0.5, TAU, {"forklift"}, {"person": PERSON, "forklift": FORK}, {"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                  BANDS, 0.5)
    s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, Spec("S4", "E-1.2.13", "f", "f", ("gcf_" + "a" * 26, s5.substrate_config_id(SUBSTRATE)), (s3.artifact_id,), {}))
    return s1, s4


HEAD_ON = (lambda t: (3.0 - 0.5 * t, 0.0), lambda t: (t, 0.0))
GAP = (lambda t: (4.0, -2.5 + t), lambda t: (2.0 + 3.0 * t, 0.0))
PARALLEL = (lambda t: (t, 3.0), lambda t: (t, 0.0))
BEYOND = (lambda t: (5.0, 0.0), lambda t: (t, 0.0))


def series(s4):
    return {r["frame_index"]: r for r in s4.tables["pair_series"]}


@pytest.mark.determinism
def test_s4_pair_series_ttc_and_pet_pred():
    _, s4 = s4_moving(10, *HEAD_ON)
    rows = series(s4)
    # Frame k (t_k = k / 10): clearance 1.7 - 1.5 t_k at the frame -> ttc = 1.1333333 - t_k; pet_pred 0 (as at t = 0).
    for k in (0, 5):
        assert rows[k]["ttc_s"] == pytest.approx(1.7 / 1.5 - k / 10, abs=1e-5) and rows[k]["ttc_s_null_reason"] is None
        assert rows[k]["pet_pred_s"] == 0.0 and rows[k]["pet_pred_s_null_reason"] is None
    assert all(validate.validate_row("pair_series", r) == [] for r in rows.values())
    rows = series(s4_moving(10, *PARALLEL)[1])
    assert (rows[0]["ttc_s"], rows[0]["ttc_s_null_reason"], rows[0]["pet_pred_s"], rows[0]["pet_pred_s_null_reason"]) == (None, "not_applicable", None, "not_applicable")
    rows = series(s4_moving(10, *GAP)[1])
    assert rows[0]["ttc_s"] is None and rows[0]["pet_pred_s"] == pytest.approx(0.6, abs=1e-5)


@pytest.mark.determinism
def test_s4_null_reasons_without_prediction():
    # 2 frames span 0.1 s < w_v / 2 = 0.25 s -> no velocity (T8.2) -> no prediction: not_observable.
    rows = series(s4_moving(2, *HEAD_ON)[1])
    assert all((r["ttc_s"], r["ttc_s_null_reason"], r["pet_pred_s_null_reason"]) == (None, "not_observable", "not_observable") for r in rows.values())
    # No person position and no calibration: the person is image_only -> uncalibrated.
    rows = series(s4_moving(10, *HEAD_ON, person_positions=False)[1])
    assert all((r["clearance_state"], r["ttc_s_null_reason"], r["pet_pred_s_null_reason"]) == ("unmeasurable_uncalibrated", "uncalibrated", "uncalibrated")
               for r in rows.values())


# --- S5: C_by_R4 (T15.4) ---------------------------------------------------------------------------------------------------

def c_r4(s1, s4, rules=R4_RULES):
    return {f.frame_index: f.C_by["R4"] for f in providers.flag_frames(s4.tables, rules, s1["frame"], s1["coverage_segment"])}


@pytest.mark.determinism
def test_r4_flag_ttc_part_and_pet_part():
    # Head-on: ttc 1.1333 < 1.5 -> 1 at frame 0.
    assert c_r4(*s4_moving(10, *HEAD_ON))[0] == 1
    # Time gap: ttc null, pet_pred 0.6 < pet_max 1.0 -> 1; with pet_max 0.5 -> 0.6 >= 0.5 -> 0 (PET part alone decides).
    s1, s4 = s4_moving(10, *GAP)
    assert c_r4(s1, s4)[0] == 1 and c_r4(s1, s4, dataclasses.replace(R4_RULES, pet_max=0.5))[0] == 0
    # Parallel: both null (not_applicable) -> both parts 0 -> 0.
    assert set(c_r4(*s4_moving(10, *PARALLEL)).values()) == {0}


@pytest.mark.determinism
def test_r4_ttc_threshold_against_horizon():
    # Person static at (5,0), forklift front 1 + t: from frame k, contact after 3.7 - t_k s. Frame 0: 3.7 > tau -> null -> 0.
    # Frame 20 (t 2.0): ttc 1.7 >= 1.5 -> 0 (pet_pred: forklift swept x in [1, 5] meets the disc [4.7, 5.3]; forklift meets
    # the disc from front 3 + t' >= 4.7 -> t' = 1.7, person from 0 to tau -> first = person: max(0, 1.7 - 2.0) = 0 < 1.0 -> 1).
    # Frame 0 pet_pred: swept x in [-1, 3], gap 1.7 -> null. So frame 0 -> 0, frame 20 -> 1 by the PET part.
    s1, s4 = s4_moving(30, *BEYOND)
    rows, flags = series(s4), c_r4(s1, s4)
    assert rows[0]["ttc_s"] is None and rows[0]["pet_pred_s"] is None and flags[0] == 0
    assert rows[20]["ttc_s"] == pytest.approx(1.7, abs=1e-5) and rows[20]["pet_pred_s"] == 0.0 and flags[20] == 1
    # Frame 25 (t 2.5): ttc = 3.7 - 2.5 = 1.2 < 1.5.
    assert rows[25]["ttc_s"] == pytest.approx(1.2, abs=1e-5)


@pytest.mark.determinism
def test_r4_unknown_without_velocity():
    # 2 frames: no velocity on either object (T8.2) -> C_by_R4 = 2 although clearance is measured.
    s1, s4 = s4_moving(2, *HEAD_ON)
    assert all(r["clearance_state"] == "measured" for r in s4.tables["pair_series"])
    assert set(c_r4(s1, s4).values()) == {2}


@pytest.mark.determinism
def test_r4_unknown_when_uncalibrated():
    assert set(c_r4(*s4_moving(10, *HEAD_ON, person_positions=False)).values()) == {2}


@pytest.mark.determinism
@pytest.mark.parametrize("change", [{"ttc_max": 2.5}, {"pet_max": 2.01}])
def test_t15_5_thresholds_above_tau_refused(change):
    s1, s4 = s4_moving(10, *HEAD_ON)
    with pytest.raises(ContractError) as err:
        build_s5(s1, s4, s5_config(rules=dataclasses.replace(R4_RULES, **change)))
    assert err.value.code == "ERR-SPEC"
    with pytest.raises(ContractError):
        providers.flag_frames(s4.tables, dataclasses.replace(R4_RULES, **change), s1["frame"], s1["coverage_segment"])
    # Equal to tau is allowed.
    build_s5(s1, s4, s5_config(rules=dataclasses.replace(R4_RULES, ttc_max=TAU, pet_max=TAU)))


@pytest.mark.determinism
def test_ct_t11_02_extended_disabled_r4_parameters():
    # R4 disabled (RULES: conflict R3 only). Different ttc_max / pet_max (both <= tau): same payload, different config IDs.
    s1, s4 = s4_moving(10, *HEAD_ON)
    a_cfg, b_cfg = s5_config(), s5_config(rules=dataclasses.replace(RULES, ttc_max=0.2, pet_max=1.9))
    a, b = build_s5(s1, s4, a_cfg), build_s5(s1, s4, b_cfg)
    assert s5.config_id(a_cfg) != s5.config_id(b_cfg) and a.payload_sha256 == b.payload_sha256
    # Enabled, the same change moves the output: frame 0 ttc 1.1333 < 1.5 -> 1, but >= 0.2 and pet_pred 0 < 1.9 -> still 1;
    # use pet_max 0.0 instead (0 < 0 false) with ttc_max 0.2 -> 0.
    on = dataclasses.replace(RULES, conflict=("R3", "R4"))
    c, d = build_s5(s1, s4, s5_config(rules=on)), build_s5(s1, s4, s5_config(rules=dataclasses.replace(on, ttc_max=0.2, pet_max=0.0)))
    assert c.payload_sha256 != d.payload_sha256


@pytest.mark.determinism
def test_r4_sets_no_borderline_flag():
    # T15.5: R4 sets no borderline flag. Same frames with conflict () and with R4 enabled: identical borderline and onset.
    s1, s4 = s4_moving(10, *HEAD_ON)
    off = providers.flag_frames(s4.tables, dataclasses.replace(RULES, conflict=()), s1["frame"], s1["coverage_segment"])
    on = providers.flag_frames(s4.tables, R4_RULES, s1["frame"], s1["coverage_segment"])
    assert [(f.borderline, f.onset) for f in off] == [(f.borderline, f.onset) for f in on]


@pytest.mark.determinism
def test_rule_configuration_records_r4():
    record = s5.rule_configuration(s5_config(rules=R4_RULES))
    r4 = next(p for p in record["providers"] if p["provider_id"] == "R4")
    assert r4 == {"provider_id": "R4", "enabled": True, "params": {"pet_max": 1.0, "ttc_max": 1.5}}
    assert validate.validate_row("rule_configuration", record) == []


# --- T15.6 baseline configurations ----------------------------------------------------------------------------------------

@pytest.mark.determinism
def test_baseline_provider_sets():
    want = {"BL-2": ("R1", (), False), "BL-3": ("R2", (), False), "BL-4": ("R2", ("R3",), False), "BL-5": ("R2", ("R4",), False),
            "BL-6": ("R2", ("R3", "R4"), True)}
    for name, (p, conflict, r5) in want.items():
        rules, params = baselines.configure(name, RULES, PARAMS)
        assert (rules.p_provider, rules.conflict, rules.r5, params.r5_enabled) == (p, conflict, r5, r5)
        # Only the provider set changes; parameter values are the caller's.
        assert dataclasses.replace(rules, p_provider=RULES.p_provider, conflict=RULES.conflict, r5=RULES.r5) == RULES
    assert baselines.PRIMARY_COMPARISONS == (("BL-2", "BL-3"), ("BL-3", "BL-6"))


@pytest.mark.determinism
def test_bl1_deferred_to_m1b():
    with pytest.raises(ContractError) as err:
        baselines.configure("BL-1", RULES, PARAMS)
    assert err.value.code == "ERR-SPEC" and "M1b" in str(err.value)


@pytest.mark.determinism
def test_baselines_run_end_to_end_with_contact_cue_in_all():
    # Every BL-2..BL-6 configuration builds an S5 artifact on the same S4, and flag_series carries exactly the enabled
    # conflict providers (BL-2 and BL-3: none).
    s1, s4 = s4_moving(30, *HEAD_ON)
    for name in baselines.PROVIDERS:
        rules, params = baselines.configure(name, RULES, PARAMS)
        art = build_s5(s1, s4, s5_config(rules=rules, params=params))
        enabled = set(rules.conflict)
        assert all(set(r["C_by_provider"]) == enabled for r in art.tables["flag_series"])
