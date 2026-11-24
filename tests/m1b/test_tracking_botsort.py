"""D-55 step 2: Ultralytics BoT-SORT adapter (T2 comparator).

Runs in `.venv-det` (`PYTHONPATH=src .venv-det/bin/python -m unittest discover -s tests/m1b -p 'test_tracking_*.py'`);
skipped in the main suite, where Ultralytics is not installed.

Expected values:
- configuration: the installed `botsort.yaml` (read here from the file text, independently of the adapter's loader)
  with exactly `with_reid: false` and `gmc_method: none` changed.
- 10-frame, two-object fixture (hand-built): object A, a 100 x 80 box moving +5 px per frame in x, score 0.9; object B,
  a 60 x 120 box fixed at (400, 300), score 0.8. Hand reasoning (installed byte_tracker.py / bot_sort.py): both scores
  >= track_high_thresh 0.25 and new_track_thresh 0.25; on frame 0 (the tracker's first frame) both tracks are activated
  and reported; on every later frame the predicted box of each track overlaps its own object with IoU close to 1 and the
  other object with IoU 0 (the boxes never overlap), so each cost 1 - IoU * score <= 1 - 0.9 * 0.8 < 0.8 and each track
  keeps its object: 10 tracked points per track, two tracker IDs, no lost track. The run is repeated: identical logs.
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

HAVE_ULTRALYTICS = importlib.util.find_spec("ultralytics") is not None


def two_objects(cls="forklift"):
    dets = []
    for i in range(10):
        a = [100.0 + 5 * i, 100.0, 200.0 + 5 * i, 180.0]
        dets.append({"frame_index": i, "det_index": 0, "class": cls, "bbox_xyxy_px": a, "score": 0.9})
        dets.append({"frame_index": i, "det_index": 1, "class": cls, "bbox_xyxy_px": [400.0, 300.0, 460.0, 420.0], "score": 0.8})
    return list(range(10)), dets


def yaml_text_defaults():
    import ultralytics
    out = {}
    for line in (Path(ultralytics.__file__).parent / "cfg/trackers/botsort.yaml").read_text().splitlines():
        m = re.match(r"^(\w+):\s*([^#\s]+)", line)
        if m:
            v = m.group(2)
            out[m.group(1)] = {"True": True, "False": False}.get(v, v)
    return out


@unittest.skipUnless(HAVE_ULTRALYTICS, "Ultralytics runs in .venv-det only")
class BoTSORTAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from rq1.tracking import botsort, grid
        cls.bs, cls.grid = botsort, grid

    def test_default_config_is_installed_except_two_switched_off(self):
        raw = yaml_text_defaults()
        cfg = self.bs.default_params()
        self.assertEqual(set(cfg), set(raw))
        changed = {k for k in raw if str(cfg[k]) != str(raw[k])}
        self.assertEqual(changed, {"gmc_method"})  # with_reid is already false in the installed file
        self.assertIs(cfg["with_reid"], False)
        self.assertEqual(cfg["gmc_method"], "none")
        for k in ("track_high_thresh", "track_low_thresh", "new_track_thresh", "match_thresh", "proximity_thresh", "appearance_thresh"):
            self.assertEqual(cfg[k], float(raw[k]), k)
        self.assertEqual(cfg["track_buffer"], 30)
        self.assertEqual(cfg["tracker_type"], "botsort")

    def test_compensation_is_off_and_no_image_is_needed(self):
        from types import SimpleNamespace
        BOTSORT = self.bs._prepare()  # lap stub first: the tracker modules import `lap`
        t = BOTSORT(SimpleNamespace(**self.bs.default_params()))
        self.assertIsNone(t.gmc.method)
        self.assertIsNone(t.encoder)

    def test_refuses_reid_or_compensation(self):
        frames, dets = two_objects()
        for bad in ({"with_reid": True}, {"gmc_method": "sparseOptFlow"}):
            with self.assertRaises(ValueError):
                self.bs.run_class(frames, dets, "forklift", {**self.bs.default_params(), **bad})

    def test_two_objects_tracked_identically_twice(self):
        frames, dets = two_objects()
        a = self.bs.run_class(frames, dets, "forklift")
        b = self.bs.run_class(frames, dets, "forklift")
        self.assertEqual(a, b)
        self.assertEqual([len(e["tracked"]) for e in a], [2] * 10)
        self.assertEqual([len(e["lost"]) for e in a], [0] * 10)
        per_track = {}
        for e in a:
            for tid, det_index, _ in e["tracked"]:
                per_track.setdefault(tid, set()).add(det_index)
        self.assertEqual(len(per_track), 2)
        self.assertEqual(sorted(map(sorted, per_track.values())), [[0], [1]])

    def test_numpy_assignment_path(self):
        import sys as _sys
        self.bs._prepare()
        with self.assertRaises(RuntimeError):
            _sys.modules["lap"].lapjv([[0.0]])

    def test_grid_job_equals_direct_run(self):
        from rq1.tracking import bytetrack
        frames, dets = two_objects()
        jobs = [{"job": "b", "tracker_id": "botsort", "class": "forklift", "params": self.bs.default_params()},
                {"job": "y", "tracker_id": "bytetrack", "class": "forklift", "params": bytetrack.default_config()["params"]}]
        out = self.grid.run(frames, dets, jobs)
        self.assertEqual(out["logs"]["b"], self.bs.run_class(frames, dets, "forklift"))
        self.assertEqual(out["logs"]["y"], bytetrack.run_class(frames, dets, "forklift"))


if __name__ == "__main__":
    unittest.main()
