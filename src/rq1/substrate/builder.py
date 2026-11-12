"""`SubstrateBuilder.build` (S4): object states, POWs, pair series, exposure profiles and activity segments
(E-1.2.1 sections 3.4, 3.5, 4.2, 5.5; Appendix T section T8)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rq1.ids.artifact import Artifact, Spec, build_artifact

from . import activity, durations, evidence, geometry, kinematics, pows

Row = dict[str, Any]
BREAKS = {"not_recorded", "gap_unobserved", "unusable"}
_TRACK_IDS: dict[str, dict[int, str]] = {}


@dataclass(frozen=True)
class SubstrateConfig:
    g_max: int
    v_min: float
    w_v: float
    horizon_s: float
    pair_classes: set[str]
    priors: dict[str, Row]
    prior_ids: dict[str, str]
    band_schemes: dict[str, list[tuple[float | None, float | None]]]
    v_part: float


def track_ids(built: Artifact) -> dict[int, str]:
    """Local track number to track ID for an S4 artifact built here (test convenience)."""
    return _TRACK_IDS[built.artifact_id]


def _null(row: Row, name: str, value: Any, reason: str) -> None:
    row[name], row[f"{name}_null_reason"] = value, (None if value is not None else reason)


class SubstrateBuilder:
    def build(self, s1: dict[str, list[Row]], s3: Artifact, positions: dict[tuple[int, int], Row], calibration: Row | None,
              cfg: SubstrateConfig, spec: Spec) -> Artifact:
        recording = s1["frame"][0]["recording_id"]
        frames_all = [f for f in s1["frame"] if f["recording_id"] == recording]
        frames = {f["frame_index"]: f for f in frames_all if f["eligible"]}
        own = [c for c in s1["coverage_segment"] if c.get("recording_id") == recording]
        timeline_id, camera_id = own[0]["timeline_id"], own[0]["camera_id"]
        coverage = [c for c in s1["coverage_segment"] if c["timeline_id"] == timeline_id and c["camera_id"] == camera_id]
        summary = next(d for d in s1["decode_summary"] if d["recording_id"] == recording)
        size = (summary["width_px"], summary["height_px"])
        tracks = {t["track_local_id"]: t for t in s3.tables["track"]}
        points = {(p["track_nk"][1], p["frame_index"]): p for p in s3.tables["track_point"]}
        states_rows: dict[tuple[str, int], Row] = {}
        object_rows = []
        for local, track in sorted(tracks.items()):
            rows = self._object_states(track, local, points, positions, calibration, frames, coverage, size, cfg)
            object_rows += rows
            states_rows.update({(track["trk_id"], r["frame_index"]): r for r in rows})
        _TRACK_IDS_PENDING = {local: t["trk_id"] for local, t in tracks.items()}
        pow_rows, pair_rows, profiles = [], [], []
        persons = [t for t in tracks.values() if t["class"] == "person"]
        forklifts = [t for t in tracks.values() if t["class"] in cfg.pair_classes]
        for person in sorted(persons, key=lambda t: t["track_local_id"]):
            for fork in sorted(forklifts, key=lambda t: t["track_local_id"]):
                pstate = {i: p["state"] for (l, i), p in points.items() if l == person["track_local_id"] and i in frames}
                fstate = {i: p["state"] for (l, i), p in points.items() if l == fork["track_local_id"] and i in frames}
                for window in pows.build(pstate, fstate, frames, coverage, cfg.g_max):
                    key = [person["trk_id"], fork["trk_id"], window.start]
                    series = [self._pair(person, fork, i, key, points, states_rows, frames, coverage, size, cfg, window)
                              for i in sorted(frames) if window.start <= i < window.end_excl]
                    self._closing(series, frames, coverage, cfg)
                    pair_rows += series
                    pow_rows.append(self._pow(key, window, series, frames, frames_all, recording, timeline_id, camera_id))
                    for scheme_id, bands in sorted(cfg.band_schemes.items()):
                        profiles.append(self._profile(key, scheme_id, bands, window, series, frames, frames_all, states_rows, fork, calibration, positions, cfg))
        detections = {i: {tracks[l]["class"] for (l, j), p in points.items() if j == i and p["state"] == "tracked"} for i in frames}
        activity_rows = activity.build(coverage, frames_all, detections, cfg.pair_classes, s3.artifact_id)
        for row in object_rows:
            row.pop("_v", None)
        built = build_artifact(spec, {"object_state": object_rows, "pow": pow_rows, "pair_series": pair_rows, "exposure_profile": profiles,
                                      "activity_segment": activity_rows})
        _TRACK_IDS[built.artifact_id] = _TRACK_IDS_PENDING
        return built

    def _object_states(self, track: Row, local: int, points: dict, positions: dict, calibration: Row | None, frames: dict[int, Row],
                       coverage: list[Row], size: tuple[int, int], cfg: SubstrateConfig) -> list[Row]:
        cls = track["class"]
        prior = cfg.priors[cls]
        rows, located = [], []
        for i in sorted(frames):
            point = points.get((local, i))
            if point is None:
                continue
            truth = positions.get((local, i))
            row = {"track_id": track["trk_id"], "frame_index": i, "footprint_prior_id": cfg.prior_ids[cls], "smoothing_window_s": cfg.w_v,
                   "evidence_state": evidence.evidence_state(point, size, None, cfg.v_part), "evidence_class": point["evidence_class"]}
            _null(row, "visibility_frac", None, "not_computed_by_config")
            _null(row, "yaw_sigma_rad", None, "not_computed_by_config" if cls != "person" else "not_applicable")
            xy, cov, reason = None, None, "not_observable"
            if truth is not None:
                row["geometry_method"] = "simulator_truth"
                xy, cov = truth["xy"], truth.get("cov")
                _null(row, "calibration_id", None, "not_applicable")
                _null(row, "world_frame_id", None, "not_supplied")
            elif calibration is not None:
                tier = calibration["calibration_tier"]
                row["geometry_method"] = "full_camera" if tier == "full_camera" else "ground_plane_homography"
                _null(row, "calibration_id", calibration["cal_id"], "uncalibrated")
                _null(row, "world_frame_id", calibration["world_frame_id"], "uncalibrated")
                if point["state"] in ("tracked", "predicted"):
                    foot = tuple(point["foot_point_px"])
                    xy = geometry.full_camera_to_floor(calibration, foot) if tier == "full_camera" else geometry.homography_to_floor(calibration["homography_img_to_floor"], foot)
                reason = "not_observable"
            else:
                row["geometry_method"] = "image_only"
                _null(row, "calibration_id", None, "uncalibrated")
                _null(row, "world_frame_id", None, "uncalibrated")
                reason = "uncalibrated"
            if point["state"] == "lost":
                xy = None
            _null(row, "x_m", None if xy is None else float(xy[0]), reason)
            _null(row, "y_m", None if xy is None else float(xy[1]), reason)
            _null(row, "pos_cov_m2", list(cov) if (cov is not None and xy is not None) else None, reason if xy is None else "not_supplied")
            row["sigma_status"] = "uncalibrated_model" if row["pos_cov_m2"] is not None else "not_estimated"
            rows.append(row)
            located.append((i, truth.get("yaw") if truth else None))
        self._kinematics(rows, frames, coverage, cfg, cls, dict(located))
        return rows

    def _kinematics(self, rows: list[Row], frames: dict[int, Row], coverage: list[Row], cfg: SubstrateConfig, cls: str, supplied_yaw: dict) -> None:
        by_frame = {r["frame_index"]: r for r in rows}
        usable = {i for i, r in by_frame.items() if r["x_m"] is not None and r["evidence_class"] in ("detected", "inferred")}
        runs = kinematics.contiguous_runs(sorted(frames), usable, lambda a, b: crosses_break(frames, coverage, a, b))
        times_all = {i: f["t_resolved_s"] for i, f in frames.items()}
        for row in rows:
            uncal = row["geometry_method"] == "image_only"
            t_k = times_all[row["frame_index"]]
            run = runs.get(row["frame_index"])
            window = [by_frame[i] for i in kinematics.shifted_window(run, times_all, t_k, cfg.w_v)] if run else []  # T9.1
            times = [times_all[r["frame_index"]] for r in window]
            if row["x_m"] is not None and kinematics.window_ok(times, cfg.w_v):
                fit = kinematics.fit_velocity(times, [r["x_m"] for r in window], [r["y_m"] for r in window])
                row["_v"] = (fit.vx, fit.vy)
                _null(row, "speed_mps", fit.speed, "not_observable")
                _null(row, "speed_sigma_mps", fit.speed_sigma, "not_observable")
                _null(row, "heading_rad", fit.heading if fit.speed >= cfg.v_min else None, "not_applicable")
                row["sigma_status"] = "uncalibrated_model"
            else:
                row["_v"] = None
                reason = "uncalibrated" if uncal else "not_observable"
                for name in ("speed_mps", "speed_sigma_mps", "heading_rad"):
                    _null(row, name, None, reason)
        if cls == "person":
            for row in rows:
                _null(row, "yaw_rad", None, "not_applicable")
            return
        yaws = kinematics.fill_yaw([supplied_yaw.get(r["frame_index"]) for r in rows], [r["speed_mps"] for r in rows], [r["heading_rad"] for r in rows], cfg.v_min)
        for row, yaw in zip(rows, yaws):
            _null(row, "yaw_rad", yaw if row["geometry_method"] != "image_only" else None, "uncalibrated" if row["geometry_method"] == "image_only" else "not_observable")

    def _pair(self, person: Row, fork: Row, i: int, key: list, points: dict, states: dict, frames: dict[int, Row], coverage: list[Row],
              size: tuple[int, int], cfg: SubstrateConfig, window: pows.Pow) -> Row:
        pp, fp = points.get((person["track_local_id"], i)), points.get((fork["track_local_id"], i))
        ps, fs = states.get((person["trk_id"], i)), states.get((fork["trk_id"], i))
        frame = frames[i]
        row: Row = {"pow_nk": key, "frame_index": i, "borderline_flags": []}
        pclass = durations.object_class(pp["state"] if pp else None)
        fclass = durations.object_class(fp["state"] if fp else None)
        pair_class = "insufficient" if frame["support_status"] == "timing_uncertain" else durations.combine(pclass, fclass)
        row["evidence_class"] = pair_class
        person_ev = ps["evidence_state"] if ps else "lost"
        fork_ev = fs["evidence_state"] if fs else "lost"
        row["q_state"], row["q_reasons"] = evidence.q_state(pair_class, person_ev, fork_ev, frame["support_status"])
        prior_p, prior_f = cfg.priors["person"], cfg.priors[fork["class"]]
        have = ps is not None and fs is not None and ps["x_m"] is not None and fs["x_m"] is not None
        sigma = None
        if have:
            person_xy, fork_xy, yaw = (ps["x_m"], ps["y_m"]), (fs["x_m"], fs["y_m"]), fs["yaw_rad"]
            if yaw is None:
                value = geometry.disc_clearance(person_xy, prior_p["radius_m"], fork_xy, geometry.circumscribed_radius(prior_f["length_m"], prior_f["width_m"]))
                row["borderline_flags"] = ["footprint_orientation_unknown"]
            else:
                value = geometry.clearance(person_xy, prior_p["radius_m"], fork_xy, yaw, prior_f["length_m"], prior_f["width_m"])
            u = geometry.clearance_gradient(person_xy, fork_xy, yaw, prior_f["length_m"], prior_f["width_m"])
            sigma = geometry.clearance_sigma(u, ps["pos_cov_m2"], fs["pos_cov_m2"], yaw, prior_f["sigma_length_m"], prior_f["sigma_width_m"], yaw is None)
            _null(row, "clearance_m", value, "not_observable")
            row["clearance_state"], row["footprint_overlap"] = "measured", geometry.footprint_overlap(value)
        else:
            uncal = (ps is not None and ps["geometry_method"] == "image_only") or (fs is not None and fs["geometry_method"] == "image_only")
            _null(row, "clearance_m", None, "uncalibrated" if uncal else "not_observable")
            row["clearance_state"] = "unmeasurable_uncalibrated" if uncal else "unmeasurable_occluded"
            row["footprint_overlap"] = 2
        _null(row, "clearance_sigma_m", sigma, "not_supplied" if have else row["clearance_m_null_reason"])
        row["sigma_status"] = "uncalibrated_model" if sigma is not None else "not_estimated"
        boxes = pp and fp and pp["state"] != "lost" and fp["state"] != "lost"
        gap = geometry.image_gap(pp["bbox_xyxy_px"], fp["bbox_xyxy_px"]) if boxes else (None, None)
        _null(row, "image_gap_px", gap[0], "not_observable")
        _null(row, "image_gap_norm", gap[1], "not_observable")
        row["predicted"], ttca = [], (None, "not_observable")
        if have and ps.get("_v") and fs.get("_v"):
            yaw = fs["yaw_rad"]
            value, t_min = geometry.predict_min_clearance((ps["x_m"], ps["y_m"]), ps["_v"], prior_p["radius_m"], (fs["x_m"], fs["y_m"]), fs["_v"], yaw,
                                                          prior_f["length_m"], prior_f["width_m"], cfg.horizon_s)
            row["predicted"] = [{"motion_model_id": "constant_velocity", "horizon_s": cfg.horizon_s, "pred_min_clearance_m": value, "sigma_m": None,
                                 "sigma_m_null_reason": "not_computed_by_config", "t_at_min_s": t_min}]
            ttca = kinematics.ttca(t_min, cfg.horizon_s)
        row["ttca_s"], row["ttca_s_null_reason"] = ttca
        return row

    def _closing(self, series: list[Row], frames: dict[int, Row], coverage: list[Row], cfg: SubstrateConfig) -> None:
        """T8.3: closing rate = -(least-squares slope of clearance vs t) over the T8.2 window, at least 3 measured frames."""
        measured = [r for r in series if r["clearance_state"] == "measured"]
        for row in series:
            t_k = frames[row["frame_index"]]["t_resolved_s"]
            window = [r for r in measured if abs(frames[r["frame_index"]]["t_resolved_s"] - t_k) <= cfg.w_v / 2 + 1e-9
                      and not crosses_break(frames, coverage, r["frame_index"], row["frame_index"])]
            if len(window) >= 3:
                rate = -kinematics.slope([frames[r["frame_index"]]["t_resolved_s"] for r in window], [r["clearance_m"] for r in window])
                _null(row, "closing_rate_mps", rate, "not_observable")
            else:
                _null(row, "closing_rate_mps", None, "not_observable")

    def _pow(self, key: list, window: pows.Pow, series: list[Row], frames: dict[int, Row], frames_all: list[Row], recording: str, timeline_id: str, camera_id: str) -> Row:
        a, b = durations.interval_extent(frames_all, window.start, window.end_excl)
        classes = {r["frame_index"]: r["evidence_class"] for r in series}
        split = durations.class_durations(frames_all, a, b, lambda i: classes.get(i, "insufficient"))
        row_out = {"person_track_id": key[0], "forklift_track_id": key[1], "start_frame": window.start, "end_frame_excl": window.end_excl,
                   "recording_id": recording, "timeline_id": timeline_id, "camera_id": camera_id, "t_start_tl_s": a, "t_end_tl_s": b, "span_s": b - a,
                   "t_detected_s": split["detected"], "t_inferred_s": split["inferred"], "t_insufficient_s": split["insufficient"],
                   "bridged_gaps": [{"start_frame": s, "end_frame_excl": e} for s, e in window.bridged], "end_reason": window.end_reason}
        if window.continuation_of is None:
            _null(row_out, "continuation_of_nk", None, "not_applicable")
        else:
            _null(row_out, "continuation_of_nk", [key[0], key[1], window.continuation_of], "not_applicable")
        return row_out

    def _profile(self, key: list, scheme_id: str, bands: list, window: pows.Pow, series: list[Row], frames: dict[int, Row], frames_all: list[Row],
                 states: dict, fork: Row, calibration: Row | None, positions: dict, cfg: SubstrateConfig) -> Row:
        a, b = durations.interval_extent(frames_all, window.start, window.end_excl)
        by_index = {r["frame_index"]: r for r in series}
        n = len(bands)
        out = {"t_in_band_detected_s": [0.0] * n, "t_in_band_inferred_s": [0.0] * n, "t_clearance_unknown_s": 0.0, "t_insufficient_s": 0.0,
               "t_moving_detected_s": 0.0, "t_moving_inferred_s": 0.0, "t_stationary_detected_s": 0.0, "t_stationary_inferred_s": 0.0,
               "t_motion_unknown_s": 0.0, "t_joint_visible_s": 0.0, "t_total_support_s": 0.0}
        for f in frames_all:
            if not f["support_s"] or f["support_start_tl_s"] is None:
                continue
            clipped = max(0.0, min(f["support_start_tl_s"] + f["support_s"], b) - max(f["support_start_tl_s"], a))
            if clipped <= 0:
                continue
            out["t_total_support_s"] += clipped
            pair = by_index.get(f["frame_index"]) if f["eligible"] else None
            cls = pair["evidence_class"] if pair else "insufficient"
            if cls == "insufficient":
                out["t_insufficient_s"] += clipped
                continue
            if pair["clearance_state"] == "measured":
                band = next(k for k, (lo, hi) in enumerate(bands) if (lo is None or pair["clearance_m"] >= lo) and (hi is None or pair["clearance_m"] < hi))
                out[f"t_in_band_{cls}_s"][band] += clipped
            else:
                out["t_clearance_unknown_s"] += clipped
            fstate = states.get((fork["trk_id"], f["frame_index"]))
            speed = fstate["speed_mps"] if fstate else None
            if speed is None:
                out["t_motion_unknown_s"] += clipped
            else:
                out[f"t_{'moving' if speed > cfg.v_min else 'stationary'}_{cls}_s"] += clipped
            pstate = states.get((key[0], f["frame_index"]))
            visible = {"visible", "partially_visible"}
            if cls == "detected" and pstate and fstate and pstate["evidence_state"] in visible and fstate["evidence_state"] in visible:
                out["t_joint_visible_s"] += clipped
        if calibration is not None:
            tier = "calibrated_validated" if calibration["quality_state"] == "validated_gv02" else "calibrated_unvalidated"
        else:
            tier = "calibrated_unvalidated" if positions else "uncalibrated"
        sigma = "uncalibrated_model" if any(r["sigma_status"] == "uncalibrated_model" for r in series) else "not_estimated"
        return {"subject_type": "pow", "subject_nk": key, "band_scheme_id": scheme_id, **out, "sigma_status": sigma, "calibration_tier": tier}


def crosses_break(frames: dict[int, Row], coverage: list[Row], a: int, b: int) -> bool:
    """True if a coverage break lies between frames a and b (T8.1, T8.2)."""
    if a == b:
        return False
    lo_i, hi_i = min(a, b), max(a, b)
    lo = frames[lo_i]["support_start_tl_s"] + frames[lo_i]["support_s"]
    hi = frames[hi_i]["support_start_tl_s"]
    return any(s["coverage_state"] in BREAKS and s["t_start_tl_s"] < hi - 1e-9 and s["t_end_tl_s"] > lo + 1e-9 for s in coverage)
