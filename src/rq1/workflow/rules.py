"""Appendix T T23 (contract E-1.2.22; D-48) with T23.16-T23.27 (contract E-1.2.23; D-49): the reporting-workflow rules as
pure functions.

Nothing here reads files or writes records; `store.py` applies these rules. Representation choices are AR-63 (decided at
D-49) and AR-64. Every indicator is a descriptive workflow measure about manager decisions or recorded reports (D-49.1
section 5), never a measure of CV accuracy or of true event rates. Points the contract leaves undefined that would change a
count, a state or a statistic are CR-031 and are not chosen here.
"""
from __future__ import annotations

import html as _html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable

from rq1.evaluation.estimators import wilson
from rq1.export.report import WORDING
from rq1.schema.errors import ContractError

# T23.14
PARAMS: dict[str, Any] = {"wf_source_config": "BL-6", "t_group_s": 2.0, "t_pending_days": 7.0, "theta_rej": 0.5,
                          "theta_over": 0.3, "n_flag_min": 10, "n_flag_min_sm": 5, "t_link_s": 60.0, "k_miss": 2}
ROLES = ("area_manager", "safety_manager", "worker", "oversight", "owner")  # T23.1 (b)
STATES = ("pending_am", "pending_sm", "recorded", "closed_rejected", "closed_duplicate", "closed_split")  # T23.4, T23.20 (e)
PENDING = ("pending_am", "pending_sm")

# T23.4 with T23.19 (c), T23.20 (c), (e): action -> (who, allowed from-states or None for "any", to-state or None for "same")
TRANSITIONS: dict[str, tuple[str, tuple[str, ...] | None, str | None]] = {
    "create_ai": ("system", (), "pending_am"),
    "create_human": ("any", (), "pending_am"),
    "am_approve": ("area_manager", ("pending_am",), "recorded"),
    "am_reject": ("area_manager", ("pending_am",), "pending_sm"),
    "am_duplicate": ("area_manager", ("pending_am",), "closed_duplicate"),
    "sm_uphold": ("safety_manager", ("pending_sm",), "closed_rejected"),
    "sm_overturn": ("safety_manager", ("pending_sm",), "recorded"),
    "sm_reclassify": ("safety_manager", ("recorded",), "closed_rejected"),
    "sm_reopen": ("safety_manager", ("closed_rejected", "closed_duplicate"), "pending_sm"),
    "edit_fields": ("editor", ("pending_am", "pending_sm", "recorded"), None),
    "set_recordability": ("safety_manager", ("recorded",), None),
    "sm_note": ("safety_manager", None, None),
    "sm_confirm_duplicate": ("safety_manager", ("pending_sm",), "closed_duplicate"),
    "am_split": ("area_manager", ("pending_am",), "closed_split"),
    "withdraw_recordability": ("safety_manager", None, None),
}
AM_DECISIONS = ("am_approve", "am_reject", "am_duplicate", "am_split")
SM_ACTIONS = ("sm_uphold", "sm_overturn", "sm_reclassify", "sm_reopen", "set_recordability", "sm_note", "sm_confirm_duplicate",
              "withdraw_recordability")
DECISIONS = AM_DECISIONS + ("sm_uphold", "sm_overturn", "sm_reclassify", "sm_reopen", "sm_confirm_duplicate")  # T23.18 (c)
REJECT_REASONS = {"not_hazardous": "not_hazardous", "no_person_or_no_forklift": "not_hazardous",
                  "cannot_tell_from_video": "ud", "other": "unsure"}  # T23.5 (b)
APPROVE_LABELS = ("nm", "ct")
KIND_OF_LABEL = {"nm": "near_miss", "ct": "incident"}  # T23.18 (e)
RECLASSIFY_LABELS = ("not_hazardous", "ud")  # T23.5 (c)
CONFIDENCE = (1.0, 2.0, 3.0)  # T22.5 (b); T23.5 (a) default 3.0
CONTRIBUTING = ("speed", "visibility", "blind corner", "pedestrian route", "load obstructing view", "training",
                "procedure", "other")  # T23.3 (a)
RECORDABLE = ("yes", "no", "undetermined")  # T23.7 (b)
DETERMINATIONS = ("not_set", "yes", "no", "undetermined", "withdrawn")  # T23.19 (b)
WITHDRAW_REASONS = ("classification_changed", "entered_in_error", "event_not_work_related", "other")  # T23.19 (c)
GROUP_RESOLUTIONS = ("one_interaction", "cannot_tell")  # T23.21 (d)
OBSERVABILITY = ("observable", "not_observable", "undetermined")  # T23.23 (c)
OBS_CATEGORIES = ("unmonitored", "monitored, not observable", "observability undetermined", "observable, matched",
                  "observable, no matching AI alert")  # T23.23 (c) 1-5
CRITERIA = ("death", "days_away", "restricted_or_transfer", "medical_treatment_beyond_first_aid",
            "loss_of_consciousness", "significant_diagnosed")
DAYS_CRITERIA = ("days_away", "restricted_or_transfer")  # "with days counts where they apply" (AR-63 item 9)
AI_LABEL = {"lbl_nm": "candidate near miss", "lbl_ud": "candidate, undetermined", "lbl_ct": "candidate contact"}  # T23.2 (d)
G2_SOURCE = tuple(AI_LABEL)  # T23.2 (a): NM, UD or CT
COMMON_AXES = ("aligned_session", "workflow_timebase_declared")  # T23.21 (c)
PER_CAMERA = "grouped per camera: no common clock"  # T23.21 (c)

