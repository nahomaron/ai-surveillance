"""CT-T12-04: Appendix T T12.4 (contract E-1.2.10) completeness CM-05 to CM-08, CM-10 and pooling. Fixtures extend FX-CM
and FX-ID-3; every expected value is a hand calculation written beside it (10 fps, 0.1 s per frame)."""
import math

import pytest

from rq1.evaluation import completeness as cm

from test_t14_completeness import fx_cm_window, fx

BANDS = [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]


def extended():
    """FX-CM (p1/f1 co-visible on frames 0-99; A matched to p1 on 0-59; F matched to f1 throughout; POW1 = (A, F) on 0-59)
    plus: POW1 clearance measured 1.5 m on 0-49 and not measured on 50-59; POW2 = (Z, F) on frames 60-79, where Z matches
    no reference (unmatched system track), clearance measured 2.5 m. Both POWs ground_plane_homography."""
    w = fx_cm_window()
    pow1 = w.pows[0]
    pow1["clearance"] = {f: (1.5 if f < 50 else None) for f in range(60)}
    pow1["clearance_state"] = {f: ("measured" if f < 50 else "unmeasurable_occluded") for f in range(60)}
    pow1["calibration_tier"] = "ground_plane_homography"
    w.pows.append({"person_track": "Z", "forklift_track": "F", "frames": {f: "detected" for f in range(60, 80)},
                   "clearance": {f: 2.5 for f in range(60, 80)}, "clearance_state": {f: "measured" for f in range(60, 80)},
                   "calibration_tier": "ground_plane_homography"})
    w.assoc.extend({"frame_index": f, "track_id": "Z", "physical_identity_id": None, "status": "unmatched_system"} for f in range(60, 80))
    for f in range(60, 80):
        w.track_class[f]["Z"] = "detected"
    return w


@pytest.mark.determinism
def test_cm_05():
    # POW frames of the basis: POW1 0-59 (60) + POW2 60-79 (20) = 80 frames, 8.0 s; POW2's 20 frames (2.0 s) are attributed
    # to no reference pair: 2.0 / 8.0 = 0.25. No ambiguous frames.
    got = cm.cm05(extended(), "detected")
    assert (got["numerator"], got["denominator"], got["value"], got["ambiguous_support_s"]) == (
        pytest.approx(2.0), pytest.approx(8.0), pytest.approx(0.25), 0.0)


@pytest.mark.determinism
def test_cm_05_excludes_ambiguous_frames():
    # Mark track A ambiguous on frames 0-9: those 1.0 s leave the ratio and are reported separately: 2.0 / 7.0.
    w = extended()
    w.assoc[:] = [{**r, "status": "ambiguous"} if r["track_id"] == "A" and r["frame_index"] < 10 else r for r in w.assoc]
    got = cm.cm05(w, "detected")
    assert (got["value"], got["ambiguous_support_s"]) == (pytest.approx(2.0 / 7.0), pytest.approx(1.0))


@pytest.mark.determinism
def test_cm_06():
    # Reference clearance of (p1, f1): 1.5 m on frames 0-49, 0.8 m on 50-99. AI: POW1 frames attributed to the pair with
    # measured clearance 0-49 at 1.5 m (frames 50-59 not measured; POW2 not attributed).
    # AI   per band: [0, 0, 0, 5.0, 0, 0]; reference per band: [0, 0, 5.0, 5.0, 0, 0].
    # Value = |0 - 5.0| + |5.0 - 5.0| = 5.0. Bland-Altman over 6 (pair, band) units, d = [0, 0, -5, 0, 0, 0]:
    # bias = -5/6 = -0.833333; squared deviations 5 x (5/6)^2 + (25/6)^2 = 125/36 + 625/36 = 750/36; SD = sqrt(750/36/5) = 2.041241.
    ref = {("p1", "f1"): {f: (1.5 if f < 50 else 0.8) for f in range(100)}}
    got = cm.cm06(extended(), "detected", BANDS, ref)
    pair = got["pairs"][("p1", "f1")]
    assert pair["value"] == pytest.approx(5.0, abs=1e-9)
    assert pair["ai_s"] == pytest.approx([0, 0, 0, 5.0, 0, 0], abs=1e-9) and pair["ref_s"] == pytest.approx([0, 0, 5.0, 5.0, 0, 0], abs=1e-9)
    ba = got["bland_altman"]
    assert (ba["n"], ba["bias"], ba["sd"]) == (6, pytest.approx(-5 / 6, abs=1e-9), pytest.approx(math.sqrt(750 / 36 / 5), abs=1e-9))
    none = cm.cm06(extended(), "detected", BANDS, None)
    assert none["pairs"][("p1", "f1")] == {"value": None, "value_null_reason": "not_supplied"} and none["bland_altman"] is None


