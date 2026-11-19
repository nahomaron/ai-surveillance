"""T-22 zero-shot probe (D-42 option (a), Owner instruction of 19 Nov 2026): frame selection and reference boxes.
Runs in the project `.venv` (PyAV, rq1). The detectors run in `.venv-det` (`zero_shot_probe.py`), reading what this writes.

Selection, fixed before any detector is run:
- 100 SDG validation frames: 5 from each of 20 validation cameras, 10 ceiling and 10 eye-level.
- Pool: the SDG validation cameras of the frozen split (`docs/preregistration/freeze_record.json`,
  `sdg_validation_runs`) that have an ORACLE-S3 (T17.4 usable truth), from `research/datasets/part3/t17_counts_sdg.json`.
  Viewpoint = camera name prefix (`ceiling_*` -> ceiling, `eye_*` -> eye_level).
- Draw: one numpy PCG64 generator seeded with 2026111901; ceiling first, then eye_level; each pool sorted by rec_id;
  10 drawn by simple random sampling without replacement (`rng.choice(n, 10, replace=False)`), the same draw style as
  the split draw (`rq1.splits.draw`). The selected cameras are listed in rec_id order within each viewpoint.
- Frames: 5 evenly spaced over the recording's eligible frames: positions floor((2j + 1) * n / 10), j = 0..4, in the
  frame_index-sorted list of eligible frames (n = 300 -> frame_index 30, 90, 150, 210, 270).
- No SmartSpaces, no test partition (refused with ERR-LEAKAGE), no real footage.

Reference: the simulator boxes of the oracle path (T17.1 `tracked` points after T17.5: dataset-visible and eligible
objects only), in CF-IMG (T17 box convention, AR-53 item 3), clipped to the image rectangle [0, W] x [0, H].

  PYTHONPATH=src .venv/bin/python research/m1b/zero_shot_frames.py select            -> prints the selection
  PYTHONPATH=src .venv/bin/python research/m1b/zero_shot_frames.py extract <out_dir> -> <out_dir>/NNN.npy + frames.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SEED = 2026111901
PER_VIEWPOINT = 10
FRAMES_PER_CAMERA = 5
VIEWPOINTS = ("ceiling", "eye_level")
CLASSES = ("person", "forklift")


class LeakageError(Exception):
    """A test-partition (or unknown) recording was offered to the probe (D-37: test partition reserved)."""

    code = "ERR-LEAKAGE"


def viewpoint(camera: str) -> str:
    if camera.startswith("ceiling_"):
        return "ceiling"
    if camera.startswith("eye_"):
        return "eye_level"
    raise ValueError(f"unknown viewpoint for camera {camera!r}")


def require_validation(cam: dict, validation_runs) -> dict:
    if cam["run"] not in set(validation_runs):
        raise LeakageError(f"{cam['rec_id']} (run {cam['run']}) is not in the SDG validation partition (D-37)")
    return cam


def select(cameras: list[dict], validation_runs, seed: int = SEED, k: int = PER_VIEWPOINT) -> list[dict]:
    """The probe cameras: k per viewpoint, drawn from validation cameras with an ORACLE-S3."""
    val = set(validation_runs)
    rng = np.random.Generator(np.random.PCG64(seed))
    out = []
    for vp in VIEWPOINTS:
        pool = sorted((c for c in cameras if c["run"] in val and c.get("s3") and viewpoint(c["camera"]) == vp), key=lambda c: c["rec_id"])
        if len(pool) < k:
            raise ValueError(f"only {len(pool)} {vp} validation cameras, {k} needed")
        chosen = sorted((pool[int(i)] for i in rng.choice(len(pool), k, replace=False)), key=lambda c: c["rec_id"])
        out += [dict(require_validation(c, val), viewpoint=vp) for c in chosen]
    return out


def even_positions(n: int, k: int = FRAMES_PER_CAMERA) -> list[int]:
    return [(2 * j + 1) * n // (2 * k) for j in range(k)]


def clip_box(box, w: float, h: float):
    """CF-IMG box clipped to [0, w] x [0, h]; None when nothing is left."""
    x1, y1, x2, y2 = max(0.0, box[0]), max(0.0, box[1]), min(float(w), box[2]), min(float(h), box[3])
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None


def committed_inputs():
    freeze = json.load(open(ROOT / "docs/preregistration/freeze_record.json"))
    counts = json.load(open(ROOT / "research/datasets/part3/t17_counts_sdg.json"))
    return counts["cameras"], freeze["split"]["sdg_validation_runs"]


def extract(out_dir: Path, seed: int = SEED, exclude: frozenset = frozenset()) -> None:
    """`seed` and `exclude` (rec_ids left out of the pool) are used by the T-25p frame-level check (D-45 item 3c:
    seed 2026111902, probe cameras excluded); the probe itself used the defaults."""
    import av
    sys.path.insert(0, str(ROOT / "research/m1a"))
    import m1a_common as m
    from rq1.adapters import oracle_truth as ot

    cameras, validation_runs = committed_inputs()
    ctx = m.Context("sdg")
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = []
    for cam in select([c for c in cameras if c["rec_id"] not in exclude], validation_runs, seed):
        ctx.camera(cam["rec_id"])  # second guard: the M1a driver's own ERR-LEAKAGE refusal
        data = m.load(ctx, cam["rec_id"])
        entry = ctx.index[cam["rec_id"]]
        summary = data.s1["decode_summary"][0]
        w, h = summary["width_px"], summary["height_px"]
        eligible = sorted(i for i in data.seq.values() if i is not None)
        targets = {eligible[p]: None for p in even_positions(len(eligible))}
        seq_of = {i: k for k, i in data.seq.items() if i in targets}
        inel = frozenset(k for k, i in data.seq.items() if i is None)
        tracks, _ = ot.camera_tracks(entry["calibration"], data.frames, m.S4_BASE["g_max"], inel)
        refs = {k: [] for k in seq_of.values()}
        for key, points in sorted(tracks.items(), key=lambda kv: str(kv[0])):
            for p in points:
                if p.decode_seq in refs and p.state == "tracked":
                    cls = data.classes[key]
                    box = clip_box(p.box, w, h)
                    if box is not None:
                        refs[p.decode_seq].append({"object": str(key), "class": cls, "box": [round(v, 3) for v in box]})
        want = set(seq_of.values())
        with av.open(str(ROOT / "data" / entry["uri"])) as container:
            for k, frame in enumerate(container.decode(video=0)):
                if k in want:
                    i = data.seq[k]
                    name = f"{len(meta):03d}.npy"
                    img = frame.to_ndarray(format="rgb24")
                    assert img.shape == (h, w, 3), img.shape
                    np.save(out_dir / name, img)
                    meta.append({"file": name, "rec_id": cam["rec_id"], "run": cam["run"], "camera": cam["camera"], "viewpoint": cam["viewpoint"],
                                 "frame_index": i, "decode_seq": k, "width_px": w, "height_px": h, "references": refs[k]})
                    want.discard(k)
                if not want:
                    break
        assert not want, f"{cam['rec_id']}: frames not decoded {sorted(want)}"
    (out_dir / "frames.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"wrote {len(meta)} frames to {out_dir}")


if __name__ == "__main__":
    if sys.argv[1] == "select":
        for c in select(*committed_inputs()):
            print(c["viewpoint"], c["rec_id"], c["run"], c["camera"])
    elif sys.argv[1] == "extract":
        extract(Path(sys.argv[2]))
