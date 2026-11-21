"""T23 workflow pages (contract E-1.2.22; D-48, with T23.16-T23.27, E-1.2.23; D-49), served by the V-02 application: one
server, one sign-in. Every page carries the T23.27 (f) statement; pages that show AI alerts and the regulator view carry the
T23.26 source banner; user-entered text is shown in "entered by" blocks (T23.22).

`WorkflowHandler` extends the V-02 `Handler` with the /wf pages. Every workflow page and export passes
`rules.lint_workflow` before it is sent (T23.12); a page that fails is not sent (HTTP 500). 127.0.0.1 only; no network URL.
"""
from __future__ import annotations

import csv
import io
import json
import re
import secrets
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

from rq1.review.server import HOST, Handler, ReviewServer, esc, page
from rq1.schema.errors import ContractError
from rq1.workflow import rules as R
from rq1.workflow.store import OWNER, SYSTEM, WorkflowStore

WF_BANNER = "Reporting workflow (research prototype). Manager decisions are records of what managers decided, not references."
RID = r"(rpt_[0-9a-f-]+)"


def _q(handler: Handler) -> dict[str, str]:
    return {k: v[-1] for k, v in parse_qs(urlsplit(handler.path).query).items()}


def _multi(body: str) -> dict[str, Any]:
    """A form with repeated keys kept as lists (checkboxes)."""
    out: dict[str, Any] = {}
    for k, v in parse_qs(body, keep_blank_values=True).items():
        out[k] = v if len(v) > 1 or k in ("roles", "area_ids", "contributing_factors", "criteria", "observability_cameras") else v[-1]
    return out


SKIP_KEYS = set(R.USER_TEXT) | {"note", "rationale"}  # T23.22: user-entered values are not linted


def lint_json(value: Any, exempt: tuple[str, ...] = ()) -> list[str]:
    """Wording check of an export: every string value except user-entered fields (keys are field names, not printed text)."""
    issues: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k not in SKIP_KEYS:
                issues += lint_json(v, exempt)
    elif isinstance(value, list):
        for v in value:
            issues += lint_json(v, exempt)
    elif isinstance(value, str):
        issues += R.lint_workflow(value, html_page=False, exempt=exempt)
    return issues


