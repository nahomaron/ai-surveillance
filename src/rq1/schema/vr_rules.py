"""Validation rules that need more than one row or outside context (Appendix T, T1)."""
from __future__ import annotations

import re
from typing import Any, Iterable

from rq1.ids import core as ids

from . import registry
from .errors import check_schema_major, ContractError
from .validate import Issue

Row = dict[str, Any]
REQUIRED_METADATA = {"schema_id", "schema_version", "artifact_id", "data_origin", "payload_sha256"}
ALLOWED_METADATA = REQUIRED_METADATA | {"ARROW:schema"}
REAL = {"real_natural", "real_staged"}
NOT_EVALUATED_COVERAGE = {"not_recorded", "gap_unobserved", "unusable"}
WORLD_FIELDS = ("x_m", "y_m", "pos_cov_m2", "yaw_rad", "speed_mps", "heading_rad")
WORLD_METHODS = {"ground_plane_homography", "full_camera", "multi_view", "simulator_truth"}
NON_SI_SUFFIX = re.compile(r"_(ms|cm|mm|km|kmh|kph|mph|ft|in|deg|min|hr|hrs|lb|lbs|g)$")
OBSERVED_CONTACT = re.compile(r"(observed|confirmed|actual)[ _-]?contact|contact[ _-]?(observed|confirmed)", re.I)
HEADLINE_METRICS = {"EV-M1", "EV-M2", "EV-M7"}
TOL_S = 1e-6


def _issue(rule: str, table: str, field: str, message: str, code: str | None = None) -> Issue:
    return Issue(rule, code, table, field, message)


def check_parquet_metadata(meta: dict[str, str], supported: str) -> list[Issue]:
    """VR-E-001."""
    issues = [_issue("VR-E-001", "*", key, "required metadata key missing") for key in sorted(REQUIRED_METADATA - set(meta))]
    issues += [_issue("VR-E-001", "*", key, "key not permitted (execution-specific)") for key in sorted(set(meta) - ALLOWED_METADATA)]
    if "schema_version" in meta:
        try:
            check_schema_major(meta["schema_version"], supported)
        except ContractError as err:
            issues.append(_issue("VR-E-001", "*", "schema_version", str(err), err.code))
    return issues


def natural_key(table: str, row: Row) -> list[Any]:
    """Natural-key value of a row. Set-like key parts are sorted by canonical JSON (section 1.5)."""
    from .canonical import sort_set

    values: list[Any] = []
    for part in registry.TABLES[table].key:
        value = ids.to_us(row[part.source]) if part.source else row[part.name]
        values.append(sort_set(value) if isinstance(value, list) and part.name.endswith(("_ids", "_nks")) else value)
    return values


def check_ids(table: str, rows: list[Row], artifact_id: str | None = None) -> list[Issue]:
    """VR-E-004: every ID is recomputable according to its identity class."""
    spec = registry.TABLES[table]
    column = f"{spec.prefix}_id"
    issues: list[Issue] = []
    if spec.prefix is None:
        return issues
    for row in rows:
        actual = row[column]
        if spec.identity_class == "anchor":
            expected = ids.source_id(row["sha256"]) if table == "source_file" else ids.anchor_id(spec.prefix, table, natural_key(table, row))
        elif spec.identity_class == "configuration":
            content = {f.name: row[f.name] for f in spec.fields if not f.derived and f.name in row}
            expected = ids.make_id(spec.prefix, content)
        elif spec.identity_class == "observation":
            expected = ids.observation_id(spec.prefix, table, artifact_id, natural_key(table, row))
        else:
            if not ids.UUID7.match(actual):
                issues.append(_issue("VR-E-004", table, column, f"not a UUIDv7 ID: {actual}"))
            continue
        if actual != expected:
            issues.append(_issue("VR-E-004", table, column, f"expected {expected}, found {actual}"))
    return issues


def check_data_origins(origins: Iterable[str], scope: str = "file") -> list[Issue]:
    """VR-E-005: one data_origin per file; real and synthetic never share a file or aggregate."""
    found = sorted(set(origins))
    return [] if len(found) <= 1 else [_issue("VR-E-005", "*", "data_origin", f"mixed origins in {scope}: {found}")]


