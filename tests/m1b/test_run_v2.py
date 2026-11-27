"""D-63 STEP 5 (T-29p): the v2 partition runner's pure functions, on hand-made inputs (expected values by hand)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/v2"))
import run_v2 as rv  # noqa: E402

FREEZE = json.loads((ROOT / "docs/preregistration/freeze_record_v2.json").read_text())


def test_expected_configs_are_the_freeze_record_values():
    w = rv.expected_configs(FREEZE)
    # typed from docs/preregistration_v2_FROZEN.md section 9a and the freeze record (tracker, substrate_and_rules)
    assert w["sbc"] == "sbc_5h5zcuzay643ohdiqy6bztul4k" and w["gcf_truth"] == "gcf_x3qktt7qr753qhjs5htbjxf7yi"
    assert w["gcf_t24"] == "gcf_pgkjo23uoswvk6giolanpq7sor"
    assert w["trc"] == "trc_osh5tvmgyy5yqov7jvvel6dfu2" and w["trc_stitched"] == "trc_y7gue6tdqawqd2ejqry72nhumz"
    assert w["rcf"]["BL-6"] == "rcf_2bvkpre4wpwznfytxy7lersh6f" and w["s2"] == ["inf_cetfxtbdg72cqgfm6teibcxsyd", "mdl_ty3jrnwz5jjdv56nwtkcos4yqs"]


def test_config_mismatches():
    w = rv.expected_configs(FREEZE)
    same = {**{k: v for k, v in w.items() if k != "rcf"}, "rcf": {"BL-2": w["rcf"]["BL-2"], "BL-6": w["rcf"]["BL-6"]}}
    assert rv.config_mismatches(same, w) == []
    assert rv.config_mismatches({**same, "trc": "trc_x"}, w) == ["trc"]
    assert rv.config_mismatches({**same, "rcf": {"BL-6": "rcf_x"}}, w) == ["rcf BL-6"]


def test_partition_guard_refuses_test():
    with pytest.raises(SystemExit, match="test waits for D-63 STEP 7"):
        rv.partition_dir("test")
    assert rv.partition_dir("reporting") == rv.OUT / "run" / "reporting"
    assert rv.partition_dir("dev") == rv.OUT / "dev"


def ev(i, labels, n=1, a=("p", "f"), b=("p", "f")):
    return {"id": i, "labels": frozenset(labels), "n_members": n, "pair": {"a": a, "b": b}}


def test_ie_share_and_single_member_check():
    events = [ev("e1", {"O", "IE"}), ev("e2", {"O"}), ev("e3", {"H", "IE"})]
    assert rv.ie_share(events) == {"events": 3, "ie_events": 2}  # 2 of 3 carry IE
    rv.check_single_member(events)
    with pytest.raises(SystemExit, match="1 events"):
        rv.check_single_member(events + [ev("e4", {"O"}, n=2)])
    with pytest.raises(SystemExit):
        rv.check_single_member([ev("e5", {"O"}, b=None)])


def test_flag_counts():
    s5 = {"episode": [{"borderline_flags": ["speed_near_v_min"]}, {"borderline_flags": ["speed_near_v_min", "onset_sensitive"]},
                      {"borderline_flags": []}, {"borderline_flags": None}]}
    assert rv.flag_counts(s5) == {"episodes": 4, "speed_near_v_min": 2, "clearance_within_k_sigma": 0, "onset_sensitive": 1,
                                  "footprint_orientation_unknown": 0}


def test_position_and_speed_rows():
    truth = {("k1", 10): ("k1", "person", 10, 1.0, 2.0), ("k2", 10): ("k2", "forklift", 10, 5.0, 5.0)}
    states = [{"track_id": "t1", "frame_index": 10, "x_m": 1.3, "y_m": 1.6, "x_m_null_reason": None, "evidence_class": "detected", "speed_mps": 1.2},
              {"track_id": "t2", "frame_index": 10, "x_m": None, "y_m": None, "x_m_null_reason": "out_of_frame", "evidence_class": "detected", "speed_mps": None},
              {"track_id": "t3", "frame_index": 10, "x_m": 9.0, "y_m": 9.0, "x_m_null_reason": None, "evidence_class": "detected", "speed_mps": 0.5}]
    ident = {"t1": "k1", "t2": "k2"}
    rows, avail = rv.position_rows(states, lambda t, i: ident.get(t), truth, {"t1"})
    assert rows == [("person", "detected", pytest.approx(0.3), pytest.approx(-0.4))]  # 1.3 - 1.0, 1.6 - 2.0
    assert avail == {"forklift|null:out_of_frame": 1, "forklift|position_without_matched_identity": 1, "person|position": 1}
    sp = rv.speed_rows(states, lambda t, i: ident.get(t), {("k1", 10): 1.0}, {"k1": "person", "k2": "forklift"})
    assert sp == [("person", "detected", pytest.approx(0.2))]  # 1.2 - 1.0; t3 has no identity


def test_artifact_digest_is_order_free_and_hash_sensitive():
    a = {"A.S3": {"id": "art_a", "payload": "1"}, "C.S4": {"id": "art_b", "payload": "2"}}
    b = dict(reversed(list(a.items())))
    assert rv.artifact_digest(a) == rv.artifact_digest(b)
    assert rv.artifact_digest(a) != rv.artifact_digest({**a, "C.S4": {"id": "art_b", "payload": "3"}})


def test_references_of_uses_the_freeze_rin_derivation():
    from rq1.ids import core
    row = {"s5": "art_s5", "references": [{"person_key": "p", "forklift_key": "f", "start_frame": 3, "end_frame_excl": 9, "t_start_tl_s": 0.1,
                                           "t_end_tl_s": 0.3, "assessable": True, "lbl_O": False, "lbl_H": True, "lbl_PC": False},
                                          {"person_key": "p", "forklift_key": "f", "start_frame": 20, "end_frame_excl": 25, "t_start_tl_s": 0.7,
                                           "t_end_tl_s": 0.8, "assessable": False, "lbl_O": False, "lbl_H": False, "lbl_PC": False}]}
    refs, groups = rv.references_of(row, "rec_x")
    rid = core.make_id("rin", {"rec_id": "rec_x", "person": "p", "forklift": "f", "start_frame": 3, "end_frame_excl": 9, "reference_s5": "art_s5"})
    assert refs[0].ref_event_id == rid and groups[rid] == frozenset({"G1"})
    assert groups[refs[1].ref_event_id] == frozenset() and refs[1].assessable is False


def test_gv04_at_simulator_positions_by_hand():
    # D-40 item 4: person (0, 0), forklift centre (5, 0), unknown yaw -> circumscribed discs (T8.2).
    # prior 3.03 x 1.13: r = 0.5 * sqrt(9.1809 + 1.2769) = 0.5 * 3.233852 = 1.616926; clearance 5 - 1.616926 - 0.30 = 3.083074
    # box 2.00 x 1.00:   r = 0.5 * sqrt(5) = 1.118034;                clearance 5 - 1.118034 - 0.30 = 3.581966
    # difference = 3.083074 - 3.581966 = -0.498892
    truth = {("p", 7): ("p", "person", 7, 0.0, 0.0, None, None, None), ("f", 7): ("f", "forklift", 7, 5.0, 0.0, None, 2.0, 1.0)}
    trk = {"tp": "p", "tf": "f"}
    series = [{"pow_nk": ["tp", "tf", 0], "frame_index": 7, "clearance_state": "measured", "clearance_m": 3.0830584, "evidence_class": "detected"},
              {"pow_nk": ["tp", "tf", 0], "frame_index": 8, "clearance_state": "unknown", "clearance_m": None, "evidence_class": "detected"}]
    rows, check = rv.gv04_rows(series, truth, trk, 0.30, (3.03, 1.13))
    assert len(rows) == 1 and rows[0][:2] == ("2.00x1.00", "detected") and rows[0][2] == pytest.approx(-0.498892, abs=1e-6)
    assert check == [1, 1]  # the stored 3.0830584 differs from the recomputed 3.083074 by more than 1e-9


def test_m_input_check_counts_missing_m_where_both_states_exist():
    # unit "sP" = track tp on frames 0-3; unit "sF" = track ta on frames 0-1, tb on frames 2-3 (stitched)
    member = {("sP", i): "tp" for i in range(4)} | {("sF", 0): "ta", ("sF", 1): "ta", ("sF", 2): "tb", ("sF", 3): "tb"}
    st = lambda trk, i, sp=1.0: {"track_id": trk, "frame_index": i, "speed_mps": sp}
    s4 = {"object_state": [st("tp", i) for i in range(4)] + [st("ta", 0), st("ta", 1), st("tb", 2), st("tb", 3, None)],
          "pow": [{"person_track_id": "sP", "forklift_track_id": "sF", "start_frame": 0, "pow_id": "pow_1"}],
          "pair_series": [{"pow_nk": ["sP", "sF", 0], "frame_index": i} for i in range(4)]}
    s5 = {"flag_series": [{"pow_id": "pow_1", "frame_index": i, "M": m} for i, m in enumerate((1, 2, 0, 2))]}
    got = rv.m_input_check(s4, s5, lambda u, f: member.get((u, f)))
    # frame 3: forklift speed null -> not counted; frames 0-2 counted; frame 1 has M unknown -> 1 of 3 missing
    assert got == {"pair_frames_with_both_states": 3, "m_missing": 1, "share_missing": pytest.approx(1 / 3)}
    assert rv.M_MISSING_MAX == 0.05
