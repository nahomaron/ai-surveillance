"""D-61 STEP 5: v2 reference building. The test-partition loader is reference-only; the ordinary loader still refuses
test (D-37); reference entries follow T21.2-T21.3 (hand-made inputs, expected values by hand beside each assertion)."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/preregistration"))
import v2_references as vr  # noqa: E402

m = vr.m
ROOT = vr.ROOT
HAVE_DATA = (ROOT / "research/datasets/part3/t17_counts_sdg.json").exists() and (ROOT / "out/s0_sdg").exists()


def _test_rec():
    freeze = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())
    counts = json.loads((ROOT / "research/datasets/part3/t17_counts_sdg.json").read_text())["cameras"]
    return next(c["rec_id"] for c in counts if c["run"] in set(freeze["split"]["sdg_test_runs"]))


@pytest.mark.skipif(not HAVE_DATA, reason="SDG S0 and T17 counts not present")
def test_ordinary_loader_still_refuses_test_and_reference_loader_allows_it():
    from rq1.schema.errors import ContractError
    ctx = m.Context("sdg")
    rec = _test_rec()
    with pytest.raises(ContractError) as e:
        ctx.camera(rec)
    assert e.value.code == "ERR-LEAKAGE"  # D-37 unchanged for every system path
    assert ctx.reference_camera(rec)["rec_id"] == rec  # D-61 STEP 5: reference building only


@pytest.mark.skipif(not (ROOT / "out/s0_smartspaces").exists(), reason="SmartSpaces S0 not present")
def test_reference_loader_refuses_smartspaces():
    from rq1.schema.errors import ContractError
    ctx = m.Context("smartspaces")
    with pytest.raises(ContractError):
        ctx.reference_camera(ctx.counts["cameras"][0]["rec_id"])  # CR-039: no SmartSpaces v2 references


@pytest.mark.skipif(not HAVE_DATA, reason="SDG S0 and T17 counts not present")
def test_camera_sets():
    t, r, x = vr.cameras("tuning"), vr.cameras("reporting"), vr.cameras("test")
    assert (len(t), len(r), len(x)) == (116, 110, 471)  # v2 notes (D-50) and the V0 plan m1a-sdg-test (471 camera groups)
    assert not (set(t) & set(r)) and not (set(t) & set(x)) and not (set(r) & set(x))
    assert x == sorted(x)


def test_reference_entries_t21_3():
    s4 = {"pow": [{"pow_id": "pow_a", "person_track_id": "trk_p", "forklift_track_id": "trk_f"}]}
    ep = lambda s, e, o, h: {"pow_id": "pow_a", "start_frame": s, "end_frame_excl": e, "t_start_tl_s": s / 30, "t_end_tl_s": e / 30,
                             "lbl_O": o, "lbl_H": h, "lbl_PC": False}
    s5 = {"episode": [ep(0, 10, True, False), ep(20, 30, False, True)]}
    keys = {"trk_p": "P1", "trk_f": "F1"}
    visible = {"P1": [5, 6, 25], "F1": [6, 40]}  # jointly visible on frame 6 only
    out = vr.reference_entries(s5, s4, keys, visible)
    assert [x["assessable"] for x in out] == [True, False]  # frame 6 lies in [0, 10); no joint frame in [20, 30)
    assert [x["status"] for x in out] == ["assessable", "unobservable_reference"]
    assert out[0]["person_key"] == "P1" and out[0]["forklift_key"] == "F1" and out[1]["lbl_H"] is True


def test_set_hash_is_order_free_and_content_bound():
    row = lambda rec, h: {"rec_id": rec, "s3": "a", "s4": "b", "s5": "c", "s3_payload_sha256": "1", "s4_payload_sha256": "2",
                          "s5_payload_sha256": h, "references_sha256": "r", "seconds": 1.0}
    a = vr.set_sha256([row("rec_1", "x"), row("rec_2", "y")])
    assert a == vr.set_sha256([row("rec_2", "y"), row("rec_1", "x")])  # sorted by rec_id
    assert a != vr.set_sha256([row("rec_1", "x"), row("rec_2", "z")])  # a payload change changes the set hash
    assert vr.set_sha256([dict(row("rec_1", "x"), seconds=9.0)]) == vr.set_sha256([row("rec_1", "x")])  # run time is not hashed


def test_window_lock_hash_proposal_ar71_item_11():
    import hashlib
    import readiness_v2 as tr
    w = {"plan_nk": ["m1a-sdg-test", "1"], "camera_group_id": "cgp_x", "window_index": 0, "t_start_tl_s": 0.0, "t_end_tl_s": 10.0, "t_guard_end_tl_s": 10.0}
    ref = {"s5": "art_s5", "s5_payload_sha256": "p", "references": [{"t_start_tl_s": 2.0, "t_end_tl_s": 3.0, "k": 1},
                                                                     {"t_start_tl_s": 10.0, "t_end_tl_s": 11.0, "k": 2}]}
    h = tr.window_lock_hash(w, "rec_x", ref)
    # By hand: only the first reference overlaps [0, 10) (the second starts at the guard end); JCS of the body, SHA-256.
    body = {"plan_nk": ["m1a-sdg-test", "1"], "camera_group_id": "cgp_x", "window_index": 0, "t_start_tl_s": 0.0, "t_end_tl_s": 10.0,
            "t_guard_end_tl_s": 10.0, "reference_set": "preregistration-v2", "rec_id": "rec_x", "reference_s5": "art_s5",
            "reference_s5_payload_sha256": "p", "references": [{"t_start_tl_s": 2.0, "t_end_tl_s": 3.0, "k": 1}]}
    assert h == hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    ref2 = dict(ref, s5_payload_sha256="q")
    assert tr.window_lock_hash(w, "rec_x", ref2) != h  # a changed reference S5 changes the lock hash
