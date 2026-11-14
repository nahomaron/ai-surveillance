"""S0 registration (WP-03): anchors, timelines, clock alignments and tiered calibrations."""
from __future__ import annotations

from typing import Any

import numpy as np

from rq1.ids import core
from rq1.ids.anchors import AnchorRegistry
from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema import registry
from rq1.schema.errors import ContractError
from rq1.schema.validate import Issue

Row = dict[str, Any]
FULL_REQUIRED = ("intrinsics_K", "R_cam_from_world", "t_cam_from_world_m", "distortion_model", "distortion_coeffs")
GROUND_EXCLUDED = ("intrinsics_K", "R_cam_from_world", "t_cam_from_world_m", "reproj_error_px_rmse")


def _fill(table: str, given: Row) -> Row:
    """Complete a row: an absent nullable field is null `not_supplied`; a present value has no reason."""
    row: Row = {}
    for f in registry.TABLES[table].fields:
        if f.derived or f.name.endswith("_null_reason"):
            continue
        if f.name in given:
            row[f.name] = given[f.name]
        elif not f.nullable:
            raise ContractError("ERR-INVARIANT", f"{table}: required field {f.name} missing")
        else:
            row[f.name] = None
        if f.nullable:
            reason = f"{f.name}_null_reason"
            row[reason] = None if row[f.name] is not None else given.get(reason) or "not_supplied"
    return row


def _fill_struct(fields, given: Row) -> Row:
    out: Row = {}
    for f in fields:
        if f.name.endswith("_null_reason"):
            continue
        out[f.name] = given.get(f.name)
        if f.nullable:
            out[f"{f.name}_null_reason"] = None if out[f.name] is not None else given.get(f"{f.name}_null_reason") or "not_supplied"
    return out


def check_calibration(c: Row) -> list[Issue]:
    """CB-01 and CB-02, with the tier table of E-1.2.1 section 5.1."""
    def bad(message: str) -> Issue:
        return Issue("CB-01", "ERR-CALIB-TIER", "calibration", "calibration_tier", message)

    issues: list[Issue] = []
    if c["calibration_tier"] == "full_camera":
        issues += [bad(f"{name} is required") for name in FULL_REQUIRED if c.get(name) is None]
        if c.get("homography_assumes_undistorted") is not False:
            issues.append(bad("homography_assumes_undistorted must be false"))
    else:
        for name in GROUND_EXCLUDED:
            if c.get(name) is not None:
                issues.append(bad(f"{name} is excluded for this tier"))
            elif c.get(f"{name}_null_reason") != "not_applicable":
                issues.append(bad(f"{name} must be null with not_applicable"))
        if c.get("homography_img_to_floor") is None:
            issues.append(bad("homography_img_to_floor is required"))
        if c.get("distortion_model") is None and c.get("homography_assumes_undistorted") is not True:
            issues.append(bad("homography_assumes_undistorted must be true without a distortion model"))
    homography = c.get("homography_img_to_floor")
    if homography is not None and not issues and abs(np.linalg.det(np.array(homography, float).reshape(3, 3))) < 1e-12:
        issues.append(Issue("CB-02", "ERR-CALIB-TIER", "calibration", "homography_img_to_floor", "not invertible"))
    return issues


def check_load_state(state: Row, calibration: Row | None, multi_view: bool = False) -> list[Issue]:
    """CB-03: height needs a full_camera calibration with a height reference or multi-view, or simulator truth."""
    if state.get("height_m") is None or state["method"] == "simulator_truth":
        return []
    allowed = calibration is not None and calibration["calibration_tier"] == "full_camera" and (bool(calibration["height_reference_ids"]) or multi_view)
    return [] if allowed else [Issue("CB-03", "ERR-CALIB-TIER", "load_state", "height_m", "height requires full_camera with a height reference or multi-view, or simulator truth")]


def check_not_recorded(segment: Row, timeline: Row) -> list[Issue]:
    """TI-11."""
    if segment["coverage_state"] != "not_recorded":
        return []
    inside = timeline["kind"] == "aligned_session" and timeline["extent_start_tl_s"] <= segment["t_start_tl_s"] and segment["t_end_tl_s"] <= timeline["extent_end_tl_s"]
    return [] if inside else [Issue("TI-11", "ERR-INVARIANT", "coverage_segment", "coverage_state", "not_recorded only on aligned_session timelines within the declared extent")]


def _strip(data: Row, *names: str) -> Row:
    return {k: v for k, v in data.items() if k not in names}


