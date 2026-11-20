"""Appendix T T23 (contract E-1.2.22; D-48): the reporting-workflow rules as pure functions.

Nothing here reads files or writes records; `store.py` applies these rules. Representation choices are AR-63; the points
T23 leaves undefined that would change a count, a state or a statistic are CR-030 and are never chosen here: where two
readings of an indicator could differ, both are computed and the value is printed only when they agree
(`Readings`), otherwise as "not determined (CR-030 item n)".
"""
from __future__ import annotations

import html as _html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from rq1.evaluation.estimators import wilson
from rq1.export.report import WORDING
from rq1.schema.errors import ContractError

# T23.14
PARAMS: dict[str, Any] = {"wf_source_config": "BL-6", "t_group_s": 2.0, "t_pending_days": 7.0, "theta_rej": 0.5,
                          "theta_over": 0.3, "n_flag_min": 10, "n_flag_min_sm": 5, "t_link_s": 60.0, "k_miss": 2}
ROLES = ("area_manager", "safety_manager", "worker", "oversight", "owner")  # T23.1 (b)
STATES = ("pending_am", "pending_sm", "recorded", "closed_rejected", "closed_duplicate")  # T23.4
PENDING = ("pending_am", "pending_sm")

# T23.4: action -> (who, allowed from-states or None for "any", to-state or None for "same")
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
}
AM_DECISIONS = ("am_approve", "am_reject", "am_duplicate")
SM_ACTIONS = ("sm_uphold", "sm_overturn", "sm_reclassify", "sm_reopen", "set_recordability", "sm_note")
REJECT_REASONS = {"not_hazardous": "not_hazardous", "no_person_or_no_forklift": "not_hazardous",
                  "cannot_tell_from_video": "ud", "other": "unsure"}  # T23.5 (b)
APPROVE_LABELS = ("nm", "ct")
RECLASSIFY_LABELS = ("not_hazardous", "ud")  # T23.5 (c)
CONFIDENCE = (1.0, 2.0, 3.0)  # T22.5 (b); T23.5 (a) default 3.0
CONTRIBUTING = ("speed", "visibility", "blind corner", "pedestrian route", "load obstructing view", "training",
                "procedure", "other")  # T23.3 (a)
RECORDABLE = ("yes", "no", "undetermined")  # T23.7 (b)
CRITERIA = ("death", "days_away", "restricted_or_transfer", "medical_treatment_beyond_first_aid",
            "loss_of_consciousness", "significant_diagnosed")
DAYS_CRITERIA = ("days_away", "restricted_or_transfer")  # "with days counts where they apply" (AR-63 item 9)
AI_LABEL = {"lbl_nm": "candidate near miss", "lbl_ud": "candidate, undetermined", "lbl_ct": "candidate contact"}  # T23.2 (d)
G2_SOURCE = tuple(AI_LABEL)  # T23.2 (a): NM, UD or CT

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
PREFILLED = ("est_id", "area_id", "camera_ids", "occurred_at", "duration_s", "objects_involved", "ai_label",
             "min_clearance_m", "min_clearance_null_reason", "geometry_method", "evasive_action_observed",
             "evidence_clip_ids", "description")  # T23.2 (d)
EDITABLE = tuple(dict.fromkeys(("kind",) + PREFILLED + NEAR_MISS_FIELDS + tuple(f for f, _, _ in INCIDENT_FIELDS)))

# Fixed texts (T23.7 c, T23.9, T23.10, T23.13).
EXPORT_301_BANNER = "Equivalent-form data for manual transcription. Not a submission to OSHA."
FLAG_TEXT = ("Above the set threshold. Possible causes include false alerts by the system, under-recording, "
             "or different definitions. The cause is not determined by this flag.")