# T23.7 (a), in the T23 order: (field, label, kind)
INCIDENT_FIELDS: list[tuple[str, str, str]] = [
    ("date_of_injury_or_illness", "Date of injury or illness", "date"),
    ("time_employee_began_work", "Time the employee began work", "text"),
    ("time_of_event", 'Time of event, or "cannot be determined"', "text"),
    ("doing_just_before", "What the employee was doing just before", "text"),
    ("what_happened", "What happened", "text"),
    ("injury_or_illness", "The injury or illness", "text"),
    ("object_or_substance", "The object or substance that directly harmed the employee", "text"),
    ("date_of_death", "Date of death, if any", "text"),
    ("treated_in_emergency_room", "Treated in an emergency room (yes/no)", "yesno"),
    ("hospitalized_overnight", "Hospitalized overnight (yes/no)", "yesno"),
    ("employee_pseudonym", "Employee pseudonym", "text"),
    ("health_care_professional", "Health care professional (optional)", "text"),
]
NEAR_MISS_FIELDS = ("occurred_at", "area_id", "description", "people_involved", "contributing_factors",
                    "immediate_action", "corrective_action", "notes")  # T23.3 (a)
# T23.2 (d) as changed by T23.24 (d): the combined clearance is a view-time review aid, never a stored field.
PREFILLED = ("est_id", "area_id", "camera_ids", "occurred_at", "duration_s", "objects_involved", "ai_label",
             "evasive_action_observed", "evidence_clip_ids", "description", "grouping_basis")
OBS_FIELDS = ("camera_observability", "observability_cameras")  # T23.23 (c): area manager, human-started reports
EDITABLE = tuple(dict.fromkeys(("kind",) + tuple(f for f in PREFILLED if f != "grouping_basis") + NEAR_MISS_FIELDS
                               + tuple(f for f, _, _ in INCIDENT_FIELDS)))
# T23.22: fields a person types (shown in an "entered by" block, skipped by the linter).
USER_TEXT = ("description", "people_involved", "immediate_action", "corrective_action", "notes") + tuple(
    f for f, _, k in INCIDENT_FIELDS if k == "text")

# Fixed texts (T23.7 c, T23.9, T23.10, T23.13, T23.23 d, T23.24 b, T23.26, T23.27 f).
EXPORT_301_BANNER = "Equivalent-form data for manual transcription. Not a submission to OSHA."
FLAG_TEXT = ("Above the set threshold. Possible causes include false alerts by the system, under-recording, "
             "or different definitions. The cause is not determined by this flag.")
REGULATOR_BANNER = "Simulated regulator view: a proposal. No data leaves this computer."
MISS_CAPTION = ("Descriptive workflow measure. A human report without a matching alert is not evidence of a detector miss; "
                "miss rates require the T22 reference method.")
DEMO_DATA_NOTE = "Simulated demo data. Descriptive workflow measure, not a validated safety-performance measure."
NO_SOURCE_FIGURE = "accuracy of the alert source: not reported"
COMBINED_LABEL = "smallest estimated separation among members (estimate from camera geometry, not a verified measurement)"
NOT_COMBINED = "not combined: members use different geometry methods"
NOT_RECORDED = "not combined: the geometry method or calibration tier is not recorded for every member"
EVASIVE_TRUE = "observed by the system in at least one member"
DURATION_LABEL = "span of member episodes"
ZERO_COUNT = "Absence of an alert is not absence of an event."
NO_TIME = "not computable: no monitored time"
NO_HOURS = "rate not computable: hours not entered"
PRIVACY_NOTICE = ("Privacy (T23.13): pseudonyms only. No data of a real person is entered; in a demo establishment every "
                  "entry is fictional.")
DEMO_NOTE = "fictional demo entry"
PREFILL_NOTE = "pre-filled by the system"
FIXED_TEXTS = (EXPORT_301_BANNER, FLAG_TEXT, REGULATOR_BANNER, MISS_CAPTION, DEMO_DATA_NOTE, NO_SOURCE_FIGURE)
# T23.12: the only qualified forms of "near miss" besides "candidate near miss", workflow pages only.
RECORDED_NM = {"am_approve": "recorded near miss (manager-approved)", "sm_overturn": "recorded near miss (safety-manager overturn)"}
RECORDABLE_BADGE = '<span class="recordable-yes">Recordable</span>'  # the only place the word is printed (T23.12)
# Section 5: terms refused on workflow pages outside the fixed T23.9 and T23.23 (d) texts.
TERMS = re.compile(r"\bfalse[- ]positives?\b|\bfalse[- ]negatives?\b|\bprecision\b|\brecall\b|\baccuracy\b|\bmiss[- ]rates?\b", re.I)


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def iso_week(ts: str) -> str:
    """T23.18 (a): the period of a report is the ISO week of its current occurred_at (UTC)."""
    y, w, _ = parse_utc(ts).isocalendar()
    return f"{y}-W{w:02d}"


