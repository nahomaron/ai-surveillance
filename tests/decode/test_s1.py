"""T-06: S1 decode, support and coverage. Expected values come from Appendix N3, Appendix T (CT-T, T7) or the hand
calculations written next to them. Fixtures declare delta_nom = 0.033 s (T7) unless a test says otherwise."""
import json
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rq1.decode import stage, timestamps, timeline_rules
from rq1.decode.timestamps import DecodeConfig, PacketRecord
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.schema import vr_rules
from rq1.schema.errors import ContractError

TOL = 1e-9
CAM = core.anchor_id("cam", "camera", ["c"])
DCF = "dcf_" + "a" * 26


def rec(name):
    return core.anchor_id("rec", "recording", [name])


def cfg(declared=None, final="delta_nom", f_untimed=0.05):
    return DecodeConfig(k_sup=1.5, f_untimed=f_untimed, f_sub=0.10, rules_version="rv1",
                        declared={k: v for k, v in (declared or {}).items()}, final_frame_support=final)


def local(name):
    return {"tl_id": core.anchor_id("tl", "timeline", ["recording_local", rec(name)]), "kind": "recording_local", "extent_start_tl_s": None, "extent_end_tl_s": None}


def spec():
    return Spec("S1", "E-1.2.4", "fixture", "fixture", (DCF,), (), {})


# AR-28: Cases B and C have 1 untimed frame in 4 (25%), so section 3.2 would reject them at the CT-T-08 test value 0.05.
FIXTURE_F_UNTIMED = {"fx_clip_b": 0.5, "fx_clip_c": 0.5}


def run(clip_dir, name, declared=0.033, final="delta_nom", f_untimed=None):
    r = rec(name)
    item = stage.S1Input(recording_id=r, camera_id=CAM, path=clip_dir / f"{name}.mkv", faults_path=clip_dir / f"{name}.faults.json")
    config = cfg({r: declared} if declared is not None else {}, final, f_untimed or FIXTURE_F_UNTIMED.get(name, 0.05))
    return stage.run_s1(local(name), [item], config, spec())


def segments(built):
    rows = sorted(built.tables["coverage_segment"], key=lambda s: s["t_start_tl_s"])
    return [(round(s["t_start_tl_s"], 9), round(s["t_end_tl_s"], 9), s["coverage_state"], s["unusable_reasons"]) for s in rows]


def usable(built):
    return sum(s["support_s"] for s in built.tables["coverage_segment"] if s["coverage_state"] in ("usable", "usable_degraded"))


def summary(built):
    return built.tables["decode_summary"][0]


def frames(built):
    return sorted(built.tables["frame"], key=lambda f: f["decode_seq"])


# CT-T-14 to 17 (frame and coverage parts) and CT-T-21: Appendix N3 values with declared delta_nom.
def test_case_a(clip_dir):
    built = run(clip_dir, "fx_clip_a")
    assert segments(built) == [(0.0, 0.033, "usable", []), (0.033, 0.066, "unusable", ["decode_error", "excluded_frame"]), (0.066, 0.133, "usable", [])]
    assert usable(built) == pytest.approx(0.100, abs=TOL)
    f1 = frames(built)[1]
    assert (f1["decode_ok"], f1["eligible"], f1["support_status"], f1["frame_index"]) == (False, False, "excluded_own_support", None)
    assert f1["support_s"] == pytest.approx(0.033, abs=TOL)


def test_case_b(clip_dir):
    built = run(clip_dir, "fx_clip_b")
    assert segments(built) == [(0.0, 0.066, "unusable", ["untimed_frame"]), (0.066, 0.133, "usable", [])]
    assert usable(built) == pytest.approx(0.067, abs=TOL)
    states = [(f["ts_status"], f["support_status"]) for f in frames(built)]
    assert states[0] == ("ok", "timing_uncertain") and states[1] == ("untimed", "zero_untimed")


def test_case_c(clip_dir):
    built = run(clip_dir, "fx_clip_c")
    assert summary(built)["reorder_depth"] == 2
    assert segments(built) == [(0.0, 0.1, "unusable", ["untimed_frame"]), (0.1, 0.133, "usable", [])]
    assert usable(built) == pytest.approx(0.033, abs=TOL)


def test_case_d(clip_dir):
    built = run(clip_dir, "fx_clip_d")
    assert segments(built) == [(0.0, 0.033, "usable", []), (0.033, 0.066, "usable_degraded", ["timing_substituted"]), (0.066, 0.133, "usable", [])]
    assert usable(built) == pytest.approx(0.133, abs=TOL)
    assert summary(built)["substituted_support_frac"] == pytest.approx(0.033 / 0.133, abs=TOL)
    f1 = frames(built)[1]
    assert (f1["ts_source"], f1["ts_status"], f1["support_status"]) == ("dts_derived", "substituted", "substituted")