REGULATOR_BANNER = "Simulated regulator view: a proposal. No data leaves this computer."
DEMO_NOTE = "fictional demo entry"
PREFILL_NOTE = "pre-filled by the system"
FIXED_TEXTS = (EXPORT_301_BANNER, FLAG_TEXT, REGULATOR_BANNER)
# T23.12: the only qualified forms of "near miss" besides "candidate near miss", workflow pages only.
RECORDED_NM = {"am_approve": "recorded near miss (manager-approved)", "sm_overturn": "recorded near miss (safety-manager overturn)"}
RECORDABLE_BADGE = '<span class="recordable-yes">Recordable</span>'  # the only place the word is printed (T23.12)


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def iso_week(ts: str) -> str:
    """T23.8: the period of a report is the ISO week of its occurred_at (UTC)."""
    y, w, _ = parse_utc(ts).isocalendar()
    return f"{y}-W{w:02d}"


def week_bounds(period: str) -> tuple[datetime, datetime]:
    m = re.fullmatch(r"(\d{4})-W(\d{2})", period)
    if not m:
        raise _spec(f"period {period!r} is not an ISO week YYYY-Www")
    start = datetime.fromisocalendar(int(m.group(1)), int(m.group(2)), 1).replace(tzinfo=timezone.utc)
    return start, start + timedelta(days=7)


# --- T23.2 intake ------------------------------------------------------------------------------------------------------

def group_episodes(episodes: list[dict[str, Any]], t_group_s: float) -> list[list[dict[str, Any]]]:
    """T23.2 (b): within one area, episodes whose [t_start, t_end] intervals overlap after each is widened by t_group_s
    on both sides form one group, transitively. Episodes are on the area's common timeline (checked by the caller).
    Widened intervals that only touch (end == start) are refused: whether touching counts as overlap is CR-030 item 7."""
    eps = sorted(episodes, key=lambda e: (e["t_start_tl_s"], e["ep_id"]))
    groups: list[list[dict[str, Any]]] = []
    end = None
    for e in eps:
        lo, hi = e["t_start_tl_s"] - t_group_s, e["t_end_tl_s"] + t_group_s
        if groups and lo == end:
            raise _spec("two widened episode intervals touch exactly; whether they overlap is undefined (CR-030 item 7)")
        if groups and lo < end:
            groups[-1].append(e)
            end = max(end, hi)
        else:
            groups.append([e])
            end = hi
    return groups


def report_kind(members: list[dict[str, Any]]) -> str:
    """T23.2 (c)."""
    return "incident_draft" if any(m["g2_label"] == "lbl_ct" for m in members) else "near_miss"


def group_ai_label(members: list[dict[str, Any]]) -> str:
    """T23.2 (d). A group whose members carry different G2 labels shows every distinct label, in CT, NM, UD order
    (AR-63 item 5); no precedence is chosen."""
    labels = [AI_LABEL[g] for g in ("lbl_ct", "lbl_nm", "lbl_ud") if any(m["g2_label"] == g for m in members)]
    return " and ".join(labels)


def _fmt_time(ts: str) -> str:
    return parse_utc(ts).strftime("%Y-%m-%d %H:%M:%S UTC")


def description(ai_label: str, area_name: str, occurred_at: str, minclr: float | None, method: str | None,
                null_reason: str | None, demo: bool) -> str:
    """T23.2 (d), the templated description. <label> is the AI label with its leading "candidate" written once
    (AR-63 item 5); a null clearance reads "not available (<reason>)" (AR-63 item 6)."""
    label = ai_label[len("candidate "):] if ai_label.startswith("candidate ") else ai_label[len("candidate"):]
    when = _fmt_time(occurred_at) + (" (simulated calendar)" if demo else "")
    sep = f"{minclr:.2f} m ({method})" if minclr is not None else f"not available ({null_reason})"
    return (f"The system flagged a candidate{'' if label.startswith(',') else ' '}{label} between a person and a forklift in "
            f"{area_name} at {when}. Minimum measured separation {sep}. Review the clip before deciding.")