def cm07_window():
    """Three reference pairs with forklift f1 visible on frames 0-49:
    (p1, f1) co-visible 0-9 and 20-29 (two intervals); (p2, f1) co-visible 40-44; (p3, f1) co-visible 30-34.
    Tracks: B matched to p1 on 0-9; C matched to p1 on 22-25; D matched to p1 on 26-28; F matched to f1 throughout.
    POWs: (B, F) 0-9, (C, F) 22-25, (D, F) 26-28. p2 and p3 are never tracked."""
    vis = {f: {"f1": "forklift"} for f in range(50)}
    for f in [*range(10), *range(20, 30)]:
        vis[f]["p1"] = "person"
    for f in range(40, 45):
        vis[f]["p2"] = "person"
    for f in range(30, 35):
        vis[f]["p3"] = "person"
    rows = [{"frame_index": f, "track_id": "F", "physical_identity_id": "f1", "status": "matched"} for f in range(50)]
    spans = {"B": range(10), "C": range(22, 26), "D": range(26, 29)}
    rows += [{"frame_index": f, "track_id": t, "physical_identity_id": "p1", "status": "matched"} for t, r in spans.items() for f in r]
    tracks = {f: {"F": "detected", **{t: "detected" for t, r in spans.items() if f in r}} for f in range(50)}
    pows = [{"person_track": t, "forklift_track": "F", "frames": {f: "detected" for f in r}} for t, r in spans.items()]
    return cm.WindowFrames(support={f: 0.1 for f in range(50)}, ref_visible=vis, ref_present={f: set(vis[f]) for f in range(50)},
                           assoc=rows, track_class=tracks, pows=pows)


@pytest.mark.determinism
def test_cm_07():
    # (p1, f1) [0, 10): POW (B, F) -> 1. (p1, f1) [20, 30): POWs (C, F) and (D, F) -> 2. (p2, f1) [40, 45): 0. (p3, f1) [30, 35): 0.
    # Summary: 0 -> 2 intervals, 1 -> 1, 2+ -> 1; pair-window fidelity (N10) = 1 / 4.
    got = cm.cm07(cm07_window(), "detected")
    assert sorted((i["pair"], i["start_frame"], i["end_frame_excl"], i["n_pows"]) for i in got["intervals"]) == [
        (("p1", "f1"), 0, 10, 1), (("p1", "f1"), 20, 30, 2), (("p2", "f1"), 40, 45, 0), (("p3", "f1"), 30, 35, 0)]
    assert got["summary"] == {"0": 2, "1": 1, "2+": 1} and got["pair_window_fidelity"] == 0.25


@pytest.mark.determinism
def test_cm_08():
    # POW frames of the basis: 80 (8.0 s); not measured: POW1 frames 50-59 (1.0 s): 1.0 / 8.0 = 0.125, one calibration tier.
    got = cm.cm08(extended(), "detected")
    assert list(got) == ["ground_plane_homography"] and got["ground_plane_homography"]["value"] == pytest.approx(0.125)


@pytest.mark.determinism
@pytest.mark.parametrize("basis", sorted(cm.BASES))
def test_cm_10(basis):
    # POW1 (A, F) has dominant pair (p1, f1). Its pair-frames 55-59 are insufficient: 0.5 s of the 10.0 s co-visible -> 0.05.
    # Frames 80-99 have no POW pair-frame: counted in neither numerator. Same value on both bases (CR-017).
    w = extended()
    for f in range(55, 60):
        w.pows[0]["frames"][f] = "insufficient"
    got = cm.cm10(w)[("p1", "f1")]
    assert (got["numerator"], got["denominator"], got["value"]) == (pytest.approx(0.5), pytest.approx(10.0), pytest.approx(0.05))
    assert cm.cm03(w, None, basis)[("p1", "f1")]["value"] == pytest.approx(5.5 / 10.0)  # insufficient frames 55-59 uncovered


@pytest.mark.determinism
def test_pooled_cm_01_over_two_res_windows():
    # Window 1 = FX-CM: CM-01(p1) = 6.0 / 10.0. Window 2 = FX-ID-3: 4.5 / 5.0 (F.1 A5.2). Weights 2 and 1:
    # weighted (2 x 6.0 + 4.5) / (2 x 10.0 + 5.0) = 16.5 / 25.0 = 0.66; unweighted 10.5 / 15.0 = 0.70.
    from rq1.evaluation import association as assoc
    inputs = fx("FX-ID-3")["inputs"]
    frames = {}
    for seg in inputs["segments"]:
        for i in range(seg["start"], seg["end_excl"]):
            frames.setdefault(i, ([], []))[0 if seg["side"] == "system" else 1].append(assoc.Box(seg["object"], seg["class"], tuple(seg["box"])))
    rows = assoc.associate({i: frames.get(i, ([], [])) for i in range(50)}, inputs["iou_cm"], inputs["eps_amb"])
    w2 = cm.WindowFrames(support={i: 0.1 for i in range(50)}, ref_visible={i: {"p1": "person"} for i in range(50)}, ref_present={i: {"p1"} for i in range(50)},
                         assoc=rows, track_class={i: {b.object_id: "detected" for b in frames.get(i, ([], []))[0]} for i in range(50)})
    ratios = [cm.cm_object(fx_cm_window(), "person", "detected")["p1"], cm.cm_object(w2, "person", "detected")["p1"]]
    got = cm.pooled(ratios, [2.0, 1.0])
    assert got["weighted"]["value"] == pytest.approx(0.66, abs=1e-9) and got["unweighted"]["value"] == pytest.approx(0.70, abs=1e-9)


@pytest.mark.determinism
def test_reference_pairs_and_fx_values_unchanged():
    # T12.4 check: FX-CM keeps CM-01 = CM-03 = 0.600 with pairs derived from the data.
    w = fx_cm_window()
    assert cm.reference_pairs(w) == [("p1", "f1")]
    assert cm.cm03(w, None, "detected")[("p1", "f1")]["value"] == pytest.approx(0.6) and cm.cm04(w, None, "detected")["value"] == 1.0