def test_ct_t_21_declared_source_recorded(clip_dir):
    s = summary(run(clip_dir, "fx_clip_a"))
    assert (s["delta_nom_s"], s["delta_nom_source"], s["delta_nom_declared_s"]) == (0.033, "declared_config", 0.033)
    assert s["delta_nom_median_s"] == pytest.approx(0.033, abs=TOL)  # T7.1 check value for Case A


def test_ct_t_22_case_b_without_declaration(clip_dir):
    built = run(clip_dir, "fx_clip_b", declared=None)
    s = summary(built)
    assert s["delta_nom_s"] == pytest.approx(0.034, abs=TOL) and s["delta_nom_source"] == "median_adjacent_pairs"
    assert s["delta_nom_declared_s"] is None and s["delta_nom_declared_s_null_reason"] == "not_supplied"
    assert usable(built) == pytest.approx(0.068, abs=TOL)
    assert segments(built)[0] == (0.0, 0.066, "unusable", ["untimed_frame"])


def _packets(n, dts_only=(), step=33):
    return [PacketRecord(index=i, seq=i, pts=None if i in dts_only else i * step, dts=i * step, decode_ok=True) for i in range(n)]


def _resolve(packets, declared=Fraction(33, 1000), **kw):
    return timestamps.resolve(packets, Fraction(1, 1000), cfg(**kw), declared)


def test_ct_t_23_at_or_below_f_sub_no_degradation():
    result = _resolve(_packets(20, dts_only={5}))
    assert result.substituted_frac == pytest.approx(0.033 / 0.66, abs=TOL)  # 0.05 <= 0.10
    assert not [p for p in result.pieces if p.state == "usable_degraded"]


def test_ct_t_23_above_f_sub_exactly_substituted_frames_degrade():
    plain = _resolve(_packets(20))
    result = _resolve(_packets(20, dts_only={5, 9, 13}))
    assert result.substituted_frac == pytest.approx(0.099 / 0.66, abs=TOL)  # 0.15 > 0.10
    degraded = [x for p in sorted(result.pieces, key=lambda p: p.start) if p.state == "usable_degraded" for x in (float(p.start), float(p.end))]
    assert degraded == pytest.approx([0.165, 0.198, 0.297, 0.330, 0.429, 0.462], abs=TOL)
    assert all(p.reasons == ("timing_substituted",) for p in result.pieces if p.state == "usable_degraded")
    def total(r):
        return sum(p.support for p in r.pieces if p.state in ("usable", "usable_degraded"))
    assert total(result) == total(plain)


def test_t7_median_all_timed_when_no_adjacent_pair():
    # Two timed frames with an untimed one between them in decode order: no adjacent pair.
    packets = [PacketRecord(0, 0, 0, 0, True), PacketRecord(1, 1, None, None, True), PacketRecord(2, 2, 66, 66, True)]
    with pytest.raises(ContractError):  # 1 untimed of 3 is above f_untimed 0.05
        _resolve(packets, declared=None)
    result = timestamps.resolve(packets, Fraction(1, 1000), DecodeConfig(1.5, 0.5, 0.10, "rv1", {}, "delta_nom"), None)
    assert (result.delta_nom, result.delta_nom_source, result.delta_nom_median) == (Fraction(66, 1000), "median_all_timed", None)


def test_t7_even_count_uses_mean_of_middle_values():
    packets = [PacketRecord(i, i, t, t, True) for i, t in enumerate([0, 30, 70])]
    result = _resolve(packets, declared=None)
    assert result.delta_nom == Fraction(35, 1000)


def test_t7_fewer_than_two_timed_frames():
    with pytest.raises(ContractError) as exc:
        timestamps.resolve([PacketRecord(0, 0, 0, 0, True)], Fraction(1, 1000), cfg(), None)
    assert exc.value.code == "ERR-TIMESTAMPS"