def prefill(members: list[dict[str, Any]], est_id: str, area: dict[str, Any], calendar_start: datetime, demo: bool,
            evidence_clip_ids: list[str]) -> dict[str, Any]:
    """T23.2 (d). occurred_at = earliest onset placed on the (simulated) calendar; duration_s = latest end minus
    earliest onset; min_clearance_m = the smallest non-null member clearance (AR-63 item 6)."""
    onset = min(m["t_start_tl_s"] for m in members)
    end = max(m["t_end_tl_s"] for m in members)
    occurred = utc(calendar_start + timedelta(seconds=onset))
    clr = [m for m in members if m.get("minclr_m") is not None]
    best = min(clr, key=lambda m: (m["minclr_m"], m["ep_id"])) if clr else None
    reasons = sorted({m.get("minclr_m_null_reason") or "not_observable" for m in members})
    e_vals = {m.get("E_ep") for m in members}
    evasive = "true" if True in e_vals or 1 in e_vals else ("unknown" if None in e_vals else "false")
    ai_label = group_ai_label(members)
    fields = {
        "kind": "incident" if report_kind(members) == "incident_draft" else "near_miss",
        "est_id": est_id, "area_id": area["area_id"], "camera_ids": sorted({m["camera_id"] for m in members}),
        "occurred_at": occurred, "duration_s": round(end - onset, 6), "objects_involved": ["person", "forklift"],
        "ai_label": ai_label, "min_clearance_m": best["minclr_m"] if best else None,
        "min_clearance_null_reason": None if best else ", ".join(reasons),
        "geometry_method": best.get("geometry_method") if best else None,
        "evasive_action_observed": evasive, "evidence_clip_ids": list(evidence_clip_ids),
    }
    fields["description"] = description(ai_label, area["name"], occurred, fields["min_clearance_m"], fields["geometry_method"],
                                        fields["min_clearance_null_reason"], demo)
    return fields


# --- fold of the report log (T23.15) -------------------------------------------------------------------------------

@dataclass
class Report:
    header: dict[str, Any]
    state: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    label: str | None = None  # the label of the latest decision
    entries: list[dict[str, Any]] = field(default_factory=list)
    prefilled: set[str] = field(default_factory=set)
    recordability: dict[str, Any] | None = None

    @property
    def report_id(self) -> str:
        return self.header["report_id"]

    @property
    def origin(self) -> str:
        return self.header["origin"]

    def actions(self, *names: str) -> list[dict[str, Any]]:
        return [e for e in self.entries if e["action"] in names]

    def deciders(self, level: str) -> set[str]:
        names = AM_DECISIONS if level == "am" else SM_ACTIONS
        return {e["actor_user_id"] for e in self.actions(*names)}

    def entered_state_at(self) -> str:
        last = [e for e in self.entries if e["state_before"] != e["state_after"]]
        return last[-1]["created_utc"] if last else self.header["created_utc"]

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
            r.fields[name] = json.loads(change["after"])
            if e["action"] == "create_ai":
                r.prefilled.add(name)
            else:
                r.prefilled.discard(name)
        if e["action"] in ("am_approve", "am_reject", "sm_uphold", "sm_overturn", "sm_reclassify") and e["label"] is not None:
            r.label = e["label"]
        if e["action"] == "set_recordability":
            r.recordability = json.loads(e["field_changes"]["recordability"]["after"])
    return r


def changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, str]]:
    """field_changes: before and after values as canonical JSON text (AR-63 item 3)."""
    dump = lambda v: json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {k: {"before": dump(before.get(k)), "after": dump(after[k])} for k in sorted(after) if before.get(k) != after[k]}


# --- readings and shares (T23.8) -----------------------------------------------------------------------------------

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
            return f"{self.k}/0 (no decisions; not defined)"
        lo, hi = self.interval
        return f"{self.k}/{self.n} = {self.k / self.n:.3f} (n = {self.n}; Wilson 95 % interval {lo:.3f} to {hi:.3f})"


