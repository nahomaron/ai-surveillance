"""T-23 (D-45 item 1): detector-path S3 artifact, T-12 identity association and IDF1 on the tracker fixtures.

The tracker runs in `.venv-det` (subprocess); everything else here runs in the main environment. Skipped when
`.venv-det` is absent.

Expected values (fixture design in `rq1.fixtures.oracle_detections`, D-45 rule, hand calculation):
- tracked points carry their detection's det_id; predicted points carry none (`not_observable`, E-1.2.1 section 5.4);
  evidence classes detected / inferred; foot point = bottom-centre of the box.
- A5.2 association against the noise-free simulator boxes at iou_cm 0.5: P1 and P2 one_to_one; the two F1 tracks
  `fragment`; in the swap fixture both tracks `id_switch` with one switch each.
- IDF1, swap fixture (hand): identities Q1, Q2 with 60 boxes each; each track covers one identity on 30 frames and the
  other on 30. Best assignment Q1-track1, Q2-track2: IDTP 60, IDFN 120 - 60 = 60, IDFP 120 - 60 = 60;
  IDF1 = 60 / (60 + 30 + 30) = 0.5.
- IDF1 toy (hand): identity A on frames 0..3; track 1 on A at 0..1, track 2 on A at 2..3, track 3 a false box at frame 0.
  Best assignment A-1 (or A-2): IDTP 2, IDFN 4 - 2 = 2, IDFP 5 - 2 = 3; IDF1 = 2 / (2 + 1.5 + 1) = 0.444444.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from rq1.evaluation import association as assoc
from rq1.fixtures import oracle_detections as fx
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.perception import s2
from rq1.tracking import bridging as br
from rq1.tracking.s3 import DetectorTrackSource

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import idf1  # noqa: E402

DET_PY = ROOT / ".venv-det/bin/python"
REC = core.make_id("rec", "tracker-fixture")
pytestmark = pytest.mark.determinism


def frames_rows(fixture):
    eligible = set(fixture["frames"])
    return [{"frame_index": i, "eligible": i in eligible, "support_s": 1 / 30, "support_start_tl_s": i / 30, "support_status": "resolved"}
            for i in fixture["all_frames"]]


def s2_rows(fixture):
    raw = {}
    for d in fixture["detections"]:
        raw.setdefault(d["frame_index"], []).append({"class": d["class"], "box": d["bbox_xyxy_px"], "score": d["score"]})
    comp = s2.component_id(s2.weights_component("fixture.pt", "00" * 32, "https://example.invalid/fixture.pt", "TEST-ONLY"))
    art = s2.build(REC, raw, fixture["width"], fixture["height"], comp, Spec("S2", "E-1.2.21", "test", "test", (core.make_id("mdl", "fixture"), core.make_id("inf", "fixture")), (), {}))
    return art.tables["detection"]


def run_tracker(tmp_path, fixture, rows):
    inp, out = tmp_path / "in.json", tmp_path / "out.json"
    inp.write_text(json.dumps({"frames": fixture["frames"], "detections": [{k: r[k] for k in ("frame_index", "det_index", "class", "bbox_xyxy_px", "score")}
                                                                          for r in rows]}))
    subprocess.run([str(DET_PY), "-m", "rq1.tracking.bytetrack", str(inp), str(out)], check=True, cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src"), "YOLO_CONFIG_DIR": str(ROOT / "out/m1b/ultralytics_config"), "YOLO_AUTOINSTALL": "false"})
    return json.loads(out.read_text())


def build_s3(fixture, rows, log):
    pts = {c: {int(k): v for k, v in br.points_from_log(log["logs"][c]).items()} for c in ("person", "forklift")}
    return DetectorTrackSource().tracks(REC, pts, rows, frames_rows(fixture), Spec("S3", "E-1.2.21", "test", "test", (core.make_id("trc", "fixture"),), (), {}))


def associate(fixture, art):
    tracks = {t["track_local_id"]: t for t in art.tables["track"]}
    frames = {i: ([], []) for i in fixture["frames"]}
    for p in art.tables["track_point"]:
        t = tracks[p["track_nk"][1]]
        frames[p["frame_index"]][0].append(assoc.Box(t["trk_id"], t["class"], tuple(p["bbox_xyxy_px"])))
    for i, key, cls, box in fixture["truth"]:
        frames[i][1].append(assoc.Box(key, cls, tuple(box)))
    rows = assoc.associate(frames, 0.5, 0.02)
    summaries, missed = assoc.summarize(rows, {i: 1 / 30 for i in fixture["frames"]})
    return rows, {s["track_id"]: s for s in summaries}, missed


needs_det = pytest.mark.skipif(not DET_PY.exists(), reason=".venv-det not present")


@needs_det
def test_s3_rows_and_association(tmp_path):
    fixture = fx.dropouts()
    rows = s2_rows(fixture)
    log = run_tracker(tmp_path, fixture, rows)
    art, local_map = build_s3(fixture, rows, log)
    det_ids = {r["det_id"] for r in rows}
    by_id = {r["det_id"]: r for r in rows}
    for p in art.tables["track_point"]:
        x1, y1, x2, y2 = p["bbox_xyxy_px"]
        assert p["foot_point_px"] == [(x1 + x2) / 2, y2]
        if p["state"] == "tracked":
            assert p["evidence_class"] == "detected" and p["detection_id"] in det_ids
            assert p["bbox_xyxy_px"] == by_id[p["detection_id"]]["bbox_xyxy_px"]  # AR-62 item 3: the detection's own box
        else:
            assert p["state"] == "predicted" and p["evidence_class"] == "inferred"
            assert p["detection_id"] is None and p["detection_id_null_reason"] == "not_observable"
        assert p["frame_index"] != 38
    _, summary, missed = associate(fixture, art)
    by_class = {}
    for t in art.tables["track"]:
        by_class.setdefault(t["class"], []).append(summary[t["trk_id"]])
    assert sorted(s["status"] for s in by_class["person"]) == ["one_to_one", "one_to_one"]
    assert [(s["status"], s["dominant_identity_id"]) for s in by_class["forklift"]] == [("fragment", "F1"), ("fragment", "F1")]
    assert missed == []
    again, _ = build_s3(fixture, rows, run_tracker(tmp_path, fixture, rows))
    assert again.artifact_id == art.artifact_id  # S3 is reproducibility class exact


@needs_det
def test_swap_reported_as_identity_switch_and_idf1(tmp_path):
    fixture = fx.swap()
    rows = s2_rows(fixture)
    art, _ = build_s3(fixture, rows, run_tracker(tmp_path, fixture, rows))
    _, summary, _ = associate(fixture, art)
    assert sorted((s["status"], s["n_switches"], s["n_identities"]) for s in summary.values()) == [("id_switch", 1, 2), ("id_switch", 1, 2)]
    tracks = {t["track_local_id"]: t["trk_id"] for t in art.tables["track"]}
    frames = {i: ({}, {}) for i in fixture["frames"]}
    for p in art.tables["track_point"]:
        frames[p["frame_index"]][0][tracks[p["track_nk"][1]]] = p["bbox_xyxy_px"]
    for i, key, _, box in fixture["truth"]:
        frames[i][1][key] = box
    r = idf1.idf1(frames, 0.5)
    assert (r["IDTP"], r["IDFN"], r["IDFP"]) == (60.0, 60.0, 60.0)
    assert r["IDF1"] == pytest.approx(0.5, abs=1e-12)


def test_idf1_toy_hand_calculation():
    a = (0.0, 0.0, 10.0, 10.0)
    frames = {0: ({"1": a, "3": (50.0, 50.0, 60.0, 60.0)}, {"A": a}), 1: ({"1": a}, {"A": a}), 2: ({"2": a}, {"A": a}), 3: ({"2": a}, {"A": a})}
    r = idf1.idf1(frames, 0.5)
    assert (r["IDTP"], r["IDFN"], r["IDFP"]) == (2.0, 2.0, 3.0)
    assert r["IDF1"] == pytest.approx(2 / 4.5, abs=1e-12)


def test_idf1_perfect_and_empty():
    a = (0.0, 0.0, 10.0, 10.0)
    assert idf1.idf1({0: ({"t": a}, {"g": a}), 1: ({"t": a}, {"g": a})})["IDF1"] == 1.0
    assert idf1.idf1({0: ({}, {"g": a})})["IDF1"] == 0.0