def week_bounds(period: str) -> tuple[datetime, datetime]:
    m = re.fullmatch(r"(\d{4})-W(\d{2})", period)
    if not m:
        raise _spec(f"period {period!r} is not an ISO week YYYY-Www")
    start = datetime.fromisocalendar(int(m.group(1)), int(m.group(2)), 1).replace(tzinfo=timezone.utc)
    return start, start + timedelta(days=7)


# --- T23.2 intake, T23.21 grouping --------------------------------------------------------------------------------------

def _axis(e: dict[str, Any]) -> tuple[str, ...]:
    """T23.21 (c): a common axis exists only on a declared one (aligned_session, or the demo's workflow_timebase_declared
    with its evidence reference); otherwise each camera's episodes form groups on their own."""
    if e.get("timeline_kind") in COMMON_AXES:
        return ("common", e.get("timeline_kind"), e.get("timeline_id", ""))
    return ("camera", e["camera_id"], e.get("timeline_id", ""))


def _basis(e: dict[str, Any]) -> str:
    if e.get("timeline_kind") in COMMON_AXES:
        ref = e.get("timebase_evidence_ref")
        return f"grouped on a declared common axis ({e['timeline_kind']}" + (f"; evidence: {ref})" if ref else ")")
    return PER_CAMERA


def group_episodes(episodes: list[dict[str, Any]], t_group_s: float) -> list[tuple[list[dict[str, Any]], str]]:
    """T23.2 (b) with T23.21 (b), (c): on one axis, episodes whose closed intervals [t_start, t_end] overlap after each is
    widened by t_group_s on both sides form one group, transitively; widened intervals that only touch are merged. Episodes
    without a common axis group per camera. Returns (group, grouping basis) in order of the first member's onset."""
    by_axis: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for e in episodes:
        by_axis.setdefault(_axis(e), []).append(e)
    out: list[tuple[list[dict[str, Any]], str]] = []
    for eps in by_axis.values():
        eps = sorted(eps, key=lambda e: (e["t_start_tl_s"], e["ep_id"]))
        groups: list[list[dict[str, Any]]] = []
        end = None
        for e in eps:
            lo, hi = e["t_start_tl_s"] - t_group_s, e["t_end_tl_s"] + t_group_s
            if groups and lo <= end:
                groups[-1].append(e)
                end = max(end, hi)
            else:
                groups.append([e])
                end = hi
        out += [(g, _basis(g[0])) for g in groups]
    return sorted(out, key=lambda x: (x[0][0]["t_start_tl_s"], x[0][0]["ep_id"]))


def report_kind(members: list[dict[str, Any]]) -> str:
    """T23.2 (c)."""
    return "incident_draft" if any(m["g2_label"] == "lbl_ct" for m in members) else "near_miss"


def group_ai_label(members: list[dict[str, Any]]) -> str:
    """T23.2 (d). A group whose members carry different G2 labels shows every distinct label, in CT, NM, UD order
    (AR-63 item 5, accepted at D-49: the order is presentational)."""
    labels = [AI_LABEL[g] for g in ("lbl_ct", "lbl_nm", "lbl_ud") if any(m["g2_label"] == g for m in members)]
    return " and ".join(labels)


def _fmt_time(ts: str) -> str:
    return parse_utc(ts).strftime("%Y-%m-%d %H:%M:%S UTC")


# --- T23.24 combined values -----------------------------------------------------------------------------------------------

MEMBER_KEYS = ("ep_id", "camera_id", "minclr_m", "minclr_m_null_reason", "geometry_method", "calibration_tier",
               "clearance_sigma_m", "sigma_status", "q_state", "q_reasons", "prov_class", "s4_artifact_id")


def combined(members: list[dict[str, Any]]) -> dict[str, Any]:
    """T23.24 (a)-(c): member clearances are combined only if every non-null value has the same geometry_method and the
    same calibration tier; the combined value is the smallest, with its provenance. Each member's values are listed.
    A view-time review aid (T23.24 d): never stored as a measurement."""
    listed = [{k: m.get(k) for k in MEMBER_KEYS} for m in sorted(members, key=lambda m: m["ep_id"])]
    values = [m for m in listed if m["minclr_m"] is not None]
    if not values:
        reasons = sorted({m.get("minclr_m_null_reason") or "not_observable" for m in listed})
        return {"combined": None, "text": f"not available ({', '.join(reasons)})", "members": listed}
    if len({(m["geometry_method"], m["calibration_tier"]) for m in values}) > 1:
        return {"combined": None, "text": NOT_COMBINED, "members": listed}
    if any(m["geometry_method"] is None or m["calibration_tier"] is None for m in values):
        # comparability cannot be shown (members drawn before E-1.2.23 carry no calibration tier): no combined value (AR-64)
        return {"combined": None, "text": NOT_RECORDED, "members": listed}
    best = min(values, key=lambda m: (m["minclr_m"], m["ep_id"]))
    c = {"value_m": best["minclr_m"], **{k: best[k] for k in MEMBER_KEYS if k not in ("minclr_m", "minclr_m_null_reason")}}
    return {"combined": c, "text": f"{best['minclr_m']:.2f} m ({best['geometry_method']}, {best['sigma_status'] or 'sigma status not recorded'})",
            "members": listed}


