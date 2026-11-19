"""Detector-path S3 artifact (E-1.2.1 sections 5.4 and 10; D-45 item 1; AR-62).

`DetectorTrackSource.tracks` turns the bridged tracker points (`rq1.tracking.bridging.points_from_log`, per class) and
the S2 `detection` rows of one recording into `track` and `track_point` rows, computed exactly as the oracle source
computes them (`rq1.substrate.oracle`), except that:
- a `tracked` point carries the matched detection's `det_id` (section 5.4; the box is the detection's box, AR-62 item 3);
- a `predicted` point carries no detection (`detection_id` null, `not_observable`, section 5.4);
- `id_switch_suspect` is false: ByteTrack flags no identity switch (T8.1: id_switch only where the tracker flags one).
Track local IDs: 1.. over the classes in object_class enum order (person, forklift), then by first frame, then by
tracker ID (AR-62 item 4).
"""
from __future__ import annotations

from typing import Any

from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema.tables import ENUMS
from rq1.substrate import durations

from .bridging import foot_point

Row = dict[str, Any]


def _gaps(states: list[str]) -> list[int]:
    runs, current = [], 0
    for state in states:
        if state != "tracked":
            current += 1
        elif current:
            runs.append(current)
            current = 0
    return runs + ([current] if current else [])


def local_order(points_by_class: dict[str, dict[int, dict]]) -> list[tuple[str, int]]:
    """(class, tracker ID) in local-ID order (AR-62 item 4)."""
    rank = {c: i for i, c in enumerate(ENUMS["object_class"])}
    keys = [(rank[c], tr["points"][0]["frame_index"], tid, c) for c, tracks in points_by_class.items() for tid, tr in tracks.items() if tr["points"]]
    return [(c, tid) for _, _, tid, c in sorted(keys)]


class DetectorTrackSource:
    def tracks(self, recording_id: str, points_by_class: dict[str, dict[int, dict]], detections: list[Row], frames: list[Row],
               spec: Spec) -> tuple[Artifact, dict[int, tuple[str, int]]]:
        """Returns the S3 artifact and local ID -> (class, tracker ID)."""
        det_id = {(d["frame_index"], d["det_index"]): d["det_id"] for d in detections}
        det_class = {(d["frame_index"], d["det_index"]): d["class"] for d in detections}
        eligible = {f["frame_index"] for f in frames if f["eligible"]}
        track_rows, point_rows, local_map = [], [], {}
        for local_id, (cls, tid) in enumerate(local_order(points_by_class), 1):
            local_map[local_id] = (cls, tid)
            points = points_by_class[cls][tid]["points"]
            for p in points:
                if p["frame_index"] not in eligible:
                    raise ValueError(f"track point on ineligible frame {p['frame_index']}")
                if p["state"] == "tracked" and det_class[(p["frame_index"], p["det_index"])] != cls:
                    raise ValueError(f"class mismatch on frame {p['frame_index']} detection {p['det_index']}")
            states = {p["frame_index"]: p["state"] for p in points}
            start, end = points[0]["frame_index"], points[-1]["frame_index"] + 1
            a, b = durations.interval_extent(frames, start, end)
            split = durations.class_durations(frames, a, b, lambda i: durations.object_class(states.get(i)))
            runs = _gaps([states.get(i, "lost") for i in range(start, end)])  # as the oracle source counts them
            track_rows.append({"recording_id": recording_id, "track_local_id": local_id, "class": cls, "start_frame": start, "end_frame_excl": end,
                               "span_s": b - a, "t_detected_s": split["detected"], "t_inferred_s": split["inferred"],
                               "t_insufficient_s": split["insufficient"], "n_gaps": len(runs), "max_gap_frames": max(runs, default=0),
                               "id_switch_suspect": False})
            for p in points:
                row = {"track_nk": [recording_id, local_id], "frame_index": p["frame_index"], "bbox_xyxy_px": list(p["bbox"]), "state": p["state"],
                       "foot_point_px": foot_point(p["bbox"]), "evidence_class": durations.object_class(p["state"])}
                if p["state"] == "tracked":
                    row.update(detection_id=det_id[(p["frame_index"], p["det_index"])], detection_id_null_reason=None)
                else:
                    row.update(detection_id=None, detection_id_null_reason="not_observable")
                point_rows.append(row)
        return build_artifact(spec, {"track": track_rows, "track_point": point_rows}), local_map