def test_ct_t_01_vfr_durations_are_support_sums(clip_dir):
    built = run(clip_dir, "ct_t_01_vfr")
    times = [f["t_resolved_s"] for f in frames(built)]
    deltas = [b - a for a, b in zip(times, times[1:])]
    # Hand calculation from section 3.3 with delta_nom 0.033 and k_sup 1.5 (delta_max 0.0495):
    # 33 ms intervals are measured; 50 ms intervals are capped at 0.033 with 0.017 s gap_unobserved.
    expected = sum(d if d <= 0.0495 + TOL else 0.033 for d in deltas) + 0.033
    assert sum(f["support_s"] for f in frames(built)) == pytest.approx(expected, abs=1e-6)
    assert usable(built) == pytest.approx(expected, abs=1e-6)
    gaps = [s for s in built.tables["coverage_segment"] if s["coverage_state"] == "gap_unobserved"]
    # Architect review of 11 Nov 2026: the 17 ms gap_unobserved segments after each 50 ms interval are correct
    # contract behaviour (delta_max = 1.5 x 0.033 = 0.0495 s < 0.050 s).
    assert len(gaps) == sum(1 for d in deltas if d > 0.0495 + TOL) > 0
    assert all(g["t_end_tl_s"] - g["t_start_tl_s"] == pytest.approx(0.017, abs=TOL) for g in gaps)
    assert summary(built)["vfr_detected"] is True


def test_ct_t_02_b_frames_follow_pts(clip_dir):
    b, i = run(clip_dir, "ct_t_02_bframes"), run(clip_dir, "ct_t_02_all_intra")
    by_index = lambda built: [(f["frame_index"], f["t_resolved_s"], f["support_s"]) for f in sorted(frames(built), key=lambda f: f["frame_index"])]
    assert by_index(b) == by_index(i)
    assert {f["ts_status"] for f in frames(b)} == {"ok", "reordered"} and {f["ts_status"] for f in frames(i)} == {"ok"}
    assert segments(b) == segments(i)


def test_ct_t_03_duplicate_pts(clip_dir):
    built = run(clip_dir, "ct_t_03_dup_pts")
    dup = [f for f in frames(built) if f["ts_status"] == "duplicate"]
    assert len(dup) == 1 and dup[0]["decode_seq"] == 10
    assert (dup[0]["support_s"], dup[0]["support_status"], dup[0]["eligible"], dup[0]["frame_index"]) == (0.0, "zero_duplicate", False, None)
    # Frames 0-8 measured (9 x 0.033); frame 9 capped 0.033 (next distinct time 0.363, gap 0.033);
    # frames 11-28 measured (18 x 0.033); frame 29 final 0.033. Total 0.957 s, no double counting.
    assert sum(f["support_s"] for f in frames(built)) == pytest.approx(0.957, abs=1e-9)


def test_ct_t_04_dropout_gap(clip_dir):
    built = run(clip_dir, "ct_t_04_dropout")
    gaps = [s for s in built.tables["coverage_segment"] if s["coverage_state"] == "gap_unobserved"]
    assert len(gaps) == 1
    assert (gaps[0]["t_start_tl_s"], gaps[0]["t_end_tl_s"]) == pytest.approx((2.970, 6.937), abs=TOL)
    assert gaps[0]["t_end_tl_s"] - gaps[0]["t_start_tl_s"] == pytest.approx(4.0 - 0.033, abs=TOL)
    assert gaps[0]["support_s"] == 0.0 and gaps[0]["start_frame"] is None


def test_ct_t_05_fifteen_undecodable_frames(clip_dir):
    built = run(clip_dir, "ct_t_05_corrupt")
    bad = [f for f in frames(built) if not f["decode_ok"]]
    assert len(bad) == 15 and all(not f["eligible"] and f["frame_index"] is None and f["support_status"] == "excluded_own_support" for f in bad)
    assert all(f["support_s"] == pytest.approx(0.033, abs=TOL) and f["quality_flags"] == ["decode_error"] for f in bad)
    unusable = [s for s in segments(built) if s[2] == "unusable"]
    assert unusable == [(0.66, 1.155, "unusable", ["decode_error", "excluded_frame"])]


def test_ct_t_06_final_frame_sensitivity(clip_dir):
    base = run(clip_dir, "ct_t_07_file_a")
    zero = run(clip_dir, "ct_t_07_file_a", final="zero")
    assert sum(1 for f in frames(base) if f["support_status"] == "final_assumed") == 1
    total = lambda built: sum(f["support_s"] for f in frames(built))
    assert total(base) - total(zero) == pytest.approx(0.033, abs=TOL)