def description(ai_label: str, area_name: str, occurred_at: str, comb: dict[str, Any], demo: bool) -> str:
    """T23.2 (d) with T23.24 (e): "Smallest estimated separation <x> m (<method>, <sigma status>)". <label> is the AI label
    with its leading "candidate" written once (AR-63 item 5). Not combined or not available: AR-64."""
    label = ai_label[len("candidate "):] if ai_label.startswith("candidate ") else ai_label[len("candidate"):]
    when = _fmt_time(occurred_at) + (" (simulated calendar)" if demo else "")
    if comb["combined"] is not None:
        sep = f"Smallest estimated separation {comb['text']}"
    elif comb["text"] in (NOT_COMBINED, NOT_RECORDED):
        sep = f"Smallest estimated separation: {comb['text']}"
    else:
        sep = f"Smallest estimated separation {comb['text']}"
    return (f"The system flagged a candidate{'' if label.startswith(',') else ' '}{label} between a person and a forklift in "
            f"{area_name} at {when}. {sep}. Review the clip before deciding.")


def prefill(members: list[dict[str, Any]], est_id: str, area: dict[str, Any], calendar_start: datetime, demo: bool,
            evidence_clip_ids: list[str], basis: str) -> dict[str, Any]:
    """T23.2 (d): occurred_at = earliest onset placed on the (simulated) calendar; duration_s = latest end minus earliest
    onset (the span of member episodes, T23.24 e); evasive_action_observed true if any member's E_ep is true."""
    onset = min(m["t_start_tl_s"] for m in members)
    end = max(m["t_end_tl_s"] for m in members)
    occurred = utc(calendar_start + timedelta(seconds=onset))
    e_vals = {m.get("E_ep") for m in members}
    evasive = "true" if True in e_vals or 1 in e_vals else ("unknown" if None in e_vals or 2 in e_vals else "false")
    ai_label = group_ai_label(members)
    fields = {
        "kind": "incident" if report_kind(members) == "incident_draft" else "near_miss",
        "est_id": est_id, "area_id": area["area_id"], "camera_ids": sorted({m["camera_id"] for m in members}),
        "occurred_at": occurred, "duration_s": round(end - onset, 6), "objects_involved": ["person", "forklift"],
        "ai_label": ai_label, "evasive_action_observed": evasive, "evidence_clip_ids": list(evidence_clip_ids),
        "grouping_basis": basis,
    }
    fields["description"] = description(ai_label, area["name"], occurred, combined(members), demo)
    return fields


# --- fold of the report log (T23.15, T23.19) -----------------------------------------------------------------------------

@dataclass
class Report:
    header: dict[str, Any]
    state: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    label: str | None = None  # the label of the latest decision
    entries: list[dict[str, Any]] = field(default_factory=list)
    prefilled: set[str] = field(default_factory=set)
    entered_by: dict[str, str] = field(default_factory=dict)  # field -> actor of the entry that last set it
    recordability: dict[str, Any] | None = None  # the latest set_recordability value
    determination: str = "not_set"  # T23.19 (b)

    @property
    def report_id(self) -> str:
        return self.header["report_id"]

    @property
    def origin(self) -> str:
        return self.header["origin"]

    @property
    def members(self) -> list[str]:
        return list(self.header.get("member_episode_ids") or [])

    def actions(self, *names: str) -> list[dict[str, Any]]:
        return [e for e in self.entries if e["action"] in names]

    def deciders(self, level: str) -> set[str]:
        names = AM_DECISIONS if level == "am" else SM_ACTIONS
        return {e["actor_user_id"] for e in self.actions(*names)}

    def entered_state_at(self) -> str:
        last = [e for e in self.entries if e["state_before"] != e["state_after"]]
        return last[-1]["created_utc"] if last else self.header["created_utc"]

    def reopened_duplicate(self) -> bool:
        """In pending_sm after sm_reopen of a closed_duplicate (T23.20 c, d)."""
        moves = [e for e in self.entries if e["state_before"] != e["state_after"]]
        return bool(self.state == "pending_sm" and moves and moves[-1]["action"] == "sm_reopen"
                    and moves[-1]["state_before"] == "closed_duplicate")

    def revised(self) -> bool:
        """T23.18 (c): a field, state or recordability entry after the report's first manager decision."""
        first = next((k for k, e in enumerate(self.entries) if e["action"] in DECISIONS), None)
        if first is None:
            return False
        return any(e["field_changes"] or e["state_before"] != e["state_after"]
                   or e["action"] in ("set_recordability", "withdraw_recordability") for e in self.entries[first + 1:])

    def wording(self) -> str:
        """T23.12: how the report is named on workflow pages."""
        if self.state == "recorded" and self.label == "nm":
            last = [e for e in self.entries if e["action"] in RECORDED_NM and e["state_after"] == "recorded"]
            if last:
                return RECORDED_NM[last[-1]["action"]]
        kind = self.fields.get("kind", "")
        return f"{'AI-started' if self.origin == 'ai' else 'human-started'} report ({kind.replace('_', ' ') if kind != 'near_miss' else 'kind near_miss'}), {self.state}"


