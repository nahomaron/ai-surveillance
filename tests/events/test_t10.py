"""Appendix T T10 (contract E-1.2.8; D-10, D-11) at S5, and the S5 artifact (CT-FK-02, CT-FK-04, CT-I-07).
Expected values are T10 checks, Appendix N values, or hand calculations written beside each assertion."""
import dataclasses
import json
import random
from pathlib import Path

import pytest

from rq1.events import candidates, engine, labels, providers, s5
from rq1.events.engine import FrameFlags, Rates
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema import validate, vr_rules
from rq1.substrate import builder, oracle

from test_engine_part_a import FORK, PARAMS, PERSON, RULES, run_n1

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
OFF = dataclasses.replace(PARAMS, r5_enabled=False)
TOL = 1e-9
US = 1e-6
BANDS = {"bsc_" + "a" * 26: [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]}


def frame(i, **kw):
    base = dict(P=1, M=1, C_by={"R3": 0}, E=0, Q=1, clearance=1.0, sigma=0.05, overlap=0, image_gap_norm=0.5)
    base.update(kw)
    return FrameFlags(i, i / 10, 0.1, **base)


# --- an S4 built from N2-style positions, with optional lost / predicted / unpositioned person frames -----------------

def s4_custom(n, person_xy, fork_x, person_states=None, no_person_position=()):
    ps = person_states or {}
    positions = {**{(1, i): {"xy": person_xy, "cov": [0.0025, 0.0, 0.0025]} for i in range(n) if i not in no_person_position},
                 **{(2, i): {"xy": [fork_x(i / 10), 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(n)}}
    s1 = synthetic_s1.build(n)
    truth = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [100.0, 100.0, 140.0, 200.0], "state": ps.get(i, "tracked")}
                                                          for i in range(n) if ps.get(i) != "missing"]},
             {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"} for i in range(n)]}]
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.8", "f", "f", ("orc_" + "a" * 26,), (), {}))
    cfg = builder.SubstrateConfig(15, 0.3, 0.5, 2.0, {"forklift"}, {"person": PERSON, "forklift": FORK}, {"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                  BANDS, 0.5)
    s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, Spec("S4", "E-1.2.8", "f", "f", ("gcf_" + "a" * 26, s5.substrate_config_id(SUBSTRATE)), (s3.artifact_id,), {}))
    return s1, s4


G = {"N2-G1": ((0.0, 1.90), lambda t: 0.0, 50), "N2-G2": ((0.0, 1.90), lambda t: -2.5 + t, 50), "N2-G3": ((5.0, 0.0), lambda t: 1.5 * t, 10)}


def s4_of(name, **kw):
    xy, fx, n = G[name]
    return s4_custom(n, list(xy), fx, **kw)


# The substrate_config record (section 5.2) S4 is built with in these tests; TEST-ONLY values (Package F section 3).
SUBSTRATE = {"g_max": 15, "pair_classes": ["forklift"], "v_min": 0.3, "k_sup": 1.5, "motion_models": ["constant_velocity"],
             "prediction_horizon_s": 2.0, "version_label": "TEST-ONLY", "version_label_null_reason": None}


def s5_config(rules=RULES, params=PARAMS, substrate=None):
    return s5.S5Config(rules, params, substrate or SUBSTRATE, "bsc_" + "a" * 26, version_label="TEST-ONLY")


def build_s5(s1, s4, cfg=None):
    cfg = cfg or s5_config()
    return s5.build(s1, s4, cfg, Spec("S5", "E-1.2.8", "f", "f", (s5.config_id(cfg),), (s4.artifact_id,), {}))


# --- CT-T10-01: contact-state order (T10.1) ------------------------------------------------------------------------

@pytest.mark.determinism
@pytest.mark.parametrize("row", [f"T{i}" for i in range(1, 12)])
def test_ct_t10_01_n1_contact_states(row):
    # T10.1 checks: T6, T8 undetermined; T7, T9 suspected; T10 undetermined; T11 not_assessable; T1-T5 none_observed.
    want = {"T6": "undetermined", "T8": "undetermined", "T7": "suspected", "T9": "suspected", "T10": "undetermined", "T11": "not_assessable"}.get(row, "none_observed")
    (episodes, _), expected = run_n1(row)
    assert episodes[0]["contact_state"] == expected["contact_state"] == want


def test_ct_t10_01_order():
    cs = labels.contact_state
    assert cs(True, True, False, 1, 1, -0.1, 0.05, 2.0) == "undetermined"  # step 2 (Q insufficient at CA) before step 3
    assert cs(True, True, True, 1, 1, -0.1, 0.05, 2.0) == "suspected"  # step 3
    assert cs(True, True, True, 2, 1, 0.5, 0.05, 2.0) == "undetermined"  # step 4: overlap unknown, even with a cue
    assert cs(True, True, True, 0, 0, None, None, 2.0) == "undetermined"  # step 4: clearance at CA null (new in T10.1)
    assert cs(True, True, True, 0, 0, 0.08, 0.05, 2.0) == "undetermined"  # step 4: 0.08 <= 2 x 0.05
    assert cs(True, True, True, 0, 0, 0.11, 0.05, 2.0) == "none_observed"  # step 5: 0.11 - 0.10 > 0
    assert cs(True, True, True, 0, 0, 0.01, None, 2.0) == "none_observed"  # sigma null uses 0
    assert cs(True, False, True, 1, 1, -0.1, 0.05, 2.0) == "not_assessable"  # step 1


# --- CT-T10-04: E on insufficient frames (T10.3(b)) ------------------------------------------------------------------

@pytest.mark.determinism
def test_ct_t10_04_e_unknown_on_a_lost_frame():
    s1, s4 = s4_of("N2-G2", person_states={10: "lost"})
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    assert flags[10].evidence_class == "insufficient" and flags[10].E == 2
    assert {f.E for f in flags if f.frame_index != 10} == {0}  # static person, constant forklift speed: no criterion is true
    (ep,), _ = engine.run_pow(flags, PARAMS)
    assert ep["E_ep"] == 2  # no true frame in I+, one unknown frame
    off = providers.flag_frames(s4.tables, dataclasses.replace(RULES, r5=False), s1["frame"], s1["coverage_segment"])
    assert {f.E for f in off} == {0}  # R5 disabled: E = 0 on every frame, the lost one included


def test_ct_t10_04_e_ep_true_if_any_true_frame_in_i_plus():
    frames = [frame(i, E=2 if i == 3 else (1 if i == 7 else 0)) for i in range(10)]
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["E_ep"] == 1


# --- CT-T10-05: the cue when R5 is disabled (T10.3(c)) ---------------------------------------------------------------

@pytest.mark.determinism
def test_ct_t10_05_cue_computed_with_r5_disabled():
    frames = [frame(i, clearance=-0.10, overlap=1, rates=Rates(0.0, 3.5, None, True)) for i in range(10)]
    (ep,), _ = engine.run_pow(frames, OFF)
    assert (ep["contact_state"], ep["lbl_CT"], ep["e_assessed"]) == ("suspected", True, False)  # decel 3.5 > k_c 3.0
    frames = [frame(i, clearance=-0.10, overlap=1, rates=None) for i in range(10)]  # null kinematics: cue unknown
    (ep,), _ = engine.run_pow(frames, OFF)
    assert ep["contact_state"] == "undetermined"
    s1, s4 = s4_of("N2-G2")
    off = providers.flag_frames(s4.tables, dataclasses.replace(RULES, r5=False), s1["frame"], s1["coverage_segment"])
    assert all(f.rates is not None for f in off)  # the rates are computed whether or not R5 is enabled


# --- CT-T10-06: borderline_flags (T10.4), on hand-built S4 tables ----------------------------------------------------

def synthetic_s4(n=20, pair=None, fork=None):
    """Minimal S4 tables. Baseline per frame: clearance 1.5 m (sigma 0.05), image gap 0.02, prediction 1.5 m (sigma null),
    forklift speed 1.0 (sigma 0), person static. Baseline sets no borderline flag: |1.5-2.0|, |0.02-0.05|, |1.5-1.0|,
    |minclr 1.5-0.5|, |1.5| at CA and |1.0-0.3| all exceed k_sigma x sigma (0.10, or 0 where sigma is null)."""
    pair, fork = pair or {}, fork or {}
    frames = [{"frame_index": i, "eligible": True, "t_tl_s": i / 10, "t_resolved_s": i / 10, "support_start_tl_s": i / 10, "support_s": 0.1,
               "recording_id": "rec_x"} for i in range(n)]
    coverage = [{"recording_id": "rec_x", "timeline_id": "tl_x", "camera_id": "cam_x", "coverage_state": "usable", "t_start_tl_s": 0.0, "t_end_tl_s": n / 10}]
    obj = lambda track, i, speed, sigma: {"track_id": track, "frame_index": i, "x_m": 0.0, "evidence_class": "detected", "evidence_state": "visible",
                                          "speed_mps": speed, "speed_sigma_mps": sigma, "heading_rad": 0.0 if speed >= 0.3 else None}
    objects = [obj("trk_p", i, 0.0, 0.0) for i in range(n)]
    objects += [obj("trk_f", i, *fork.get(i, (1.0, 0.0))) for i in range(n)]
    rows = []
    for i in range(n):
        row = {"pow_nk": ["trk_p", "trk_f", 0], "frame_index": i, "clearance_m": 1.5, "clearance_sigma_m": 0.05, "clearance_sigma_m_null_reason": None,
               "clearance_state": "measured", "footprint_overlap": 0, "image_gap_norm": 0.02, "q_state": "sufficient", "evidence_class": "detected",
               "predicted": [{"motion_model_id": "constant_velocity", "horizon_s": 2.0, "pred_min_clearance_m": 1.5, "sigma_m": None}],
               "closing_rate_mps": 0.0, "ttca_s": None, "ttca_s_null_reason": "not_applicable", "borderline_flags": []}
        row.update(pair.get(i, {}))
        rows.append(row)
    s4 = {"pow": [{"person_track_id": "trk_p", "forklift_track_id": "trk_f", "start_frame": 0}], "object_state": objects, "pair_series": rows}
    return s4, frames, coverage


def flags_for(pair=None, fork=None, rules=RULES):
    s4, frames, coverage = synthetic_s4(pair=pair, fork=fork)
    episodes, _ = engine.run_pow(providers.flag_frames(s4, rules, frames, coverage), PARAMS)
    return episodes[0]["borderline_flags"]


R1 = dataclasses.replace(RULES, p_provider="R1")
CLR = "clearance_within_k_sigma"


@pytest.mark.determinism
def test_ct_t10_06_baseline_has_no_flag():
    assert flags_for() == [] and flags_for(rules=R1) == []


@pytest.mark.determinism
@pytest.mark.parametrize("rules,expected", [(RULES, [CLR]), (R1, [])])
def test_ct_t10_06_clearance_against_d_p(rules, expected):
    # Frame 5 clearance 1.95: |1.95 - 2.0| = 0.05 <= 2 x 0.05 = 0.10, so the R2 configuration sets the flag.
    # Appendix T T11.1 (E-1.2.9): the d_p bullet applies only if the P provider is R2, so the R1 configuration sets none.
    assert flags_for(pair={5: {"clearance_m": 1.95}}, rules=rules) == expected


@pytest.mark.determinism
def test_ct_t10_06_r1_image_gap_equality():
    # Frame 5 gap 0.05 = k_img: |0.05 - 0.05| <= 0. R1 configurations only; an R2 configuration ignores the image gap.
    assert flags_for(pair={5: {"image_gap_norm": 0.05}}, rules=R1) == [CLR]
    assert flags_for(pair={5: {"image_gap_norm": 0.05}}, rules=RULES) == []


@pytest.mark.determinism
def test_ct_t10_06_prediction_against_d_pc():
    pred = lambda v, s: {"predicted": [{"motion_model_id": "constant_velocity", "horizon_s": 2.0, "pred_min_clearance_m": v, "sigma_m": s}]}
    assert flags_for(pair={5: pred(1.0, None)}) == [CLR]  # |1.0 - 1.0| <= 0 (sigma null uses 0)
    assert flags_for(pair={5: pred(1.1, 0.05)}) == [CLR]  # |1.1 - 1.0| = 0.10 <= 2 x 0.05
    assert flags_for(pair={5: pred(1.2, 0.05)}) == []  # 0.20 > 0.10


@pytest.mark.determinism
def test_ct_t10_06_minclr_against_d_nm():
    # Frame 5 clearance 0.55 is the minimum: |0.55 - 0.5| = 0.05 <= 2 x 0.05. Nothing else is near: |0.55| at CA > 0.10.
    assert flags_for(pair={5: {"clearance_m": 0.55}}) == [CLR]


@pytest.mark.determinism
def test_ct_t10_06_clearance_at_ca():
    # Frame 5 clearance 0.08 is CA: |0.08| <= 2 x 0.05. minclr 0.08 vs d_nm: |0.08 - 0.5| = 0.42 > 0.10.
    assert flags_for(pair={5: {"clearance_m": 0.08}}) == [CLR]


@pytest.mark.determinism
@pytest.mark.parametrize("rules,expected", [(RULES, ["speed_near_v_min"]), (R1, [])])
def test_ct_t10_06_speed_near_v_min(rules, expected):
    # Frame 5 forklift speed 0.35, sigma 0.05: |0.35 - 0.3| = 0.05 <= 2 x 0.05 = 0.10, so the R2 configuration sets the flag.
    # Appendix T T11.1 (E-1.2.9): the v_min bullet applies only if R2 (the M provider) is enabled, so R1 sets none.
    assert flags_for(fork={5: (0.35, 0.05)}, rules=rules) == expected


@pytest.mark.determinism
def test_ct_t10_06_footprint_orientation_unknown():
    assert flags_for(pair={5: {"borderline_flags": ["footprint_orientation_unknown"]}}) == ["footprint_orientation_unknown"]


@pytest.mark.determinism
def test_ct_t10_06_onset_sensitive():
    # Opening frame 0 has clearance 1.95: borderline for P (R2), so onset_sensitive as well (T9.8).
    assert flags_for(pair={0: {"clearance_m": 1.95}}) == [CLR, "onset_sensitive"]


@pytest.mark.determinism
def test_ct_t10_06_borderline_in_i_plus_outside_i_sets_no_flag():
    # Frames 10-19 have clearance 2.5 (P = 0; prediction 1.5 >= d_pc, so C = 0): I = [0, 10), I+ = [0, 20).
    # Frame 11 clearance 2.05 (|2.05 - 2.0| <= 0.10) and frame 12 speed 0.35 (sigma 0.05) are borderline but outside I.
    pair = {i: {"clearance_m": 2.5} for i in range(10, 20)}
    pair[11] = {"clearance_m": 2.05}
    s4, frames, coverage = synthetic_s4(pair=pair, fork={12: (0.35, 0.05)})
    (ep,), _ = engine.run_pow(providers.flag_frames(s4, RULES, frames, coverage), PARAMS)
    assert (ep["end_frame_excl"], ep["attr_end_frame_excl"], ep["borderline_flags"]) == (10, 20, [])


@pytest.mark.determinism
def test_ct_t10_06_borderline_flags_never_change_labels():
    s4, frames, coverage = synthetic_s4()
    base = engine.run_pow(providers.flag_frames(s4, RULES, frames, coverage), PARAMS)[0][0]
    s4, frames, coverage = synthetic_s4(pair={5: {"clearance_m": 1.95, "borderline_flags": ["footprint_orientation_unknown"]}}, fork={5: (1.0, 0.0)})
    flagged = engine.run_pow(providers.flag_frames(s4, RULES, frames, coverage), PARAMS)[0][0]
    keys = [k for k in base if k.startswith("lbl_")] + ["summary_label", "review_route", "contact_state", "K"]
    assert [base[k] for k in keys] == [flagged[k] for k in keys] and flagged["borderline_flags"] != base["borderline_flags"]


# --- CT-T10-07: exposure fields (T10.5) ------------------------------------------------------------------------------

def episodes_of(name, **kw):
    s1, s4 = s4_of(name, **kw)
    return build_s5(s1, s4).tables["episode"]


@pytest.mark.determinism
def test_ct_t10_07_g1():
    (ep,) = episodes_of("N2-G1")
    assert ep["support_detected_frac"] == pytest.approx(1.0, abs=TOL)
    assert ep["exp_speed_at_ca_mps"] == pytest.approx(0.0, abs=TOL)
    assert ep["exp_closing_rate_max_mps"] == pytest.approx(0.0, abs=TOL)
    assert (ep["exp_ttca_min_s"], ep["exp_ttca_min_s_null_reason"]) == (None, "not_applicable")
    # Hand: clearance 1.10 lies in band [1, 2) (index 3); 50 frames x 0.1 s = 5.0 s; both objects visible on every frame.
    assert ep["exp_t_in_band_detected_s"] == pytest.approx([0.0, 0.0, 0.0, 5.0, 0.0, 0.0], abs=US)
    assert ep["exp_t_clearance_unknown_s"] == 0.0 and ep["exp_visible_frac"] == pytest.approx(1.0, abs=TOL)


@pytest.mark.determinism
def test_ct_t10_07_g2():
    (ep,) = episodes_of("N2-G2")
    assert ep["exp_speed_at_ca_mps"] == pytest.approx(1.0, abs=TOL)  # CA = the earliest frame of minimum clearance
    assert ep["closest_approach_frame"] == min(f for f in range(50) if abs(-2.5 + f / 10) <= 1.0)  # frame 15, x = -1.0
    assert ep["exp_t_in_band_detected_s"] == pytest.approx([0.0, 0.0, 0.0, 5.0, 0.0, 0.0], abs=US)  # 1.10 to 1.7518, all in [1, 2)


@pytest.mark.determinism
def test_ct_t10_07_g3():
    (ep,) = episodes_of("N2-G3")
    assert ep["exp_closing_rate_max_mps"] == pytest.approx(1.5, abs=TOL)
    assert ep["exp_t_in_band_detected_s"] == pytest.approx([0.0, 0.0, 0.0, 0.0, 1.0, 0.0], abs=US)  # 2.35 to 3.70, all in [2, 4)


@pytest.mark.determinism
def test_ct_t10_07_mixed_evidence_classes():
    # G2 with person predicted on frames 20-24 (inferred, positions given), lost on frame 30 (insufficient) and without a
    # position on frame 35 (detected, clearance not measured). Hand: inferred 0.5 s, insufficient 0.1 s,
    # clearance unknown 0.1 s (frame 35 only; frame 30 is insufficient), detected in band 5.0 - 0.5 - 0.1 - 0.1 = 4.3 s.
    (ep,) = episodes_of("N2-G2", person_states={**{i: "predicted" for i in range(20, 25)}, 30: "lost"}, no_person_position=(35,))
    assert (ep["start_frame"], ep["end_frame_excl"]) == (0, 50)
    assert ep["duration_inferred_s"] == pytest.approx(0.5, abs=US) and ep["duration_insufficient_s"] == pytest.approx(0.1, abs=US)
    assert ep["exp_t_clearance_unknown_s"] == pytest.approx(0.1, abs=US)
    assert sum(ep["exp_t_in_band_detected_s"]) == pytest.approx(4.3, abs=US) and sum(ep["exp_t_in_band_inferred_s"]) == pytest.approx(0.5, abs=US)
    assert ep["support_detected_frac"] == pytest.approx(4.4 / 5.0, abs=TOL)
    # Frames 20-24 (person occluded_predicted) and 30 (lost) are not jointly visible: (5.0 - 0.6) / 5.0.
    assert ep["exp_visible_frac"] == pytest.approx(4.4 / 5.0, abs=TOL)


CONSISTENCY_CASES = [("N2-G1", {}), ("N2-G2", {}), ("N2-G3", {}),
                     ("N2-G2", {"person_states": {**{i: "predicted" for i in range(20, 25)}, 30: "lost"}, "no_person_position": (35,)}),
                     ("N2-G1", {"person_states": {i: "predicted" for i in range(5, 12)}, "no_person_position": (40, 41)})]


@pytest.mark.determinism
@pytest.mark.parametrize("name,kw", CONSISTENCY_CASES)
def test_ct_t10_07_consistency_sum(name, kw):
    # T10.5: sum(in band, detected) + detected clearance-unknown support = detected support of I (1 us), likewise inferred.
    # The class split of the clearance-unknown support is recomputed here from flag inputs, independently of the engine.
    s1, s4 = s4_of(name, **kw)
    built = build_s5(s1, s4)
    pair = {r["frame_index"]: r for r in s4.tables["pair_series"]}
    support = {f["frame_index"]: f["support_s"] for f in s1["frame"]}
    for ep in built.tables["episode"]:
        inside = range(ep["start_frame"], ep["end_frame_excl"])
        for cls in ("detected", "inferred"):
            unknown = sum(support[i] for i in inside if pair[i]["evidence_class"] == cls and pair[i]["clearance_state"] != "measured")
            total = sum(support[i] for i in inside if pair[i]["evidence_class"] == cls)
            assert sum(ep[f"exp_t_in_band_{cls}_s"]) + unknown == pytest.approx(total, abs=US)
            assert ep[f"duration_{cls}_s"] == pytest.approx(total, abs=US)


# --- CT-T10-08: event counts (T10.6) ---------------------------------------------------------------------------------

@pytest.mark.determinism
def test_ct_t10_08_g1_counts():
    s1, s4 = s4_of("N2-G1")
    counts = build_s5(s1, s4).tables["event_count_summary"]
    assert len(counts) == 2 * 3 * 8  # recording and timeline scopes, three scenarios, eight labels, zeros written
    rec = [c for c in counts if c["scope_type"] == "recording"]
    for scenario in candidates.SCENARIOS:
        got = {c["label"]: c["n_events"] for c in rec if c["scenario"] == scenario}
        assert got == {"all": 1, "O": 1, "H": 0, "PC": 0, "NM": 0, "UD": 0, "CT": 0, "IE": 0}  # T10.6 check
    assert all(c["n_ambiguous_groups"] == 0 and c["n_unresolved_identity_episodes"] == 0 for c in counts)


@pytest.mark.determinism
def test_ct_t10_08_overlapping_labels():
    # Appendix N1 T5 gives one episode labelled H and NM: counted under all, H and NM; the counts overlap.
    (episodes, _), expected = run_n1("T5")
    assert expected["labels"] == ["H", "NM"]
    eps = [{**ep, "pow_id": "pow_" + "a" * 26, "camera_id": "cam_x", "recording_id": "rec_x", "timeline_id": "tl_x"} for ep in episodes]
    counts = candidates.count_summaries(candidates.candidate_events(eps), eps, [("recording", "rec_x")])
    got = {c["label"]: c["n_events"] for c in counts if c["scenario"] == "S_VIEW"}
    assert got == {"all": 1, "O": 0, "H": 1, "PC": 0, "NM": 1, "UD": 0, "CT": 0, "IE": 0}


# --- S5 artifact ------------------------------------------------------------------------------------------------------

@pytest.mark.determinism
def test_s5_artifact_tables_and_rule_configuration():
    s1, s4 = s4_of("N2-G3")
    built = build_s5(s1, s4)
    assert {k: len(v) for k, v in built.tables.items()} == {"flag_series": 10, "episode": 1, "discarded_episode": 0, "candidate_event": 3, "event_count_summary": 48}
    ep = built.tables["episode"][0]
    assert ep["ep_id"].startswith("ep_") and ep["pow_id"] == s4.tables["pow"][0]["pow_id"]
    assert (ep["attr_end_frame_excl"], ep["e_assessed"], ep["ca_observed"]) == (10, True, True)
    assert all(e["member_episode_ids"] == [ep["ep_id"]] for e in built.tables["candidate_event"])
    assert validate.validate_row("rule_configuration", s5.rule_configuration(s5_config())) == []
    assert vr_rules.check_episode_labels(ep) == [] and all(vr_rules.check_event_labels(e) == [] for e in built.tables["candidate_event"])


@pytest.mark.determinism
def test_s5_discarded_episode_and_continuation():
    # Person missing on frames 10-25 (16 > g_max 15): two POWs, the second with continuation_of (T8.1). G1 has P = 1
    # throughout, so the first episode runs to the end of POW 1 and the second starts at POW 2: they are linked (step 6).
    s1, s4 = s4_of("N2-G1", person_states={i: "missing" for i in range(10, 26)})
    built = build_s5(s1, s4)
    pows = sorted(s4.tables["pow"], key=lambda p: p["start_frame"])
    eps = sorted(built.tables["episode"], key=lambda e: e["start_frame"])
    assert len(pows) == 2 and len(eps) == 2
    assert eps[0]["continuation_of_nk"] is None and eps[0]["continuation_of_nk_null_reason"] == "not_applicable"
    assert eps[1]["continuation_of_nk"] == [pows[0]["pow_id"], 0] and eps[1]["continuation_of_id"] == eps[0]["ep_id"]


@pytest.mark.determinism
def test_s5_discarded_rows():
    # Clearance 1.5 (P = 1) on frame 0 only, 2.5 (P = 0) afterwards: the episode [0, 1) spans 0.1 s < t_min 0.2 s (N1 T13 pattern).
    s4, frames, coverage = synthetic_s4(pair={i: {"clearance_m": 2.5} for i in range(1, 20)})
    episodes, discarded = engine.run_pow(providers.flag_frames(s4, RULES, frames, coverage), PARAMS)
    assert episodes == [] and discarded == [{"start_frame": 0, "end_frame_excl": 1, "span_s": pytest.approx(0.1), "discard_reason": "shorter_than_t_min"}]


@pytest.mark.determinism
def test_ct_fk_04_exact_rerun():
    s1, s4 = s4_of("N2-G2")
    a, b = build_s5(s1, s4), build_s5(s1, s4)
    assert (a.artifact_id, a.payload_sha256) == (b.artifact_id, b.payload_sha256) and a.tables == b.tables


@pytest.mark.determinism
@pytest.mark.parametrize("seed", range(3))
def test_ct_fk_02_shuffled_inputs_give_identical_ids(seed):
    rng = random.Random(seed)
    s1, s4 = s4_of("N2-G1", person_states={i: "missing" for i in range(10, 26)})
    base = build_s5(s1, s4)
    shuffle = lambda rows: rng.sample(rows, len(rows))
    s1b = {k: shuffle(v) for k, v in s1.items()}
    s4b = dataclasses.replace(s4, tables={k: shuffle(v) for k, v in s4.tables.items()})
    again = build_s5(s1b, s4b)
    assert again.artifact_id == base.artifact_id and again.tables == base.tables  # every derived ID column identical


@pytest.mark.determinism
def test_ct_i_07_rule_change():
    s1, s4 = s4_of("N2-G2")
    _, s4_again = s4_of("N2-G2")
    a = build_s5(s1, s4)
    changed = s5_config(rules=dataclasses.replace(RULES, d_p=1.5))
    b = build_s5(s1, s4, changed)
    assert s4_again.artifact_id == s4.artifact_id  # substrate art_ unchanged
    assert s5.config_id(changed) != s5.config_id(s5_config()) and a.artifact_id != b.artifact_id
    assert not {e["ep_id"] for e in a.tables["episode"]} & {e["ep_id"] for e in b.tables["episode"]}  # S5 IDs new


@pytest.mark.determinism
def test_ar_40_item_3_configuration_id_covers_parameters_of_disabled_providers():
    # An R1-only configuration still reads d_p, v_min and d_pc for T10.4 flags, so they must change the configuration ID.
    r1 = dataclasses.replace(RULES, p_provider="R1")
    record = s5.rule_configuration(s5_config(rules=r1))
    assert [(p["provider_id"], p["enabled"]) for p in record["providers"]] == [("R1", True), ("R2", False), ("R3", True), ("R5", True)]
    assert s5.config_id(s5_config(rules=r1)) != s5.config_id(s5_config(rules=dataclasses.replace(r1, d_p=1.5)))
    assert validate.validate_row("rule_configuration", record) == []