def test_ct_t_07_two_files_on_aligned_timeline(clip_dir):
    tl = {"tl_id": core.anchor_id("tl", "timeline", ["aligned_session", "s"]), "kind": "aligned_session", "extent_start_tl_s": 0.0, "extent_end_tl_s": 63.96}
    a, b = rec("a"), rec("b")
    items = [stage.S1Input(a, CAM, clip_dir / "ct_t_07_file_a.mkv", clip_dir / "ct_t_07_file_a.faults.json", offset_s=0.0, drift_ppm=0.0),
             stage.S1Input(b, CAM, clip_dir / "ct_t_07_file_b.mkv", clip_dir / "ct_t_07_file_b.faults.json", offset_s=61.98, drift_ppm=0.0)]
    built = stage.run_s1(tl, items, cfg({a: 0.033, b: 0.033}), spec())
    rows = segments(built)
    assert rows == [(0.0, 1.98, "usable", []), (1.98, 61.98, "not_recorded", []), (61.98, 63.96, "usable", [])]
    gap = [s for s in built.tables["coverage_segment"] if s["coverage_state"] == "not_recorded"][0]
    assert gap["recording_id"] is None and gap["start_frame"] is None and gap["t_end_tl_s"] - gap["t_start_tl_s"] == pytest.approx(60.0, abs=TOL)


def test_ct_t_08_untimed_stream_rejected_and_nothing_written(clip_dir, tmp_path):
    with pytest.raises(ContractError) as exc:
        run(clip_dir, "ct_t_08_untimed")
    assert exc.value.code == "ERR-TIMESTAMPS"


def test_ct_t_09_support_split_across_window_boundary():
    parts = [timeline_rules.clip_support(0.0, 0.033, a, b) for a, b in ((0.0, 0.02), (0.02, 0.06))]
    assert parts == pytest.approx([0.02, 0.013], abs=TOL) and sum(parts) == pytest.approx(0.033, abs=TOL)


def test_ct_t_10_interval_ending_mid_support():
    assert timeline_rules.clip_support(0.0, 0.033, 0.0, 0.025) == pytest.approx(0.025, abs=TOL)


def test_ct_t_11_unaligned_files_have_no_gap_segment(clip_dir):
    for name in ("ct_t_07_file_a", "ct_t_07_file_b"):
        assert {s[2] for s in segments(run(clip_dir, name))} == {"usable"}


def test_ct_t_12_linked_edges_need_one_aligned_timeline():
    a = {"tl_id": "tl_a", "kind": "recording_local"}
    b = {"tl_id": "tl_b", "kind": "recording_local"}
    assert [i.rule for i in timeline_rules.check_edge("L", a, b)] == ["TI-12"]
    assert timeline_rules.check_edge("U", a, b) == []
    shared = {"tl_id": "tl_s", "kind": "aligned_session"}
    assert timeline_rules.check_edge("L", shared, shared) == []


def test_ct_t_13_cross_timeline_window_rejected():
    assert [i.rule for i in timeline_rules.check_window_timeline("tl_a", "tl_b")] == ["TI-13"]
    assert timeline_rules.check_window_timeline("tl_a", "tl_a") == []


def test_vr_and_ti_invariants_on_every_clip(clip_dir):
    for name in ("fx_clip_a", "fx_clip_b", "fx_clip_c", "fx_clip_d", "ct_t_01_vfr", "ct_t_03_dup_pts", "ct_t_04_dropout", "ct_t_05_corrupt", "fx_10"):
        built = run(clip_dir, name)
        s = summary(built)
        assert vr_rules.check_frames(built.tables["frame"]) == [], name
        assert vr_rules.check_coverage_tiling(built.tables["coverage_segment"], (s["extent_start_tl_s"], s["extent_end_tl_s"])) == [], name
        assert timeline_rules.check_ti_02(built.tables["frame"], built.tables["coverage_segment"]) == [], name
        assert timeline_rules.check_ti_03(built.tables["coverage_segment"]) == [], name
        assert sum(1 for f in built.tables["frame"] if f["support_status"] == "final_assumed") == 1, name  # TI-07


def test_ct_e_04_coverage_needs_no_detector_and_is_deterministic(clip_dir):
    import rq1.decode.stage as module
    source = open(module.__file__).read() + open(timestamps.__file__).read()
    assert "perception" not in source and "detection" not in source
    assert run(clip_dir, "fx_10").artifact_id == run(clip_dir, "fx_10").artifact_id


def test_s1_artifact_ids_recompute(clip_dir):
    built = run(clip_dir, "fx_clip_d")
    for table, rows in built.tables.items():
        assert vr_rules.check_ids(table, rows, built.artifact_id) == [], table