def fold(header: dict[str, Any], entries: list[dict[str, Any]]) -> Report:
    r = Report(header)
    for e in entries:
        r.entries.append(e)
        r.state = e["state_after"]
        for name, change in e["field_changes"].items():
            if name == "recordability":
                continue
            r.fields[name] = json.loads(change["after"])
            r.entered_by[name] = e["actor_user_id"]
            if e["action"] == "create_ai":
                r.prefilled.add(name)
            else:
                r.prefilled.discard(name)
        if e["action"] in ("am_approve", "am_reject", "sm_uphold", "sm_overturn", "sm_reclassify") and e["label"] is not None:
            r.label = e["label"]
        if e["action"] == "set_recordability":
            r.recordability = json.loads(e["field_changes"]["recordability"]["after"])
            r.determination = r.recordability["recordable"]
        if e["action"] == "withdraw_recordability":
            r.determination = "withdrawn"  # T23.19 (c); the previous determination stays in the log
    return r


def changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, str]]:
    """field_changes: before and after values as canonical JSON text (AR-63 item 3)."""
    dump = lambda v: json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {k: {"before": dump(before.get(k)), "after": dump(after[k])} for k in sorted(after) if before.get(k) != after[k]}


# --- shares and cells -----------------------------------------------------------------------------------------------------

@dataclass
class Share:
    k: int
    n: int

    @property
    def interval(self) -> tuple[float, float] | None:
        return wilson(self.k, self.n)  # the T-13 function, z = 1.959964

    @property
    def value(self) -> float | None:
        return self.k / self.n if self.n else None

    def text(self) -> str:
        if not self.n:
            return f"{self.k}/0 (none; not defined)"
        lo, hi = self.interval
        return f"{self.k}/{self.n} = {self.k / self.n:.3f} (n = {self.n}; Wilson 95 % interval {lo:.3f} to {hi:.3f})"


@dataclass
class Cell:
    """One indicator value with the counts printed beside it (T23.18 c, d; section 5)."""
    value: Any
    notes: dict[str, Any] = field(default_factory=dict)
    determined: bool = True  # every CR-030 item is ruled (D-49): one reading per indicator

    def text(self, fmt: Callable[[Any], str] = str) -> str:
        extra = "".join(f"; {k}: {_note(v)}" for k, v in self.notes.items())
        return fmt(self.value) + extra


def _note(v: Any) -> str:
    if isinstance(v, dict):
        return ", ".join(f"{k} {_note(x)}" for k, x in v.items()) or "none"
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "none"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def one(value: Any) -> Cell:
    return Cell(value)


# --- monitoring (T23.23 a, b) --------------------------------------------------------------------------------------------

Interval = tuple[datetime, datetime]


def union(intervals: Iterable[Interval]) -> list[Interval]:
    out: list[list[datetime]] = []
    for a, b in sorted(i for i in intervals if i[1] > i[0]):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def intersect(xs: list[Interval], ys: list[Interval]) -> list[Interval]:
    out = []
    for a, b in union(xs):
        for c, d in union(ys):
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                out.append((lo, hi))
    return union(out)


def clip(xs: list[Interval], lo: datetime, hi: datetime) -> list[Interval]:
    return union((max(a, lo), min(b, hi)) for a, b in xs)


def seconds(xs: list[Interval]) -> float:
    return sum((b - a).total_seconds() for a, b in union(xs))


def processed_intervals(row: dict[str, Any]) -> list[dict[str, Any]]:
    """A camera's processed coverage: S5 artifacts of the source configuration with the window each covers (AR-64). A row
    written before E-1.2.23 has only has_source_output: its whole coverage is processed by one artifact."""
    if "processed" in row:
        return row["processed"]
    if row.get("has_source_output") and row["segments"]:
        return [{"start_utc": row["segments"][0]["start_utc"], "end_utc": row["segments"][-1]["end_utc"], "s5_artifact_id": None}]
    return []


def check_processed(camera_id: str, processed: list[dict[str, Any]]) -> None:
    """T23.23 (a): two S5 artifacts of the source configuration covering the same camera and window give ERR-SPEC."""
    spans = sorted((parse_utc(p["start_utc"]), parse_utc(p["end_utc"]), p.get("s5_artifact_id")) for p in processed)
    for (a, b, x), (c, d, y) in zip(spans, spans[1:]):
        if c < b and x != y:
            raise _spec(f"camera {camera_id}: two S5 artifacts of the source configuration cover the same window (T23.23 a)")


def camera_coverage(row: dict[str, Any] | None) -> dict[str, list[Interval]]:
    if row is None:
        return {"usable": [], "usable_degraded": [], "processed": [], "monitored": []}
    seg = lambda state: union((parse_utc(s["start_utc"]), parse_utc(s["end_utc"])) for s in row["segments"] if s["coverage_state"] == state)
    processed = processed_intervals(row)
    check_processed(row["camera_id"], processed)
    proc = union((parse_utc(p["start_utc"]), parse_utc(p["end_utc"])) for p in processed)
    usable = seg("usable")
    return {"usable": usable, "usable_degraded": seg("usable_degraded"), "processed": proc, "monitored": intersect(usable, proc)}


def area_hours(monitoring: dict[str, dict[str, Any]], cams: list[str], lo: datetime, hi: datetime) -> dict[str, Any]:
    """T23.23 (b): area time is the union over the area's cameras; camera-hours (the sum) are descriptive only."""
    cov = {c: camera_coverage(monitoring.get(c)) for c in cams}
    u = lambda key: seconds(clip([i for c in cams for i in cov[c][key]], lo, hi)) / 3600.0
    return {"usable_h": u("usable"), "usable_degraded_h": u("usable_degraded"), "processed_h": u("processed"),
            "monitored_area_h": u("monitored"), "camera_h": sum(seconds(clip(cov[c]["monitored"], lo, hi)) for c in cams) / 3600.0,
            "unprocessed_cameras": sum(1 for c in cams if not cov[c]["processed"])}


