"""S2 detector stage: raw detector boxes -> `detection` rows (E-1.2.1 section 5.4; Appendix T T8.6; D-45 items 0 and 2; AR-62).

The detector itself runs in `.venv-det` (`research/m1b/s2_yolo_world.py`); this module builds the S2 artifact from its
raw output in the main environment. S2 is reproducibility class `tolerance` (E-1.2.1 section 10; `TOLERANCE_STAGES`).

- One row per kept box. A box is kept when its score >= the class threshold (D-45 item 0, fixed from the T-22 probe:
  YOLO-World v2-s person 0.20, forklift 0.05). Classes other than the prompted ones never occur.
- det_index: 0.. per frame, ordered by class (object_class enum order: person before forklift), then descending score,
  then x1, then y1 (section 5.4; enum order for "class" is AR-62 item 1).
- truncated: the box is within 1 px of an image border (T8.6): x1 <= 1 or y1 <= 1 or x2 >= W - 1 or y2 >= H - 1.
- score: the raw detector score (not a probability); score_calibrated null (`not_computed_by_config`).
- model_component_id: the `license_component` anchor ID of the weights (`weights_component`).
"""
from __future__ import annotations

from typing import Any

from rq1.ids import core
from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema.tables import ENUMS

Row = dict[str, Any]
THRESHOLDS = {"person": 0.20, "forklift": 0.05}  # D-45 item 0 (YOLO-World v2-s)
_RANK = {c: i for i, c in enumerate(ENUMS["object_class"])}


def weights_component(name: str, sha256: str, url: str, license_label: str) -> Row:
    """The `license_component` row of a weights file (version = its SHA-256)."""
    return {"component": name, "version": f"sha256:{sha256}", "component_type": "model_weights", "license_label": license_label,
            "terms_location": "license_file", "obligations": ["source_url " + url], "license_status": "verified", "verified_utc": None,
            "verified_utc_null_reason": "not_supplied", "decision_ref": "D-43", "decision_ref_null_reason": None}


def component_id(row: Row) -> str:
    return core.anchor_id("lic", "license_component", [row["component"], row["version"]])


def truncated(box: list[float], width: float, height: float) -> bool:
    """T8.6: within 1 px of an image border."""
    x1, y1, x2, y2 = box
    return x1 <= 1.0 or y1 <= 1.0 or x2 >= width - 1.0 or y2 >= height - 1.0


def detection_rows(recording_id: str, raw: dict[int, list[dict]], width: float, height: float, model_component_id: str,
                   thresholds: dict[str, float] = THRESHOLDS) -> list[Row]:
    """`raw`: frame_index -> [{"class", "box", "score"}] as the detector returned them (any score)."""
    rows = []
    for i in sorted(raw):
        kept = [d for d in raw[i] if d["class"] in thresholds and d["score"] >= thresholds[d["class"]]]
        kept.sort(key=lambda d: (_RANK[d["class"]], -d["score"], d["box"][0], d["box"][1]))
        for k, d in enumerate(kept):
            box = [float(v) for v in d["box"]]
            rows.append({"recording_id": recording_id, "frame_index": i, "det_index": k, "class": d["class"], "bbox_xyxy_px": box,
                         "truncated": truncated(box, width, height), "score": float(d["score"]), "score_calibrated": None,
                         "score_calibrated_null_reason": "not_computed_by_config", "model_component_id": model_component_id})
    return rows


def build(recording_id: str, raw: dict[int, list[dict]], width: float, height: float, model_component_id: str, spec: Spec,
          thresholds: dict[str, float] = THRESHOLDS, license_rows: list[Row] | None = None) -> Artifact:
    """`license_rows` (D-47 item 5, from D-55 step 1 on): the `license_component` rows of every weight file the run
    loads, stored in the artifact beside the detections. Omitted (the pilot builds): the payload is `detection` only, so
    earlier S2 artifact IDs are unchanged."""
    if spec.stage != "S2":
        raise ValueError(spec.stage)
    tables = {"detection": detection_rows(recording_id, raw, width, height, model_component_id, thresholds)}
    if license_rows is not None:
        ids = [component_id(r) for r in license_rows]
        if model_component_id not in ids or len(set(ids)) != len(ids):
            raise ValueError("license_rows must hold the detector weights' row once, and no row twice")
        tables["license_component"] = sorted(license_rows, key=lambda r: (r["component"], r["version"]))
    return build_artifact(spec, tables)
