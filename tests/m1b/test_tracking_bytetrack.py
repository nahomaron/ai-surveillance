"""T-23 (D-45 item 1): Ultralytics ByteTrack adapter on the oracle-detection fixtures (FX-TRK-1, FX-TRK-2).

Runs in `.venv-det` (`PYTHONPATH=src .venv-det/bin/python -m unittest discover -s tests/m1b -p 'test_tracking_*.py'`);
skipped in the main suite, where Ultralytics is not installed (the main suite runs the same fixtures through
`.venv-det` in `test_s3_detector_path.py`).

Expected values come from the fixture design (`rq1.fixtures.oracle_detections`) and the D-45 rule, not from a run:
- P1: predicted on 20..24 (5 frames); no point on 60..79 (20 frames > g_max); one tracker ID before and after.
- P2: predicted on 30..45 except the ineligible frame 38 (15 eligible frames = g_max).
- F1: no point on 70..109; two tracker IDs (the 40-frame dropout exceeds track_buffer 30).
- Swap: each track holds one location, so it reports Q1 then Q2 (or Q2 then Q1).
"""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from rq1.fixtures import oracle_detections as fx  # noqa: E402
from rq1.tracking import bridging as br  # noqa: E402

HAVE_ULTRALYTICS = importlib.util.find_spec("ultralytics") is not None


def identities(fixture, cls, points_by_track):
    """tracker ID -> list of (frame, state, identity of the matched detection or None)."""
    ident = {(d["frame_index"], d["det_index"]): d["_identity"] for d in fixture["detections"]}
    return {tid: [(p["frame_index"], p["state"], ident.get((p["frame_index"], p["det_index"])) if p["det_index"] is not None else None)
                  for p in tr["points"]] for tid, tr in points_by_track.items()}


@unittest.skipUnless(HAVE_ULTRALYTICS, "Ultralytics runs in .venv-det only")
class ByteTrackAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from rq1.tracking import bytetrack
        cls.bt = bytetrack
        cls.fx = fx.dropouts()
        cls.out = bytetrack.run(cls.fx["frames"], cls.fx["detections"])
        cls.pts = {c: br.points_from_log(cls.out["logs"][c]) for c in bytetrack.CLASSES}

    def tracks_of(self, cls, key):
        ids = identities(self.fx, cls, self.pts[cls])
        return {tid: pts for tid, pts in ids.items() if any(k == key for _, _, k in pts)}

    def test_p1_bridged_then_lost_long_run(self):
        tracks = self.tracks_of("person", "P1")
        self.assertEqual(len(tracks), 1, "P1 keeps one tracker ID across both dropouts")
        (pts,) = tracks.values()
        self.assertEqual([f for f, s, _ in pts if s == "predicted"], list(range(20, 25)))
        self.assertFalse({f for f, _, _ in pts} & set(range(60, 80)))
        self.assertTrue(all(k == "P1" for _, s, k in pts if s == "tracked"))

    def test_p2_bridge_counted_in_eligible_frames(self):
        (pts,) = self.tracks_of("person", "P2").values()
        self.assertEqual([f for f, s, _ in pts if s == "predicted"], [i for i in range(30, 46) if i != 38])

    def test_f1_fragment_after_long_dropout(self):
        tracks = self.tracks_of("forklift", "F1")
        self.assertEqual(len(tracks), 2)
        frames = sorted(f for pts in tracks.values() for f, _, _ in pts)
        self.assertFalse(set(frames) & set(range(70, 110)))
        self.assertFalse(any(s == "predicted" for pts in tracks.values() for _, s, _ in pts))
        # AR-62 item 7: a track started after the first frame is reported from its second matched frame on (ByteTrack
        # leaves it unconfirmed on its first); F1 reappears at frame 110, so the new track's first point is frame 111.
        self.assertEqual(sorted(pts[0][0] for pts in tracks.values()), [0, 111])

    def test_numpy_assignment_path(self):
        import sys as _sys
        self.assertEqual(self.out["config"]["assignment"], "ultralytics.utils.ops.linear_sum_assignment (use_lap=False)")
        with self.assertRaises(RuntimeError):
            _sys.modules["lap"].lapjv([[0.0]])  # AR-62 item 5: the stub is never used

    def test_no_cross_class_identity(self):
        for tid, pts in identities(self.fx, "forklift", self.pts["forklift"]).items():
            self.assertTrue(all(k in (None, "F1") for _, _, k in pts))

    def test_deterministic(self):
        self.assertEqual(self.bt.run(self.fx["frames"], self.fx["detections"]), self.out)

    def test_swap_switches_identity(self):
        s = fx.swap()
        out = self.bt.run(s["frames"], s["detections"])
        ids = identities(s, "person", br.points_from_log(out["logs"]["person"]))
        self.assertEqual(len(ids), 2)
        for pts in ids.values():
            seq = [k for _, _, k in pts]
            self.assertEqual(len(seq), 60)
            self.assertEqual(seq[0] != seq[30] and len(set(seq[:30])) == 1 and len(set(seq[30:])) == 1, True)

    def test_config_is_the_installed_default(self):
        cfg = self.out["config"]["params"]
        self.assertEqual(cfg, {"fuse_score": True, "match_thresh": 0.8, "new_track_thresh": 0.25, "track_buffer": 30, "track_high_thresh": 0.25,
                               "track_low_thresh": 0.1, "tracker_type": "bytetrack"})


if __name__ == "__main__":
    unittest.main()