def monitored_in(monitoring: dict[str, dict[str, Any]], cams: list[str], lo: datetime, hi: datetime) -> bool:
    """Monitored at any instant of the closed window [lo, hi] (T23.23 c 1)."""
    for c in cams:
        for a, b in camera_coverage(monitoring.get(c))["monitored"]:
            if a <= hi and b >= lo and (b > a):
                return True
    return False


# --- T23.23 (c) observability of a human-started report --------------------------------------------------------------

def observability_category(r: Report, ai_reports: list[Report], ep_times: dict[str, tuple[datetime, datetime, str]],
                           monitoring: dict[str, dict[str, Any]], area_cams: list[str], t_link_s: float) -> int:
    """Index into OBS_CATEGORIES. ep_times: member episode -> (start, end, camera) on the calendar."""
    at = parse_utc(r.fields["occurred_at"])
    lo, hi = at - timedelta(seconds=t_link_s), at + timedelta(seconds=t_link_s)
    if not monitored_in(monitoring, area_cams, lo, hi):
        return 0
    obs = r.fields.get("camera_observability")
    if obs == "not_observable":
        return 1
    if obs != "observable":
        return 2
    cams = set(r.fields.get("observability_cameras") or [])
    for a in ai_reports:
        if a.state == "closed_split" or a.fields.get("area_id") != r.fields.get("area_id"):
            continue
        for m in a.members:
            s, e, cam = ep_times.get(m, (None, None, None))
            if cam in cams and s is not None and s <= hi and e >= lo:
                return 3
    return 4


# --- indicators (T23.8 with D-49.1 section 5) and flags (T23.9) --------------------------------------------------------

def _in_scope(r: Report, est_id: str, area_id: str | None, period: str, splits: bool = False) -> bool:
    """Section 5: closed_split originals are excluded everywhere (counted beside I2/I3 only)."""
    f = r.fields
    return ((r.state != "closed_split" or splits) and f.get("est_id") == est_id and (area_id is None or f.get("area_id") == area_id)
            and "occurred_at" in f and iso_week(f["occurred_at"]) == period)


def _am_decision(r: Report) -> str | None:
    am = r.actions(*AM_DECISIONS)
    return am[0]["action"] if am else None  # the area manager decides once per report


