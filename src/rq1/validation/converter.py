"""`SimReferenceConverter.convert` (CV-SIM): simulator truth to reference tables for one window and camera
(E-1.2.1 section 5.8; F.1 A3 timeline form, A5.1 reference classes)."""
from __future__ import annotations

from typing import Any

from .coverage_rules import REASON, eligible_support

Row = dict[str, Any]
GEOMETRIC = "independent_perceptual_geometric"


def _base(window: Row, camera_id: str, timeline_id: str) -> Row:
    return {"window_id": window["rwn_id"], "camera_id": camera_id, "timeline_id": timeline_id, "prov_class": "simulator_truth",
            "label_source": "simulator_truth", "reference_class": GEOMETRIC}


class SimReferenceConverter:
    def convert(self, window: Row, s1: dict[str, list[Row]], truth: Row, world_frame_id: str) -> dict[str, list[Row]]:
        frames = sorted(s1["frame"], key=lambda f: (f["support_start_tl_s"] is None, f["support_start_tl_s"] or 0.0))
        coverage = sorted(s1["coverage_segment"], key=lambda c: c["t_start_tl_s"])
        timeline_id, camera_id = coverage[0]["timeline_id"], coverage[0]["camera_id"]
        a0, b0 = window["t_start_tl_s"], window["t_guard_end_tl_s"]
        eligible = [f for f in frames if f["eligible"] and f["support_s"] and a0 - 1e-9 <= f["support_start_tl_s"] < b0 - 1e-9]
        present = {i for obj in truth["objects"] for i in obj["frames"]}

        def state_at(f: Row) -> str:
            t = f["support_start_tl_s"]
            if any(x["t_onset_tl_s"] - 1e-9 <= t < x["t_offset_tl_s"] - 1e-9 for x in truth["interactions"]):
                return "interaction_present"
            if f["frame_index"] in present:
                return "objects_present_no_interaction"
            return "reference_verified_absent" if window["exhaustive"] else "not_annotated"

        spans: list[Row] = []
        for c in coverage:
            a, b = max(c["t_start_tl_s"], a0), min(c["t_end_tl_s"], b0)
            if b <= a + 1e-12:
                continue
            if c["coverage_state"] in REASON:
                spans.append([a, b, "unobservable", REASON[c["coverage_state"]]])
                continue
            pieces = []
            for f in eligible:
                if a - 1e-9 <= f["support_start_tl_s"] < b - 1e-9:
                    start, end = f["support_start_tl_s"], min(f["support_start_tl_s"] + f["support_s"], b)
                    if pieces and pieces[-1][2] == state_at(f) and abs(pieces[-1][1] - start) < 1e-9:
                        pieces[-1][1] = end
                    else:
                        pieces.append([start, end, state_at(f), None])
            if pieces:
                pieces[0][0], pieces[-1][1] = a, b
            spans += pieces
        rows = []
        for a, b, state, reason in spans:
            row = {**_base(window, camera_id, timeline_id), "t_start_tl_s": a, "t_end_tl_s": b, "ref_activity_state": state,
                   "eligible_support_s": eligible_support(frames, a, b)}
            indices = [f["frame_index"] for f in eligible if a - 1e-9 <= f["support_start_tl_s"] < b - 1e-9 and f["support_status"] != "timing_uncertain"]
            if state == "unobservable":
                indices = []
            row["unobservable_reason"], row["unobservable_reason_null_reason"] = reason, (None if reason else "not_applicable")
            row["start_frame"], row["start_frame_null_reason"] = (min(indices), None) if indices else (None, "not_applicable")
            row["end_frame_excl"], row["end_frame_excl_null_reason"] = (max(indices) + 1, None) if indices else (None, "not_applicable")
            rows.append(row)
        window_indices = [f["frame_index"] for f in eligible]
        presence, geometry = [], []
        delta = eligible[1]["support_start_tl_s"] - eligible[0]["support_start_tl_s"] if len(eligible) > 1 else 0.0
        for obj in sorted(truth["objects"], key=lambda o: o["physical_identity_id"]):
            seen = [i for i in window_indices if i in obj["frames"]]
            if not seen:
                continue
            intervals, run = [], [seen[0], seen[0] + 1]
            for i in seen[1:]:
                if i == run[1]:
                    run[1] += 1
                else:
                    intervals.append(run)
                    run = [i, i + 1]
            intervals.append(run)
            base = {"window_id": window["rwn_id"], "camera_id": camera_id, "prov_class": "simulator_truth", "label_source": "simulator_truth",
                    "reference_class": GEOMETRIC}
            presence.append({**base, "class": obj["class"], "physical_identity_id": obj["physical_identity_id"],
                             "presence_intervals": [{"start_frame": s, "end_frame_excl": e} for s, e in intervals],
                             "keyframes": [{"frame_index": i, "bbox_xyxy_px": list(obj["frames"][i]["bbox"]), "evidence_state": "visible"} for i in seen],
                             "keyframe_interval_s": delta, "consensus_method": "simulator", "source_record_ids": []})
            for i in seen:
                if obj["frames"][i].get("xy") is not None:
                    x, y = obj["frames"][i]["xy"]
                    geometry.append({**base, "physical_identity_id": obj["physical_identity_id"], "frame_index": i, "x_m": float(x), "y_m": float(y),
                                     "sigma_m": 0.0, "method": "simulator_truth", "click_count": 0, "click_spread_m": None,
                                     "click_spread_m_null_reason": "not_applicable", "world_frame_id": world_frame_id, "interp_method": "none"})
        interactions = []
        for x in truth["interactions"]:
            if not (a0 <= x["t_onset_tl_s"] < window["t_end_tl_s"]):
                continue  # an event belongs to the window of its onset (section 8)
            inside = [f["frame_index"] for f in eligible if x["t_onset_tl_s"] - 1e-9 <= f["support_start_tl_s"] < x["t_offset_tl_s"] - 1e-9]
            row = {"window_id": window["rwn_id"], "person_identity_id": x["person"], "forklift_identity_id": x["forklift"],
                   "per_camera": [{"camera_id": camera_id, "start_frame": min(inside), "end_frame_excl": max(inside) + 1, "assessable": True}],
                   "t_onset_tl_s": x["t_onset_tl_s"], "t_offset_tl_s": x["t_offset_tl_s"], "assessability": "assessable",
                   "visible_contact": "cant_tell", "evasive_action": x.get("evasive_action", "cant_tell"), "consensus_method": "simulator",
                   "source_record_ids": [], "prov_class": "simulator_truth", "label_source": "simulator_truth", "reference_class": "rule_conformance"}
            for name in ("evasive_onset_tl_s", "boundary_agreement_iou"):
                row[name], row[f"{name}_null_reason"] = x.get(name), (None if x.get(name) is not None else "not_applicable")
            interactions.append(row)
        out = {"ref_coverage_label": rows, "ref_object_presence": presence, "ref_geometry": geometry}
        if interactions:
            out["ref_interaction"] = interactions
        return out