class Registrar:
    """`Registrar.register` of E-1.2.1 section 10.2. Keeps ANC-1 across the S0 artifacts it builds."""

    def __init__(self) -> None:
        self.anchors = AnchorRegistry()
        self._file_rows: dict[str, str] = {}  # src_id -> dataset_source row (T16.1: each file belongs to exactly one row)

    def register(self, metadata: Row, spec: Spec) -> Artifact:
        tables: dict[str, list[Row]] = {name: [] for name in ("license_component", "dataset_source", "site", "session", "camera", "source_file", "recording", "timeline", "camera_group")}
        licenses = {}
        for item in metadata["licenses"]:
            tables["license_component"].append(_fill("license_component", item))
            licenses[(item["component"], item["version"])] = core.anchor_id("lic", "license_component", [item["component"], item["version"]])
        sessions, cameras, sites, frames = {}, {}, {}, {}
        for dataset in metadata["datasets"]:
            key = (dataset["name"], dataset["version"])
            dsr = core.anchor_id("dsr", "dataset_source", list(key))
            tables["dataset_source"].append(_fill("dataset_source", {**_strip(dataset, "sites", "license"), "license_component_id": licenses[tuple(dataset["license"])]}))
            for site in dataset["sites"]:
                sit = core.anchor_id("sit", "site", [dsr, site["site_label"]])
                sites[(key, site["site_label"])] = sit
                tables["site"].append(_fill("site", {**_strip(site, "cameras", "sessions", "world_frames", "context_maps"), "dataset_id": dsr}))
                for camera in site["cameras"]:
                    cameras[(key, site["site_label"], camera["camera_label"])] = core.anchor_id("cam", "camera", [sit, camera["camera_label"]])
                    tables["camera"].append(_fill("camera", {**camera, "site_id": sit}))
                for session in site["sessions"]:
                    ses = core.anchor_id("ses", "session", [sit, session["session_label"]])
                    sessions[(key, site["site_label"], session["session_label"])] = (ses, session.get("extent"))
                    lineage = _fill_struct(registry.TABLES["session"].fields[[f.name for f in registry.TABLES["session"].fields].index("lineage")].type.fields, session.get("lineage", {}))
                    tables["session"].append(_fill("session", {**_strip(session, "extent", "lineage"), "site_id": sit, "lineage": lineage}))
                for frame in site.get("world_frames", []):
                    frames[(key, site["site_label"], frame["label"], frame["version"])] = core.anchor_id("wf", "world_frame", [sit, frame["label"], frame["version"]])
                    tables.setdefault("world_frame", []).append(_fill("world_frame", {**frame, "site_id": sit}))
                for context in site.get("context_maps", []):
                    tables.setdefault("context_map", []).append(_fill("context_map", {**context, "site_id": sit}))
        tables["source_file"] = [_fill("source_file", item) for item in metadata["source_files"]]
        self._recordings(metadata, tables, sessions, cameras)
        for item in metadata.get("calibrations", []):
            self._calibration(item, tables, cameras, frames)
        tables = {name: rows for name, rows in tables.items() if rows}
        file_rows = self._file_dataset_rows(metadata)
        built = build_artifact(spec, tables)
        self.anchors.add(built)
        self._file_rows.update(file_rows)
        return built

    def _file_dataset_rows(self, metadata: Row) -> dict[str, str]:
        """T16.1 / VR-E-005: a file listed under two dataset_source rows is refused, within one registration or across
        the registrations of this registrar."""
        seen: dict[str, str] = {}
        for item in metadata["recordings"]:
            src, dsr = core.source_id(item["sha256"]), core.anchor_id("dsr", "dataset_source", list(item["dataset"]))
            if seen.setdefault(src, self._file_rows.get(src, dsr)) != dsr:
                raise ContractError("ERR-INVARIANT", f"T16.1: file {src} is listed under two dataset_source rows")
        return seen

    def _recordings(self, metadata: Row, tables: dict[str, list[Row]], sessions: dict, cameras: dict) -> None:
        groups: dict[str, list[str]] = {}
        timelines: dict[str, Row] = {}
        for item in metadata["recordings"]:
            key = (tuple(item["dataset"]), item["site"])
            session_id, extent = sessions[(*key, item["session"])]
            camera_id = cameras[(*key, item["camera"])]
            src = core.source_id(item["sha256"])
            recording = core.anchor_id("rec", "recording", [src, session_id, camera_id, item["registration_label"]])
            alignment = item.get("alignment")
            if alignment and extent is None:
                raise ContractError("ERR-INVARIANT", "aligned_session timelines need a declared session extent (section 3.1)")
            if alignment:
                timeline = core.anchor_id("tl", "timeline", ["aligned_session", session_id])
                timelines[timeline] = _fill("timeline", {"kind": "aligned_session", "anchor_id": session_id, "extent_start_tl_s": extent[0], "extent_end_tl_s": extent[1], "extent_source": "session_metadata"})
                tables.setdefault("clock_alignment", []).append(_fill("clock_alignment", {**alignment, "recording_id": recording, "timeline_id": timeline}))
            else:
                timeline = core.anchor_id("tl", "timeline", ["recording_local", recording])
                timelines[timeline] = _fill("timeline", {"kind": "recording_local", "anchor_id": recording, "extent_start_tl_s_null_reason": "not_applicable",
                                                         "extent_end_tl_s_null_reason": "not_applicable", "extent_source": "recording_extent"})
            groups.setdefault(timeline, [])
            if camera_id not in groups[timeline]:
                groups[timeline].append(camera_id)
            tables["recording"].append(_fill("recording", {"src_id": src, "session_id": session_id, "camera_id": camera_id, "registration_label": item["registration_label"], "timeline_id": timeline}))
        tables["timeline"] = list(timelines.values())
        tables["camera_group"] = [_fill("camera_group", {"timeline_id": t, "camera_ids": c, "grouping_basis": "whole_session"}) for t, c in groups.items()]

    def _calibration(self, item: Row, tables: dict[str, list[Row]], cameras: dict, frames: dict) -> None:
        key = (tuple(item["dataset"]), item["site"])
        row = _fill("calibration", {**_strip(item, "dataset", "site", "camera", "world_frame"), "camera_id": cameras[(*key, item["camera"])],
                                    "world_frame_id": frames[(*key, *item["world_frame"])]})
        issues = check_calibration(row)
        if issues:
            raise ContractError(issues[0].code, issues[0].message)
        tables.setdefault("calibration", []).append(row)