def indicators(reports: list[Report], est_id: str, area_id: str | None, period: str, areas: dict[str, dict[str, Any]],
               monitoring: dict[str, dict[str, Any]], hours: float | None, params: dict[str, Any], as_of: datetime,
               ep_times: dict[str, tuple[datetime, datetime, str]] | None = None) -> dict[str, Any]:
    """Every value from the report log truncated at as_of (the caller folds the truncated log)."""
    ep_times = ep_times or {}
    scope = [r for r in reports if _in_scope(r, est_id, area_id, period)]
    ai = [r for r in scope if r.origin == "ai"]
    human = [r for r in scope if r.origin == "human"]
    rev = lambda rs: sum(1 for r in rs if r.revised())
    out: dict[str, Any] = {"period": period}
    dup = sum(1 for r in ai if r.state == "closed_duplicate")
    out["I1"] = Cell(len(ai), {"excluding closed_duplicate": len(ai) - dup, "closed_duplicate": dup})
    am = {r.report_id: _am_decision(r) for r in ai}
    decided = [r for r in ai if am[r.report_id] in ("am_approve", "am_reject")]
    approve = sum(1 for r in decided if am[r.report_id] == "am_approve")
    side = {"undecided": sum(1 for r in ai if r.state == "pending_am"),
            "am_duplicate": sum(1 for r in ai if am[r.report_id] == "am_duplicate"),
            "am_split": sum(1 for r in reports if r.origin == "ai" and r.state == "closed_split" and _in_scope(r, est_id, area_id, period, True)),
            "revised after first decision": rev(decided)}
    out["I2"] = Cell(Share(approve, len(decided)), dict(side))
    out["I3"] = Cell(Share(len(decided) - approve, len(decided)), dict(side))
    # I4: the latest SM decision per AI report; confirmations and overturns of duplicates are counted beside.
    in4, confirm, dup_over = [], 0, 0
    acts = {"sm_confirm_duplicate": sum(len(r.actions("sm_confirm_duplicate")) for r in ai),
            "overturn of a duplicate": sum(1 for r in ai for e in r.actions("sm_overturn") if _from_reopened_duplicate(r, e))}
    for r in ai:
        dec = r.actions("sm_uphold", "sm_overturn", "sm_confirm_duplicate")
        if not dec:
            continue
        last = dec[-1]
        if last["action"] == "sm_confirm_duplicate":
            confirm += 1
        elif last["action"] == "sm_overturn" and _from_reopened_duplicate(r, last):
            dup_over += 1
        else:
            in4.append((r, last["action"]))
    out["I4"] = Cell(Share(sum(1 for _, a in in4 if a == "sm_overturn"), len(in4)),
                     {"undecided": sum(1 for r in ai if r.state == "pending_sm"),
                      # counted beside, outside n; the unit is not stated for these side counts (CR-031 item 4): both are printed
                      "sm_confirm_duplicate": {"reports (latest decision)": confirm, "actions": acts["sm_confirm_duplicate"]},
                      "overturn of a duplicate": {"reports (latest decision)": dup_over, "actions": acts["overturn of a duplicate"]},
                      "revised after first decision": rev([r for r, _ in in4])})
    ever = [r for r in ai if any(e["state_after"] == "recorded" for e in r.entries)]
    out["I5"] = Cell(Share(sum(1 for r in ever if r.actions("sm_reclassify")), len(ever)),
                     {"undecided": sum(1 for r in ever if r.state in PENDING), "revised after first decision": rev(ever)})
    limit = timedelta(days=params["t_pending_days"])
    stale = {s: 0 for s in PENDING}
    stale_c = {s: 0 for s in PENDING}
    for r in scope:
        if r.state in PENDING:
            stale[r.state] += as_of - parse_utc(r.entered_state_at()) > limit
            stale_c[r.state] += as_of - parse_utc(r.header["created_utc"]) > limit
    out["I6"] = Cell(stale, {"age since creation": stale_c})
    lo, hi = week_bounds(period)
    cams = [c for a in areas.values() if a["est_id"] == est_id and (area_id is None or a["area_id"] == area_id) for c in a["camera_ids"]]
    mon = area_hours(monitoring, cams, lo, hi) if area_id else _est_hours(monitoring, areas, est_id, lo, hi)
    out["monitoring"] = Cell(mon)
    rec_nm = lambda rs: [r for r in rs if r.state == "recorded" and r.fields.get("kind") == "near_miss"]
    ai_nm = rec_nm(ai)
    out["I7_ai"] = Cell(len(ai_nm), {"group_resolution = cannot_tell": sum(1 for r in ai_nm if r.fields.get("group_resolution") == "cannot_tell"),
                                     "revised after first decision": rev(ai_nm)})
    out["I7_human"] = Cell(len(rec_nm(human)), {"revised after first decision": rev(rec_nm(human))})
    h = mon["monitored_area_h"]
    rate_notes = {"numerator": len(ai_nm), "denominator_h": h, "unprocessed cameras": mon["unprocessed_cameras"]}
    out["I7_ai_rate"] = Cell(len(ai_nm) / h if h > 0 else NO_TIME, rate_notes)
    all_ai = [r for r in reports if r.origin == "ai"]
    cats = {c: 0 for c in OBS_CATEGORIES}
    listed: dict[str, list[str]] = {c: [] for c in OBS_CATEGORIES}
    pop8 = [r for r in human if r.state == "recorded" and r.fields.get("kind") in ("near_miss", "incident")]
    for r in pop8:
        k = observability_category(r, all_ai, ep_times, monitoring, areas.get(r.fields["area_id"], {}).get("camera_ids", []),
                                   params["t_link_s"])
        cats[OBS_CATEGORIES[k]] += 1
        listed[OBS_CATEGORIES[k]].append(r.report_id)
    out["I8"] = Cell(cats[OBS_CATEGORIES[4]], {"categories": cats, "reports (category 5)": listed[OBS_CATEGORIES[4]],
                                                "revised after first decision": rev(pop8)})
    est_areas = [a for a in areas.values() if a["est_id"] == est_id]
    out["area_monitoring_share"] = Cell(Share(sum(1 for a in est_areas if area_hours(monitoring, a["camera_ids"], lo, hi)["monitored_area_h"] > 0),
                                              len(est_areas)))
    incidents = [r for r in scope if r.fields.get("kind") == "incident"]
    cases = [r for r in incidents if r.state == "recorded" and r.determination == "yes"]
    by = {c: sum(1 for r in cases if c in r.recordability["criteria"]) for c in CRITERIA}
    side9 = {"not_set": sum(1 for r in incidents if r.determination == "not_set"),
             "undetermined": sum(1 for r in incidents if r.determination == "undetermined"),
             "withdrawn": sum(1 for r in incidents if r.determination == "withdrawn"),
             "yes on reports not currently recorded": sum(1 for r in incidents if r.determination == "yes" and r.state != "recorded"),
             "revised after first decision": rev(incidents)}
    out["I9"] = Cell({"cases": len(cases), "by_criterion": by}, side9)
    out["hours_worked"] = hours
    provisional = side9["not_set"] > 0 or side9["undetermined"] > 0
    out["incidence_rate"] = Cell(len(cases) * 200_000 / hours if hours else None, {"provisional": provisional})
    return out


def _from_reopened_duplicate(r: Report, decision: dict[str, Any]) -> bool:
    k = r.entries.index(decision)
    moves = [e for e in r.entries[:k] if e["state_before"] != e["state_after"]]
    return bool(moves and moves[-1]["action"] == "sm_reopen" and moves[-1]["state_before"] == "closed_duplicate")


def _est_hours(monitoring, areas, est_id, lo, hi) -> dict[str, Any]:
    """An establishment's figures: the sum over its areas of each area's union (areas share no camera, T23.1 a)."""
    per = [area_hours(monitoring, a["camera_ids"], lo, hi) for a in areas.values() if a["est_id"] == est_id]
    keys = ("usable_h", "usable_degraded_h", "processed_h", "monitored_area_h", "camera_h", "unprocessed_cameras")
    return {k: sum(p[k] for p in per) for k in keys}


