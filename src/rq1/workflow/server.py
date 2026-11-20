"""T23 workflow pages (contract E-1.2.22; D-48), served by the V-02 application: one server, one sign-in.

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
from rq1.workflow.store import CR030_1, OWNER, SYSTEM, WorkflowStore

WF_BANNER = "Reporting workflow (research prototype). Manager decisions are records of what managers decided, not references."
RID = r"(rpt_[0-9a-f-]+)"


def _q(handler: Handler) -> dict[str, str]:
    return {k: v[-1] for k, v in parse_qs(urlsplit(handler.path).query).items()}


def _multi(body: str) -> dict[str, Any]:
    """A form with repeated keys kept as lists (checkboxes)."""
    out: dict[str, Any] = {}
    for k, v in parse_qs(body, keep_blank_values=True).items():
        out[k] = v if len(v) > 1 or k in ("roles", "area_ids", "contributing_factors", "criteria") else v[-1]
    return out


def lint_json(value: Any) -> list[str]:
    """Wording check of an export: every string value (keys are field names and are not printed text)."""
    issues: list[str] = []
    if isinstance(value, dict):
        for v in value.values():
            issues += lint_json(v)
    elif isinstance(value, list):
        for v in value:
            issues += lint_json(v)
    elif isinstance(value, str):
        issues += R.lint_workflow(value, html_page=False)
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

    def wsend(self, title: str, body: str, who: dict[str, Any]) -> None:
        html_text = page(title, f'<div class="card"><strong>{esc(WF_BANNER)}</strong> <a href="/wf">Workflow home</a></div>' + body, who)
        issues = R.lint_workflow(html_text)
        if issues:
            return self.send(page("Not sent", f'<div class="card err"><p>Wording rule (T23.12): {esc("; ".join(issues))}</p></div>', who),
                             HTTPStatus.INTERNAL_SERVER_ERROR)
        self.send(html_text)

    def wexport(self, data: Any, ctype: str, text: str | None = None) -> None:
        issues = lint_json(data) if text is None else R.lint_workflow(text, html_page=False)
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
        return (f'<p><label>Description<br><textarea name="description" required>{esc(values.get("description", ""))}</textarea></label></p>'
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
                       for a in sorted(self.wstore.areas().values(), key=lambda a: (ests[a["est_id"]]["name"], a["name"])))
        body = ('<form class="card" method="post" action="/wf/file"><p>Anyone signed in can file a report. A report never needs an AI alert '
                '(T23.6). Use pseudonyms only. In a demo establishment every entry is fictional.</p>'
                '<p><label>Kind <select name="kind"><option value="near_miss">near_miss</option><option value="incident">incident</option></select></label></p>'
                f'<p><label>Area <select name="area_id">{opts}</select></label></p>'
                '<p><label>Occurred at (UTC) <input type="datetime-local" step="1" name="occurred_at" required></label></p>'
                f'{self._near_miss_inputs()}<h2>Incident fields (kind incident only)</h2>{self._incident_inputs()}'
                '<button>File the report</button></form>')
        self.wsend("File a report", body, who)

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
        head = (f'<div class="card{" err" if chain["report_log"] or chain["status_log"] else ""}"><p class="chain">{chain_txt}</p>'
                f'<p><strong>{esc(r.wording())}</strong> · {esc(est["name"])} · {esc(area["name"])}</p>'
                + (f'<p>AI label: <strong>{esc(f.get("ai_label"))}</strong> (an automated output; the manager decides).</p>' if r.origin == "ai" else "")
                + (f'<p class="muted">Demo establishment: {esc(R.DEMO_NOTE)}; every incident field is fictional.</p>' if est["demo"] else "")
                + '</div>')
        rows = []
        for k in R.EDITABLE:
            if k not in f:
                continue
            v = f[k]
            text = ", ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else str(v))
            mark = f' <span class="muted">({R.PREFILL_NOTE})</span>' if k in r.prefilled else ""
            rows.append(f'<tr><td>{esc(k)}</td><td>{esc(text)}{mark}</td></tr>')
        if f.get("kind") == "incident":
            rec = r.recordability
            if not rec:
                rows.append('<tr><td>recordability</td><td>recordability pending</td></tr>')
            elif rec["recordable"] == "yes":
                rows.append(f'<tr><td>recordability</td><td>{R.RECORDABLE_BADGE} (set by safety manager {esc(people.get(rec["decided_by"], rec["decided_by"]))}): '
                            f'{esc(", ".join(rec["criteria"]))} {esc(json.dumps(rec["days"]) if rec["days"] else "")}; note: {esc(rec["note"])}</td></tr>')
            else:
                rows.append(f'<tr><td>recordability</td><td>{esc(rec["recordable"])} (set by safety manager {esc(people.get(rec["decided_by"], rec["decided_by"]))}); note: {esc(rec["note"])}</td></tr>')
        fields = f'<div class="card"><h2>Current fields</h2><table>{"".join(rows)}</table>'
        if f.get("kind") == "incident":
            fields += f'<p><a href="/wf/report/{report_id}/301.json">301-style export (JSON)</a> · <a href="/wf/report/{report_id}/301.csv">CSV</a></p>'
        fields += '</div>'
        clips = ""
        if r.origin == "ai":
            eps = store.episodes()
            parts = []
            for k, ep_id in enumerate(r.header["member_episode_ids"], 1):
                ep = eps[ep_id]
                parts.append(f'<p>Member {k}: episode <code>{esc(ep_id)}</code>, camera <code>{esc(ep["camera_id"])}</code>, '
                             f'AI label {esc(R.AI_LABEL.get(ep["g2_label"], "none"))}, evidence clip <code>{esc(r.fields.get("evidence_clip_ids", [""] * k)[k - 1] if len(r.fields.get("evidence_clip_ids", [])) >= k else "")}</code></p>')
            first = eps[r.header["member_episode_ids"][0]]
            sel = self._q_member(r)
            clips = (f'<div class="card"><h2>Evidence clips ({len(r.header["member_episode_ids"])})</h2>{"".join(parts)}'
                     f'<p>Showing member {sel + 1}. ' + " ".join(f'<a href="?member={k}">member {k + 1}</a>' for k in range(len(r.header["member_episode_ids"]))) + '</p></div>'
                     + self._player(self._wf_clip(who, eps[r.header["member_episode_ids"][sel]] if sel < len(r.header["member_episode_ids"]) else first)))
        hist = []
        for e in r.entries:
            if e["action"] in ("create_ai", "create_human"):
                ch = f'{len(e["field_changes"])} fields set'
            elif e["action"] == "set_recordability":
                rec = json.loads(e["field_changes"]["recordability"]["after"])
                ch = f'recordability {rec["recordable"]}; criteria: {", ".join(rec["criteria"]) or "none"}; days: {rec["days"] or "none"}'
            else:
                ch = "; ".join(f'{k}: {json.loads(v["before"])!r} → {json.loads(v["after"])!r}' for k, v in e["field_changes"].items())
            blocked = (f'<br><span class="muted">{esc(CR030_1)}</span>' if r.origin == "ai" and e["action"] in ("sm_uphold", "sm_overturn", "sm_reclassify") else "")
            hist.append(f'<tr><td>{e["seq"]}</td><td>{esc(e["created_utc"])}</td><td>{esc(people.get(e["actor_user_id"], e["actor_user_id"]))}</td>'
                        f'<td>{esc(e["action"])}</td><td>{esc(e["state_before"] or "—")} → {esc(e["state_after"])}</td><td>{esc(e["label"] or "")}</td>'
                        f'<td>{esc(e["reason"] or "")}</td><td>{esc(e["note"] or "")}</td><td>{esc(ch)}</td><td>{esc(", ".join(e["linked_record_ids"]))}{blocked}</td></tr>')
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

        def form(action: str, title: str, inner: str) -> None:
            if store.permitted(user, r, action) is None:
                out.append(f'<form class="card" method="post" action="{act}"><h3>{esc(title)}</h3><input type="hidden" name="action" value="{action}">'
                           f'{inner}<button>{esc(title)}</button></form>')
        ai = r.origin == "ai"
        rationale = '<p><label>What you saw in the clip (rationale)<br><textarea name="rationale" required></textarea></label></p>' if ai else ""
        conf = ('<p>Confidence <select name="confidence"><option value="3.0">high (3.0)</option><option value="2.0">medium (2.0)</option>'
                '<option value="1.0">low (1.0)</option></select></p>' if ai else "")
        note = '<p><label>Note<br><textarea name="note" required></textarea></label></p>'
        form("am_approve", "Approve (record the report)", '<p>Label <label><input type="radio" name="label" value="nm" required> nm</label> '
             '<label><input type="radio" name="label" value="ct"> ct</label></p>' + conf + rationale)
        form("am_reject", "Reject (goes to the safety manager)", '<p>Reason <select name="reason">' +
             "".join(f'<option value="{k}">{k}</option>' for k in R.REJECT_REASONS) + '</select></p>' + rationale)
        others = [x for x in store.headers() if x != r.report_id]
        form("am_duplicate", "Mark duplicate", '<p>Duplicate of <select name="duplicate_of">' +
             "".join(f'<option value="{x}">{x[-12:]}</option>' for x in others) + '</select></p>')
        form("sm_uphold", "Uphold the rejection", note)
        form("sm_overturn", "Overturn (record the report)", '<p>Label <label><input type="radio" name="label" value="nm" required> nm</label> '
             '<label><input type="radio" name="label" value="ct"> ct</label></p>' + note)
        form("sm_reclassify", "Reclassify (close as rejected)", '<p><label>Reason <input name="reason" required size="50"></label></p>'
             '<p>Label <select name="label"><option value="not_hazardous">not_hazardous</option><option value="ud">ud</option></select></p>' + note)
        form("sm_reopen", "Reopen", note)
        crit = "".join(f'<label class="opt"><input type="checkbox" name="criteria" value="{c}"> {c}</label>' for c in R.CRITERIA)
        form("set_recordability", "Set recordability", '<p>Recordability <select name="recordable"><option>undetermined</option><option>yes</option>'
             f'<option>no</option></select></p><p>Criteria (when yes; 29 CFR 1904.7)</p>{crit}'
             '<p><label>Days away (if that criterion) <input name="days_days_away" size="5"></label> '
             '<label>Days restricted or transferred (if that criterion) <input name="days_restricted_or_transfer" size="5"></label></p>' + note)
        form("sm_note", "Add a note", '<p><label>Note<br><textarea name="note" required></textarea></label></p>')
        if store.permitted(user, r, "edit_fields") is None:
            kind = ""
            if r.state in R.PENDING:
                kind = ('<p><label>Kind <select name="kind">' + "".join(f'<option{" selected" if r.fields.get("kind") == k else ""}>{k}</option>'
                                                                         for k in ("near_miss", "incident")) + '</select></label></p>')
            inner = (kind + f'<p><label>Occurred at (UTC) <input name="occurred_at" value="{esc(r.fields.get("occurred_at", ""))}" size="30"></label></p>'
                     + self._near_miss_inputs(r.fields) + (self._incident_inputs(r.fields) if r.fields.get("kind") == "incident" else ""))
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
            form = {k: v for k, v in form.items() if k in R.EDITABLE}
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
        self.wexport(data, "text/csv; charset=utf-8", self.wstore.export_301_csv(data))

    # --- indicators (T23.8, T23.9) and the regulator view (T23.10) ------------------------------------------------------

    def _periods(self, est_id: str) -> list[str]:
        return sorted({R.iso_week(r.fields["occurred_at"]) for r in self.wstore.reports() if r.fields.get("est_id") == est_id})

    def compute(self, est_id: str, area_id: str | None, period: str) -> dict[str, Any]:
        store = self.wstore
        reports = store.reports()  # the snapshot
        n, head = store.report_log.head()
        cfg = store.config()
        ind = R.indicators(reports, est_id, area_id, period, store.areas(), store.monitoring(), store.hours(est_id, period), cfg, store.clock())
        return {"indicators": ind, "flags": R.flags(ind, cfg), "log_length": n, "head_hash": head, "params": cfg}

    def _scope(self, user: dict[str, Any]) -> list[str]:
        ests = sorted(self.wstore.establishments())
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
            return ", ".join(f"{k} {n}" for k, n in v.items())
        return "not available (no hours entered)" if v is None else str(v)

    INDICATOR_LABELS = [
        ("I1", "I1 AI alert reports created"), ("I2", "I2 area-manager approval share (AI reports)"),
        ("I3", "I3 area-manager rejection share (AI reports)"), ("I4", "I4 safety-manager overturn share"),
        ("I5", "I5 safety-manager reclassification share (AI reports)"), ("I6", f"I6 reports pending longer than t_pending_days, by state"),
        ("I7_ai", "I7 recorded reports, label or kind near_miss: AI-started"), ("I7_human", "I7 recorded reports, label or kind near_miss: human-started"),
        ("monitored_camera_hours", "Monitored camera-hours in the period"), ("I7_ai_per_camera_hour", "I7 AI-started, per monitored camera-hour"),
        ("I8", "I8 human-only signal"), ("area_monitoring_share", "Share of areas with any monitoring"),
        ("I9", "I9 cases with recordability yes (set by the safety manager)"), ("incidence_rate", "I9 incidence rate = cases × 200,000 / hours worked (BLS formula)"),
    ]

    def _ind_rows(self, c: dict[str, Any]) -> str:
        ind = c["indicators"]
        rows = [f'<tr><td>{esc(label)}</td><td>{esc(ind[k].text(self._fmt))}</td></tr>' for k, label in self.INDICATOR_LABELS if k in ind]
        rows.append(f'<tr><td>Hours worked (entered) for {esc(ind["period"])}</td><td>{esc(self._fmt(ind["hours_worked"]))}</td></tr>')
        return "".join(rows)

    def _flag_rows(self, c: dict[str, Any]) -> str:
        ind, out = c["indicators"], []
        basis = {"F1": ind["I3"], "F2": ind["I4"], "F3": ind["I6"], "F4": ind["I8"]}
        for k, fl in c["flags"].items():
            state = ("raised" if fl.value else "not raised") if fl.determined else fl.text(lambda v: "raised" if v else "not raised")
            text = f'<br><em>{esc(R.FLAG_TEXT)}</em>' if fl.determined and fl.value else ""
            out.append(f'<tr><td>{k}</td><td>{esc(state)}; numbers: {esc(basis[k].text(self._fmt))}{text}</td></tr>')
        return "".join(out)

    def _params(self, c: dict[str, Any]) -> str:
        p = c["params"]
        return esc(", ".join(f"{k} = {p[k]}" for k in R.PARAMS) + f" (wf_config store_version {p['store_version']})")

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
        c = self.compute(est, area, period)
        ests, areas = self.wstore.establishments(), self.wstore.areas()
        nav = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": est, "period": p})}">{p}</a>' for p in periods)
        an = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": est, "period": period, "area": a["area_id"]})}">{esc(a["name"])}</a>'
                        for a in areas.values() if a["est_id"] == est)
        estnav = " · ".join(f'<a href="/wf/indicators?{urlencode({"est": e})}">{esc(ests[e]["name"])}</a>' for e in scope)
        body = (f'<div class="card"><p>Establishments: {estnav}</p><p>Periods: {nav or "none"}</p><p>Areas: {an} · <a href="/wf/indicators?{urlencode({"est": est, "period": period})}">all areas</a></p>'
                f'<p><strong>{esc(ests[est]["name"])}</strong>, {esc(areas[area]["name"]) if area else "all areas"}, period {esc(period)}. '
                f'Computed from the report log snapshot: length {c["log_length"]}, head hash <code>{esc(c["head_hash"])}</code>.</p></div>'
                f'<div class="card"><h2>Indicators (T23.8)</h2><table>{self._ind_rows(c)}</table></div>'
                f'<div class="card"><h2>Disagreement flags (T23.9)</h2><table>{self._flag_rows(c)}</table><p class="muted">Flags change no report, state or record.</p></div>'
                f'<div class="card"><p class="muted">Parameters: {self._params(c)}</p></div>')
        self.wsend("Indicators and flags", body, who)

    def regulator_data(self, est: str, period: str) -> dict[str, Any]:
        c = self.compute(est, None, period)
        ind, ver = c["indicators"], self.wstore.verify()
        out: dict[str, Any] = {"banner": R.REGULATOR_BANNER, "establishment": self.wstore.establishments()[est]["name"], "period": period,
                               "demo": self.wstore.establishments()[est]["demo"],
                               "report_log": {"length": c["log_length"], "head_hash": c["head_hash"], "verification": "intact" if not ver["report_log"] else "broken"},
                               "status_log": {"verification": "intact" if not ver["status_log"] else "broken"},
                               "parameters": {k: c["params"][k] for k in R.PARAMS}, "wf_config_store_version": c["params"]["store_version"],
                               "indicators": {}, "flags": {}}
        for k, label in self.INDICATOR_LABELS:
            if k in ind:
                out["indicators"][k] = {"label": label, "value": ind[k].text(self._fmt)}
        out["indicators"]["hours_worked"] = {"label": "Hours worked (entered)", "value": self._fmt(ind["hours_worked"])}
        for k, fl in c["flags"].items():
            out["flags"][k] = {"state": (("raised" if fl.value else "not raised") if fl.determined else fl.text(lambda v: "raised" if v else "not raised")),
                               "text": R.FLAG_TEXT if fl.determined and fl.value else ""}
        return out

    def _reg_args(self, user: dict[str, Any]) -> tuple[str, str] | None:
        q, scope = _q(self), self._scope(user)
        est = q.get("est") or (scope[0] if scope else "")
        if est not in scope:
            return None
        periods = self._periods(est)
        return est, q.get("period") or (periods[0] if periods else R.iso_week(R.utc(self.wstore.clock())))

    def wf_regulator(self) -> None:
        got = self.wneed("oversight", "owner")
        if not got:
            return
        who, user = got
        args = self._reg_args(user)
        if not args:
            return self.fail(HTTPStatus.NOT_FOUND, "No establishment.", who)
        est, period = args
        d = self.regulator_data(est, period)
        ests = self.wstore.establishments()
        estnav = " · ".join(f'<a href="/wf/regulator?{urlencode({"est": e})}">{esc(ests[e]["name"])}</a>' for e in self._scope(user))
        pnav = " · ".join(f'<a href="/wf/regulator?{urlencode({"est": est, "period": p})}">{p}</a>' for p in self._periods(est))
        rows = "".join(f'<tr><td>{esc(v["label"])}</td><td>{esc(v["value"])}</td></tr>' for v in d["indicators"].values())
        frows = "".join(f'<tr><td>{k}</td><td>{esc(v["state"])}{"<br><em>" + esc(v["text"]) + "</em>" if v["text"] else ""}</td></tr>' for k, v in d["flags"].items())
        q = urlencode({"est": est, "period": period})
        body = (f'<div class="card" style="border-width:3px"><strong>{esc(R.REGULATOR_BANNER)}</strong></div>'
                f'<div class="card"><p>Establishments: {estnav}</p><p>Periods: {pnav}</p><p><strong>{esc(d["establishment"])}</strong>, period {esc(period)}'
                f'{" (" + esc(R.DEMO_NOTE) + "s; simulated establishment)" if d["demo"] else ""}. Read-only.</p>'
                f'<p>Report log: {d["report_log"]["length"]} entries, head hash <code>{esc(d["report_log"]["head_hash"])}</code>, verification {d["report_log"]["verification"]}. '
                f'Status log verification: {d["status_log"]["verification"]}.</p>'
                f'<p><a href="/wf/regulator.json?{q}">Export JSON</a> · <a href="/wf/regulator.csv?{q}">Export CSV</a></p></div>'
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
        w.writerow(["section", "item", "value"])
        w.writerow(["scope", "establishment", d["establishment"]])
        w.writerow(["scope", "period", d["period"]])
        w.writerow(["logs", "report_log", f'{d["report_log"]["length"]} entries, head {d["report_log"]["head_hash"]}, {d["report_log"]["verification"]}'])
        w.writerow(["logs", "status_log", d["status_log"]["verification"]])
        for k, v in d["indicators"].items():
            w.writerow(["indicator", v["label"], v["value"]])
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
        self.wsend("Workflow setup", body, who)

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