@dataclass
class Readings:
    """An indicator under the readings CR-030 lists for it. Printed only when every reading gives the same value."""
    values: dict[str, Any]
    item: str

    @property
    def determined(self) -> bool:
        vals = list(self.values.values())
        return all(_same(v, vals[0]) for v in vals)

    @property
    def value(self) -> Any:
        return next(iter(self.values.values())) if self.determined else None

    def text(self, fmt=str) -> str:
        if self.determined:
            return fmt(self.value)
        parts = "; ".join(f"{k}: {fmt(v)}" for k, v in self.values.items())
        return f"not determined: readings differ (CR-030 item {self.item}; {parts})"


def _same(a: Any, b: Any) -> bool:
    if isinstance(a, Share) and isinstance(b, Share):
        return (a.k, a.n) == (b.k, b.n)
    return a == b


def one(value: Any) -> Readings:
    return Readings({"T23": value}, "")


# --- monitoring (I7, I8) ---------------------------------------------------------------------------------------------

def monitored_seconds(segments: list[dict[str, Any]], lo: datetime, hi: datetime, states: tuple[str, ...]) -> float:
    """Seconds of a camera's calendar-placed S1 coverage segments with coverage_state in `states`, inside [lo, hi)."""
    total = 0.0
    for s in segments:
        if s["coverage_state"] not in states:
            continue
        a, b = max(parse_utc(s["start_utc"]), lo), min(parse_utc(s["end_utc"]), hi)
        if b > a:
            total += (b - a).total_seconds()
    return total


# Readings of "monitored ... with assessable footage" (CR-030 item 6): (a) usable segments only; (b) usable and
# usable_degraded; and, for cameras without an S5 artifact of the source configuration, (c) counted / (d) not counted.
MONITOR_READINGS = {"usable, cameras with source output": (("usable",), True),
                    "usable+degraded, cameras with source output": (("usable", "usable_degraded"), True),
                    "usable, all cameras": (("usable",), False),
                    "usable+degraded, all cameras": (("usable", "usable_degraded"), False)}


def area_monitored_s(monitoring: dict[str, dict[str, Any]], camera_ids: list[str], lo: datetime, hi: datetime,
                     states: tuple[str, ...], source_only: bool) -> float:
    return sum(monitored_seconds(monitoring[c]["segments"], lo, hi, states) for c in camera_ids
               if c in monitoring and (monitoring[c]["has_source_output"] or not source_only))


def is_monitored(monitoring: dict[str, dict[str, Any]], camera_ids: list[str], at: datetime, states: tuple[str, ...],
                 source_only: bool) -> bool:
    return area_monitored_s(monitoring, camera_ids, at, at + timedelta(microseconds=1), states, source_only) > 0


# --- indicators (T23.8) and flags (T23.9) ----------------------------------------------------------------------------

def _in_scope(r: Report, est_id: str, area_id: str | None, period: str) -> bool:
    f = r.fields
    return f.get("est_id") == est_id and (area_id is None or f.get("area_id") == area_id) and iso_week(f["occurred_at"]) == period