def flags(ind: dict[str, Any], params: dict[str, Any]) -> dict[str, Cell]:
    """T23.9 with section 5: F1 and F2 are not evaluated below their minimum n (value None, "insufficient n")."""
    def share_flag(c: Cell, n_min: int, theta: float) -> Cell:
        s = c.value
        if s.n < n_min:
            return Cell(None, {"insufficient n": f"{s.n} < {n_min}"})
        return Cell(bool(s.interval and s.interval[0] > theta))
    return {"F1": share_flag(ind["I3"], params["n_flag_min"], params["theta_rej"]),
            "F2": share_flag(ind["I4"], params["n_flag_min_sm"], params["theta_over"]),
            "F3": Cell(sum(ind["I6"].value.values()) > 0),
            "F4": Cell(ind["I8"].value >= params["k_miss"])}


# --- source quality (T23.26) ------------------------------------------------------------------------------------------

def source_name(sq: dict[str, Any]) -> str:
    return f"configuration {sq['config']} ({sq['path']})"


def source_banner(sq: dict[str, Any] | None) -> str:
    """T23.26: the banner on every page that shows AI alerts, the regulator view and W-01."""
    if not sq or sq.get("cm03") is None:
        src = source_name(sq) if sq else "a source this store does not name"
        return f"AI alerts in this demo come from {src}; {NO_SOURCE_FIGURE}. Workflow measures describe the workflow, not the system's accuracy."
    figs = ", ".join(f"{k} {sq[v]:.2f}" for k, v in (("CM-03", "cm03"), ("EV-M1", "ev_m1"), ("EV-M2", "ev_m2")) if sq.get(v) is not None)
    return (f"AI alerts in this demo come from {source_name(sq)}. On SDG validation that source covers {sq['cm03'] * 100:.0f} % of "
            "worker–forklift co-visible frames (CM-03); most interactions produce no alert. Workflow measures describe the "
            f"workflow, not the system's accuracy. Reported figures: {figs} ({sq.get('report_ref') or 'no report reference'}).")


# --- wording (T23.12, T23.22, section 5) --------------------------------------------------------------------------------

_TAG = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", re.S | re.I)
_RECORDABLE = re.compile(r"\brecordable\b", re.I)
# T23.22: user-entered blocks, and the editing form's own text areas (they hold the person's text); T23.26 banner.
_EXEMPT_BLOCKS = re.compile(r'<blockquote class="user-entered">.*?</blockquote>|<div class="source-banner">.*?</div>'
                            r'|(?<=<textarea)[^>]*>.*?(?=</textarea>)', re.S)


def user_block(pseudonym: str, text: Any) -> str:
    """T23.22: user text stored verbatim, shown HTML-escaped in a block marked "entered by <pseudonym>"."""
    value = ", ".join(map(str, text)) if isinstance(text, list) else ("" if text is None else str(text))
    return (f'<blockquote class="user-entered"><span class="muted">entered by {_html.escape(pseudonym)}:</span> '
            f'{_html.escape(value)}</blockquote>')


def banner_block(sq: dict[str, Any] | None) -> str:
    return f'<div class="source-banner"><p><strong>{_html.escape(source_banner(sq), quote=False)}</strong></p></div>'


def visible_text(page: str) -> str:
    """The text of an HTML page with tags, scripts, styles and the exempt blocks removed (one line per block)."""
    marked = _EXEMPT_BLOCKS.sub("\n", page).replace(RECORDABLE_BADGE, "\x00RECORDABLE_YES\x00")
    text = _TAG.sub("\n", marked)
    return _html.unescape(text)


def lint_workflow(text: str, html_page: bool = True, exempt: Iterable[str] = ()) -> list[str]:
    """W1-W6 (rq1.export.report.WORDING), T23.12 and the section 5 term list on a workflow page or export. Accepted only
    here: the two "recorded near miss (...)" forms, the fixed texts, "Recordable" printed by `RECORDABLE_BADGE`, and the
    user-entered and source-banner blocks (T23.22, T23.26)."""
    body = visible_text(text) if html_page else text
    issues = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        for fixed in tuple(exempt) + tuple(FIXED_TEXTS):
            line = line.replace(fixed, " ")
        for phrase in RECORDED_NM.values():
            line = line.replace(phrase, " ")
        if _RECORDABLE.search(line.replace("\x00RECORDABLE_YES\x00", " ")):
            issues.append(f"T23.12 recordable: {line}")
        for rule, pattern in WORDING:
            if pattern.search(line):
                issues.append(f"{rule}: {line}")
        if TERMS.search(line):
            issues.append(f"section 5 term list: {line}")
    return issues


def check_params(p: dict[str, Any]) -> dict[str, Any]:
    out = dict(PARAMS)
    out.update(p)
    for k in ("n_flag_min", "n_flag_min_sm", "k_miss"):
        if type(out[k]) is not int or out[k] < 0:
            raise _spec(f"{k} is a non-negative integer")
    for k in ("t_group_s", "t_pending_days", "theta_rej", "theta_over", "t_link_s"):
        out[k] = float(out[k])
        if out[k] < 0:
            raise _spec(f"{k} is non-negative")
    return out


def sorted_unique(xs: Iterable[str]) -> list[str]:
    return sorted(set(xs))
