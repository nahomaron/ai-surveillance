"""The T23 workflow store (contract E-1.2.22; D-48, with T23.16-T23.27, E-1.2.23; D-49), in the same folder and sign-in as
the V-02 validation store.

`WorkflowStore` extends the V-02 `Store`: the T23 tables (wf_*) are JSONL files beside the V-02 files, every row checked
with `validate.validate_row` before it is written; `wf_report_log.jsonl` is append-only and hash-chained like
validation_status_log. candidate_review assessments go into the V-02 `reviewer_assessment.jsonl` (so the T22.2 (b)
exposure rule sees them, T23.11 c) and status entries into the V-02 status log. Nothing is updated or deleted.

System-side helper files that are not contract tables (AR-63 item 4): `wf_episode.jsonl` (what the server needs to
play a member's clip and write its status entry), `wf_monitoring.jsonl` (calendar-placed S1 coverage per camera),
`wf_displays.jsonl` (first display of a report to a person, for review_time_s and the T23.25 c exposure rule).

E-1.2.23: safety-manager decisions on AI reports write candidate_review adjudications (reference_class null, T23.16) and
status entries; every successful action is one hash-chained log entry and a refused action writes nothing (T23.20 f).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from rq1.review import protocol as P
from rq1.review.registry import StoreRegistry
from rq1.review.store import KDF_ITERATIONS, Store, _now, human_id
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.schema.validate import Issue
from rq1.workflow import rules as R
from rq1.workflow.clips import frame_hashes

GENESIS = "0" * 64
SYSTEM = "system"
OWNER = "owner"
AM_QUAL = "workflow area_manager (T23): manager decision record, not a reference reviewer"
SM_QUAL = "workflow safety_manager (T23): manager decision record, not a reference adjudicator"


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


def _forbidden(message: str) -> ContractError:
    return ContractError("ERR-SPEC", "not permitted: " + message)


class HashLog:
    """An append-only JSONL log with a SHA-256 hash chain over the canonical JSON of each entry (as StatusLog)."""

    def __init__(self, path: Path, table: str) -> None:
        self.path, self.table = path, table

    @staticmethod
    def _hash(entry: dict[str, Any]) -> str:
        return hashlib.sha256(canonical_json({k: v for k, v in entry.items() if k != "record_hash"})).hexdigest()

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_bytes().splitlines():
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    out.append({"_unreadable": line.decode("utf-8", "replace")})
        return out

    def append(self, row: dict[str, Any]) -> dict[str, Any]:
        entries = self.entries()
        entry = {"seq": len(entries), **row, "prev_hash": entries[-1].get("record_hash", "") if entries else GENESIS}
        entry["record_hash"] = self._hash(entry)
        Store._check(self.table, entry)
        with open(self.path, "ab") as handle:
            handle.write(canonical_json(entry) + b"\n")
        return entry

    def verify(self) -> list[Issue]:
        previous, last = GENESIS, ""
        for k, e in enumerate(self.entries()):
            if "_unreadable" in e or e.get("seq") != k or e.get("prev_hash") != previous or e.get("record_hash") != self._hash(e):
                return [Issue("T23.15", "ERR-INVARIANT", self.table, "record_hash", f"chain broken at seq {k}")]
            if e.get("created_utc", "") < last:  # T23.18 (b); canonical UTC text sorts as time
                return [Issue("T23.18", "ERR-INVARIANT", self.table, "created_utc", f"created_utc decreases at seq {k} (T23.18 b)")]
            previous, last = e["record_hash"], e.get("created_utc", "")
        return []

    def head(self) -> tuple[int, str]:
        entries = self.entries()
        return len(entries), (entries[-1].get("record_hash", "?") if entries else GENESIS)


class WorkflowStore(Store):
    def __init__(self, root: str | Path, clock: Callable[[], datetime] = _now, kdf_iterations: int = KDF_ITERATIONS,
                 registry: StoreRegistry | None = None) -> None:
        super().__init__(root, clock, kdf_iterations, registry=registry)
        self.report_log = HashLog(self.root / "wf_report_log.jsonl", "wf_report_log")

    # --- rows -------------------------------------------------------------------------------------------------------

    def _row(self, table: str, row: dict[str, Any], file: str | None = None) -> dict[str, Any]:
        self._check(table, row)
        self._append(file or f"{table}.jsonl", row)
        return row

    def establishments(self) -> dict[str, dict[str, Any]]:
        """In registration order (T23.27 e: no page sorts establishments)."""
        return {r["est_id"]: r for r in self._read("wf_establishment.jsonl")}

    def areas(self) -> dict[str, dict[str, Any]]:
        return {r["area_id"]: r for r in self._read("wf_area.jsonl")}

    def users(self) -> dict[str, dict[str, Any]]:
        return {r["user_id"]: r for r in self._read("wf_user.jsonl")}

    def headers(self) -> dict[str, dict[str, Any]]:
        return {r["report_id"]: r for r in self._read("wf_report.jsonl")}

    def episodes(self) -> dict[str, dict[str, Any]]:
        return {r["ep_id"]: r for r in self._read("wf_episode.jsonl")}

    def clips(self) -> dict[str, dict[str, Any]]:
        return {r["ecl_id"]: r for r in self._read("evidence_clip.jsonl")}

    def monitoring(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for r in self._read("wf_monitoring.jsonl"):
            out[r["camera_id"]] = r
        return out

    # --- setup (Owner) ----------------------------------------------------------------------------------------------

    def config(self) -> dict[str, Any]:
        rows = self._read("wf_config.jsonl")
        return rows[-1] if rows else {**R.check_params({}), "store_version": 0}

    def set_config(self, params: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            p = R.check_params({k: v for k, v in params.items() if k in R.PARAMS})
            row = {"wfc_id": human_id("wfc"), "store_version": self.config()["store_version"] + 1, **p,
                   "created_utc": R.utc(self.clock())}
            return self._row("wf_config", row)

    def add_establishment(self, name: str, demo: bool, est_id: str | None = None) -> dict[str, Any]:
        with self.lock:
            if not name.strip():
                raise _spec("an establishment has a name")
            if demo is not True:
                raise _spec("only demo (simulated) establishments exist in the present RQ1 work; demo = false is refused (T23.27 b)")
            return self._row("wf_establishment", {"est_id": est_id or human_id("est"), "name": name.strip(), "demo": bool(demo)})

    def add_area(self, est_id: str, name: str, camera_ids: list[str], area_id: str | None = None) -> dict[str, Any]:
        with self.lock:
            if est_id not in self.establishments():
                raise _spec("unknown establishment")
            taken = {c for a in self.areas().values() for c in a["camera_ids"]}
            if set(camera_ids) & taken or len(set(camera_ids)) != len(camera_ids):
                raise _spec("every camera belongs to at most one area (T23.1 a)")
            return self._row("wf_area", {"area_id": area_id or human_id("area"), "est_id": est_id, "name": name.strip(),
                                         "camera_ids": sorted(camera_ids)})

    def add_user(self, pseudonym: str, roles: list[str], est_id: str | None, area_ids: list[str], passphrase: str,
                 user_id: str | None = None) -> dict[str, Any]:
        with self.lock:
            pseudonym = pseudonym.strip()
            if not pseudonym or any(u["pseudonym"] == pseudonym for u in self.users().values()):
                raise _spec("a new, non-empty pseudonym is required (one person = one pseudonym, T23.1 b)")
            if not roles or any(r not in R.ROLES for r in roles):
                raise _spec(f"roles are from {', '.join(R.ROLES)}")
            areas = self.areas()
            if "area_manager" in roles and not area_ids:
                raise _spec("an area_manager has one or more areas (T23.1 b)")
            if any(a not in areas for a in area_ids):
                raise _spec("unknown area")
            if "safety_manager" in roles and est_id is None:
                raise _spec("a safety_manager has one establishment (T23.1 b)")
            if est_id is not None and est_id not in self.establishments():
                raise _spec("unknown establishment")
            row = {"user_id": user_id or human_id("usr"), "pseudonym": pseudonym, "roles": sorted(set(roles), key=R.ROLES.index),
                   "est_id": est_id, "est_id_null_reason": None if est_id else "not_applicable", "area_ids": sorted(area_ids)}
            self._check("wf_user", row)
            data = self._profiles()
            data.setdefault("wf_users", {})[row["user_id"]] = self._hash(passphrase)
            self._append("wf_user.jsonl", row)
            self._save_profiles(data)
            return row

    def add_hours(self, est_id: str, period: str, hours_worked: Any, entered_by: str) -> dict[str, Any]:
        with self.lock:
            R.week_bounds(period)
            if est_id not in self.establishments():
                raise _spec("unknown establishment")
            try:
                hours = float(hours_worked)
            except (TypeError, ValueError):
                raise _spec("hours worked is a number") from None
            return self._row("wf_hours", {"est_id": est_id, "period": period, "hours_worked": hours, "entered_by": entered_by,
                                          "created_utc": R.utc(self.clock())})

    def hours(self, est_id: str, period: str, as_of: str | None = None) -> float | None:
        """Human-entered hours worked; the latest entry for the period entered by as_of (AR-64)."""
        rows = [r for r in self._read("wf_hours.jsonl") if r["est_id"] == est_id and r["period"] == period
                and (as_of is None or r["created_utc"] <= as_of)]
        return rows[-1]["hours_worked"] if rows else None

    def set_monitoring(self, camera_id: str, segments: list[dict[str, Any]], has_source_output: bool, source: str,
                       processed: list[dict[str, Any]] | None = None) -> None:
        """Calendar-placed S1 coverage of one camera (start_utc, end_utc, coverage_state per segment) and its processed
        coverage: the S5 artifacts of the source configuration with the window each covers (T23.23 a; AR-64)."""
        if processed is None:
            processed = ([{"start_utc": segments[0]["start_utc"], "end_utc": segments[-1]["end_utc"], "s5_artifact_id": None}]
                         if has_source_output and segments else [])
        R.check_processed(camera_id, processed)  # before anything is written
        self._append("wf_monitoring.jsonl", {"camera_id": camera_id, "segments": segments, "has_source_output": bool(processed),
                                             "source": source, "processed": processed})

    # --- sign-in (V-02 plus wf users) -----------------------------------------------------------------------------------

    def profiles(self) -> list[dict[str, str]]:
        secrets_ = self._profiles()
        out = [p for p in super().profiles() if p["profile_id"] == OWNER or p["profile_id"] in secrets_["annotators"]]
        out += [{"profile_id": u["user_id"], "pseudonym": u["pseudonym"], "role": "workflow: " + ", ".join(u["roles"])}
                for u in sorted(self.users().values(), key=lambda u: u["pseudonym"])]
        return out

    def login(self, profile_id: str, passphrase: str) -> dict[str, Any] | None:
        if profile_id == OWNER or profile_id in self.annotators():
            return super().login(profile_id, passphrase)
        secret = self._profiles().get("wf_users", {}).get(profile_id)
        if not secret or not self._matches(secret, passphrase or ""):
            return None
        u = self.users()[profile_id]
        return {"profile_id": profile_id, "pseudonym": u["pseudonym"], "role": "workflow: " + ", ".join(u["roles"]),
                "roles": list(u["roles"])}

    def actor(self, who: dict[str, Any]) -> dict[str, Any]:
        """The workflow identity of a signed-in profile: wf users with their roles; the V-02 Owner as role owner."""
        if who["profile_id"] == OWNER:
            return {"user_id": OWNER, "pseudonym": who["pseudonym"], "roles": ["owner"], "est_id": None, "area_ids": []}
        u = self.users().get(who["profile_id"])
        if u is None:
            raise _forbidden("workflow pages are for workflow users and the Owner")
        return u

    def _manager_annotator(self, user: dict[str, Any], role: str) -> str:
        """The annotator row (E-1.2.1 5.8) behind a manager's candidate_review records: one row per person and role,
        identified by the pseudonym (AR-61 item 4); reused if the person already has one (AR-63 item 10)."""
        for a in self.annotators().values():
            if a["pseudonym"] == user["pseudonym"] and a["role"] == role:
                return a["anr_id"]
        row = {"anr_id": human_id("anr"), "role": role, "qualification_ref": AM_QUAL if role == "c_layer_reviewer" else SM_QUAL,
               "independence_attestation": False, "pseudonym": user["pseudonym"]}
        self._check("annotator", row)
        self._append("annotator.jsonl", row)
        return row["anr_id"]

    # --- reports -------------------------------------------------------------------------------------------------------

    def reports(self, as_of: str | None = None) -> list[R.Report]:
        """The fold of the report log, truncated at as_of (entries with created_utc <= as_of, T23.18 b) when given. A report
        whose creation entry is after as_of does not exist yet."""
        by: dict[str, list[dict[str, Any]]] = {}
        for e in self.report_log.entries():
            if "report_id" in e and (as_of is None or e["created_utc"] <= as_of):
                by.setdefault(e["report_id"], []).append(e)
        return [R.fold(h, by[rid]) for rid, h in self.headers().items() if rid in by]

    def calendar_start(self) -> str | None:
        m = self.demo_manifest()
        return m["calendar_start_utc"] if m else None

    def ep_times(self) -> dict[str, tuple[datetime, datetime, str]]:
        """Member episode -> (start, end, camera) on the calendar (T23.23 c)."""
        out = {}
        fallback = self.calendar_start()
        for ep_id, e in self.episodes().items():
            cal = e.get("calendar_start_utc") or fallback
            if cal:
                c = R.parse_utc(cal)
                out[ep_id] = (c + timedelta(seconds=e["t_start_tl_s"]), c + timedelta(seconds=e["t_end_tl_s"]), e["camera_id"])
        return out

    def view(self, est_id: str, area_id: str | None, period: str, as_of: str | None = None,
             params: dict[str, Any] | None = None) -> dict[str, Any]:
        """T23.18 (b): every indicator, flag and regulator-view figure from the report log truncated at as_of. The view
        prints as_of, the truncated log length and its head hash."""
        as_of = as_of or R.utc(self.clock())
        R.parse_utc(as_of)
        entries = [e for e in self.report_log.entries() if e.get("created_utc", "") <= as_of]
        cfg = {**self.config(), **(params or {})}
        ind = R.indicators(self.reports(as_of), est_id, area_id, period, self.areas(), self.monitoring(),
                           self.hours(est_id, period, as_of), cfg, R.parse_utc(as_of), self.ep_times())
        return {"indicators": ind, "flags": R.flags(ind, cfg), "as_of": as_of, "log_length": len(entries),
                "head_hash": entries[-1]["record_hash"] if entries else GENESIS, "params": cfg}

    def source_quality(self) -> dict[str, Any] | None:
        """T23.26: the alert source's recorded figures, from the demo manifest (None if not recorded)."""
        m = self.demo_manifest()
        return (m or {}).get("source_quality")

    def combined(self, report: R.Report) -> dict[str, Any]:
        """T23.24: the view-time combined clearance of an AI report's members (never stored)."""
        eps = self.episodes()
        return R.combined([eps[m] for m in report.members if m in eps])

    def report(self, report_id: str) -> R.Report:
        h = self.headers().get(report_id)
        if h is None:
            raise _spec("no such report")
        return R.fold(h, [e for e in self.report_log.entries() if e.get("report_id") == report_id])

    def _log(self, report: R.Report | None, report_id: str, action: str, actor: str, state_after: str,
             field_changes: dict[str, Any], label: str | None = None, reason: str | None = None, note: str | None = None,
             linked: list[str] | None = None) -> dict[str, Any]:
        row = {"entry_id": human_id("wfe"), "report_id": report_id, "action": action, "actor_user_id": actor,
               "state_before": report.state if report else None,
               "state_before_null_reason": None if report else "not_applicable", "state_after": state_after,
               "field_changes": field_changes, "label": label, "label_null_reason": None if label else "not_applicable",
               "reason": reason, "reason_null_reason": None if reason else "not_applicable",
               "note": note, "note_null_reason": None if note else "not_applicable",
               "linked_record_ids": list(linked or []), "created_utc": R.utc(self.clock())}
        return self.report_log.append(row)

    def register_episode(self, desc: dict[str, Any], calendar_start: datetime | None = None) -> None:
        if desc["ep_id"] not in self.episodes():
            row = dict(desc)
            if calendar_start is not None:
                row["calendar_start_utc"] = R.utc(calendar_start)
            self._append("wf_episode.jsonl", row)

    def _retention_policy(self) -> str:
        rows = self._read("retention_policy.jsonl")
        if rows:
            return rows[0]["rtp_id"]
        row = {"rtp_id": human_id("rtp"), "label": "workflow store (research prototype)", "applies_to": "evidence_clip",
               "retain_days": None, "retain_days_null_reason": "not_applicable",
               "deletion_method": "the store folder is deleted as a whole; rows are never edited",
               "legal_basis_ref": None, "legal_basis_ref_null_reason": "not_applicable"}
        return self._row("retention_policy", row)["rtp_id"]

    def _evidence_clip(self, ep: dict[str, Any]) -> str:
        """One evidence_clip row per member (T23.2 d); window = the T22.4 clip window of the episode (AR-63 item 7)."""
        start = max(0, int(round(ep["clip_start_s"] * ep["fps"])))
        end = int(round(ep["clip_end_s"] * ep["fps"]))
        row = {"ecl_id": human_id("ecl"), "recording_id": ep["recording_id"], "start_frame": start, "end_frame_excl": end,
               "purpose": "review", "decoded_frame_sha256": frame_hashes(ep["video"], start, end),
               "encoding": "source recording, played between the window bounds (no re-encode)", "redaction_state": "none",
               "access_class": "publishable_synthetic_only" if ep.get("synthetic", True) else "restricted_research",
               "retention_policy_id": self._retention_policy(), "expires_utc": None, "expires_utc_null_reason": "not_applicable"}
        return self._row("evidence_clip", row)["ecl_id"]

    def intake(self, area_id: str, episodes: list[dict[str, Any]], calendar_start: datetime) -> list[str]:
        """T23.2: AI alert intake for one area. Episodes are system-side descriptions (see `register_episode`)."""
        with self.lock:
            area = self.areas().get(area_id)
            if area is None:
                raise _spec("unknown area")
            est = self.establishments()[area["est_id"]]
            cfg = self.config()
            done = {m for h in self.headers().values() for m in (h["member_episode_ids"] or [])}
            eps = [e for e in episodes if e["g2_label"] in R.G2_SOURCE and e["camera_id"] in area["camera_ids"] and e["ep_id"] not in done]
            created = []
            for group, basis in R.group_episodes(eps, cfg["t_group_s"]):  # T23.21 (b), (c)
                for m in group:
                    self.register_episode(m, calendar_start)
                clips = [self._evidence_clip(m) for m in sorted(group, key=lambda m: m["ep_id"])]
                fields = R.prefill(group, est["est_id"], area, calendar_start, est["demo"], clips, basis)
                created.append(self._create_ai(group, est["est_id"], area_id, fields))
            return created

    def _create_ai(self, group: list[dict[str, Any]], est_id: str, area_id: str, fields: dict[str, Any]) -> str:
        header = {"report_id": human_id("rpt"), "kind_initial": R.report_kind(group), "origin": "ai",
                  "est_id": est_id, "area_id": area_id, "member_episode_ids": sorted(m["ep_id"] for m in group),
                  "member_episode_ids_null_reason": None, "created_utc": R.utc(self.clock())}
        self._row("wf_report", header)
        self._log(None, header["report_id"], "create_ai", SYSTEM, "pending_am", R.changes({}, fields))
        return header["report_id"]

    def create_human(self, who: dict[str, Any], form: dict[str, Any]) -> str:
        """T23.6: any signed-in workflow user (or the Owner) files a report for an area."""
        with self.lock:
            user = self.actor(who)
            kind = form.get("kind")
            if kind not in ("near_miss", "incident"):
                raise _spec("kind is near_miss or incident (T23.3)")
            area = self.areas().get(form.get("area_id", ""))
            if area is None:
                raise _spec("choose an area")
            fields = self._clean_fields({k: v for k, v in form.items() if k in R.EDITABLE and k not in ("est_id", "area_id")}, kind)
            if not fields.get("description"):
                raise _spec("a description is required (T23.6)")
            if not fields.get("occurred_at"):
                raise _spec("occurred_at is required (T23.6)")
            fields.update({"kind": kind, "est_id": area["est_id"], "area_id": area["area_id"]})
            header = {"report_id": human_id("rpt"), "kind_initial": kind, "origin": "human", "est_id": area["est_id"],
                      "area_id": area["area_id"], "member_episode_ids": None, "member_episode_ids_null_reason": "not_applicable",
                      "created_utc": R.utc(self.clock())}
            self._row("wf_report", header)
            self._log(None, header["report_id"], "create_human", user["user_id"], "pending_am", R.changes({}, fields))
            return header["report_id"]

    def _clean_fields(self, raw: dict[str, Any], kind: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in raw.items():
            if k == "occurred_at":
                out[k] = _occurred(v)
            elif k == "contributing_factors":
                vals = v if isinstance(v, list) else [x for x in str(v).split("|") if x]
                if any(x not in R.CONTRIBUTING for x in vals):
                    raise _spec(f"contributing factors are from: {', '.join(R.CONTRIBUTING)}")
                out[k] = vals
            elif k == "people_involved":
                out[k] = v if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]
            elif k in ("treated_in_emergency_room", "hospitalized_overnight"):
                if v not in ("", "yes", "no"):
                    raise _spec(f"{k} is yes or no")
                out[k] = v
            elif k == "duration_s":
                out[k] = None if v in ("", None) else float(v)
            elif k in ("camera_ids", "evidence_clip_ids", "objects_involved"):
                out[k] = v if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]
            else:
                out[k] = v.strip() if isinstance(v, str) else v
        if kind == "near_miss":
            for f, _, _ in R.INCIDENT_FIELDS:
                out.pop(f, None)
        return out  # T23.22: stored verbatim; a report is never refused for its wording

    def _observability(self, report: R.Report, form: dict[str, Any]) -> dict[str, Any]:
        """T23.23 (c): camera_observability with the camera IDs checked, set by the area manager on a human-started report."""
        obs = form.get("camera_observability")
        cams = form.get("observability_cameras") or []
        cams = cams if isinstance(cams, list) else [c for c in str(cams).split(",") if c]
        if obs in (None, "") and not cams:
            return {}
        if report.origin != "human":
            raise _spec("camera_observability is a field of human-started reports (T23.23 c)")
        if obs not in R.OBSERVABILITY:
            raise _spec(f"camera_observability is one of {', '.join(R.OBSERVABILITY)} (T23.23 c)")
        area = self.areas()[report.fields["area_id"]]
        if obs != "undetermined" and not cams:
            raise _spec("camera_observability needs the camera IDs checked (T23.23 c)")
        if any(c not in area["camera_ids"] for c in cams):
            raise _spec("the cameras checked are cameras of the report's area")
        return {"camera_observability": obs, "observability_cameras": sorted(set(cams))}

    # --- actions (T23.4) ---------------------------------------------------------------------------------------------

    def permitted(self, user: dict[str, Any], report: R.Report, action: str) -> str | None:
        """None if the action is permitted for this user on this report now; otherwise the reason (T23.4, T23.1 b)."""
        who, froms, _ = R.TRANSITIONS[action]
        if froms is not None and report.state not in froms and action != "edit_fields":
            return f"{action} is taken from {', '.join(froms) or 'nothing'}; the report is {report.state}"
        area_id, est_id = report.fields.get("area_id"), report.fields.get("est_id")
        is_am = "area_manager" in user["roles"] and area_id in user["area_ids"]
        is_sm = "safety_manager" in user["roles"] and user.get("est_id") == est_id
        if action in R.AM_DECISIONS:
            if not is_am:
                return "only an area manager of the report's area"
            if action == "am_split" and (report.origin != "ai" or len(report.members) < 2):
                return "am_split is for an AI report with at least two members (T23.20 e)"
            return None
        if action in R.SM_ACTIONS:
            if not is_sm:
                return "only the safety manager of the report's establishment"
            if user["user_id"] in report.deciders("am"):
                return "this person decided the report as area manager and cannot act on it as its safety manager (T23.1 b)"
            if action == "set_recordability" and report.fields.get("kind") != "incident":
                return "recordability is set on a recorded incident only (T23.7 b)"
            if action == "sm_confirm_duplicate" and not report.reopened_duplicate():
                return "sm_confirm_duplicate follows sm_reopen of a closed_duplicate (T23.20 c)"
            if action == "withdraw_recordability" and report.determination in ("not_set", "withdrawn"):
                return f"there is no recordability determination to withdraw (it is {report.determination}; T23.19 c)"
            return None
        if action == "edit_fields":
            if report.state == "pending_am":
                return None if is_am else "in pending_am, fields are edited by an area manager of the area"
            if report.state in ("pending_sm", "recorded"):
                if not is_sm:
                    return "in pending_sm and recorded, fields are edited by the safety manager"
                if user["user_id"] in report.deciders("am"):
                    return "this person decided the report as area manager (T23.1 b)"
                return None
            return f"fields are not edited in {report.state}"
        return f"{action} is not a user action"

    def note_display(self, report_id: str, user_id: str) -> None:
        with self.lock:
            if not any(d["report_id"] == report_id and d["user_id"] == user_id for d in self._read("wf_displays.jsonl")):
                self._append("wf_displays.jsonl", {"report_id": report_id, "user_id": user_id, "first_display_utc": R.utc(self.clock())})

    def _review_time(self, report_id: str, user_id: str, now: datetime) -> float | None:
        for d in self._read("wf_displays.jsonl"):
            if d["report_id"] == report_id and d["user_id"] == user_id:
                return (now - R.parse_utc(d["first_display_utc"])).total_seconds()
        return None

    def act(self, who: dict[str, Any], report_id: str, action: str, form: dict[str, Any]) -> dict[str, Any]:
        """One T23.4 action. Every input is checked before the first write, so a refused action writes nothing to any file
        and leaves the state unchanged (T23.20 f)."""
        with self.lock:
            user = self.actor(who)
            report = self.report(report_id)
            if action not in R.TRANSITIONS or action in ("create_ai", "create_human"):
                raise _spec(f"unknown action {action!r}")
            why = self.permitted(user, report, action)
            if why:
                raise _forbidden(why)
            to = R.TRANSITIONS[action][2] or report.state
            note = (form.get("note") or "").strip() or None
            ai = report.origin == "ai"
            multi = ai and len(report.members) >= 2
            if action in ("am_approve", "sm_overturn"):
                label = form.get("label")
                if label not in R.APPROVE_LABELS:
                    raise _spec(f"{action} requires label nm or ct (T23.4)")
                if action == "sm_overturn" and not note:
                    raise _spec("sm_overturn requires a note (T23.4)")
                ch_after: dict[str, Any] = {"kind": R.KIND_OF_LABEL[label]}  # T23.18 (e)
                dup = action == "sm_overturn" and report.reopened_duplicate()
                gr = form.get("group_resolution") or None
                if multi or dup:  # T23.21 (d), T23.20 (d)
                    if gr not in R.GROUP_RESOLUTIONS:
                        raise _spec(f"{action} on this report requires group_resolution one_interaction or cannot_tell; if the "
                                    "members show several interactions, the area manager uses am_split first (T23.21 d)")
                    ch_after["group_resolution"] = gr
                elif gr:
                    raise _spec("group_resolution is given for an AI report with two or more members (T23.21 d)")
                if dup:
                    ch_after["duplicate_of"] = None  # T23.20 (d)
                if action == "am_approve":
                    ch_after.update(self._observability(report, form))
                    plan = self._am_plan(user, report, form) if ai else None
                    ch = R.changes(report.fields, ch_after)
                    linked = self._am_records(user, report, label, plan, "approve") if ai else []
                else:
                    ch = R.changes(report.fields, ch_after)
                    linked = self._sm_records(user, report, label) if ai else []
                return self._log(report, report_id, action, user["user_id"], to, ch, label=label, note=note, linked=linked)
            if action == "am_reject":
                reason = form.get("reason")
                if reason not in R.REJECT_REASONS:
                    raise _spec("am_reject requires a reason from not_hazardous, no_person_or_no_forklift, cannot_tell_from_video, other (T23.5 b)")
                label = R.REJECT_REASONS[reason]
                ch = R.changes(report.fields, self._observability(report, form))
                plan = self._am_plan(user, report, form) if ai else None
                linked = self._am_records(user, report, label, plan, "reject") if ai else []
                return self._log(report, report_id, action, user["user_id"], to, ch, label=label, reason=reason, note=note, linked=linked)
            if action == "am_duplicate":
                dup = form.get("duplicate_of", "")
                target = self._reports_by_id().get(dup)
                if dup == report_id or target is None:
                    raise _spec("am_duplicate requires duplicate_of, a different report (T23.20 b)")
                if target.fields.get("est_id") != report.fields.get("est_id"):
                    raise _spec("duplicate_of is a report of the same establishment (T23.20 b)")
                if target.state in ("closed_duplicate", "closed_split"):
                    raise _spec(f"duplicate_of cannot be a report in state {target.state}: no chains or cycles (T23.20 b)")
                return self._log(report, report_id, action, user["user_id"], to, R.changes(report.fields, {"duplicate_of": dup}),
                                 reason=f"duplicate_of {dup}", note=note)
            if action in ("sm_uphold", "sm_reclassify", "sm_reopen", "sm_note", "sm_confirm_duplicate", "withdraw_recordability") and not note:
                raise _spec(f"{action} requires a note (T23.4)")
            if action == "sm_uphold":
                am = report.actions(*R.AM_DECISIONS)
                if not am or am[-1]["action"] != "am_reject":
                    raise _spec("sm_uphold requires that the latest area-manager decision is am_reject; rule T23.20 (a)")
                label = am[-1]["label"]
                linked = self._sm_records(user, report, label) if ai else []
                return self._log(report, report_id, action, user["user_id"], to, {}, label=label if ai else None, note=note, linked=linked)
            if action == "sm_reclassify":
                if report.determination in ("yes", "no"):
                    raise _spec(f"the recordability determination is {report.determination}: withdraw it or edit the kind or label "
                                "before sm_reclassify (T23.19 (e))")
                reason = (form.get("reason") or "").strip()
                if not reason:
                    raise _spec("sm_reclassify requires a reason (T23.4)")
                label = form.get("label") or "not_hazardous"
                if label not in R.RECLASSIFY_LABELS:
                    raise _spec("sm_reclassify writes not_hazardous unless the safety manager picks ud (T23.5 c)")
                linked = self._sm_records(user, report, label) if ai else []
                return self._log(report, report_id, action, user["user_id"], to, {}, label=label, reason=reason, note=note, linked=linked)
            if action in ("sm_reopen", "sm_note", "sm_confirm_duplicate"):
                return self._log(report, report_id, action, user["user_id"], to, {}, note=note)
            if action == "withdraw_recordability":
                reason = form.get("reason")
                if reason not in R.WITHDRAW_REASONS:
                    raise _spec(f"withdraw_recordability requires a reason from {', '.join(R.WITHDRAW_REASONS)} (T23.19 c)")
                return self._log(report, report_id, action, user["user_id"], to, {}, reason=reason, note=note)
            if action == "am_split":
                return self._split(user, report, form, note)
            if action == "edit_fields":
                raw = {k: v for k, v in form.items() if k in R.EDITABLE}
                kind = raw.get("kind", report.fields.get("kind"))
                if kind != report.fields.get("kind"):
                    if report.state not in R.PENDING or kind not in ("near_miss", "incident"):
                        raise _spec("a report changes between near_miss and incident only while pending (T23.3 c)")
                new = self._clean_fields(raw, kind)
                if "area_id" in new:
                    area = self.areas().get(new["area_id"])
                    if area is None:
                        raise _spec("unknown area")
                    new["est_id"] = area["est_id"]
                if any(k in form for k in R.OBS_FIELDS):
                    if report.state != "pending_am":
                        raise _spec("camera_observability is set by the area manager (T23.23 c)")
                    new.update(self._observability(report, form))
                ch = R.changes(report.fields, new)
                if not ch:
                    raise _spec("edit_fields requires changed fields (T23.4)")
                return self._log(report, report_id, action, user["user_id"], to, ch, note=note)
            if action == "set_recordability":
                rec = self._recordability(user, form)
                dump = lambda v: json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                ch = {"recordability": {"before": dump(report.recordability), "after": dump(rec)}}  # always one entry (T23.19 b)
                return self._log(report, report_id, action, user["user_id"], to, ch, note=rec["note"])
            raise _spec(f"unknown action {action!r}")

    def _reports_by_id(self) -> dict[str, R.Report]:
        return {r.report_id: r for r in self.reports()}

    def duplicates_of(self, report_id: str) -> list[str]:
        """T23.20 (b): the reports whose current duplicate_of is this report."""
        return sorted(r.report_id for r in self.reports() if r.fields.get("duplicate_of") == report_id)

    def _split(self, user: dict[str, Any], report: R.Report, form: dict[str, Any], note: str | None) -> dict[str, Any]:
        """T23.20 (e): a partition of the members into two or more non-empty parts; one new pending_am AI report per part
        (a create_ai entry carrying split_from); no assessment, adjudication or status entry for the original."""
        if not note:
            raise _spec("am_split requires a note (T23.20 e)")
        parts = form.get("parts")
        if parts is None:
            by: dict[str, list[str]] = {}
            for m in report.members:
                k = str(form.get(f"part_{m}", "")).strip()
                if not k:
                    raise _spec("am_split assigns every member episode to a part (T23.20 e)")
                by.setdefault(k, []).append(m)
            parts = [by[k] for k in sorted(by)]
        flat = [m for part in parts for m in part]
        if sorted(flat) != sorted(report.members) or len(set(flat)) != len(flat) or any(not part for part in parts):
            raise _spec("am_split requires a partition of the member episodes (T23.20 e)")
        if len(parts) < 2:
            raise _spec("am_split requires two or more non-empty parts (T23.20 e)")
        eps, area = self.episodes(), self.areas()[report.fields["area_id"]]
        est = self.establishments()[report.fields["est_id"]]
        clip_of = dict(zip(sorted(report.members), report.fields.get("evidence_clip_ids", [])))
        cal = eps[report.members[0]].get("calendar_start_utc") or self.calendar_start()
        if cal is None:
            raise _spec("the members' calendar start is not recorded; the parts' occurred_at cannot be placed")
        prepared = []
        for part in parts:
            group = sorted((eps[m] for m in part), key=lambda e: e["ep_id"])
            fields = R.prefill(group, est["est_id"], area, R.parse_utc(cal), est["demo"], [clip_of.get(m["ep_id"]) for m in group if m["ep_id"] in clip_of],
                               report.fields.get("grouping_basis") or R.PER_CAMERA)
            fields["split_from"] = report.report_id
            prepared.append((group, fields))
        entry = self._log(report, report.report_id, "am_split", user["user_id"], "closed_split", {},
                          reason=f"split into {len(parts)} parts", note=note)
        for group, fields in prepared:
            self._create_ai(group, est["est_id"], area["area_id"], fields)
        return entry

    def _recordability(self, user: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
        """T23.7 (b): recordable in {yes, no, undetermined}; when yes, one or more criteria, with days counts where they apply."""
        rec = form.get("recordable")
        if rec not in R.RECORDABLE:
            raise _spec("recordability is yes, no or undetermined (T23.7 b)")
        crit = form.get("criteria") or []
        crit = crit if isinstance(crit, list) else [c for c in str(crit).split("|") if c]
        if any(c not in R.CRITERIA for c in crit):
            raise _spec("criteria are from the 29 CFR 1904.7 general recording criteria (T23.7 b)")
        if rec == "yes" and not crit:
            raise _spec("when yes, one or more criteria (T23.7 b)")
        if rec != "yes" and crit:
            raise _spec("criteria are given only when yes (T23.7 b)")
        days = {}
        for c in R.DAYS_CRITERIA:
            if c in crit:
                v = form.get(f"days_{c}", "")
                if not str(v).isdigit():
                    raise _spec(f"{c} needs a days count (T23.7 b)")
                days[c] = int(v)
        note = (form.get("note") or "").strip()
        if not note:
            raise _spec("set_recordability requires a note (T23.7 b)")
        return {"recordable": rec, "criteria": sorted(crit, key=R.CRITERIA.index), "days": days, "decided_by": user["user_id"], "note": note}

    def _am_plan(self, user: dict[str, Any], report: R.Report, form: dict[str, Any]) -> dict[str, Any]:
        """The checked inputs of an area-manager decision on an AI report (checked before anything is written)."""
        try:
            confidence = float(form.get("confidence") or 3.0)
        except ValueError:
            raise _spec("confidence is 1.0, 2.0 or 3.0") from None
        return {"confidence": P.check_confidence(confidence), "rationale": P.check_rationale(form.get("rationale"))}

    def _am_records(self, user: dict[str, Any], report: R.Report, label: str, plan: dict[str, Any], kind: str) -> list[str]:
        """T23.5 (a), (b), (d): one candidate_review assessment and one status entry per member episode."""
        anr = self._manager_annotator(user, "c_layer_reviewer")
        eps = self.episodes()
        now = self.clock()
        rt = self._review_time(report.report_id, user["user_id"], now)
        linked = []
        for ep_id in report.members:
            ep = eps[ep_id]
            row = {"rva_id": human_id("rva"), "annotator_id": anr, "namespace": "candidate_review", "target_type": "system_episode",
                   "target_id": ep_id, "label": label, "confidence": plan["confidence"], "rationale": plan["rationale"], "blind": False,
                   "shown_system_output": True, "review_time_s": rt, "review_time_s_null_reason": None if rt is not None else "not_observable",
                   "submitted_utc": R.utc(now)}
            self._check("reviewer_assessment", row)
            self._append("reviewer_assessment.jsonl", {"batch_id": None, "report_id": report.report_id, "recording_id": ep["recording_id"], "row": row})
            status = P.status_for(label, P.map_g2(ep["g2_label"])) if kind == "approve" else "disputed"
            entry = self.status_log.append(target_type="system_episode", target_id=ep_id, config_id=ep["config_id"], status=status,
                                           layer="C", namespace="candidate_review", basis_ids=[row["rva_id"]], actor_id=anr,
                                           created_utc=now)
            linked += [row["rva_id"], entry["status_id"]]
        return linked

    def _sm_records(self, user: dict[str, Any], report: R.Report, final_label: str) -> list[str]:
        """T23.5 (c), (d) with T23.16: one candidate_review adjudication per member (tier2, method adjudicator, reference_class
        null with reason not_applicable; on pages a "safety-manager decision"), listing the area manager's latest assessment of
        that member, and one status entry per member with the T22.8 (b) mapping of the final label."""
        anr = self._manager_annotator(user, "adjudicator")
        eps = self.episodes()
        latest: dict[str, str] = {}
        for e in self.assessments():
            if e.get("report_id") == report.report_id and e["row"]["namespace"] == "candidate_review":
                latest[e["row"]["target_id"]] = e["row"]["rva_id"]
        now = self.clock()
        linked = []
        for ep_id in report.members:
            ep = eps[ep_id]
            target = {"target_type": "system_episode", "target_id": ep_id, "recording_id": ep["recording_id"]}
            row = self.add_candidate_review_adjudication(target, final_label, [latest[ep_id]] if ep_id in latest else [], anr,
                                                         report.report_id)
            entry = self.status_log.append(target_type="system_episode", target_id=ep_id, config_id=ep["config_id"],
                                           status=P.status_for(final_label, P.map_g2(ep["g2_label"])), layer="C",
                                           namespace="candidate_review", basis_ids=[row["adj_id"]], actor_id=anr, created_utc=now)
            linked += [row["adj_id"], entry["status_id"]]
        return linked

    # --- verification, snapshots, exports ----------------------------------------------------------------------------

    def verify(self) -> dict[str, list[Issue]]:
        return {"report_log": self.report_log.verify(), "status_log": self.status_log.verify()}

    def export_301(self, report: R.Report) -> dict[str, Any]:
        """T23.7 (c): a 301-style record of one incident, headed with the fixed banner."""
        if report.fields.get("kind") != "incident":
            raise _spec("the 301-style export is for incidents (T23.7 c)")
        est = self.establishments()[report.fields["est_id"]]
        out = {"banner": R.EXPORT_301_BANNER, "statement": R.DEMO_DATA_NOTE, "report_id": report.report_id, "state": report.state,
               "establishment": est["name"], "area": self.areas()[report.fields["area_id"]]["name"],
               "fields": {f: report.fields.get(f) for f, _, _ in R.INCIDENT_FIELDS},
               "labels": {f: label for f, label, _ in R.INCIDENT_FIELDS},
               "recordability": report.recordability or "recordability pending"}
        if est["demo"]:
            out["demo"] = R.DEMO_NOTE
        return out

    @staticmethod
    def export_301_csv(data: dict[str, Any]) -> str:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow([data["banner"]])
        w.writerow([data["statement"]])
        if data.get("demo"):
            w.writerow([data["demo"]])
        w.writerow(["item", "value"])
        w.writerow(["report_id", data["report_id"]])
        w.writerow(["establishment", data["establishment"]])
        w.writerow(["area", data["area"]])
        for f, v in data["fields"].items():
            w.writerow([data["labels"][f], "" if v is None else v])
        rec = data["recordability"]
        if isinstance(rec, str):
            w.writerow(["recordability", rec])
        else:
            w.writerow(["recordability", f'{rec["recordable"]} (set by the safety manager, user {rec["decided_by"]})'])
            w.writerow(["criteria (29 CFR 1904.7)", "; ".join(rec["criteria"])])
            w.writerow(["days", "; ".join(f"{k} {v}" for k, v in rec["days"].items())])
            w.writerow(["recordability note", rec["note"]])
        return buf.getvalue()

    # --- demo manifest (T23.11) ------------------------------------------------------------------------------------------

    def demo_manifest(self) -> dict[str, Any] | None:
        path = self.root / "demo_manifest.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _occurred(value: Any) -> str:
    """occurred_at from a form: YYYY-MM-DDTHH:MM[:SS] (UTC) or the stored UTC form."""
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return R.utc(datetime.strptime(text, fmt).replace(tzinfo=R.timezone.utc))
        except ValueError:
            continue
    raise _spec("occurred_at is a date and time, YYYY-MM-DDTHH:MM (UTC)")
