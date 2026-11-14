"""Oracle track points and reference visibility from simulator truth, per camera (Appendix T T17 as amended by T18,
contract E-1.2.16).

T17.1 visible frame -> `tracked` with the dataset's visible box (SDG tight box; SmartSpaces visible-list entry).
T17.2 not-visible frame between the object's first and last visible frame in the camera -> `predicted` with the
      image-clipped reprojection of the object's 3D box; `lost` (no point) when that reprojection is empty.
      T18 amendment 2: only when the run of consecutive not-visible frames it belongs to has <= g_max frames (the T8.1
      parameter). A longer run is `lost` on every frame (no points); the track continues when the object is visible again.
      Run lengths count the camera's frames as the truth lists them (decoded frames; CR-024).
T17.3 no point outside the visible span; an object never visible in the camera has no track. The SDG loose box is never
      a track point.
T17.4 a camera has simulator truth only when every annotation file has as many lines as the video has frames and camera
      parameters exist.
T17.5 (SDG) loose-box excess beyond the clipped reprojected 3D box: > 120 px -> truth_defect, the object-frame is treated
      as not visible (3D pose kept); an excess in (90, 150] px (T18 amendment 1) -> ERR-INVARIANT; a box with a 3D corner
      behind the camera is not checked (counted).
T17.6 reference visible support = the T17.1 frames after T17.5 (`reference_objects`).

Coordinates (AR-53 item 3): track-point boxes are CF-IMG (E-1.2.1: origin at the top-left corner, pixel centre at
(i + 0.5, j + 0.5), x1 < x2, y1 < y2). Both datasets give boxes as inclusive pixel indices (maxima W-1 and H-1; one-pixel
boxes with x1 = x2), so a dataset box [x0, y0, x1, y1] covers pixels x0..x1 and is [x0, y0, x1 + 1, y1 + 1] in CF-IMG
(`cf_img`). The T17.5 excess is computed in dataset coordinates, as the ruling's figures were (`sdg_truth.hull_excess`).

Image-clipped reprojection (AR-53 items 1-2): the 3D box is cut at the near plane z_cam = NEAR_M, its vertices are
projected, and the convex hull of the projections is clipped to the image rectangle [0, W] x [0, H] (CF-IMG); the result
is the bounding box of that polygon, or empty when the polygon has no area.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable

import numpy as np

from rq1.schema.errors import ContractError
from rq1.substrate.surrogate import hull

from . import sdg_truth, smartspaces

DEFECT_PX = 120.0  # T17.5: adapter data-quality parameter, not a research threshold
REFUSE_BAND_PX = (90.0, 150.0)  # T17.5 as amended by T18: an excess in (90, 150] px is refused
NEAR_M = 1e-3  # near plane of the reprojection (AR-53 item 1)
VISIBILITY_NOTE = "reference visibility: binary, dataset-defined, no minimum visible area"  # T17.6 report text
_EDGES = [(a, a | bit) for a in range(8) for bit in (1, 2, 4) if not a & bit]  # corners are indexed 4*ix + 2*iy + iz
Box = tuple[float, float, float, float]


def _clip_polygon(poly: list[tuple[float, float]], w: float, h: float) -> list[tuple[float, float]]:
    """Sutherland-Hodgman against the rectangle [0, w] x [0, h]."""
    for axis, bound, keep_below in ((0, 0.0, False), (0, w, True), (1, 0.0, False), (1, h, True)):
        out: list[tuple[float, float]] = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            p_in = p[axis] <= bound if keep_below else p[axis] >= bound
            q_in = q[axis] <= bound if keep_below else q[axis] >= bound
            if p_in:
                out.append(p)
            if p_in != q_in:
                u = (bound - p[axis]) / (q[axis] - p[axis])
                out.append((p[0] + u * (q[0] - p[0]), p[1] + u * (q[1] - p[1])))
        poly = out
        if not poly:
            break
    return poly


def clipped_reprojection(cal: dict[str, Any], corners: np.ndarray) -> Box | None:
    """T17.2 box: the image-clipped reprojection of a 3D box (8 world corners); None when it is empty."""
    k = np.array(cal["intrinsics_K"], float).reshape(3, 3)
    r = np.array(cal["R_cam_from_world"], float).reshape(3, 3)
    cam = corners @ r.T + np.array(cal["t_cam_from_world_m"], float)
    points = [c for c in cam if c[2] >= NEAR_M]
    for a, b in _EDGES:  # where an edge crosses the near plane
        za, zb = cam[a][2], cam[b][2]
        if (za < NEAR_M) != (zb < NEAR_M):
            points.append(cam[a] + (NEAR_M - za) / (zb - za) * (cam[b] - cam[a]))
    if not points:
        return None  # behind the camera
    uv = [(float((k[0] @ p) / p[2]), float((k[1] @ p) / p[2])) for p in points]
    poly = list(hull(uv))
    if len(poly) < 3:
        return None
    w, h = cal["image_size_px"]
    poly = _clip_polygon(poly, float(w), float(h))
    if len(poly) < 3:
        return None
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    box = (min(xs), min(ys), max(xs), max(ys))
    return box if box[2] > box[0] and box[3] > box[1] else None


def cf_img(box: tuple) -> Box:
    """A dataset box in inclusive pixel indices -> CF-IMG edges."""
    return (float(box[0]), float(box[1]), float(box[2]) + 1.0, float(box[3]) + 1.0)


@dataclass(frozen=True)
class Obs:
    """One object on one decoded frame in one camera."""
    cls: str
    visible: Box | None  # the dataset's visible box in dataset pixel indices (after T17.5)
    corners: Any  # 8 world corners of the 3D box (8 x 3), or a zero-argument callable returning them (computed only when needed)
    xy: tuple[float, float]
    yaw: float | None


@dataclass(frozen=True)
class Point:
    decode_seq: int
    state: str  # tracked | predicted
    box: Box
    xy: tuple[float, float]
    yaw: float | None


def usable_truth(n_video_frames: int, annotation_lines: dict[str, int | None]) -> bool:
    """T17.4. `annotation_lines`: every annotation file of the camera (camera parameters included) -> its line count,
    None when the file does not exist."""
    return bool(annotation_lines) and all(n == n_video_frames for n in annotation_lines.values())


def sdg_obs(cal: dict[str, Any], obj: sdg_truth.ObjectTruth) -> tuple[Obs, str | None]:
    """One SDG object-frame under T17.5. Returns the observation and `truth_defect`, `unchecked` or None.
    Forklift yaw = the box long-axis yaw, the "simulator yaw when supplied" of T8.2 (CR-023 / D-32, Architect 14 Nov 2026)."""
    note, visible = None, obj.tight
    if obj.loose is not None:
        excess = sdg_truth.hull_excess(cal, obj)
        if excess is None:
            note = "unchecked"  # a 3D corner behind the camera (stated limitation)
        elif REFUSE_BAND_PX[0] < excess <= REFUSE_BAND_PX[1]:
            raise ContractError("ERR-INVARIANT", f"T17.5: loose-box excess {excess:.1f} px of {obj.prim} lies in (90, 150] px")
        elif excess > DEFECT_PX:
            note, visible = "truth_defect", None
    return Obs(obj.cls, visible, sdg_truth.box_corners(obj.box3d), obj.xy, obj.yaw if obj.cls == "forklift" else None), note


def smartspaces_obs(obj: smartspaces.ObjectTruth, camera: str) -> Obs:
    return Obs(obj.cls, obj.visible.get(camera), lambda: smartspaces.box_corners(obj), obj.xy, obj.yaw)


def _visible_frames(frames: list[dict[Hashable, Obs]]) -> dict[Hashable, list[int]]:
    seen: dict[Hashable, list[int]] = {}
    for k, objs in enumerate(frames):
        for key, o in objs.items():
            seen.setdefault(key, [])
            if o.visible is not None:
                seen[key].append(k)
    return seen


def _runs(visible: list[int]) -> list[tuple[int, int]]:
    """(first frame, length) of every run of not-visible frames between consecutive visible frames."""
    return [(a + 1, b - a - 1) for a, b in zip(visible, visible[1:]) if b - a > 1]


def not_visible_spans(frames: list[dict[Hashable, Obs]]) -> dict[Hashable, list[tuple[int, int]]]:
    """(first decoded frame, length) of every not-visible run inside each object's visible span, in frame order.
    Objects that are never visible have no span and are left out."""
    return {key: _runs(visible) for key, visible in _visible_frames(frames).items() if visible}


def not_visible_runs(frames: list[dict[Hashable, Obs]]) -> dict[Hashable, list[int]]:
    """T18 amendment 3: the lengths (frames) of those runs."""
    return {key: [n for _, n in runs] for key, runs in not_visible_spans(frames).items()}


def run_length_summary(lengths: list[int]) -> dict[str, int | None]:
    """min, median, P90, P99, max of run lengths in frames. Percentiles are nearest-rank: the value at rank ceil(q n) of the
    sorted lengths (always an observed length)."""
    v = sorted(lengths)
    rank = lambda num, den: v[max(1, -(-num * len(v) // den)) - 1] if v else None
    return {"runs": len(v), "frames": sum(v), "min": v[0] if v else None, "median": rank(1, 2), "p90": rank(9, 10), "p99": rank(99, 100),
            "max": v[-1] if v else None}


def camera_tracks(cal: dict[str, Any], frames: list[dict[Hashable, Obs]], g_max: int) -> tuple[dict[Hashable, list[Point]], dict[str, int]]:
    """T17.1-T17.3 for one camera, with the T18 absence length. `frames[k]`: object key -> observation on decoded frame k.
    Returns the points of every object that is visible at least once (sorted by decode_seq) and the T17.7 counts.
    `lost` counts every lost frame; `lost_long_run` is the part of it that lies in runs longer than g_max."""
    if g_max < 0:
        raise ContractError("ERR-SPEC", f"g_max must be >= 0, got {g_max}")
    counts = {"tracked": 0, "predicted": 0, "lost": 0, "lost_long_run": 0, "outside_span": 0, "never_visible_objects": 0}
    seen = _visible_frames(frames)
    tracks: dict[Hashable, list[Point]] = {}
    for key in sorted(seen, key=str):
        visible = seen[key]
        present = sum(1 for objs in frames if key in objs)
        if not visible:
            counts["never_visible_objects"] += 1
            counts["outside_span"] += present
            continue
        long_run = {k for start, n in _runs(visible) if n > g_max for k in range(start, start + n)}
        points = []
        for k in range(visible[0], visible[-1] + 1):
            o = frames[k].get(key)
            if o is not None and o.visible is not None:
                points.append(Point(k, "tracked", cf_img(o.visible), o.xy, o.yaw))
                counts["tracked"] += 1
                continue
            if k in long_run:
                counts["lost"] += 1  # T18 amendment 2: a run longer than g_max is lost on every frame
                counts["lost_long_run"] += 1
                continue
            box = None if o is None else clipped_reprojection(cal, o.corners() if callable(o.corners) else o.corners)
            if box is None:
                counts["lost"] += 1  # T17.2: empty reprojection (or no pose on this frame): no point
            else:
                points.append(Point(k, "predicted", box, o.xy, o.yaw))
                counts["predicted"] += 1
        counts["outside_span"] += present - sum(1 for k in range(visible[0], visible[-1] + 1) if key in frames[k])
        tracks[key] = points
    return tracks, counts


def s3_truth(tracks: dict[Hashable, list[Point]], classes: dict[Hashable, str], seq_to_index: dict[int, int | None]) -> tuple[list[dict], dict]:
    """Input of `OracleTrackSource.tracks` and the S4 oracle positions. Points on frames without a frame_index (not
    eligible) are left out; a track left without points is dropped. local_id = 1.. in sorted key order of all tracks.
    Simulator positions carry a zero covariance (AR-36 item 4)."""
    truth, positions = [], {}
    for local_id, key in enumerate(sorted(tracks, key=str), 1):
        points = [(seq_to_index.get(p.decode_seq), p) for p in tracks[key]]
        points = [(i, p) for i, p in points if i is not None]
        if not points:
            continue
        truth.append({"local_id": local_id, "class": classes[key], "physical_identity_id": str(key),
                      "points": [{"frame_index": i, "bbox": list(p.box), "state": p.state} for i, p in points]})
        for i, p in points:
            positions[(local_id, i)] = {"xy": [p.xy[0], p.xy[1]], "cov": [0.0, 0.0, 0.0], **({"yaw": p.yaw} if p.yaw is not None else {})}
    return truth, positions


def reference_objects(tracks: dict[Hashable, list[Point]], classes: dict[Hashable, str], seq_to_index: dict[int, int | None]) -> list[dict]:
    """T17.6: CV-SIM `truth["objects"]`. An object is present, with its visible box and simulator position, on its T17.1
    frames (after T17.5) only."""
    out = []
    for key in sorted(tracks, key=str):
        frames = {seq_to_index[p.decode_seq]: {"bbox": list(p.box), "xy": [p.xy[0], p.xy[1]]}
                  for p in tracks[key] if p.state == "tracked" and seq_to_index.get(p.decode_seq) is not None}
        if frames:
            out.append({"physical_identity_id": str(key), "class": classes[key], "frames": frames})
    return out