def check_frames(frames: list[Row]) -> list[Issue]:
    """VR-E-010 (amended)."""
    issues = [_issue("VR-E-010", "frame", "support_s", "negative support") for f in frames if f["support_s"] < 0]
    by_recording: dict[str, list[Row]] = {}
    for frame in frames:
        if frame["eligible"]:
            by_recording.setdefault(frame["recording_id"], []).append(frame)
    for recording, rows in sorted(by_recording.items()):
        rows.sort(key=lambda r: r["frame_index"])
        if [r["frame_index"] for r in rows] != list(range(len(rows))):
            issues.append(_issue("VR-E-010", "frame", "frame_index", f"{recording}: not contiguous from 0"))
        for a, b in zip(rows, rows[1:]):
            if not a["t_resolved_s"] < b["t_resolved_s"]:
                issues.append(_issue("VR-E-010", "frame", "t_resolved_s", f"{recording}: not strictly increasing at {b['frame_index']}"))
    return issues


def check_intervals(table: str, rows: list[Row], start: str, end: str, extent: tuple[float, float] | None = None,
                    n_eligible: int | None = None) -> list[Issue]:
    """VR-E-011 (amended)."""
    issues: list[Issue] = []
    for row in rows:
        if not row[start] < row[end]:
            issues.append(_issue("VR-E-011", table, start, f"start {row[start]} is not before end {row[end]}"))
        if extent and not (extent[0] <= row[start] and row[end] <= extent[1]):
            issues.append(_issue("VR-E-011", table, start, "interval outside its timeline extent"))
        if n_eligible is not None:
            for name in (start, end):
                if not 0 <= row[name] <= n_eligible:
                    issues.append(_issue("VR-E-011", table, name, "frame index outside [0, n_frames_eligible]"))
    return issues


def check_tiling(rule: str, table: str, rows: list[Row], extent: tuple[float, float], start: str = "t_start_tl_s", end: str = "t_end_tl_s") -> list[Issue]:
    """Exact tiling of a half-open extent, compared in integer microseconds."""
    ordered = sorted(rows, key=lambda r: ids.to_us(r[start]))
    cursor = ids.to_us(extent[0])
    issues: list[Issue] = []
    for row in ordered:
        if ids.to_us(row[start]) != cursor:
            issues.append(_issue(rule, table, start, f"gap or overlap at {row[start]}"))
        cursor = ids.to_us(row[end])
    if cursor != ids.to_us(extent[1]) or not ordered:
        issues.append(_issue(rule, table, end, "does not end at the extent end"))
    return issues


def check_coverage_tiling(rows: list[Row], extent: tuple[float, float]) -> list[Issue]:
    """VR-E-012 (= TI-01), for one (timeline, camera)."""
    return check_tiling("VR-E-012", "coverage_segment", rows, extent)


def check_activity(rows: list[Row], extent: tuple[float, float]) -> list[Issue]:
    """VR-E-013 (= CD-01, CD-02), for one (timeline, camera)."""
    issues = check_tiling("VR-E-013", "activity_segment", rows, extent)
    for row in rows:
        expected = row["coverage_state"] in NOT_EVALUATED_COVERAGE
        if (row["ai_activity_state"] == "not_evaluated") != expected:
            issues.append(_issue("VR-E-013", "activity_segment", "ai_activity_state", f"{row['ai_activity_state']} on {row['coverage_state']}"))
    return issues


def check_object_states(rows: list[Row], calibrations: dict[str, Row]) -> list[Issue]:
    """VR-E-014 (amended) and VR-E-020."""
    issues: list[Issue] = []
    for row in rows:
        calibration = calibrations.get(row.get("calibration_id"))
        has_world = any(row.get(name) is not None for name in WORLD_FIELDS)
        if calibration and calibration["quality_state"] == "failed":
            if has_world:
                issues.append(_issue("VR-E-020", "object_state", "calibration_id", "geometry from a failed calibration", "ERR-CALIB-FAILED"))
            continue
        if not has_world:
            continue
        method = row["geometry_method"]
        if method not in WORLD_METHODS:
            issues.append(_issue("VR-E-014", "object_state", "geometry_method", f"world quantities with method {method}"))
        elif method != "simulator_truth" and calibration is None:
            issues.append(_issue("VR-E-014", "object_state", "calibration_id", "world quantities without a calibration"))
        elif method in ("full_camera", "multi_view") and calibration and calibration["calibration_tier"] != "full_camera":
            issues.append(_issue("VR-E-014", "object_state", "geometry_method", "tier does not permit this method", "ERR-CALIB-TIER"))
    return issues


