"""AR-60: the indexed completeness metrics, `association.summarize` and `gv.realized_min` are speed-only changes. Every
output must be identical (repr-equal, so floats are bit-identical) to the frozen pre-AR-60 code in
`tests/evaluation/reference_pre_ar60/` (commit 636b311) on seeded random windows. The random windows deliberately include
cases real data does not produce (an identity matched to two tracks on one frame, rows out of order within a frame,
non-contiguous frames, classes that differ by frame) so the exact semantics of the scans are pinned, not only the common case.
"""
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "reference_pre_ar60"))
import completeness_ref as cm_ref  # noqa: E402
import completeness_ref_assoc as assoc_ref  # noqa: E402
import gv_ref  # noqa: E402

from rq1.evaluation import association as assoc  # noqa: E402
from rq1.evaluation import completeness as cm  # noqa: E402
from rq1.evaluation import gv  # noqa: E402

BANDS = [(None, 0.0), (0.0, 0.5), (0.5, 1.5), (1.5, None)]
PERSONS, FORKS = ("p1", "p2", "p3"), ("f1", "f2")
P_TRACKS, F_TRACKS = ("A", "B", "C"), ("F", "G")
STATUSES = ("matched", "matched", "matched", "ambiguous", "unmatched_system", "missed_reference")


def random_window(rng: random.Random) -> dict:
    frames = sorted(rng.sample(range(120), rng.randint(5, 60)))  # non-contiguous: CM-07 runs split
    support = {f: rng.choice([0.1, rng.random() * 0.1, 1 / 3]) for f in frames}
    fork_class = {f: rng.choice(["forklift", "pallet_truck"]) for f in FORKS}
    ref_visible, ref_present, ref_moving, track_class, rows = {}, {}, {}, {}, []
    for f in frames:
        vis = {i: "person" for i in PERSONS if rng.random() < 0.6}
        vis.update({i: fork_class[i] for i in FORKS if rng.random() < 0.6})
        if rng.random() < 0.03 and vis:  # an identity listed under another class on one frame
            k = rng.choice(sorted(vis))
            vis[k] = "person" if vis[k] != "person" else "forklift"
        if vis or rng.random() < 0.5:
            ref_visible[f] = vis
        ref_present[f] = set(vis) | {i for i in PERSONS + FORKS if rng.random() < 0.2}
        ref_moving[f] = {i for i in FORKS if rng.random() < 0.5}
        track_class[f] = {t: rng.choice(["detected", "inferred", "predicted"]) for t in P_TRACKS + F_TRACKS if rng.random() < 0.7}
        frame_rows = []
        for _ in range(rng.randint(0, 6)):
            st = rng.choice(STATUSES)
            pick_person = rng.random() < 0.5
            track = rng.choice(P_TRACKS if pick_person else F_TRACKS)
            ident = rng.choice(PERSONS if pick_person else FORKS)
            if st == "unmatched_system":
                ident = None
            if st == "missed_reference":
                track = None
            frame_rows.append({"frame_index": f, "track_id": track, "physical_identity_id": ident, "status": st})
        rows += frame_rows  # duplicates and arbitrary order within a frame kept on purpose
    pows = []
    for _ in range(rng.randint(0, 5)):
        pf = [f for f in frames if rng.random() < 0.6]
        pows.append({"person_track": rng.choice(P_TRACKS), "forklift_track": rng.choice(F_TRACKS),
                     "frames": {f: rng.choice(["detected", "inferred", "predicted", "insufficient"]) for f in pf},
                     "clearance_state": {f: rng.choice(["measured", "measured", "unmeasurable"]) for f in pf if rng.random() < 0.9},
                     "clearance": {f: (None if rng.random() < 0.1 else rng.uniform(-0.5, 2.5)) for f in pf if rng.random() < 0.9},
                     "calibration_tier": rng.choice(["simulator_truth", "full_camera"])})
    ref_clear = {(p, k): {f: (None if rng.random() < 0.1 else rng.uniform(-0.5, 2.5)) for f in frames if rng.random() < 0.7}
                 for p in PERSONS for k in FORKS if rng.random() < 0.8}
    data = dict(support=support, ref_visible=ref_visible, ref_present=ref_present, assoc=rows, track_class=track_class, pows=pows,
                ref_moving=ref_moving, ref_class={**{p: "person" for p in PERSONS}, **fork_class})
    return {"data": data, "ref_clear": ref_clear}


def all_metrics(mod, w, ref_clear) -> list:
    out = [mod.reference_pairs(w)]
    odd_pairs = [("p1", "f1"), ("p1", "p2"), ("f2", "p3"), ("p9", "f1")]
    for basis in sorted(mod.BASES):
        out += [mod.cm_object(w, "person", basis), mod.cm_object(w, "forklift", basis, moving_only=True),
                mod.cm03(w, None, basis), mod.cm03(w, odd_pairs, basis), mod.cm04(w, None, basis), mod.cm04(w, odd_pairs, basis),
                mod.cm05(w, basis), mod.cm06(w, basis, BANDS, ref_clear), mod.cm06(w, basis, BANDS, None), mod.cm07(w, basis),
                mod.cm08(w, basis), mod.cm09(w, basis)]
    out.append(mod.cm10(w))
    out.append(mod.cm07(w, "detected"))  # repeated call on the same window (index reuse)
    return out


@pytest.mark.parametrize("seed", range(300))
def test_ar60_completeness_identical_to_pre_ar60(seed):
    case = random_window(random.Random(seed))
    new = all_metrics(cm, cm.WindowFrames(**case["data"]), case["ref_clear"])
    old = all_metrics(cm_ref, cm_ref.WindowFrames(**case["data"]), case["ref_clear"])
    assert repr(new) == repr(old)


@pytest.mark.parametrize("seed", range(100))
def test_ar60_summarize_identical_to_pre_ar60(seed):
    case = random_window(random.Random(10_000 + seed))["data"]
    assert repr(assoc.summarize(case["assoc"], case["support"])) == repr(assoc_ref.summarize(case["assoc"], case["support"]))


@pytest.mark.parametrize("seed", range(100))
def test_ar60_realized_min_identical_to_pre_ar60(seed):
    rng = random.Random(20_000 + seed)
    t, series = 0.0, []
    for _ in range(rng.randint(1, 80)):
        t += rng.choice([0.0, 0.1, 1 / 30, rng.random()])  # time order, ties allowed
        series.append((t, None if rng.random() < 0.2 else rng.uniform(-1, 3)))
    for k in range(len(series)):
        for tau in (0.0, 0.1, 0.5, 1.0, 2.0, rng.random() * 3):
            assert gv.realized_min(series, k, tau) == gv_ref.realized_min(series, k, tau)


def test_ar60_window_index_is_not_part_of_equality_or_repr():
    data = random_window(random.Random(1))["data"]
    a, b = cm.WindowFrames(**data), cm.WindowFrames(**data)
    cm.cm07(a, "detected")  # fills a's index only
    assert a == b and repr(a) == repr(b)