def indicators(reports: list[Report], est_id: str, area_id: str | None, period: str, areas: dict[str, dict[str, Any]],
               monitoring: dict[str, dict[str, Any]], hours: float | None, params: dict[str, Any], now: datetime) -> dict[str, Any]:
    scope = [r for r in reports if _in_scope(r, est_id, area_id, period)]
    ai = [r for r in scope if r.origin == "ai"]
    human = [r for r in scope if r.origin == "human"]
    out: dict[str, Any] = {}
    out["I1"] = one(len(ai))
    approve = sum(len(r.actions("am_approve")) for r in ai)
    reject = sum(len(r.actions("am_reject")) for r in ai)
    out["I2"] = one(Share(approve, approve + reject))
    out["I3"] = one(Share(reject, approve + reject))

    def sm_share(rs: list[Report], per_report: bool) -> Share:
        if per_report:  # the latest SM decision per report
            last = [r.actions("sm_overturn", "sm_uphold")[-1]["action"] for r in rs if r.actions("sm_overturn", "sm_uphold")]
            return Share(last.count("sm_overturn"), len(last))
        o = sum(len(r.actions("sm_overturn")) for r in rs)
        return Share(o, o + sum(len(r.actions("sm_uphold")) for r in rs))
    out["I4"] = Readings({"AI reports, actions": sm_share(ai, False), "all reports, actions": sm_share(scope, False),
                          "AI reports, latest decision per report": sm_share(ai, True),
                          "all reports, latest decision per report": sm_share(scope, True)}, "2")
    ever = [r for r in ai if any(e["state_after"] == "recorded" for e in r.entries)]
    now_rec = [r for r in ai if r.state == "recorded"]
    recl_actions = sum(len(r.actions("sm_reclassify")) for r in ai)
    recl_reports = sum(1 for r in ai if r.actions("sm_reclassify"))
    out["I5"] = Readings({"reports ever recorded": Share(recl_reports, len(ever)),
                          "actions over reports ever recorded": Share(recl_actions, len(ever)),
                          "reports now recorded": Share(recl_reports, len(now_rec))}, "3")
    limit = timedelta(days=params["t_pending_days"])

    def stale(since_creation: bool) -> dict[str, int]:
        counts = {s: 0 for s in PENDING}
        for r in scope:
            if r.state in PENDING:
                start = r.header["created_utc"] if since_creation else r.entered_state_at()
                if now - parse_utc(start) > limit:
                    counts[r.state] += 1
        return counts
    out["I6"] = Readings({"since creation": stale(True), "since entering the current state": stale(False)}, "4")
    lo, hi = week_bounds(period)
    cams = sorted({c for a in areas.values() if a["est_id"] == est_id and (area_id is None or a["area_id"] == area_id)
                   for c in a["camera_ids"]})

    def rec_nm(rs: list[Report], by_kind: bool) -> int:
        return sum(1 for r in rs if r.state == "recorded" and (r.fields.get("kind") == "near_miss" if by_kind else r.label == "nm"))
    out["I7_ai"] = Readings({"kind near_miss": rec_nm(ai, True), "label nm": rec_nm(ai, False)}, "5")
    out["I7_human"] = Readings({"kind near_miss": rec_nm(human, True), "label nm": rec_nm(human, False)}, "5")
    hours_m = {k: area_monitored_s(monitoring, cams, lo, hi, st, so) / 3600.0 for k, (st, so) in MONITOR_READINGS.items()}
    out["monitored_camera_hours"] = Readings(hours_m, "6")
    rates = {}
    for kk in ("kind near_miss", "label nm"):
        for k, h in hours_m.items():
            rates[f"{kk}; {k}"] = (rec_nm(ai, kk == "kind near_miss") / h) if h > 0 else "no monitored time"
    out["I7_ai_per_camera_hour"] = Readings(rates, "5, 6")
    link = timedelta(seconds=params["t_link_s"])
    all_ai = [r for r in reports if r.origin == "ai"]

    def human_only(states: tuple[str, ...], source_only: bool) -> int:
        n = 0
        for r in human:
            if r.state != "recorded" or r.fields.get("kind") != "near_miss":
                continue
            at = parse_utc(r.fields["occurred_at"])
            area_cams = areas.get(r.fields["area_id"], {}).get("camera_ids", [])
            if not is_monitored(monitoring, area_cams, at, states, source_only):
                continue
            if any(a.fields.get("area_id") == r.fields["area_id"] and abs(parse_utc(a.fields["occurred_at"]) - at) <= link for a in all_ai):
                continue
            n += 1
        return n
    out["I8"] = Readings({k: human_only(st, so) for k, (st, so) in MONITOR_READINGS.items()}, "6")
    out["area_monitoring_share"] = Readings(
        {k: Share(sum(1 for a in areas.values() if a["est_id"] == est_id and area_monitored_s(monitoring, a["camera_ids"], lo, hi, st, so) > 0),
                  sum(1 for a in areas.values() if a["est_id"] == est_id)) for k, (st, so) in MONITOR_READINGS.items()}, "6")

    def recordable(now_recorded_only: bool) -> dict[str, Any]:
        cases = [r for r in scope if r.recordability and r.recordability["recordable"] == "yes"
                 and (r.state == "recorded" or not now_recorded_only)]
        by = {c: sum(1 for r in cases if c in r.recordability["criteria"]) for c in CRITERIA}
        return {"cases": len(cases), "by_criterion": by}
    out["I9"] = Readings({"incidents now recorded": recordable(True), "every incident set yes": recordable(False)}, "8")
    out["hours_worked"] = hours
    out["incidence_rate"] = Readings({k: (v["cases"] * 200_000 / hours) if hours else None for k, v in out["I9"].values.items()}, "8")
    out["period"] = period
    return out


