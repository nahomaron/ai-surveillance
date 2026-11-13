"""SDG-Warehouse per-camera truth (T-18 part B, WP-13): object classes, simulator floor poses and the raw 2D boxes.

One `object_detection.jsonl` line per video frame, in presentation order (line k <-> decode_seq k, not frame_index, which
renumbers eligible frames only; AR-50). Per frame, `agents` maps a prim path to its annotators and agent data.

- Class: the forklift is identified by prim name (`/World/Robots/forklift/Forklift`; its label class is `robot`, qualification
  Part 2); a person is an agent with label class `character`. Anything else is not an E1 pair object.
- Pose: `metro_agent_data.world_position` is constant over a run while the objects move (a stale initial pose), so it is
  not used. The pose is the 3D box: USD row-vector transform T (p_world = [p_local, 1] . T). The footprint centre is the
  centre of the box's floor face, ((x_min + x_max)/2, (y_min + y_max)/2, z_min) in local coordinates (D-8: the oracle and
  simulator path uses the simulator footprint centre). Yaw is the direction of the local x axis, atan2(T01, T00), in
  (-pi, pi]; the footprint rectangle is symmetric, so the sign of the axis does not matter.
- Boxes: `loose` (full projected extent) is present whenever the object is annotated; `tight` (visible pixels) only when
  the object is visible in that camera. Which box feeds the oracle tracks, and the state of a not-visible frame, are open
  (CR-019); this module only reads them.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from rq1.schema.errors import ContractError

FORKLIFT_PRIM = "/World/Robots/forklift/Forklift"
PERSON_LABEL = "character"


@dataclass(frozen=True)
class ObjectTruth:
    prim: str
    cls: str  # person | forklift
    xy: tuple[float, float]  # footprint centre, world metres
    yaw: float  # local x axis direction, (-pi, pi]
    loose: tuple[int, int, int, int] | None  # [x_min, y_min, x_max, y_max] px
    tight: tuple[int, int, int, int] | None  # None: not visible in this camera
    box3d: dict[str, Any]  # the raw `bounding_box_3d_fast` record (local extents and transform)


def object_class(prim: str, agent: dict[str, Any]) -> str | None:
    if prim == FORKLIFT_PRIM:
        return "forklift"
    if agent.get("label", {}).get("class") == PERSON_LABEL:
        return "person"
    return None


def _wrap(angle: float) -> float:
    return math.pi if angle <= -math.pi else angle


def floor_pose(box3d: dict[str, Any]) -> tuple[tuple[float, float], float]:
    t = np.array(box3d["transform"], float)
    local = np.array([(box3d["x_min"] + box3d["x_max"]) / 2, (box3d["y_min"] + box3d["y_max"]) / 2, box3d["z_min"], 1.0])
    world = local @ t
    return (float(world[0]), float(world[1])), _wrap(math.atan2(float(t[0, 1]), float(t[0, 0])))


def box_corners(box3d: dict[str, Any]) -> np.ndarray:
    """The 8 world corners (8 x 3) of the 3D box."""
    t = np.array(box3d["transform"], float)
    c = np.array([[x, y, z, 1.0] for x in (box3d["x_min"], box3d["x_max"]) for y in (box3d["y_min"], box3d["y_max"])
                  for z in (box3d["z_min"], box3d["z_max"])])
    return (c @ t)[:, :3]


def _box(record: dict[str, Any] | None) -> tuple[int, int, int, int] | None:
    return None if record is None else (record["x_min"], record["y_min"], record["x_max"], record["y_max"])


def parse_frame(line: str | bytes) -> list[ObjectTruth]:
    """E1 objects of one frame, sorted by prim path. Objects without a 3D box have no pose and are left out."""
    out = []
    for prim, agent in sorted(json.loads(line)["agents"].items()):
        cls = object_class(prim, agent)
        ann = agent.get("annotators", {})
        if cls is None or ann.get("bounding_box_3d_fast") is None:
            continue
        xy, yaw = floor_pose(ann["bounding_box_3d_fast"])
        out.append(ObjectTruth(prim, cls, xy, yaw, _box(ann.get("bounding_box_2d_loose_fast")), _box(ann.get("bounding_box_2d_tight_fast")),
                               ann["bounding_box_3d_fast"]))
    return out


def parse_camera(lines: Iterable[str | bytes], n_video_frames: int) -> list[list[ObjectTruth]]:
    """All frames of one camera; refuses an annotation file whose line count differs from the video's frame count, since
    line k could then not be tied to decode_seq k (the use of such cameras is CR-019 item 3)."""
    frames = [parse_frame(line) for line in lines]
    if len(frames) != n_video_frames:
        raise ContractError("ERR-INVARIANT", f"annotation has {len(frames)} lines, video has {n_video_frames} frames")
    return frames


def hull_excess(cal: dict[str, Any], obj: ObjectTruth) -> float | None:
    """Reprojection check (part A data check, now code): how far the dataset's loose box extends beyond the image-clipped
    projection of the 3D box, in px (<= 0: contained). None when a corner is behind the camera or there is no loose box."""
    from .sdg_camera import project

    if obj.loose is None:
        return None
    corners = box_corners(obj.box3d)
    r = np.array(cal["R_cam_from_world"]).reshape(3, 3)
    if ((corners @ r.T + np.array(cal["t_cam_from_world_m"]))[:, 2] <= 0).any():
        return None
    uv = project(cal, corners)
    w, h = cal["image_size_px"]
    hull = (max(uv[:, 0].min(), 0), max(uv[:, 1].min(), 0), min(uv[:, 0].max(), w - 1), min(uv[:, 1].max(), h - 1))
    lb = obj.loose
    return float(max(hull[0] - lb[0], hull[1] - lb[1], lb[2] - hull[2], lb[3] - hull[3]))