@st.composite
def packet_lists(draw):
    n = draw(st.integers(4, 30))
    steps = draw(st.lists(st.sampled_from([33, 34, 50, 100, 500]), min_size=n, max_size=n))
    times, t = [], 0
    for s in steps:
        times.append(t)
        t += s
    order = list(range(n))
    if draw(st.booleans()):  # local reordering, as with B-frames
        for i in range(1, n - 2, 3):
            order[i], order[i + 1] = order[i + 1], order[i]
    untimed = draw(st.sets(st.integers(1, n - 1), max_size=1))
    dup = draw(st.sets(st.integers(1, n - 1), max_size=2))
    corrupt = draw(st.sets(st.integers(0, n - 1), max_size=3))
    dts_only = draw(st.sets(st.integers(0, n - 1), max_size=3))
    packets = []
    for position, frame in enumerate(order):
        pts = times[frame - 1] if frame in dup else times[frame]
        packets.append(PacketRecord(index=position, seq=frame, pts=None if frame in untimed | dts_only else pts,
                                    dts=None if frame in untimed else pts, decode_ok=frame not in corrupt))
    return packets


@settings(max_examples=500, deadline=None)
@given(packet_lists())
def test_ct_t_20_a_b_property(packets):
    config = DecodeConfig(1.5, 0.5, 0.10, "rv1", {}, "delta_nom")
    try:
        result = timestamps.resolve(packets, Fraction(1, 1000), config, None)
    except ContractError as err:
        assert err.code == "ERR-TIMESTAMPS"
        return
    supports = sorted((f.support_start, f.support_start + f.support) for f in result.frames if f.support > 0)
    assert all(a[1] <= b[0] for a, b in zip(supports, supports[1:]))  # (a) no overlap
    usable_pieces = [p for p in result.pieces if p.state in ("usable", "usable_degraded")]
    blocked = [p for p in result.pieces if p.state == "unusable"]
    for u in usable_pieces:  # (b) disjoint from unusable and timing-uncertain intervals
        for b in blocked:
            assert u.end <= b.start or b.end <= u.start
    for region in result.uncertain:
        for u in usable_pieces:
            assert u.end <= region[0] or region[1] <= u.start
    pieces = sorted(result.pieces, key=lambda p: p.start)
    assert all(a.end == b.start for a, b in zip(pieces, pieces[1:]))  # pieces tile the recording extent


def test_ar28_case_b_is_rejected_at_the_ct_t_08_value(clip_dir):
    with pytest.raises(ContractError) as exc:
        run(clip_dir, "fx_clip_b", f_untimed=0.05)
    assert exc.value.code == "ERR-TIMESTAMPS"


# Appendix T T7.1 (E-1.2.5)
def test_t7_1_decode_seq_is_demux_order(clip_dir):
    built = run(clip_dir, "fx_clip_c")
    by_seq = {f["decode_seq"]: f for f in built.tables["frame"]}
    assert [by_seq[i]["pts"] for i in range(4)] == [0, 100, None, 66]  # packets I0 P100 B33 B66 in file order
    assert summary(built)["reorder_depth"] == 2


def test_t7_1_check_value_case_a_undeclared(clip_dir):
    s = summary(run(clip_dir, "fx_clip_a", declared=None))
    assert (s["delta_nom_s"], s["delta_nom_source"]) == (pytest.approx(0.033, abs=TOL), "median_adjacent_pairs")


def test_t7_1_check_value_case_c_falls_back_to_step_3(clip_dir):
    s = summary(run(clip_dir, "fx_clip_c", declared=None))
    assert s["delta_nom_source"] == "median_all_timed" and s["delta_nom_median_s"] is None
    assert s["delta_nom_s"] == pytest.approx(0.050, abs=TOL)  # hand calculation: median of 0.066 and 0.034


def test_t7_1_b_frame_clip_uses_presentation_order_pairs(clip_dir):
    s = summary(run(clip_dir, "ct_t_02_bframes", declared=None))
    assert s["reorder_depth"] > 0
    assert s["delta_nom_source"] == "median_adjacent_pairs"  # not the all-intervals fallback
    assert s["delta_nom_s"] == pytest.approx(0.033, abs=TOL)


def test_t7_1_pairs_overlapping_an_uncertainty_region_are_excluded():
    packets = [PacketRecord(0, 0, 0, 0, True), PacketRecord(1, 1, None, None, True), PacketRecord(2, 2, 100, 100, True),
               PacketRecord(3, 3, 134, 134, True), PacketRecord(4, 4, 168, 168, True)]
    result = timestamps.resolve(packets, Fraction(1, 1000), DecodeConfig(1.5, 0.5, 0.10, "rv1", {}, "delta_nom"), None)
    assert result.uncertain == [(Fraction(0), Fraction(100, 1000))]
    assert result.delta_nom == Fraction(34, 1000)  # the 0.100 s pair inside U is excluded