def flags(ind: dict[str, Any], params: dict[str, Any]) -> dict[str, Readings]:
    """T23.9. A flag of an undetermined indicator is itself not determined."""
    def share_flag(r: Readings, n_min: int, theta: float) -> Readings:
        return Readings({k: bool(s.n >= n_min and s.interval and s.interval[0] > theta) for k, s in r.values.items()}, r.item)
    return {
        "F1": share_flag(ind["I3"], params["n_flag_min"], params["theta_rej"]),
        "F2": share_flag(ind["I4"], params["n_flag_min_sm"], params["theta_over"]),
        "F3": Readings({k: sum(v.values()) > 0 for k, v in ind["I6"].values.items()}, ind["I6"].item),
        "F4": Readings({k: v >= params["k_miss"] for k, v in ind["I8"].values.items()}, ind["I8"].item),
    }


# --- wording (T23.12) ------------------------------------------------------------------------------------------------

_TAG = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", re.S | re.I)
_RECORDABLE = re.compile(r"\brecordable\b", re.I)


def visible_text(page: str) -> str:
    """The text of an HTML page with tags, scripts and styles removed (one line per block)."""
    marked = page.replace(RECORDABLE_BADGE, "\x00RECORDABLE_YES\x00")
    text = _TAG.sub("\n", marked)
    return _html.unescape(text)


def lint_workflow(text: str, html_page: bool = True) -> list[str]:
    """W1-W6 (rq1.export.report.WORDING) plus T23.12 on a workflow page or export. Accepted only here: the two
    "recorded near miss (...)" forms, the T23 fixed texts, and "Recordable" printed by `RECORDABLE_BADGE`."""
    body = visible_text(text) if html_page else text
    issues = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        for fixed in FIXED_TEXTS:
            line = line.replace(fixed, " ")
        for phrase in RECORDED_NM.values():
            line = line.replace(phrase, " ")
        if _RECORDABLE.search(line.replace("\x00RECORDABLE_YES\x00", " ")):
            issues.append(f"T23.12 recordable: {line}")
        for rule, pattern in WORDING:
            if pattern.search(line):
                issues.append(f"{rule}: {line}")
    return issues


def check_human_text(*texts: Any) -> None:
    """User-entered text is refused when it would break the wording rules on a workflow page (T23.12; AR-63 item 8)."""
    for t in texts:
        values = t if isinstance(t, list) else [t]
        for v in values:
            if isinstance(v, str) and lint_workflow(v, html_page=False):
                raise _spec('wording rule (T23.12): write what happened without the words "near miss", "collision", '
                            '"recordable", "validated" or a contact claim; issues: ' + "; ".join(lint_workflow(v, html_page=False)))


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