def check_pair_series(rows: list[Row]) -> list[Issue]:
    """VR-E-015."""
    issues: list[Issue] = []
    for row in rows:
        clearance, measured = row["clearance_m"], row["clearance_state"] == "measured"
        if (clearance is None) == measured:
            issues.append(_issue("VR-E-015", "pair_series", "clearance_m", "null iff clearance_state is not measured"))
        elif measured and (row["footprint_overlap"] == 1) != (clearance <= 0):
            issues.append(_issue("VR-E-015", "pair_series", "footprint_overlap", "overlap iff clearance_m <= 0 when measured"))
    return issues


def check_exposure_sums(rows: list[Row]) -> list[Issue]:
    """VR-E-016 (amended), tolerance 1 microsecond."""
    issues: list[Issue] = []
    for row in rows:
        total = row["t_total_support_s"]
        bands = sum(row["t_in_band_detected_s"]) + sum(row["t_in_band_inferred_s"]) + row["t_clearance_unknown_s"] + row["t_insufficient_s"]
        motion = row["t_moving_detected_s"] + row["t_moving_inferred_s"] + row["t_stationary_detected_s"] + row["t_stationary_inferred_s"] + row["t_motion_unknown_s"] + row["t_insufficient_s"]
        if abs(bands - total) > TOL_S:
            issues.append(_issue("VR-E-016", "exposure_profile", "t_total_support_s", f"band sum {bands} differs from {total}"))
        if abs(motion - total) > TOL_S:
            issues.append(_issue("VR-E-016", "exposure_profile", "t_total_support_s", f"motion sum {motion} differs from {total}"))
    return issues


def check_profile_cardinality(pow_keys: list[Any], band_scheme_ids: list[str], profiles: list[Row]) -> list[Issue]:
    """VR-E-017: exactly one profile per POW and band scheme."""
    from .canonical import canonical_json

    counts: dict[bytes, int] = {}
    for row in profiles:
        if row["subject_type"] == "pow":
            key = canonical_json([row["subject_nk"], row["band_scheme_id"]])
            counts[key] = counts.get(key, 0) + 1
    issues = []
    for pow_key in pow_keys:
        for scheme in band_scheme_ids:
            found = counts.get(canonical_json([pow_key, scheme]), 0)
            if found != 1:
                issues.append(_issue("VR-E-017", "exposure_profile", "subject_nk", f"{found} profiles for {pow_key}, {scheme}"))
    return issues


def check_sigma_status(rows: list[Row], gv05_evidence: dict[str, str]) -> list[Issue]:
    """VR-E-018: `calibrated` needs a GV-05 evidence reference, keyed by calibration ID (AR-13)."""
    return [_issue("VR-E-018", "object_state", "sigma_status", "calibrated without GV-05 evidence")
            for row in rows if row["sigma_status"] == "calibrated" and not gv05_evidence.get(row.get("calibration_id"))]


def check_unit_suffixes(columns: Iterable[str], table: str = "*") -> list[Issue]:
    """VR-E-021, mechanical part: no column uses a non-SI unit suffix (section 1.2; AR-13)."""
    return [_issue("VR-E-021", table, c, "non-SI unit suffix") for c in columns if NON_SI_SUFFIX.search(c)]


def _flags(row: Row, suffix: str) -> tuple[bool, bool, bool]:
    return row[f"P_{suffix}"], row[f"X_{suffix}"], row[f"C_{suffix}"]


def _expected_summary(row: Row) -> str:
    for label in ("CT", "UD", "NM", "PC", "H", "O"):
        if row[f"lbl_{label}"]:
            return label
    return ""


def check_episode_labels(row: Row) -> list[Issue]:
    """VR-E-030: CL-INV-01 to 11 on one episode (E-1.2.1 section 6)."""
    return _check_labels(row, "ep", "K", "contact_state", "episode", "VR-E-030")


def check_event_labels(row: Row) -> list[Issue]:
    """VR-E-032: candidate-event labels are recomputed from event flags, never unioned."""
    return _check_labels(row, "ev", "K_ev", "contact_state_ev", "candidate_event", "VR-E-032")