class WorkflowHandler(Handler):
    server: "WorkflowServer"

    ROUTES_GET = Handler.ROUTES_GET + [
        (r"/wf", "wf_home"), (r"/wf/inbox", "wf_inbox"), (r"/wf/queue", "wf_queue"), (r"/wf/file", "wf_file_form"),
        (rf"/wf/report/{RID}", "wf_report"), (rf"/wf/report/{RID}/301\.json", "wf_301_json"),
        (rf"/wf/report/{RID}/301\.csv", "wf_301_csv"), (r"/wf/indicators", "wf_indicators"),
        (r"/wf/regulator", "wf_regulator"), (r"/wf/regulator\.json", "wf_regulator_json"),
        (r"/wf/regulator\.csv", "wf_regulator_csv"), (r"/wf/setup", "wf_setup"), (r"/wf/clip/([A-Za-z0-9_-]+)", "wf_clip"),
    ]
    ROUTES_POST = Handler.ROUTES_POST + [
        (r"/wf/file", "wf_file_post"), (rf"/wf/report/{RID}/act", "wf_act"), (r"/wf/setup/([a-z]+)", "wf_setup_post"),
    ]

    @property
    def wstore(self) -> WorkflowStore:
        return self.server.store  # type: ignore[return-value]

    # --- plumbing ----------------------------------------------------------------------------------------------------

    def wsend(self, title: str, body: str, who: dict[str, Any], alerts: bool = True) -> None:
        top = (f'<div class="card"><strong>{esc(WF_BANNER)}</strong> <a href="/wf">Workflow home</a>'
               f'<p class="muted">{esc(R.DEMO_DATA_NOTE)}</p></div>')
        if alerts:
            top += f'<div class="card">{self.wstore.banner_block()}</div>'
        html_text = page(title, top + body, who)
        issues = R.lint_workflow(html_text)
        if issues:
            return self.send(page("Not sent", f'<div class="card err"><p>Wording rule (T23.12): {esc("; ".join(issues))}</p></div>', who),
                             HTTPStatus.INTERNAL_SERVER_ERROR)
        self.send(html_text)

    def wexport(self, data: Any, ctype: str, text: str | None = None, lint_text: str | None = None) -> None:
        exempt = (self.wstore.banner(),)
        issues = lint_json(data, exempt) if text is None else R.lint_workflow(lint_text if lint_text is not None else text,
                                                                           html_page=False, exempt=exempt)
        if issues:
            return self.send("wording rule (T23.12): " + "; ".join(issues), HTTPStatus.INTERNAL_SERVER_ERROR, "text/plain; charset=utf-8")
        body = text if text is not None else json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
        self.send(body, ctype=ctype)

    def wneed(self, *roles: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Signed in as a workflow user (or the Owner) holding one of `roles` (any role if none given)."""
        who = self.who()
        if who is None:
            self.redirect("/")
            return None
        try:
            user = self.wstore.actor(who)
        except ContractError as error:
            self.fail(HTTPStatus.FORBIDDEN, str(error), who)
            return None
        if roles and not set(roles) & set(user["roles"]):
            self.fail(HTTPStatus.FORBIDDEN, "This page is not available to this profile.", who)
            return None
        return who, user

    def _people(self) -> dict[str, str]:
        out = {u["user_id"]: u["pseudonym"] for u in self.wstore.users().values()}
        out.update({OWNER: "Owner", SYSTEM: "system"})
        return out

    def get_home(self) -> None:
        who = self.who()
        if who and (who["profile_id"] == OWNER or who["profile_id"] in self.wstore.users()):
            if who["profile_id"] != OWNER:
                return self.redirect("/wf")
            body = ('<div class="card"><h2>Review (V-02)</h2><ul><li><a href="/setup">Annotators (setup)</a></li><li><a href="/batches">Batches</a></li>'
                    '<li><a href="/audit">Audit trail</a></li><li><a href="/statuslog">Status log check</a></li></ul>'
                    '<h2>Reporting workflow (T23)</h2><ul><li><a href="/wf">Workflow home</a></li><li><a href="/wf/setup">Workflow setup</a></li></ul></div>')
            return self.send(page("Owner", body, who))
        super().get_home()

    # --- home, inbox, queue -----------------------------------------------------------------------------------------------

    def wf_home(self) -> None:
        got = self.wneed()
        if not got:
            return
        who, user = got
        links = ['<li><a href="/wf/file">File a report</a></li>']
        if "area_manager" in user["roles"]:
            links.append('<li><a href="/wf/inbox">Area manager inbox</a></li>')
        if "safety_manager" in user["roles"]:
            links.append('<li><a href="/wf/queue">Safety manager queue</a></li>')
        if set(user["roles"]) & {"area_manager", "safety_manager", "owner"}:
            links.append('<li><a href="/wf/indicators">Indicators and flags</a></li>')
        if set(user["roles"]) & {"oversight", "owner"}:
            links.append('<li><a href="/wf/regulator">Simulated regulator view</a></li>')
        if "owner" in user["roles"]:
            links.append('<li><a href="/wf/setup">Workflow setup</a></li>')
        mine = [r for r in self.wstore.reports() if r.entries and r.entries[0]["actor_user_id"] == user["user_id"]]
        body = (f'<div class="card"><ul>{"".join(links)}</ul></div>'
                f'<div class="card"><h2>Reports you filed</h2>{self._table(mine) if mine else "<p>None.</p>"}</div>')
        self.wsend("Workflow", body, who)

    def _table(self, reports: list[R.Report]) -> str:
        areas, ests = self.wstore.areas(), self.wstore.establishments()
        rows = []
        for r in sorted(reports, key=lambda r: (r.fields.get("occurred_at", ""), r.report_id)):
            f = r.fields
            ai = esc(f.get("ai_label", "")) if r.origin == "ai" else "human-started"
            rows.append(f'<tr><td><a href="/wf/report/{r.report_id}">{esc(r.report_id[-12:])}</a></td><td>{esc(ests[f["est_id"]]["name"])}</td>'
                        f'<td>{esc(areas[f["area_id"]]["name"])}</td><td>{esc(f.get("occurred_at", ""))}</td><td>{esc(f.get("kind", ""))}</td>'
                        f'<td>{ai}</td><td>{esc(r.state)}</td></tr>')
        return ('<table><tr><th>Report</th><th>Establishment</th><th>Area</th><th>Occurred (UTC)</th><th>Kind</th><th>Origin / AI label</th>'
                f'<th>State</th></tr>{"".join(rows)}</table>')

    def wf_inbox(self) -> None:
        got = self.wneed("area_manager")
        if not got:
            return
        who, user = got
        pending = [r for r in self.wstore.reports() if r.state == "pending_am" and r.fields.get("area_id") in user["area_ids"]]
        self.wsend("Area manager inbox", f'<div class="card"><p>{len(pending)} pending report(s) in your areas.</p>{self._table(pending)}</div>', who)

    def wf_queue(self) -> None:
        got = self.wneed("safety_manager")
        if not got:
            return
        who, user = got
        mine = [r for r in self.wstore.reports() if r.fields.get("est_id") == user["est_id"]]
        groups = [("Rejected by the area manager: uphold or overturn (pending_sm)", [r for r in mine if r.state == "pending_sm"]),
                  ("Incidents waiting for recordability", [r for r in mine if r.state == "recorded" and r.fields.get("kind") == "incident" and not r.recordability]),
                  ("Recorded reports (review, reclassify)", [r for r in mine if r.state == "recorded"]),
                  ("Closed reports (reopen)", [r for r in mine if r.state in ("closed_rejected", "closed_duplicate")]),
                  ("Pending with the area manager", [r for r in mine if r.state == "pending_am"])]
        body = "".join(f'<div class="card"><h2>{esc(t)}</h2>{self._table(rs) if rs else "<p>None.</p>"}</div>' for t, rs in groups)
        self.wsend("Safety manager queue", body, who)

    # --- filing (T23.6) ------------------------------------------------------------------------------------------------

    def _incident_inputs(self, values: dict[str, Any] | None = None) -> str:
        values = values or {}
        out = []
        for f, label, kind in R.INCIDENT_FIELDS:
            v = values.get(f) or ""
            if kind == "yesno":
                opts = "".join(f'<option value="{o}"{" selected" if v == o else ""}>{o or "(not given)"}</option>' for o in ("", "yes", "no"))
                out.append(f'<p><label>{esc(label)} <select name="{f}">{opts}</select></label></p>')
            else:
                out.append(f'<p><label>{esc(label)} <input name="{f}" size="50" value="{esc(v)}"></label></p>')
        return "".join(out)

    def _near_miss_inputs(self, values: dict[str, Any] | None = None) -> str:
        values = values or {}
        factors = "".join(f'<label class="opt" style="display:inline-block;margin-right:12px"><input type="checkbox" name="contributing_factors" value="{esc(c)}"'
                          f'{" checked" if c in (values.get("contributing_factors") or []) else ""}> {esc(c)}</label>' for c in R.CONTRIBUTING)
        people = ", ".join(values.get("people_involved") or [])
        return (f'<p class="muted">{esc(R.PRIVACY_NOTICE)}</p>'
                f'<p><label>Description<br><textarea name="description" required>{esc(values.get("description", ""))}</textarea></label></p>'
                f'<p><label>People involved (pseudonyms, comma separated) <input name="people_involved" size="50" value="{esc(people)}"></label></p>'
                f'<p>Contributing factors<br>{factors}</p>'
                f'<p><label>Immediate action <input name="immediate_action" size="60" value="{esc(values.get("immediate_action", ""))}"></label></p>'
                f'<p><label>Corrective action <input name="corrective_action" size="60" value="{esc(values.get("corrective_action", ""))}"></label></p>'
                f'<p><label>Notes <input name="notes" size="60" value="{esc(values.get("notes", ""))}"></label></p>')

    def wf_file_form(self) -> None:
        got = self.wneed()
        if not got:
            return
        who, _ = got
        ests = self.wstore.establishments()
        opts = "".join(f'<option value="{a["area_id"]}">{esc(ests[a["est_id"]]["name"])}: {esc(a["name"])}</option>'
                       for e in ests for a in self.wstore.areas().values() if a["est_id"] == e)  # registration order (T23.27 e)
        body = ('<form class="card" method="post" action="/wf/file"><p>Anyone signed in can file a report. A report never needs an AI alert '
                '(T23.6). Use pseudonyms only. In a demo establishment every entry is fictional.</p>'
                '<p><label>Kind <select name="kind"><option value="near_miss">near_miss</option><option value="incident">incident</option></select></label></p>'
                f'<p><label>Area <select name="area_id">{opts}</select></label></p>'
                '<p><label>Occurred at (UTC) <input type="datetime-local" step="1" name="occurred_at" required></label></p>'
                f'{self._near_miss_inputs()}<h2>Incident fields (kind incident only)</h2>{self._incident_inputs()}'
                '<button>File the report</button></form>')
        self.wsend("File a report", body, who, alerts=False)

    def wf_file_post(self) -> None:
        got = self.wneed()
        if not got:
            return
        who, _ = got
        form = _multi(self._body)
        if form.get("kind") == "near_miss":
            for f, _, _ in R.INCIDENT_FIELDS:
                form.pop(f, None)
        form = {k: v for k, v in form.items() if v not in ("", [])}
        rid = self.wstore.create_human(who, form)
        self.redirect(f"/wf/report/{rid}")

    # --- report page -----------------------------------------------------------------------------------------------------

    def _visible(self, user: dict[str, Any], r: R.Report) -> bool:
        if "owner" in user["roles"]:
            return True
        if "area_manager" in user["roles"] and r.fields.get("area_id") in user["area_ids"]:
            return True
        if "safety_manager" in user["roles"] and r.fields.get("est_id") == user["est_id"]:
            return True
        return bool(r.entries) and r.entries[0]["actor_user_id"] == user["user_id"]

    def _wf_clip(self, who: dict[str, Any], ep: dict[str, Any]) -> dict[str, Any]:
        token = secrets.token_urlsafe(18)
        with self.server.lock:
            self.server.wf_clips[token] = (ep["video"], who["profile_id"])
        return {"clip": f"/wf/clip/{token}", "start_s": ep["clip_start_s"], "end_s": ep["clip_end_s"], "fps": ep["fps"], "outlines": []}

    def wf_clip(self, token: str) -> None:
        who, entry = self.who(), self.server.wf_clips.get(token)
        if not who or not entry or entry[1] != who["profile_id"]:
            return self.send(b"", HTTPStatus.NOT_FOUND, "text/plain")
        self._stream(Path(entry[0]))

    def _value(self, r: R.Report, k: str, v: Any, people: dict[str, str]) -> str:
        """One field value: user-entered text in an "entered by" block (T23.22); system values escaped."""
        if k in R.USER_TEXT and k not in r.prefilled and v not in (None, "", []):
            return R.user_block(people.get(r.entered_by.get(k, ""), r.entered_by.get(k, "")), v)
        if k == "evasive_action_observed" and v == "true":
            return esc(R.EVASIVE_TRUE)  # T23.24 (e)
        text = ", ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else str(v))
        return esc(text)

    def _combined_block(self, r: R.Report) -> str:
        """T23.24 (a)-(c): the combined value with its provenance, or "not combined", and every member's own values."""
        c = self.wstore.combined(r)
        rows = "".join(
            f'<tr><td><code>{esc(m["ep_id"])}</code></td><td><code>{esc(m["camera_id"])}</code></td>'
            f'<td>{esc(f"{m["minclr_m"]:.2f} m" if m["minclr_m"] is not None else "not available (" + str(m["minclr_m_null_reason"]) + ")")}</td>'
            f'<td>{esc(m["geometry_method"] or "not recorded")}</td><td>{esc(m["calibration_tier"] or "not recorded")}</td>'
            f'<td>{esc(m["clearance_sigma_m"] if m["clearance_sigma_m"] is not None else "none")} / {esc(m["sigma_status"] or "not recorded")}</td>'
            f'<td>{esc(m["q_state"] or "not recorded")} {esc(", ".join(m["q_reasons"] or []))}</td>'
            f'<td>{esc(m["prov_class"] or R.PROV_NOT_RECORDED)}</td><td><code>{esc(m["s4_artifact_id"] or "not recorded")}</code></td></tr>'
            for m in c["members"])
        if c["combined"] is not None:
            b = c["combined"]
            head = (f'<p><strong>{esc(R.COMBINED_LABEL)}</strong>: {esc(c["text"])}; source episode <code>{esc(b["ep_id"])}</code>, camera '
                    f'<code>{esc(b["camera_id"])}</code>, geometry_method {esc(b["geometry_method"])}, clearance_sigma_m '
                    f'{esc(b["clearance_sigma_m"] if b["clearance_sigma_m"] is not None else "none")}, sigma_status {esc(b["sigma_status"] or "not recorded")}, '
                    f'evidence sufficiency {esc(b["q_state"] or "not recorded")} {esc(", ".join(b["q_reasons"] or []))}, prov_class '
                    f'{esc(b["prov_class"] or R.PROV_NOT_RECORDED)}, S4 artifact <code>{esc(b["s4_artifact_id"] or "not recorded")}</code>. '
                    'A review aid: never stored as a measurement (T23.24 d).</p>')
        else:
            head = f'<p><strong>Smallest estimated separation</strong>: {esc(c["text"])}.</p>'
        return (f'<div class="card"><h2>Member clearances (T23.24)</h2>{head}<table><tr><th>Episode</th><th>Camera</th><th>Clearance</th>'
                '<th>geometry_method</th><th>Calibration tier</th><th>clearance_sigma_m / sigma_status</th><th>q_state</th>'
                f'<th>prov_class</th><th>S4 artifact</th></tr>{rows}</table></div>')

    def wf_report(self, report_id: str) -> None:
        got = self.wneed()
        if not got:
            return
        who, user = got
        r = self.wstore.report(report_id)
        if not self._visible(user, r):
            return self.fail(HTTPStatus.FORBIDDEN, "This report is not in your areas or establishment.", who)
        self.wstore.note_display(report_id, user["user_id"])
        store, f = self.wstore, r.fields
        est, area = store.establishments()[f["est_id"]], store.areas()[f["area_id"]]
        people = self._people()
        chain = store.verify()
        chain_txt = (f'Report log hash chain: <strong>{"intact" if not chain["report_log"] else "BROKEN: " + esc(chain["report_log"][0].message)}</strong>. '
                     f'Status log hash chain: <strong>{"intact" if not chain["status_log"] else "BROKEN: " + esc(chain["status_log"][0].message)}</strong>.')
        dups = store.duplicates_of(report_id)
        dup_txt = (f'<p>duplicates: {len(dups)} ' + " ".join(f'<a href="/wf/report/{d}">{esc(d[-12:])}</a>' for d in dups) + '</p>') if dups else ""
        parts = [x.report_id for x in store.reports() if x.fields.get("split_from") == report_id]
        split_txt = (f'<p>Split into {len(parts)} reports: ' + " ".join(f'<a href="/wf/report/{d}">{esc(d[-12:])}</a>' for d in parts) + '</p>') if parts else ""
        if f.get("split_from"):
            split_txt += f'<p>Split from <a href="/wf/report/{f["split_from"]}">{esc(f["split_from"][-12:])}</a>.</p>'
        if f.get("duplicate_of"):
            dup_txt += f'<p>duplicate_of <a href="/wf/report/{f["duplicate_of"]}">{esc(f["duplicate_of"][-12:])}</a></p>'
        basis = f.get("grouping_basis") or ("grouping basis not recorded (report created before E-1.2.23)" if r.origin == "ai" else "")
        head = (f'<div class="card{" err" if chain["report_log"] or chain["status_log"] else ""}"><p class="chain">{chain_txt}</p>'
                f'<p><strong>{esc(r.wording())}</strong> · {esc(est["name"])} · {esc(area["name"])}</p>'
                + (f'<p>AI label: <strong>{esc(f.get("ai_label"))}</strong> (an automated output; the manager decides). '
                   f'Alert grouping: {esc(basis)}. A group is a review convenience, not a claim that the members show one interaction (T23.21 a).</p>' if r.origin == "ai" else "")
                + dup_txt + split_txt
                + (f'<p class="muted">Demo establishment: {esc(R.DEMO_NOTE)}; every incident field is fictional.</p>' if est["demo"] else "")
                + '</div>')
        rows = []
        labels = {"duration_s": f"duration_s ({R.DURATION_LABEL})"}
        for k in R.EDITABLE + ("grouping_basis", "group_resolution", "duplicate_of", "split_from") + R.OBS_FIELDS:
            if k not in f or k in ("duplicate_of", "split_from") and f[k] is None:
                continue
            mark = f' <span class="muted">({R.PREFILL_NOTE})</span>' if k in r.prefilled else ""
            rows.append(f'<tr><td>{esc(labels.get(k, k))}</td><td>{self._value(r, k, f[k], people)}{mark}</td></tr>')
        if f.get("kind") == "incident":
            rec = r.recordability
            if r.determination == "not_set":
                rows.append('<tr><td>recordability</td><td>recordability pending (not_set)</td></tr>')
            elif r.determination == "withdrawn":
                rows.append('<tr><td>recordability</td><td>withdrawn (the earlier determination stays in the history)</td></tr>')
            elif rec["recordable"] == "yes":
                rows.append(f'<tr><td>recordability</td><td>{R.RECORDABLE_BADGE} (set by safety manager {esc(people.get(rec["decided_by"], rec["decided_by"]))}): '
                            f'{esc(", ".join(rec["criteria"]))} {esc(json.dumps(rec["days"]) if rec["days"] else "")}; note: '
                            f'{R.user_block(people.get(rec["decided_by"], rec["decided_by"]), rec["note"])}</td></tr>')
            else:
                rows.append(f'<tr><td>recordability</td><td>{esc(rec["recordable"])} (set by safety manager {esc(people.get(rec["decided_by"], rec["decided_by"]))}); '
                            f'note: {R.user_block(people.get(rec["decided_by"], rec["decided_by"]), rec["note"])}</td></tr>')
        fields = f'<div class="card"><h2>Current fields</h2><table>{"".join(rows)}</table>'
        if f.get("kind") == "incident":
            fields += f'<p><a href="/wf/report/{report_id}/301.json">301-style export (JSON)</a> · <a href="/wf/report/{report_id}/301.csv">CSV</a></p>'
        fields += '</div>'
        clips = ""
        if r.origin == "ai":
            eps = store.episodes()
            clip_ids = f.get("evidence_clip_ids", [])
            parts_html = []
            for k, ep_id in enumerate(r.members, 1):
                ep = eps[ep_id]
                parts_html.append(f'<p>Member {k}: episode <code>{esc(ep_id)}</code>, camera <code>{esc(ep["camera_id"])}</code>, '
                                  f'AI label {esc(R.AI_LABEL.get(ep["g2_label"], "none"))}, evidence clip <code>{esc(clip_ids[k - 1] if len(clip_ids) >= k else "")}</code></p>')
            sel = self._q_member(r)
            sel = sel if sel < len(r.members) else 0
            clips = (f'<div class="card"><h2>Evidence clips ({len(r.members)})</h2>{"".join(parts_html)}'
                     f'<p>Showing member {sel + 1}. ' + " ".join(f'<a href="?member={k}">member {k + 1}</a>' for k in range(len(r.members))) + '</p></div>'
                     + self._player(self._wf_clip(who, eps[r.members[sel]])) + self._combined_block(r))
        adjs = {e["row"]["adj_id"]: e["row"] for e in store.adjudications()}
        hist = []
        for e in r.entries:
            if e["action"] in ("create_ai", "create_human"):
                ch = f'{len(e["field_changes"])} fields set'
            elif e["action"] == "set_recordability":
                rec = json.loads(e["field_changes"]["recordability"]["after"])
                ch = f'recordability {rec["recordable"]}; criteria: {", ".join(rec["criteria"]) or "none"}; days: {rec["days"] or "none"}'
            else:
                ch = "; ".join(f'{k}: {json.loads(v["before"])!r} → {json.loads(v["after"])!r}' for k, v in e["field_changes"].items())
            linked = ", ".join(f'{x} (safety-manager decision)' if x in adjs and adjs[x]["namespace"] == "candidate_review" else x
                               for x in e["linked_record_ids"])  # T23.16 (c): never printed as a tier
            actor = people.get(e["actor_user_id"], e["actor_user_id"])
            reason = R.user_block(actor, e["reason"]) if e["reason"] and e["action"] == "sm_reclassify" else esc(e["reason"] or "")
            note = R.user_block(actor, e["note"]) if e["note"] else ""
            hist.append(f'<tr><td>{e["seq"]}</td><td>{esc(e["created_utc"])}</td><td>{esc(actor)}</td>'
                        f'<td>{esc(e["action"])}</td><td>{esc(e["state_before"] or "—")} → {esc(e["state_after"])}</td><td>{esc(e["label"] or "")}</td>'
                        f'<td>{reason}</td><td>{note}</td><td>{esc(ch)}</td><td>{esc(linked)}</td></tr>')
        history = (f'<div class="card"><h2>History (report log, append-only)</h2><table><tr><th>seq</th><th>UTC</th><th>Who</th><th>Action</th><th>State</th>'
                   f'<th>Label</th><th>Reason</th><th>Note</th><th>Changes</th><th>Linked records</th></tr>{"".join(hist)}</table></div>')
        self.wsend("Report", head + clips + fields + self._forms(user, r) + history, who)

    def _q_member(self, r: R.Report) -> int:
        try:
            return max(0, int(_q(self).get("member", "0")))
        except ValueError:
            return 0

    def _forms(self, user: dict[str, Any], r: R.Report) -> str:
        store, out = self.wstore, []
        act = f'/wf/report/{r.report_id}/act'
        privacy = f'<p class="muted">{esc(R.PRIVACY_NOTICE)}</p>'

        def form(action: str, title: str, inner: str) -> None:
            if store.permitted(user, r, action) is None:
                out.append(f'<form class="card" method="post" action="{act}"><h3>{esc(title)}</h3><input type="hidden" name="action" value="{action}">'
                           f'{inner}<button>{esc(title)}</button></form>')
        ai = r.origin == "ai"
        multi = ai and len(r.members) >= 2
        rationale = (privacy + '<p><label>What you saw in the clip (rationale)<br><textarea name="rationale" required></textarea></label></p>') if ai else ""
        conf = ('<p>Confidence <select name="confidence"><option value="3.0">high (3.0)</option><option value="2.0">medium (2.0)</option>'
                '<option value="1.0">low (1.0)</option></select></p>' if ai else "")
        note = privacy + '<p><label>Note<br><textarea name="note" required></textarea></label></p>'
        group = ('<p>How many interactions do the members show (T23.21 d)? <label><input type="radio" name="group_resolution" value="one_interaction" required> '
                 'one interaction</label> <label><input type="radio" name="group_resolution" value="cannot_tell"> cannot tell</label>. If they show '
                 'several interactions, split the report first.</p>')
        obs = ""
        if not ai:
            cams = "".join(f'<label class="opt"><input type="checkbox" name="observability_cameras" value="{esc(c)}"> {esc(c)}</label>'
                           for c in store.areas()[r.fields["area_id"]]["camera_ids"])
            obs = ('<p>Camera observability of the event (T23.23 c) <select name="camera_observability"><option value="">not set</option>'
                   + "".join(f'<option>{o}</option>' for o in R.OBSERVABILITY) + f'</select></p><p>Cameras checked: {cams}</p>')
        labels = ('<p>Label <label><input type="radio" name="label" value="nm" required> nm</label> '
                  '<label><input type="radio" name="label" value="ct"> ct</label></p>')
        form("am_approve", "Approve (record the report)", labels + (group if multi else "") + conf + rationale + obs)
        form("am_reject", "Reject (goes to the safety manager)", '<p>Reason <select name="reason">' +
             "".join(f'<option value="{k}">{k}</option>' for k in R.REJECT_REASONS) + '</select></p>' + rationale + obs)
        if multi:
            sel = "".join(f'<p>Member <code>{esc(m)}</code>: part <select name="part_{esc(m)}">' +
                          "".join(f'<option>{k}</option>' for k in range(1, len(r.members) + 1)) + '</select></p>' for m in r.members)
            form("split", "Split into separate reports (T23.20 e, T23.28 a)", sel + note)
        others = [x for x in store.reports() if x.report_id != r.report_id and x.fields.get("est_id") == r.fields.get("est_id")
                  and x.state not in ("closed_duplicate", "closed_split")]
        form("am_duplicate", "Mark duplicate", '<p>Duplicate of <select name="duplicate_of">' +
             "".join(f'<option value="{x.report_id}">{x.report_id[-12:]}</option>' for x in others) + '</select></p>' + privacy)
        form("sm_uphold", "Uphold the rejection", note)
        form("sm_overturn", "Overturn (record the report)", labels + (group if multi else "") + note)
        form("sm_confirm_duplicate", "Confirm the duplicate", note)
        form("sm_reclassify", "Reclassify (close as rejected)", privacy + '<p><label>Reason <input name="reason" required size="50"></label></p>'
             '<p>Label <select name="label"><option value="not_hazardous">not_hazardous</option><option value="ud">ud</option></select></p>' + note)
        form("sm_reopen", "Reopen", note)
        crit = "".join(f'<label class="opt"><input type="checkbox" name="criteria" value="{c}"> {c}</label>' for c in R.CRITERIA)
        form("set_recordability", "Set recordability", '<p>Recordability <select name="recordable"><option>undetermined</option><option>yes</option>'
             f'<option>no</option></select></p><p>Criteria (when yes; 29 CFR 1904.7)</p>{crit}'
             '<p><label>Days away (if that criterion) <input name="days_days_away" size="5"></label> '
             '<label>Days restricted or transferred (if that criterion) <input name="days_restricted_or_transfer" size="5"></label></p>' + note)
        form("withdraw_recordability", "Withdraw the recordability determination (T23.19 c)", '<p>Reason <select name="reason">'
             + "".join(f'<option>{w}</option>' for w in R.WITHDRAW_REASONS) + '</select></p>' + note)
        form("sm_note", "Add a note", note)
        if store.permitted(user, r, "edit_fields") is None:
            kind = ""
            if r.state in R.PENDING:
                kind = ('<p><label>Kind <select name="kind">' + "".join(f'<option{" selected" if r.fields.get("kind") == k else ""}>{k}</option>'
                                                                         for k in ("near_miss", "incident")) + '</select></label></p>')
            inner = (kind + f'<p><label>Occurred at (UTC) <input name="occurred_at" value="{esc(r.fields.get("occurred_at", ""))}" size="30"></label></p>'
                     + self._near_miss_inputs(r.fields) + (self._incident_inputs(r.fields) if r.fields.get("kind") == "incident" else "")
                     + (obs if r.state == "pending_am" else ""))
            out.append(f'<form class="card" method="post" action="{act}"><h3>Edit fields</h3><input type="hidden" name="action" value="edit_fields">'
                       f'{inner}<button>Save changes</button></form>')
        return "".join(out) or '<div class="card"><p class="muted">No action is open to you on this report now.</p></div>'

    def wf_act(self, report_id: str) -> None:
        got = self.wneed()
        if not got:
            return
        who, user = got
        form = _multi(self._body)
        action = form.pop("action", "")
        if action == "edit_fields":
            current = self.wstore.report(report_id).fields
            form = {k: v for k, v in form.items() if k in R.EDITABLE or (k in R.OBS_FIELDS and v not in ("", []))}
            if "contributing_factors" not in form and "description" in form:
                form["contributing_factors"] = []
            form = {k: v for k, v in form.items() if not (v == "" and current.get(k) in (None, ""))}
            if isinstance(form.get("contributing_factors"), str):
                form["contributing_factors"] = [form["contributing_factors"]]
        if isinstance(form.get("criteria"), str):
            form["criteria"] = [form["criteria"]]
        self.wstore.act(who, report_id, action, form)
        self.redirect(f"/wf/report/{report_id}")

    def wf_301_json(self, report_id: str) -> None:
        got = self.wneed("safety_manager", "owner", "area_manager")
        if not got:
            return
        who, user = got
        r = self.wstore.report(report_id)
        if not self._visible(user, r):
            return self.fail(HTTPStatus.FORBIDDEN, "Not your report.", who)
        self.wexport(self.wstore.export_301(r), "application/json; charset=utf-8")

    def wf_301_csv(self, report_id: str) -> None:
        got = self.wneed("safety_manager", "owner", "area_manager")
        if not got:
            return
        who, user = got
        r = self.wstore.report(report_id)
        if not self._visible(user, r):
            return self.fail(HTTPStatus.FORBIDDEN, "Not your report.", who)
        data = self.wstore.export_301(r)
        blank = {**data, "fields": {k: ("" if k in R.USER_TEXT else v) for k, v in data["fields"].items()},
                 "recordability": data["recordability"] if isinstance(data["recordability"], str) else {**data["recordability"], "note": ""}}
        self.wexport(data, "text/csv; charset=utf-8", self.wstore.export_301_csv(data), lint_text=self.wstore.export_301_csv(blank))

    # --- indicators (T23.8, T23.9) and the regulator view (T23.10) ------------------------------------------------------

    def _periods(self, est_id: str) -> list[str]:
        return sorted({R.iso_week(r.fields["occurred_at"]) for r in self.wstore.reports() if r.fields.get("est_id") == est_id})

    def compute(self, est_id: str, area_id: str | None, period: str, as_of: str | None = None) -> dict[str, Any]:
        """T23.18 (b): the view from the report log truncated at as_of (default: now)."""
        v = self.wstore.view(est_id, area_id, period, as_of=as_of)
        return {**v, "indicators": v["indicators"], "flags": v["flags"]}

    def _as_of(self) -> str | None:
        q = _q(self).get("as_of")
        if q:
            R.parse_utc(q)
        return q or None

    def _scope(self, user: dict[str, Any]) -> list[str]:
        ests = list(self.wstore.establishments())  # registration order; never sorted or ranked (T23.27 e)
        if "owner" in user["roles"] or "oversight" in user["roles"]:
            return ests
        return [e for e in ests if e == user.get("est_id") or any(self.wstore.areas()[a]["est_id"] == e for a in user["area_ids"])]

    @staticmethod
    def _fmt(v: Any) -> str:
        if isinstance(v, R.Share):
            return v.text()
        if isinstance(v, float):
            return f"{v:.4f}"
        if isinstance(v, dict) and "cases" in v:
            return f'{v["cases"]} case(s); by criterion: ' + ", ".join(f"{k} {n}" for k, n in v["by_criterion"].items())
        if isinstance(v, dict):
            return ", ".join(f"{k} {n:.4f}" if isinstance(n, float) else f"{k} {n}" for k, n in v.items())
        return "not available" if v is None else str(v)

    INDICATOR_LABELS = [
        ("I1", "I1 AI alert reports created (count; not an event or hazard frequency)"),
        ("I2", "I2 area-manager approval share (AI-started reports)"),
        ("I3", "I3 area-manager rejection share (AI-started reports; not a verified false alert)"),
        ("I4", "I4 safety-manager overturn share of rejections (AI-started reports, latest decision per report)"),
        ("I5", "I5 reclassification of AI-started reports ever recorded"),
        ("I6", "I6 reports pending longer than t_pending_days since entering their current state, by state"),
        ("I7_ai", "I7 recorded reports of kind near_miss: AI-started"),
        ("I7_human", "I7 recorded reports of kind near_miss: human-started (own line; feeds no flag)"),
        ("monitoring", "Usable, usable_degraded, processed and monitored area-hours; camera-hours (descriptive only); unprocessed cameras"),
        ("I7_ai_rate", "I7 AI-started, per monitored area-hour"),
        ("I8", "I8 human-started reports by observability category (I8 = category 5)"),
        ("area_monitoring_share", "Share of areas with any monitored time"),
        ("I9", "I9 definitive cases: recorded incidents with recordability yes (set by the safety manager)"),
        ("incidence_rate", "I9 incidence rate = cases × 200,000 / hours worked entered for the period (BLS formula; view time only)"),
    ]

    def _value_text(self, ind: dict[str, Any], k: str) -> str:
        c = ind[k]
        if k == "I7_ai_rate":
            if isinstance(c.value, str):
                return f'{c.value}; numerator {c.notes["numerator"]}, denominator 0.0000 monitored area-hours, unprocessed cameras {c.notes["unprocessed cameras"]}'
            if c.notes["numerator"] == 0:
                return (f'0 in {c.notes["denominator_h"]:.4f} monitored area-hours. {R.ZERO_COUNT} '
                        f'(numerator 0, denominator {c.notes["denominator_h"]:.4f} h, unprocessed cameras {c.notes["unprocessed cameras"]})')
            return c.text(self._fmt)
        if k == "incidence_rate":
            if c.value is None:
                return R.NO_HOURS
            return f'{c.value:.4f}' + (" (provisional: an incident report in the period is not_set or undetermined)" if c.notes["provisional"] else "")
        if k == "I8":
            return c.text(self._fmt)
        return c.text(self._fmt)

    def _ind_rows(self, c: dict[str, Any]) -> str:
        ind = c["indicators"]
        rows = [f'<tr><td>{esc(label)}</td><td>{esc(self._value_text(ind, k))}</td></tr>' for k, label in self.INDICATOR_LABELS if k in ind]
        rows.append(f'<tr><td>Hours worked (entered) for {esc(ind["period"])}</td><td>{esc(self._fmt(ind["hours_worked"]))}</td></tr>')
        return "".join(rows)

    def _flag_state(self, fl: R.Cell) -> str:
        if fl.value is None:
            return "not evaluated: insufficient n (" + fl.notes.get("insufficient n", "") + ")"
        return "raised" if fl.value else "not raised"

    def _flag_rows(self, c: dict[str, Any]) -> str:
        ind, out = c["indicators"], []
        basis = {"F1": "I3", "F2": "I4", "F3": "I6", "F4": "I8"}
        for k, fl in c["flags"].items():
            text = f'<br><em>{esc(R.FLAG_TEXT)}</em>' if fl.value else ""
            out.append(f'<tr><td>{k}</td><td>{esc(self._flag_state(fl))}; numbers: {esc(self._value_text(ind, basis[k]))}{text}</td></tr>')
        return "".join(out)

    def _params(self, c: dict[str, Any]) -> str:
        p = c["params"]
        return esc(", ".join(f"{k} = {p[k]}" for k in R.PARAMS) + f" (wf_config store_version {p['store_version']})")

    def _view_head(self, c: dict[str, Any]) -> str:
        return (f'Computed from the report log truncated at as_of {esc(c["as_of"])}: length {c["log_length"]}, head hash '
                f'<code>{esc(c["head_hash"])}</code>.')

    def wf_indicators(self) -> None:
        got = self.wneed("area_manager", "safety_manager", "owner")
        if not got:
            return
        who, user = got
        q, scope = _q(self), self._scope(user)
        est = q.get("est") or (scope[0] if scope else "")
        if est not in scope:
            return self.fail(HTTPStatus.FORBIDDEN, "Not your establishment.", who)
        area = q.get("area") or None
        periods = self._periods(est)
        period = q.get("period") or (periods[0] if periods else R.iso_week(R.utc(self.wstore.clock())))
        c = self.compute(est, area, period, self._as_of())
        ests, areas = self.wstore.establishments(), self.wstore.areas()
        nav = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": est, "period": p})}">{p}</a>' for p in periods)
        an = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": est, "period": period, "area": a["area_id"]})}">{esc(a["name"])}</a>'
                        for a in areas.values() if a["est_id"] == est)
        estnav = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": e})}">{esc(ests[e]["name"])}</a>' for e in scope)
        i8 = c["indicators"]["I8"]
        cat5 = i8.notes["reports (category 5)"]
        miss = (f'<div class="card"><h2>Human-started reports without a matching alert on an observable camera (category 5)</h2>'
                f'<p>{len(cat5)}: ' + (" ".join(f'<a href="/wf/report/{x}">{esc(x[-12:])}</a>' for x in cat5) or "none")
                + f'</p><p><em>{esc(R.MISS_CAPTION)}</em></p></div>')
        body = (f'<div class="card"><p>Establishments: {estnav}</p><p>Periods: {nav or "none"}</p><p>Areas: {an} · <a href="/wf/indicators?{urlencode({"est": est, "period": period})}">all areas</a></p>'
                f'<p><strong>{esc(ests[est]["name"])}</strong>, {esc(areas[area]["name"]) if area else "all areas"}, period {esc(period)} (ISO week of occurred_at). '
                f'{self._view_head(c)}</p><p class="muted">Every value is a descriptive workflow measure about manager decisions or recorded reports.</p></div>'
                f'<div class="card"><h2>Indicators (T23.8; D-49.1 section 5)</h2><table>{self._ind_rows(c)}</table></div>' + miss +
                f'<div class="card"><h2>Disagreement flags (T23.9)</h2><table>{self._flag_rows(c)}</table><p class="muted">Flags change no report, state or record.</p></div>'
                f'<div class="card"><p class="muted">Parameters: {self._params(c)}</p></div>')
        self.wsend("Indicators and flags", body, who)

    def regulator_data(self, est: str, period: str, as_of: str | None = None) -> dict[str, Any]:
        c = self.compute(est, None, period, as_of)
        ind, ver = c["indicators"], self.wstore.verify()
        out: dict[str, Any] = {"banner": R.REGULATOR_BANNER, "statement": R.DEMO_DATA_NOTE,
                               "source_banner": self.wstore.banner(),
                               "establishment": self.wstore.establishments()[est]["name"], "period": period,
                               "demo": self.wstore.establishments()[est]["demo"], "as_of": c["as_of"],
                               "report_log": {"length": c["log_length"], "head_hash": c["head_hash"], "verification": "intact" if not ver["report_log"] else "broken"},
                               "status_log": {"verification": "intact" if not ver["status_log"] else "broken"},
                               "parameters": {k: c["params"][k] for k in R.PARAMS}, "wf_config_store_version": c["params"]["store_version"],
                               "indicators": {}, "flags": {}}
        for k, label in self.INDICATOR_LABELS:
            if k in ind:
                out["indicators"][k] = {"label": label, "value": self._value_text(ind, k) if k in ("I7_ai_rate", "incidence_rate") else self._fmt(ind[k].value),
                                        "notes": {n: R._note(v) for n, v in ind[k].notes.items()}}
        out["indicators"]["hours_worked"] = {"label": "Hours worked (entered)", "value": self._fmt(ind["hours_worked"]), "notes": {}}
        for k, fl in c["flags"].items():
            out["flags"][k] = {"state": self._flag_state(fl), "text": R.FLAG_TEXT if fl.value else ""}
        return out

    def _reg_args(self, user: dict[str, Any]) -> tuple[str, str, str | None] | None:
        q, scope = _q(self), self._scope(user)
        est = q.get("est") or (scope[0] if scope else "")
        if est not in scope:
            return None
        periods = self._periods(est)
        return est, q.get("period") or (periods[0] if periods else R.iso_week(R.utc(self.wstore.clock()))), self._as_of()

    def wf_regulator(self) -> None:
        got = self.wneed("oversight", "owner")
        if not got:
            return
        who, user = got
        args = self._reg_args(user)
        if not args:
            return self.fail(HTTPStatus.NOT_FOUND, "No establishment.", who)
        est, period, as_of = args
        d = self.regulator_data(est, period, as_of)
        ests = self.wstore.establishments()
        estnav = " · ".join(f'<a href="/wf/regulator?{urlencode({"est": e})}">{esc(ests[e]["name"])}</a>' for e in self._scope(user))
        pnav = " · ".join(f'<a href="/wf/regulator?{urlencode({"est": est, "period": p})}">{p}</a>' for p in self._periods(est))
        rows = "".join(f'<tr><td>{esc(v["label"])}</td><td>{esc(v["value"])}{"; " + esc("; ".join(f"{n}: {x}" for n, x in v["notes"].items())) if v["notes"] else ""}</td></tr>'
                       for v in d["indicators"].values())
        frows = "".join(f'<tr><td>{k}</td><td>{esc(v["state"])}{"<br><em>" + esc(v["text"]) + "</em>" if v["text"] else ""}</td></tr>' for k, v in d["flags"].items())
        qq = urlencode({"est": est, "period": period, "as_of": d["as_of"]})
        body = (f'<div class="card" style="border-width:3px"><strong>{esc(R.REGULATOR_BANNER)}</strong></div>'
                f'<div class="card"><p>Establishments (one at a time; never compared or ranked): {estnav}</p><p>Periods: {pnav}</p><p><strong>{esc(d["establishment"])}</strong>, period {esc(period)}'
                f'{" (" + esc(R.DEMO_NOTE) + "s; simulated establishment)" if d["demo"] else ""}. Read-only.</p>'
                f'<p>As of {esc(d["as_of"])}. Report log: {d["report_log"]["length"]} entries, head hash <code>{esc(d["report_log"]["head_hash"])}</code>, verification {d["report_log"]["verification"]}. '
                f'Status log verification: {d["status_log"]["verification"]}.</p>'
                f'<p><a href="/wf/regulator.json?{qq}">Export JSON</a> · <a href="/wf/regulator.csv?{qq}">Export CSV</a></p></div>'
                f'<div class="card"><h2>Indicators</h2><table>{rows}</table></div><div class="card"><h2>Flags</h2><table>{frows}</table></div>'
                f'<div class="card"><p class="muted">Workflow parameters in force: {esc(json.dumps(d["parameters"]))} (store_version {d["wf_config_store_version"]}).</p></div>')
        self.wsend("Simulated regulator view", body, who)

    def wf_regulator_json(self) -> None:
        got = self.wneed("oversight", "owner")
        if not got:
            return
        args = self._reg_args(got[1])
        if not args:
            return self.fail(HTTPStatus.NOT_FOUND, "No establishment.", got[0])
        self.wexport(self.regulator_data(*args), "application/json; charset=utf-8")

    def wf_regulator_csv(self) -> None:
        got = self.wneed("oversight", "owner")
        if not got:
            return
        args = self._reg_args(got[1])
        if not args:
            return self.fail(HTTPStatus.NOT_FOUND, "No establishment.", got[0])
        d = self.regulator_data(*args)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow([d["banner"]])
        w.writerow([d["statement"]])
        w.writerow([d["source_banner"]])
        w.writerow(["section", "item", "value"])
        w.writerow(["scope", "establishment", d["establishment"]])
        w.writerow(["scope", "period", d["period"]])
        w.writerow(["scope", "as_of", d["as_of"]])
        w.writerow(["logs", "report_log", f'{d["report_log"]["length"]} entries, head {d["report_log"]["head_hash"]}, {d["report_log"]["verification"]}'])
        w.writerow(["logs", "status_log", d["status_log"]["verification"]])
        for k, v in d["indicators"].items():
            w.writerow(["indicator", v["label"], v["value"] + "".join(f"; {n}: {x}" for n, x in v["notes"].items())])
        for k, v in d["flags"].items():
            w.writerow(["flag", k, (v["state"] + (" " + v["text"] if v["text"] else ""))])
        for k, v in d["parameters"].items():
            w.writerow(["parameter", k, v])
        self.wexport(d, "text/csv; charset=utf-8", buf.getvalue())

    # --- Owner setup (T23.11, T23.14) ---------------------------------------------------------------------------------------

    def wf_setup(self) -> None:
        got = self.wneed("owner")
        if not got:
            return
        who, _ = got
        s = self.wstore
        ests, areas, users, cfg = s.establishments(), s.areas(), s.users(), s.config()
        est_opts = "".join(f'<option value="{e}">{esc(v["name"])}</option>' for e, v in ests.items())
        area_opts = "".join(f'<option value="{a}">{esc(ests[v["est_id"]]["name"])}: {esc(v["name"])}</option>' for a, v in areas.items())
        roles = "".join(f'<label class="opt" style="display:inline-block;margin-right:12px"><input type="checkbox" name="roles" value="{r}"> {r}</label>' for r in R.ROLES)
        erows = "".join(f'<tr><td>{esc(v["name"])}</td><td>{"demo" if v["demo"] else ""}</td><td><code>{e}</code></td></tr>' for e, v in ests.items())
        arows = "".join(f'<tr><td>{esc(ests[v["est_id"]]["name"])}</td><td>{esc(v["name"])}</td><td>{len(v["camera_ids"])}</td></tr>' for v in areas.values())
        urows = "".join(f'<tr><td>{esc(u["pseudonym"])}</td><td>{esc(", ".join(u["roles"]))}</td><td>{esc(ests.get(u["est_id"], {}).get("name", ""))}</td>'
                        f'<td>{esc(", ".join(areas[a]["name"] for a in u["area_ids"]))}</td></tr>' for u in users.values())
        params = "".join(f'<label style="display:inline-block;margin-right:12px">{k} <input name="{k}" value="{esc(cfg[k])}" size="6"></label>' for k in R.PARAMS)
        demo = s.demo_manifest()
        demo_txt = (f'<p>Demo manifest: seed {demo["seed"]}, source {esc(demo["source_path"])}, {len(demo["runs"])} runs.</p>' if demo else
                    ('<form method="post" action="/wf/setup/demo"><p><label>Demo seed <input name="seed" required pattern="[0-9]+"></label> '
                     '<label>Demo n_flag_min <input name="n_flag_min" size="4"></label> <label>n_flag_min_sm <input name="n_flag_min_sm" size="4"></label></p>'
                     '<button>Run the demo draw (T23.11)</button></form>' if self.server.demo_source else '<p class="muted">No demo source configured for this server.</p>'))
        body = (f'<div class="card"><h2>Establishments</h2><table>{erows}</table><form method="post" action="/wf/setup/est"><input name="name" required placeholder="name"> '
                '<label><input type="checkbox" name="demo" value="yes" checked> demo (simulated)</label> <button>Add</button></form></div>'
                f'<div class="card"><h2>Areas</h2><table>{arows}</table><form method="post" action="/wf/setup/area"><select name="est_id">{est_opts}</select> '
                '<input name="name" required placeholder="area name"> <input name="camera_ids" size="60" placeholder="camera IDs, comma separated"> <button>Add</button></form></div>'
                f'<div class="card"><h2>Users (pseudonyms only)</h2><table>{urows}</table><form method="post" action="/wf/setup/user"><p><input name="pseudonym" required placeholder="pseudonym"></p>'
                f'<p>{roles}</p><p>Establishment (safety_manager) <select name="est_id"><option value="">none</option>{est_opts}</select></p>'
                f'<p>Areas (area_manager) <select name="area_ids" multiple size="4">{area_opts}</select></p>'
                '<p>Local passphrase <input type="password" name="passphrase" required></p><button>Add user</button></form></div>'
                f'<div class="card"><h2>Hours worked</h2><form method="post" action="/wf/setup/hours"><select name="est_id">{est_opts}</select> '
                '<input name="period" placeholder="2026-W47" required> <input name="hours_worked" placeholder="hours" required> <button>Enter</button></form></div>'
                f'<div class="card"><h2>Workflow parameters (T23.14)</h2><form method="post" action="/wf/setup/config">{params}<button>Save as a new store version</button></form></div>'
                f'<div class="card"><h2>Demo draw (T23.11)</h2>{demo_txt}</div>')
        self.wsend("Workflow setup", body, who, alerts=False)

    def wf_setup_post(self, what: str) -> None:
        got = self.wneed("owner")
        if not got:
            return
        who, user = got
        f, s = _multi(self._body), self.wstore
        if what == "est":
            s.add_establishment(f.get("name", ""), f.get("demo") == "yes")
        elif what == "area":
            s.add_area(f.get("est_id", ""), f.get("name", ""), [c.strip() for c in f.get("camera_ids", "").split(",") if c.strip()])
        elif what == "user":
            roles = f.get("roles") or []
            areas = f.get("area_ids") or []
            s.add_user(f.get("pseudonym", ""), roles if isinstance(roles, list) else [roles], f.get("est_id") or None,
                       areas if isinstance(areas, list) else [areas], f.get("passphrase", ""))
        elif what == "hours":
            s.add_hours(f.get("est_id", ""), f.get("period", ""), f.get("hours_worked"), user["user_id"])
        elif what == "config":
            p = {}
            for k, v in R.PARAMS.items():
                if k in f:
                    p[k] = int(f[k]) if isinstance(v, int) else (f[k] if isinstance(v, str) else float(f[k]))
            s.set_config(p)
        elif what == "demo":
            from rq1.workflow.demo import draw_demo
            if not re.fullmatch(r"\d+", f.get("seed", "")):
                raise ContractError("ERR-SPEC", "the demo seed is a non-negative integer")
            mins = {k: int(f[k]) for k in ("n_flag_min", "n_flag_min_sm") if f.get(k)}
            draw_demo(s, self.server.demo_source(), int(f["seed"]), mins or None)
        else:
            raise ContractError("ERR-SPEC", "unknown setup form")
        self.redirect("/wf/setup")


class WorkflowServer(ReviewServer):
    def __init__(self, store: WorkflowStore, frames: dict[str, Any], port: int = 0, host: str = HOST, demo_source: Any = None) -> None:
        super().__init__(store, frames, port=port, host=host, handler=WorkflowHandler)
        self.wf_clips: dict[str, tuple[str, str]] = {}
        self.demo_source = demo_source


def make_server(store: WorkflowStore, frames: dict[str, Any], port: int = 0, host: str = HOST, demo_source: Any = None) -> WorkflowServer:
    return WorkflowServer(store, frames, port=port, host=host, demo_source=demo_source)
