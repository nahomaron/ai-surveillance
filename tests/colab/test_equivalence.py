"""D-60 STEP 4 (c): the equivalence comparator on hand-made raw files (expected values by hand beside each assertion)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/colab"))
import equivalence as E  # noqa: E402


def det(cls, box, score):
    return {"class": cls, "box": box, "score": score}


def raw(rec, frames):
    return {"rec_id": rec, "frames": [{"decode_seq": k, "frame_index": k, "detections": d} for k, d in enumerate(frames)]}


BOX = [0.0, 0.0, 100.0, 100.0]
NEAR = [0.0, 0.0, 100.0, 104.0]  # IoU = 10000 / 10400 = 0.9615 >= 0.95
FAR = [0.0, 0.0, 100.0, 110.0]  # IoU = 10000 / 11000 = 0.909 < 0.95


def test_iou_by_hand():
    assert E.iou(BOX, BOX) == 1.0
    assert abs(E.iou(BOX, NEAR) - 10000 / 10400) < 1e-12 and abs(E.iou(BOX, FAR) - 10000 / 11000) < 1e-12
    assert E.iou(BOX, [200.0, 200.0, 300.0, 300.0]) == 0.0


def test_identical_files_pass():
    r = raw("rec_a", [[det("person", BOX, 0.5), det("forklift", BOX, 0.3)], []])
    v = E.verdict([E.compare(r, r)])
    assert v["pass"] and v["failed"] == []
    k = v["cameras"][0]["classes"]["person"]
    assert (k["n_cpu"], k["n_colab"], k["matched_pairs"], k["score_diff_p99_all_kept"]) == (1, 1, 1, 0.0)


def test_c1_unmatched_strong_box_fails_weak_box_does_not():
    cpu = raw("rec_a", [[det("person", BOX, 0.21)], [det("person", BOX, 0.50)]])  # 0.21 < 0.20 + 0.02: not in C1; 0.50 is
    gpu = raw("rec_a", [[], [det("person", FAR, 0.50)]])  # 0.50 box only at IoU 0.909 -> unmatched
    v = E.verdict([E.compare(cpu, gpu)])
    c1 = [x for x in v["checks"] if x["check"] == "C1" and x["class"] == "person"][0]
    assert c1["value"] == 1 and not c1["pass"] and not v["pass"]
    cpu2 = raw("rec_a", [[det("person", BOX, 0.21)], [det("person", BOX, 0.50)]])
    gpu2 = raw("rec_a", [[], [det("person", NEAR, 0.50)]])
    c1 = [x for x in E.verdict([E.compare(cpu2, gpu2)])["checks"] if x["check"] == "C1" and x["class"] == "person"][0]
    assert c1["value"] == 0 and c1["pass"]  # the 0.21 box is unmatched but below threshold + margin


def test_one_to_one_matching():
    # two CPU boxes, one Colab box: one pair only, so one strong CPU box is unmatched
    cpu = raw("rec_a", [[det("person", BOX, 0.9), det("person", NEAR, 0.8)]])
    gpu = raw("rec_a", [[det("person", BOX, 0.9)]])
    k = E.compare(cpu, gpu)["classes"]["person"]
    assert k["matched_pairs"] == 1 and k["unmatched"] == 1


def test_c2_p99_and_c3_counts():
    # 100 frames, one person box each; Colab scores differ by 0.01 on 98 frames and 0.10 on 2.
    # Sorted diffs: 98 x 0.01 then 2 x 0.10; P99 by linear interpolation at rank 0.99 * 99 = 98.01:
    # value = d[98] + 0.01 * (d[99] - d[98]) = 0.10 -> fails (> 0.02)
    cpu = raw("rec_a", [[det("person", BOX, 0.5)] for _ in range(100)])
    gpu = raw("rec_a", [[det("person", BOX, 0.5 + (0.10 if k >= 98 else 0.01))] for k in range(100)])
    v = E.verdict([E.compare(cpu, gpu)])
    c2 = [x for x in v["checks"] if x["check"] == "C2_all_kept" and x["rec_id"] == "rec_a" and x["class"] == "person"][0]
    assert abs(c2["value"] - 0.10) < 1e-9 and not c2["pass"]
    # 1 of 100 at 0.10: rank 98.01 lies between d[98] = 0.01 and d[99] = 0.10 -> 0.01 + 0.01 * 0.09 = 0.0109 -> passes
    gpu = raw("rec_a", [[det("person", BOX, 0.5 + (0.10 if k == 99 else 0.01))] for k in range(100)])
    c2 = [x for x in E.verdict([E.compare(cpu, gpu)])["checks"] if x["check"] == "C2_all_kept" and x["rec_id"] == "rec_a" and x["class"] == "person"][0]
    assert abs(c2["value"] - 0.0109) < 1e-9 and c2["pass"]
    # C3: 100 CPU person boxes; 102 Colab passes (2 %), 103 fails
    for extra, ok in ((2, True), (3, False)):
        g = raw("rec_a", [[det("person", BOX, 0.5)] + ([det("person", [500.0, 500.0, 600.0, 600.0], 0.5)] if k < extra else []) for k in range(100)])
        c3 = [x for x in E.verdict([E.compare(cpu, g)])["checks"] if x["check"] == "C3" and x["rec_id"] == "rec_a" and x["class"] == "person"][0]
        assert c3["value"] == [100, 100 + extra] and c3["pass"] is ok
    assert E.count_ok(0, 0) and not E.count_ok(0, 1)


def test_frame_lists_must_agree():
    cpu = raw("rec_a", [[], []])
    gpu = raw("rec_a", [[]])
    v = E.verdict([E.compare(cpu, gpu)])
    assert not v["pass"] and v["failed"][0]["check"] == "frames_equal"