def _check_labels(row: Row, suffix: str, k_name: str, contact_name: str, table: str, rule: str) -> list[Issue]:
    p, x, c = _flags(row, suffix)
    k, contact = row[k_name], row[contact_name]
    h, pc, o, nm, ud, ct, ie = (row[f"lbl_{n}"] for n in ("H", "PC", "O", "NM", "UD", "CT", "IE"))
    violations = []
    if h != x:
        violations.append("H must equal X")
    if pc != c:
        violations.append("PC must equal C")
    if o != (p and not h and not pc):
        violations.append("CL-INV-01: O iff P and not H and not PC")
    if not (o or h or pc):
        violations.append("CL-INV-02: O or H or PC")
    if h and not p:
        violations.append("CL-INV-03: H implies P")
    if nm + ud + ct > 1:
        violations.append("CL-INV-04: at most one of NM, UD, CT")
    if nm != ((h or pc) and k == 1 and contact == "none_observed"):
        violations.append("CL-INV-05: NM rule")
    if ud != ((h or pc) and k == 1 and contact == "undetermined"):
        violations.append("CL-INV-05: UD rule")
    if ct != (contact == "suspected"):
        violations.append("CL-INV-05: CT rule")
    if (nm or ud) and not (h or pc):
        violations.append("CL-INV-06: NM or UD implies H or PC")
    if contact == "not_assessable" and (not ie or nm or ud or ct):
        violations.append("CL-INV-07: not_assessable implies IE and no G2 label")
    if k == 2 and (h or pc) and (not ie or nm or ud):
        violations.append("CL-INV-08: unknown K implies IE, not NM, not UD")
    if row["summary_label"] != _expected_summary(row):
        violations.append("CL-INV-11: summary label must derive from the labels")
    return [_issue(rule, table, "lbl_*", v) for v in violations]


def check_linked_edge(edge: Row, context: Row, tau_sync: float, chi2_link: float) -> list[Issue]:
    """VR-E-031 (amended): requirements of an `L` edge."""
    if edge["edge"] != "L":
        return []
    problems = []
    a, b = context["cal_a"], context["cal_b"]
    if not (a and b) or a["world_frame_id"] != b["world_frame_id"] or "failed" in (a["quality_state"], b["quality_state"]):
        problems.append("both cameras need non-failed calibrations in one world frame")
    if not context["same_aligned_timeline"]:
        problems.append("both recordings must share one aligned_session timeline")
    sa, sb = context["sigma_a"], context["sigma_b"]
    if sa is None or sb is None:
        problems.append("clock sigma must be non-null")
    elif (sa * sa + sb * sb) ** 0.5 > tau_sync:
        problems.append("combined clock sigma exceeds tau_sync")
    if edge["median_mahalanobis"] is None or edge["median_mahalanobis"] > chi2_link:
        problems.append("median Mahalanobis exceeds chi2_link")
    return [_issue("VR-E-031", "event_link", "edge", p) for p in problems]


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def check_no_observed_contact(table: str, rows: list[Row]) -> list[Issue]:
    """VR-E-034."""
    return [_issue("VR-E-034", table, "*", f"forbidden value: {s}") for r in rows for s in _strings(r) if OBSERVED_CONTACT.search(s)]


def check_no_reference_states(table: str, rows: list[Row]) -> list[Issue]:
    """VR-E-040: no `reference_verified_absent` in the Observation store or OBX exports."""
    return [_issue("VR-E-040", table, "*", "reference state in Observation store or export")
            for r in rows for s in _strings(r) if s == "reference_verified_absent"]


def check_v0_inputs(inputs: list[Row]) -> list[Issue]:
    """VR-E-050: V0 uses no Observation input other than coverage."""
    issues = []
    for item in inputs:
        if item["stage"] in {"S2", "S3", "S4", "S5"}:
            issues.append(_issue("VR-E-050", "sampling_plan", "inputs", f"V0 consumed {item['stage']}"))
        elif item["stage"] == "S1" and item["table"] not in {"coverage_segment", "decode_summary"}:
            issues.append(_issue("VR-E-050", "sampling_plan", "inputs", f"V0 consumed S1 table {item['table']}"))
    return issues


def check_headline_sample_type(rows: list[Row], aggregate_metric_ids: set[str] = frozenset()) -> list[Issue]:
    """VR-E-051: headline and frequency, duration or per-hour aggregates use RES windows only."""
    wanted = HEADLINE_METRICS | set(aggregate_metric_ids)
    return [_issue("VR-E-051", "metric_result", "sample_type", f"{r['metric_id']} from ECS windows", "ERR-ECS-AGGREGATE")
            for r in rows if r["metric_id"] in wanted and r["sample_type"] == "ECS"]


