"""ORACLE-S3 (E-1.2.1 section 10.1): fixture or simulator-truth tracks become an S3 artifact."""
from __future__ import annotations

from typing import Any

from rq1.ids.artifact import Artifact, Spec, build_artifact

from . import durations

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


class OracleTrackSource:
    """Oracle `tracked` points count as detected: the simulator truth stands in for the detection (AR-29)."""

    def tracks(self, recording_id: str, truth: list[Row], frames: list[Row], spec: Spec) -> Artifact:
        track_rows, point_rows = [], []
        for track in truth:
            points = sorted(track["points"], key=lambda p: p["frame_index"])
            states = {p["frame_index"]: p["state"] for p in points}
            start, end = points[0]["frame_index"], points[-1]["frame_index"] + 1
            a, b = durations.interval_extent(frames, start, end)
            split = durations.class_durations(frames, a, b, lambda i: durations.object_class(states.get(i)))
            runs = _gaps([states.get(i, "lost") for i in range(start, end)])
            track_rows.append({"recording_id": recording_id, "track_local_id": track["local_id"], "class": track["class"], "start_frame": start,
                               "end_frame_excl": end, "span_s": b - a, "t_detected_s": split["detected"], "t_inferred_s": split["inferred"],
                               "t_insufficient_s": split["insufficient"], "n_gaps": len(runs), "max_gap_frames": max(runs, default=0), "id_switch_suspect": False})
            for p in points:
                x1, y1, x2, y2 = p["bbox"]
                point_rows.append({"track_nk": [recording_id, track["local_id"]], "frame_index": p["frame_index"], "detection_id": None,
                                   "detection_id_null_reason": "not_applicable", "bbox_xyxy_px": list(p["bbox"]), "state": p["state"],
                                   "foot_point_px": [(x1 + x2) / 2, y2], "evidence_class": durations.object_class(p["state"])})
        return build_artifact(spec, {"track": track_rows, "track_point": point_rows})
