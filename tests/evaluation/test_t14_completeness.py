"""T-14 part B: completeness CM-01, CM-02, CM-03, CM-04, CM-09 (F.1 Appendix N6). FX-CM and FX-ID-3 expected values
come from Appendix N6 and F.1 A5.2; CT-F-03 and the other cases are hand calculations written beside them."""
import json
from pathlib import Path

import pytest

from rq1.evaluation import association as assoc
from rq1.evaluation import completeness as cm
from rq1.schema import validate

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
S = 0.1  # 10 fps


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


def fx_cm_window():
    """Appendix N6 FX-CM: reference person p1 visible on 100 frames; system track A matched on 60, missing on 40; the
    forklift f1 (track F) matched on every frame; one POW of (A, F) on the frames where A exists."""
    inputs = fx("FX-CM")["inputs"]
    n, m = inputs["reference_person_visible_frames"], inputs["matched_frames"]
    rows = [{"frame_index": i, "track_id": "A", "physical_identity_id": "p1", "status": "matched"} for i in range(m)]
    rows += [{"frame_index": i, "track_id": None, "physical_identity_id": "p1", "status": "missed_reference"} for i in range(m, n)]
    rows += [{"frame_index": i, "track_id": "F", "physical_identity_id": "f1", "status": "matched"} for i in range(n)]
    tracks = {i: {"A": "detected", "F": "detected"} if i < m else {"F": "detected"} for i in range(n)}
    return cm.WindowFrames(support={i: S for i in range(n)}, ref_visible={i: {"p1": "person", "f1": "forklift"} for i in range(n)},
                           ref_present={i: {"p1", "f1"} for i in range(n)}, assoc=rows, track_class=tracks,
                           pows=[{"person_track": "A", "forklift_track": "F", "frames": {i: "detected" for i in range(m)}}])


@pytest.mark.determinism
@pytest.mark.parametrize("basis", sorted(cm.BASES))
def test_fx_cm(basis):
    expected = fx("FX-CM")["expected"]
    w = fx_cm_window()
    assert cm.cm_object(w, "person", basis)["p1"]["value"] == pytest.approx(expected["CM-01"], abs=1e-9)  # 6.0 s / 10.0 s
    assert cm.cm03(w, [("p1", "f1")], basis)[("p1", "f1")]["value"] == pytest.approx(expected["CM-03"], abs=1e-9)
    assert cm.cm_object(w, "forklift", basis)["f1"]["value"] == pytest.approx(1.0, abs=1e-9)  # forklift always matched
    assert cm.cm04(w, [("p1", "f1")], basis)["value"] == 1.0  # the pair has covered frames


@pytest.mark.determinism
def test_fx_id_3_cm_01():
    # F.1 A5.2 FX-ID-3: p1 visible 50 frames; tracks A (0-19) and B (25-49) matched; 45 x 0.1 = 4.5 s of 5.0 s = 0.9.
    inputs = fx("FX-ID-3")["inputs"]
    frames = {}
    for seg in inputs["segments"]:
        for i in range(seg["start"], seg["end_excl"]):
            frames.setdefault(i, ([], []))[0 if seg["side"] == "system" else 1].append(assoc.Box(seg["object"], seg["class"], tuple(seg["box"])))
    rows = assoc.associate({i: frames.get(i, ([], [])) for i in range(50)}, inputs["iou_cm"], inputs["eps_amb"])
    tracks = {i: {b.object_id: "detected" for b in frames.get(i, ([], []))[0]} for i in range(50)}
    w = cm.WindowFrames(support={i: S for i in range(50)}, ref_visible={i: {"p1": "person"} for i in range(50)}, ref_present={i: {"p1"} for i in range(50)},
                        assoc=rows, track_class=tracks)
    assert cm.cm_object(w, "person", "detected")["p1"]["value"] == pytest.approx(fx("FX-ID-3")["expected"]["CM-01"]["p1"], abs=1e-9)


def test_ct_f_03_cm_09():
    # Track A is inferred on frames 0-9; it is matched to p1 on all ten, but p1 is present only on frames 0-4:
    # 5 x 0.1 / (10 x 0.1) = 0.5. On the detected basis there are no inferred frames: null (not_applicable).
    rows = [{"frame_index": i, "track_id": "A", "physical_identity_id": "p1", "status": "matched"} for i in range(10)]
    w = cm.WindowFrames(support={i: S for i in range(10)}, ref_visible={}, ref_present={i: ({"p1"} if i < 5 else set()) for i in range(10)},
                        assoc=rows, track_class={i: {"A": "inferred"} for i in range(10)})
    assert cm.cm09(w, "detected_plus_inferred")["value"] == pytest.approx(0.5, abs=1e-12)
    got = cm.cm09(w, "detected")
    assert (got["value"], got["value_null_reason"], got["denominator"]) == (None, "not_applicable", 0.0)


def test_cm_bases_and_cm_02_moving_restriction():
    # Forklift f1 visible on frames 0-9, moving on 0-3; track F matched on 0-9, detected on 0-5 and inferred on 6-9.
    rows = [{"frame_index": i, "track_id": "F", "physical_identity_id": "f1", "status": "matched"} for i in range(10)]
    w = cm.WindowFrames(support={i: S for i in range(10)}, ref_visible={i: {"f1": "forklift"} for i in range(10)}, ref_present={i: {"f1"} for i in range(10)},
                        assoc=rows, track_class={i: {"F": "detected" if i < 6 else "inferred"} for i in range(10)},
                        ref_moving={i: {"f1"} for i in range(4)})
    assert cm.cm_object(w, "forklift", "detected")["f1"]["value"] == pytest.approx(0.6)  # 6 of 10 frames detected
    assert cm.cm_object(w, "forklift", "detected_plus_inferred")["f1"]["value"] == pytest.approx(1.0)
    assert cm.cm_object(w, "forklift", "detected", moving_only=True)["f1"]["value"] == pytest.approx(1.0)  # frames 0-3, all detected


@pytest.mark.determinism
def test_cm_04_counts_pairs():
    # Pairs (p1, f1) covered, (p2, f1) never covered: 1 / 2.
    w = fx_cm_window()
    w.ref_visible[0]["p2"] = "person"
    assert cm.cm04(w, [("p1", "f1"), ("p2", "f1")], "detected") == {"numerator": 1.0, "denominator": 2.0, "value": 0.5, "value_null_reason": None}


@pytest.mark.determinism
def test_completeness_record_matches_the_schema():
    w = fx_cm_window()
    row = cm.record("rwn_" + "a" * 26, "CM-01", "detected", {"physical_identity_id": "p1"}, cm.cm_object(w, "person", "detected")["p1"], "none", 0.5, 1.0)
    assert validate.validate_row("completeness_record", row) == []
    empty = cm.record("rwn_" + "a" * 26, "CM-09", "detected", {}, cm.cm09(w, "detected"), "none", 0.5, 1.0)
    assert validate.validate_row("completeness_record", empty) == [] and empty["value"] is None