def check_ref_coverage(spans: list[Row], window: Row) -> list[Issue]:
    """VR-E-052 with F.1 A3 RC-01 and RC-03, for one (window, camera)."""
    issues = check_tiling("VR-E-052", "ref_coverage_label", spans, (window["t_start_tl_s"], window["t_guard_end_tl_s"]))
    for span in spans:
        if span["ref_activity_state"] != "reference_verified_absent":
            continue
        if not window["exhaustive"]:
            issues.append(_issue("VR-E-052", "ref_coverage_label", "ref_activity_state", "window is not exhaustive"))
        if span["eligible_support_s"] <= 0:
            issues.append(_issue("VR-E-052", "ref_coverage_label", "eligible_support_s", "no eligible support"))
        if span["label_source"] not in ("simulator_truth", "human_manual"):
            issues.append(_issue("VR-E-052", "ref_coverage_label", "label_source", "source not permitted"))
    return issues


def check_blind_reference(table: str, rows: list[Row]) -> list[Issue]:
    """VR-E-053."""
    issues = []
    for row in rows:
        if row["namespace"] != "reference":
            continue
        blind = row.get("blind_to_system", row.get("blind"))
        if blind is not True or row.get("shown_system_output", False) is not False:
            issues.append(_issue("VR-E-053", table, "blind_to_system", "reference record is not blind"))
    return issues


def check_windows_locked(windows: list[Row], s8_run_start) -> list[Issue]:
    """VR-E-054."""
    return [_issue("VR-E-054", "reference_window", "locked_utc", "not locked before the first S8 run")
            for w in windows if w["locked_utc"] is None or not w["locked_utc"] < s8_run_start]


def check_split(split: Row, context: Row | None = None) -> list[Issue]:
    """VR-E-060 (amended): per-tier split check."""
    context = context or {}
    partitions: dict[str, set[str]] = {}
    for assignment in split["assignments"]:
        partitions.setdefault(assignment["leakage_group_id"], set()).add(assignment["partition"])
    spanning = {g for g, p in partitions.items() if len(p) > 1}
    tier, problems = split["tier"], []
    if tier == "T2b":
        declared = set(split["t2b_shared_sessions"] or [])
        group_sessions = context.get("group_sessions", {})
        undeclared = sorted(g for g in spanning if not set(group_sessions.get(g, [])) <= declared or not group_sessions.get(g))
        if undeclared:
            problems.append(f"undeclared shared groups: {undeclared}")
        if spanning and not split["shared_scene_content"]:
            problems.append("shared_scene_content must be true")
    elif spanning:
        problems.append(f"groups span partitions: {sorted(spanning)}")
    if tier == "T2a" and set(context.get("test_camera_placements", [])) & set(context.get("train_camera_placements", [])):
        problems.append("test camera placement also in training")
    if tier == "T3" and set(context.get("test_site_recordings", [])) & set(context.get("manifest_recordings", [])):
        problems.append("test-site recording in a training, tuning or selection manifest")
    return [_issue("VR-E-060", "split_manifest", "assignments", p, "ERR-LEAKAGE") for p in problems]


def check_attribution(rows: list[Row], data_origin: str) -> list[Issue]:
    """VR-E-061."""
    return [_issue("VR-E-061", "error_attribution", "attribution_status", "verified_* needs synthetic data and oracle runs")
            for r in rows if r["attribution_status"].startswith("verified_") and (data_origin in REAL or not r["oracle_artifact_ids"])]


def check_conditional_companions(rows: list[Row]) -> list[Issue]:
    """VR-E-062: EV-M6 and conditional_on_selection results need a coverage companion."""
    return [_issue("VR-E-062", "metric_result", "coverage_companion_id", "conditional metric without a coverage companion")
            for r in rows if (r["metric_id"] == "EV-M6" or r["estimand"] == "conditional_on_selection") and r["coverage_companion_id"] is None]


def check_retention(source_files: list[Row], real_source_ids: set[str], policy_ids: set[str], clips: list[Row]) -> list[Issue]:
    """VR-E-070 (amended)."""
    issues = [_issue("VR-E-070", "source_file", "retention_policy_id", "real-origin file without a retention policy")
              for f in source_files if f["src_id"] in real_source_ids and f.get("retention_policy_id") not in policy_ids]
    issues += [_issue("VR-E-070", "evidence_clip", "access_class", "derived clip without an access class") for c in clips if not c.get("access_class")]
    return issues


def check_real_clip_access(clips: list[Row], real_recording_ids: set[str]) -> list[Issue]:
    """VR-E-071."""
    return [_issue("VR-E-071", "evidence_clip", "access_class", "real-origin clip marked publishable")
            for c in clips if c["recording_id"] in real_recording_ids and c["access_class"] == "publishable_synthetic_only"]
