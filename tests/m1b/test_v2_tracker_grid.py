"""D-55 steps 1, 3 and 4: probe S2 configuration, grid configurations and tracking measures (expected values by hand).

Measures fixture (one class, eligible frames 0..4, image large enough that clipping changes nothing). Reference
identity A at (0, 0, 10, 10) on every frame (5 references). Tracker log:
  frame 0, 1, 3: track 1 tracked on detection 0 at A's box (score 0.9)
  frame 2:       track 1 lost, predicted box (1, 1, 11, 11)  -> IoU with A = 81 / 119 = 0.681 (>= 0.5 and >= 0.3)
  frame 4:       track 2 tracked on detection 0 at A's box (0.8); track 3 tracked on detection 1 at (50, 50, 60, 60) (0.7)
Points (g_max 15): track 1 tracked 0, 1, 3 and predicted 2 (one bridged run of 1 frame); tracks 2 and 3 one point each.
Primary (state tracked): matched references frames 0, 1, 3, 4 = 4 / 5 -> coverage 0.8; tracked points 5, matched 4 ->
  precision 0.8; A covered by tracks {1, 2} -> 2 fragments.
Secondary (tracked and predicted): frame 2 also matched -> coverage 5 / 5 = 1.0; points 6, matched 5 -> 5 / 6.
IDF1 (iou_cm 0.5): system boxes 6 (track 1: 4, tracks 2 and 3: 1 each), reference boxes 5; best assignment A-track 1
  with 4 potential matches: IDTP 4, IDFN 1, IDFP 2; IDF1 = 4 / (4 + 0.5 * 2 + 0.5 * 1) = 4 / 5.5 = 0.727273.
Counts: tracks 3, tracked 5, predicted 1, runs_bridged 1, longest bridged gap 1.
Pool of two copies: IDF1 unchanged (sums double), coverage 0.8, fragments per identity 2.0, identities 2, both >= 2.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import v2_tracker_measures as vm  # noqa: E402

A = [0.0, 0.0, 10.0, 10.0]
LOG = [{"frame_index": 0, "tracked": [[1, 0, A]], "lost": []}, {"frame_index": 1, "tracked": [[1, 0, A]], "lost": []},
       {"frame_index": 2, "tracked": [], "lost": [[1, [1.0, 1.0, 11.0, 11.0]]]}, {"frame_index": 3, "tracked": [[1, 0, A]], "lost": []},
       {"frame_index": 4, "tracked": [[2, 0, A], [3, 1, [50.0, 50.0, 60.0, 60.0]]], "lost": []}]
REFS = {i: [("A", tuple(A))] for i in range(5)}
SCORE = {(0, 0): 0.9, (1, 0): 0.9, (3, 0): 0.9, (4, 0): 0.8, (4, 1): 0.7}


def fixture():
    return vm.measures(LOG, REFS, REFS, SCORE, list(range(5)))


def test_measures_hand_case():
    m = fixture()
    assert m["coverage"] == {"references": 5, "matched_tracked": 4, "matched_all": 5}
    assert m["precision"] == {"points_tracked": 5, "points_all": 6, "points_matched_tracked": 4, "points_matched_all": 5}
    assert m["fragments"] == {"A": {"tracked": 2, "all": 2}}
    assert (m["idf1"]["IDTP"], m["idf1"]["IDFN"], m["idf1"]["IDFP"]) == (4.0, 1.0, 2.0)
    assert m["counts"] == {"tracks": 3, "tracked": 5, "predicted": 1, "runs_bridged": 1, "longest_bridged": 1}


def test_pool_hand_case():
    p = vm.pool([fixture(), fixture()])
    assert p["idf1"] == pytest.approx(4 / 5.5)
    assert p["tracked"]["coverage"] == 0.8 and p["all"]["coverage"] == 1.0
    assert p["tracked"]["precision"] == 0.8 and p["all"]["precision"] == pytest.approx(5 / 6)
    assert p["tracked"]["fragments_per_identity"] == 2.0
    assert (p["tracked"]["identities"], p["tracked"]["identities_covered"], p["tracked"]["identities_two_or_more"]) == (2, 2, 2)
    assert p["counts"]["longest_bridged"] == 1 and p["counts"]["runs_bridged"] == 2


def test_longest_bridged_ignores_runs_beyond_g_max():
    log = [{"frame_index": i, "tracked": [[1, 0, A]] if i in (0, 17) else [], "lost": [] if i in (0, 17) else [[1, A]]} for i in range(18)]
    assert vm.longest_bridged(log, 15) == 0  # 16 frames between the hits > g_max
    assert vm.longest_bridged(log, 16) == 16


def test_quantiles():
    assert vm.median([1, 3, 2]) == 2 and vm.median([1, 2, 3, 4]) == 2.5
    assert vm.quantile(list(range(1, 11)), 90) == 9 and vm.quantile([5], 90) == 5 and vm.quantile([], 90) is None


def test_probe_s2_configuration_is_the_pilots():
    """The pilot S2 configuration IDs, as stored in every pilot S2 manifest (read from the stored outputs)."""
    import v2_probe_s2 as ps
    assert ps.config_ids() == ("inf_cetfxtbdg72cqgfm6teibcxsyd", "mdl_ty3jrnwz5jjdv56nwtkcos4yqs")
    rows = ps.license_rows()
    assert [r["component"] for r in rows] == ["yolov8s-worldv2.pt", "ViT-B-32.pt"]


@pytest.mark.skipif(not (ROOT / "out/m1b/pilot/cam").exists(), reason="stored pilot outputs absent")
def test_grid_configurations():
    import v2_tracker_grid as vg
    cfgs = vg.configurations()
    assert len(cfgs) == 73 and len({c["config_id"] for c in cfgs}) == 73
    assert cfgs[0]["family"] == "C" and cfgs[0]["config_id"] == "trc_i4ljlcifrwgephzz4cgjkmo5ej" and cfgs[0]["parameters_changed"] == 0
    for fam, tid in (("T1", "bytetrack"), ("T2", "botsort")):
        rows = [c for c in cfgs if c["family"] == fam]
        assert len(rows) == 36 and all(c["tracker_id"] == tid for c in rows)
        assert {(c["grid"]["track_high_thresh"], c["grid"]["new_track_thresh"]) for c in rows} == set(vg.PAIRS)
        assert all(c["params"]["track_low_thresh"] == 0.05 and c["params"]["match_thresh"] == 0.8 for c in rows)
        assert {c["params"]["track_buffer"] for c in rows} == {30, 60, 90} and {c["params"]["fuse_score"] for c in rows} == {True, False}
        assert all(c["run_config"]["classes"]["person"]["params"] == cfgs[0]["params"] for c in rows)
        assert all(c["run_config"]["classes"]["forklift"]["tracker_id"] == tid for c in rows)
    t2 = [c for c in cfgs if c["family"] == "T2"]
    assert all(c["params"]["gmc_method"] == "none" and c["params"]["with_reid"] is False for c in t2)
    # hand: (0.25, 0.25), fuse true, buffer 30 changes only track_low_thresh (ByteTrack 1; BoT-SORT + gmc_method = 2)
    corner = lambda rows: next(c for c in rows if c["grid"]["track_high_thresh"] == 0.25 and c["grid"]["fuse_score"] and c["grid"]["track_buffer"] == 30)
    assert corner([c for c in cfgs if c["family"] == "T1"])["parameters_changed"] == 1 and corner(t2)["parameters_changed"] == 2
    json.dumps([c["run_config"] for c in cfgs])
