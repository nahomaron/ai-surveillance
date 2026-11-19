"""V-02 part A: the T22 blind review application. Python standard-library HTTP server bound to 127.0.0.1 only; plain HTML
and inline JavaScript; no network URL, no external file.

What a reviewer's pages and JSON responses carry is limited to T22.4: the clip (the recording's own video file, played
between the T22.4 start and end, with no marker of the interval), the outlines where T22.4 asks for them, playback
controls, the T22.5 definitions and the person's own submitted record. Target IDs are replaced by per-person item
numbers and the video by a random clip token.
"""
from __future__ import annotations

import html
import json
import re
import secrets
import threading
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from rq1.review import protocol as P
from rq1.review.store import Store
from rq1.schema.errors import ContractError

BANNER = "Research review tool. Synthetic data. Labels are review records, not safety findings."
HOST = "127.0.0.1"
CHUNK = 2 * 1024 * 1024
CSS = """
:root{--bg:#f6f6f4;--fg:#1d1d1b;--muted:#5d5d58;--line:#d6d6d0;--card:#fff;--accent:#2f5d8a}
@media (prefers-color-scheme:dark){:root{--bg:#1b1c1e;--fg:#ececea;--muted:#a3a39d;--line:#3a3b3e;--card:#242528;--accent:#8db6e0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,system-ui,sans-serif}
.banner{background:#3b3b38;color:#fff;padding:8px 16px;font-weight:600;font-size:14px}
header{display:flex;gap:16px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line)}
header .who{margin-left:auto;color:var(--muted)}main{padding:16px;max-width:1100px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px;margin:0 0 14px}
a{color:var(--accent)}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
label.opt{display:block;padding:5px 0}textarea{width:100%;min-height:80px}button,input,select,textarea{font:inherit}
.player{position:relative;max-width:960px}.player video,.player canvas{width:100%;display:block}.player canvas{position:absolute;inset:0;pointer-events:none}
.controls{display:flex;gap:10px;align-items:center;margin:8px 0}.controls input[type=range]{flex:1}
.card{overflow-x:auto}td code{word-break:break-all}.err{border-color:#b04a3a}.muted{color:var(--muted)}code,pre{font:13px ui-monospace,monospace}pre{white-space:pre-wrap}
"""

PLAYER_JS = """
(function(){
const v=document.getElementById('clip'), c=document.getElementById('overlay'), s=+v.dataset.start, e=+v.dataset.end;
const fps=+v.dataset.fps, outlines=JSON.parse(document.getElementById('outlines').textContent);
const bar=document.getElementById('seek'), t=document.getElementById('t'), play=document.getElementById('play');
bar.min=0; bar.max=(e-s).toFixed(3); bar.step=(1/fps).toFixed(4);
function clamp(){ if(v.currentTime<s) v.currentTime=s; if(v.currentTime>=e){ v.pause(); v.currentTime=e; } }
v.addEventListener('loadedmetadata',()=>{ v.currentTime=s; c.width=v.videoWidth; c.height=v.videoHeight; });
v.addEventListener('timeupdate',()=>{ clamp(); bar.value=(v.currentTime-s).toFixed(3); t.textContent=(v.currentTime-s).toFixed(2)+' s / '+(e-s).toFixed(2)+' s'; });
v.addEventListener('seeking',clamp);
play.onclick=()=>{ if(v.paused){ if(v.currentTime>=e) v.currentTime=s; v.play(); } else v.pause(); };
document.getElementById('restart').onclick=()=>{ v.currentTime=s; };
document.getElementById('back').onclick=()=>{ v.pause(); v.currentTime=Math.max(s, v.currentTime-1/fps); };
document.getElementById('fwd').onclick=()=>{ v.pause(); v.currentTime=Math.min(e, v.currentTime+1/fps); };
bar.oninput=()=>{ v.currentTime=s+(+bar.value); };
document.getElementById('rate').onchange=(ev)=>{ v.playbackRate=+ev.target.value; };
function draw(){ const g=c.getContext('2d'); g.clearRect(0,0,c.width,c.height); g.lineWidth=4;
  for(const o of outlines){ let best=null; for(const b of o.boxes){ if(Math.abs(b[0]-v.currentTime)<=0.5/fps){ best=b; break; } }
    if(best){ g.strokeStyle=o.colour; g.strokeRect(best[1],best[2],best[3]-best[1],best[4]-best[2]); } }
  requestAnimationFrame(draw); }
requestAnimationFrame(draw);
})();
"""


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str, who: dict[str, str] | None = None) -> str:
    user = f'<span class="who">{esc(who["pseudonym"])} ({esc(who["role"])}) <form method="post" action="/logout" style="display:inline"><button>Sign out</button></form></span>' if who else ""
    nav = '<a href="/home">Home</a>' if who else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body><div class="banner">{esc(BANNER)}</div>'
            f'<header><strong>RQ1 review</strong>{nav}{user}</header><main><h1>{esc(title)}</h1>{body}</main></body></html>')


def label_options(name: str = "label", checked: str | None = None) -> str:
    return "".join(f'<label class="opt"><input type="radio" name="{name}" value="{k}" required{" checked" if k == checked else ""}> '
                   f'<strong>{k}</strong>: {esc(v)}</label>' for k, v in P.DEFINITIONS.items())


def confidence_options() -> str:
    return "".join(f'<label class="opt" style="display:inline-block;margin-right:16px"><input type="radio" name="confidence" value="{k:.1f}" required> {v}</label>'
                   for k, v in P.CONFIDENCE.items())


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store: Store, frames: dict[str, Any], port: int = 0, host: str = HOST) -> None:
        if host != HOST:
            raise ContractError("ERR-SPEC", "the review server binds to 127.0.0.1 only")
        super().__init__((host, port), Handler)
        self.store, self.frames = store, frames
        self.sessions: dict[str, dict[str, str]] = {}
        self.clips: dict[str, tuple[str, str, str]] = {}
        self.lock = threading.Lock()

    def clip_token(self, batch_id: str, target_id: str, profile_id: str) -> str:
        token = secrets.token_urlsafe(18)
        with self.lock:
            self.clips[token] = (batch_id, target_id, profile_id)
        return token


class Handler(BaseHTTPRequestHandler):
    server: ReviewServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # keep the console quiet; no request log is kept
        pass

    # --- plumbing -----------------------------------------------------------------------------------------------------------

    @property
    def store(self) -> Store:
        return self.server.store

    def who(self) -> dict[str, str] | None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        token = cookie["rq1review"].value if "rq1review" in cookie else None
        return self.server.sessions.get(token) if token else None

    def send(self, body: str | bytes, status: int = 200, ctype: str = "text/html; charset=utf-8", headers: dict[str, str] | None = None) -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; media-src 'self'")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def redirect(self, where: str, headers: dict[str, str] | None = None) -> None:
        self.send("", HTTPStatus.SEE_OTHER, headers={"Location": where, **(headers or {})})

    def fail(self, status: int, message: str, who: dict[str, str] | None = None) -> None:
        self.send(page("Not done", f'<div class="card err"><p>{esc(message)}</p><p><a href="javascript:history.back()">Back</a></p></div>', who), status)

    def form(self) -> dict[str, str]:
        return {k: v[-1] for k, v in parse_qs(self._body, keep_blank_values=True).items()}

    # --- dispatch -----------------------------------------------------------------------------------------------------------

    ROUTES_GET = [
        (r"/", "get_index"), (r"/home", "get_home"), (r"/setup", "get_setup"), (r"/batches", "get_batches"),
        (r"/batch/(rvb_[0-9a-f-]+)", "get_batch"), (r"/batch/(rvb_[0-9a-f-]+)/agreement", "get_agreement"), (r"/statuslog", "get_statuslog"),
        (r"/audit", "get_audit_list"), (r"/audit/([a-z0-9]{2,4}_[0-9a-z-]+)", "get_audit_target"),
        (r"/review/(rvb_[0-9a-f-]+)", "get_review_next"), (r"/review/(rvb_[0-9a-f-]+)/(\d+)", "get_review_item"),
        (r"/api/item/(rvb_[0-9a-f-]+)/(\d+)", "get_api_item"), (r"/clip/([A-Za-z0-9_-]+)", "get_clip"),
        (r"/adjudicate/(rvb_[0-9a-f-]+)", "get_adjudicate_list"), (r"/adjudicate/(rvb_[0-9a-f-]+)/(\d+)", "get_adjudicate_item"),
    ]
    ROUTES_POST = [
        (r"/login", "post_login"), (r"/logout", "post_logout"), (r"/setup", "post_setup"), (r"/batches", "post_batches"),
        (r"/review/(rvb_[0-9a-f-]+)/(\d+)", "post_review_item"), (r"/adjudicate/(rvb_[0-9a-f-]+)/(\d+)", "post_adjudicate_item"),
    ]

    def _dispatch(self, routes: list[tuple[str, str]]) -> None:
        path = urlsplit(self.path).path
        for pattern, name in routes:
            m = re.fullmatch(pattern, path)
            if m:
                try:
                    getattr(self, name)(*m.groups())
                except ContractError as error:
                    self.fail(HTTPStatus.BAD_REQUEST, f"{error.code}: {error}", self.who())
                return
        self.fail(HTTPStatus.NOT_FOUND, "No such page.", self.who())

    def do_GET(self) -> None:
        self._dispatch(self.ROUTES_GET)

    def do_HEAD(self) -> None:
        self._dispatch(self.ROUTES_GET)

    def do_POST(self) -> None:
        # Read the body before any refusal, so an unread body never reaches the next request on a kept-alive connection.
        length = int(self.headers.get("Content-Length") or 0)
        self._body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        self._dispatch(self.ROUTES_POST)

    def need(self, *roles: str) -> dict[str, str] | None:
        who = self.who()
        if who is None:
            self.redirect("/")
            return None
        if roles and who["role"] not in roles:
            self.fail(HTTPStatus.FORBIDDEN, "This page is not available to this profile.", who)
            return None
        return who

    # --- sign-in -------------------------------------------------------------------------------------------------------------

    def get_index(self) -> None:
        if self.who():
            return self.redirect("/home")
        profiles = self.store.profiles()
        if not profiles:
            body = '<div class="card"><p>No Owner profile yet. Create it on this computer with <code>python -m rq1.review init</code>.</p></div>'
        else:
            opts = "".join(f'<option value="{esc(p["profile_id"])}">{esc(p["pseudonym"])} ({esc(p["role"])})</option>' for p in profiles)
            body = (f'<form class="card" method="post" action="/login"><p><label>Profile <select name="profile">{opts}</select></label></p>'
                    f'<p><label>Passphrase <input type="password" name="passphrase" required></label></p><button>Sign in</button>'
                    f'<p class="muted">Sign-in separates the sessions of people who share this computer. It is not a security boundary.</p></form>')
        self.send(page("Sign in", body))

    def post_login(self) -> None:
        f = self.form()
        profile = self.store.login(f.get("profile", ""), f.get("passphrase", ""))
        if not profile:
            return self.fail(HTTPStatus.UNAUTHORIZED, "Profile or passphrase not recognised.")
        token = secrets.token_urlsafe(24)
        self.server.sessions[token] = profile
        self.redirect("/home", {"Set-Cookie": f"rq1review={token}; HttpOnly; SameSite=Strict; Path=/"})

    def post_logout(self) -> None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        if "rq1review" in cookie:
            self.server.sessions.pop(cookie["rq1review"].value, None)
        self.redirect("/", {"Set-Cookie": "rq1review=; Max-Age=0; Path=/"})

    # --- home ----------------------------------------------------------------------------------------------------------------

    def _my_batches(self, anr: str) -> list[str]:
        return [b for b in self.store.batch_ids() if self.store.role_in(b, anr)]

    def get_home(self) -> None:
        who = self.need()
        if not who:
            return
        if who["role"] == "owner":
            body = ('<div class="card"><ul><li><a href="/setup">Annotators (setup)</a></li><li><a href="/batches">Batches</a></li>'
                    '<li><a href="/audit">Audit trail (status history per target)</a></li><li><a href="/statuslog">Status log check</a></li></ul></div>')
            return self.send(page("Owner", body, who))
        rows = []
        for k, b in enumerate(self._my_batches(who["profile_id"]), 1):
            order = self.store.order(b, who["profile_id"])
            done = sum(1 for t in order if who["profile_id"] in self.store.latest(b, t))
            links = [f'<a href="/review/{b}">Blind review</a> ({done} of {len(order)} done)'] if order else ['<span class="muted">No blind items yet</span>']
            if self._may_decide(b, who):
                links.append(f'<a href="/adjudicate/{b}">Adjudication</a>')
            rows.append(f'<tr><td>Batch {k}</td><td>{" · ".join(links)}</td></tr>')
        body = f'<div class="card"><table><tr><th>Batch</th><th>Your work</th></tr>{"".join(rows) or "<tr><td colspan=2>No batch yet.</td></tr>"}</table></div>'
        self.send(page("Your review work", body, who))

    # --- Owner: setup, batches, status log, agreement -------------------------------------------------------------------------------

    def get_setup(self) -> None:
        who = self.need("owner")
        if not who:
            return
        rows = "".join(f'<tr><td>{esc(a["pseudonym"])}</td><td>{esc(a["role"])}</td><td>{esc(a["qualification_ref"])}</td>'
                       f'<td>{"yes" if a["independence_attestation"] else "no"}</td></tr>' for a in self.store.annotators().values())
        body = (f'<div class="card"><table><tr><th>Pseudonym</th><th>Role</th><th>Qualification</th><th>Independence attested</th></tr>{rows}</table></div>'
                '<form class="card" method="post" action="/setup"><h2>New annotator row</h2>'
                '<p><label>Pseudonym (never a real name) <input name="pseudonym" required></label></p>'
                '<p><label>Role <select name="role"><option value="c_layer_reviewer">c_layer_reviewer</option><option value="adjudicator">adjudicator</option></select></label></p>'
                '<p><label>Qualification (T22.2 c) <input name="qualification_ref" size="60" required placeholder="completed T22 handbook training and pilot batch, 2026-11-20"></label></p>'
                '<p><label><input type="checkbox" name="independence_attestation" value="yes"> The person attests independence as T22.2 (a) defines it.</label></p>'
                '<p><label>Their local passphrase <input type="password" name="passphrase" required></label></p><button>Create</button></form>')
        self.send(page("Annotators", body, who))

    def post_setup(self) -> None:
        if not self.need("owner"):
            return
        f = self.form()
        self.store.add_annotator(f.get("pseudonym", ""), f.get("role", ""), f.get("qualification_ref", ""),
                                 f.get("independence_attestation") == "yes", f.get("passphrase", ""))
        self.redirect("/setup")

    def get_batches(self) -> None:
        who = self.need("owner")
        if not who:
            return
        rows = []
        for b in self.store.batch_ids():
            m, p = self.store.manifest(b), self.store.progress(b)
            rows.append(f'<tr><td><a href="/batch/{b}">{b}</a></td><td>{"pilot" if m["pilot"] else "reference"}</td><td>{esc(m["configuration"]["name"])}</td>'
                        f'<td>{p["targets"]}</td><td>{p["adjudicated"]}</td><td>{esc(m["created_utc"])}</td></tr>')
        people = self.store.annotators().values()
        rev = "".join(f'<option value="{a["anr_id"]}">{esc(a["pseudonym"])}</option>' for a in people if a["role"] == "c_layer_reviewer")
        adj = "".join(f'<option value="{a["anr_id"]}">{esc(a["pseudonym"])}</option>' for a in people if a["role"] == "adjudicator")
        configs = "".join(f'<option>{esc(k)}</option>' for k in self.server.frames)
        body = (f'<div class="card"><table><tr><th>Batch</th><th>Kind</th><th>Configuration</th><th>Targets</th><th>Adjudicated</th><th>Created</th></tr>'
                f'{"".join(rows) or "<tr><td colspan=6>None yet.</td></tr>"}</table></div>'
                '<form class="card" method="post" action="/batches"><h2>New batch (T22.6)</h2>'
                f'<p><label>Configuration <select name="configuration">{configs}</select></label> · partition: validation</p>'
                '<p><label>Batch seed (supplied by the Owner) <input name="seed" required inputmode="numeric" pattern="[0-9]+"></label></p>'
                f'<p><label>Reviewer 1 <select name="reviewer1">{rev}</select></label> <label>Reviewer 2 <select name="reviewer2">{rev}</select></label></p>'
                f'<p><label>Adjudicator <select name="adjudicator"><option value="">none available</option>{adj}</select></label></p>'
                '<p><label><input type="checkbox" name="pilot" value="yes"> Pilot batch (n_pilot targets; reviewed together; never in agreement statistics)</label></p>'
                '<button>Create batch</button></form>')
        self.send(page("Batches", body, who))

    def post_batches(self) -> None:
        if not self.need("owner"):
            return
        f = self.form()
        frame = self.server.frames.get(f.get("configuration", ""))
        if frame is None:
            raise ContractError("ERR-SPEC", "unknown configuration")
        if not re.fullmatch(r"\d+", f.get("seed", "")):
            raise ContractError("ERR-SPEC", "the batch seed is a non-negative integer")
        m = self.store.create_batch(frame, int(f["seed"]), [f.get("reviewer1", ""), f.get("reviewer2", "")], f.get("adjudicator") or None,
                                    f.get("pilot") == "yes")
        self.redirect(f"/batch/{m['batch_id']}")

    def get_batch(self, batch_id: str) -> None:
        who = self.need("owner")
        if not who:
            return
        m, p = self.store.manifest(batch_id), self.store.progress(batch_id)
        agreement = (f'<p><a href="/batch/{batch_id}/agreement">Agreement panel</a></p>' if self.store.fully_adjudicated(batch_id)
                     else '<p class="muted">The agreement panel opens when the batch is fully adjudicated (pilot batches have none).</p>')
        body = (f'<div class="card"><h2>Progress</h2><pre>{esc(json.dumps(p, indent=1))}</pre>{agreement}</div>'
                f'<div class="card"><h2>Manifest (immutable)</h2><pre>{esc(json.dumps(m, indent=1, sort_keys=True))}</pre></div>')
        self.send(page(f"Batch {batch_id}", body, who))

    def get_agreement(self, batch_id: str) -> None:
        who = self.need("owner")
        if not who:
            return
        a = self.store.agreement(batch_id)
        self.send(page("Agreement panel", render_agreement(a), who))

    def get_statuslog(self) -> None:
        who = self.need("owner")
        if not who:
            return
        entries = self.store.status_log._entries()
        issues = self.store.status_log.verify()
        rows = "".join(f'<tr><td>{e["seq"]}</td><td>{esc(e["target_id"])}</td><td>{esc(e["status"])}</td><td>{esc(e["layer"])}</td><td>{esc(", ".join(e["basis_ids"]))}</td></tr>' for e in entries)
        body = (f'<div class="card"><p>Hash chain (CT-E-24): {"intact" if not issues else "BROKEN: " + esc(issues[0].message)}; {len(entries)} entries.</p>'
                f'<table><tr><th>seq</th><th>target</th><th>status</th><th>layer</th><th>basis</th></tr>{rows}</table></div>')
        self.send(page("Validation status log", body, who))

    def _chain(self) -> str:
        issues = self.store.status_log.verify()
        return "intact" if not issues else "BROKEN: " + esc(issues[0].message)

    def get_audit_list(self) -> None:
        """Audit trail view (original V-02 item 3): every target with status entries, read-only."""
        who = self.need("owner")
        if not who:
            return
        by_target: dict[str, list[dict[str, Any]]] = {}
        for e in self.store.status_log._entries():
            by_target.setdefault(e["target_id"], []).append(e)
        rows = "".join(f'<tr><td><a href="/audit/{esc(t)}">{esc(t)}</a></td><td>{esc(es[0]["target_type"])}</td><td>{len(es)}</td>'
                       f'<td>{esc(es[-1]["status"])}</td></tr>' for t, es in sorted(by_target.items()))
        body = (f'<div class="card"><p>Hash chain (CT-E-24): {self._chain()}.</p>'
                f'<table><tr><th>Target</th><th>Type</th><th>Entries</th><th>Latest status</th></tr>'
                f'{rows or "<tr><td colspan=4>No status entry yet.</td></tr>"}</table></div>')
        self.send(page("Audit trail", body, who))

    def get_audit_target(self, target_id: str) -> None:
        """The full status history of one target, in log order, with its basis adjudications and hashes. Read-only."""
        who = self.need("owner")
        if not who:
            return
        adjs = {e["row"]["adj_id"]: e["row"] for e in self.store.adjudications()}
        entries = [e for e in self.store.status_log._entries() if e["target_id"] == target_id]
        rows = []
        for e in entries:
            basis = "; ".join(f'{esc(b)}: {esc(adjs[b]["final_label"])}, {esc(adjs[b]["tier"])}, {esc(adjs[b]["method"])}, '
                              f'{len(adjs[b]["assessment_ids"])} assessments, {esc(adjs[b]["reference_class"])}' if b in adjs else esc(b)
                              for b in e["basis_ids"])
            rows.append(f'<tr class="entry"><td>{e["seq"]}</td><td>{esc(e["created_utc"])}</td><td>{esc(e["status"])}</td>'
                        f'<td>{esc(e["layer"])} / {esc(e["namespace"])}</td><td>{esc(e["config_id"])}</td><td>{esc(e["actor_id"])}</td>'
                        f'<td>{basis}</td></tr><tr class="hash"><td></td><td colspan="6" class="muted">prev_hash <code>{esc(e["prev_hash"])}</code><br>'
                        f'record_hash <code>{esc(e["record_hash"])}</code></td></tr>')
        body = (f'<div class="card"><p>Target <code>{esc(target_id)}</code>. Hash chain (CT-E-24): {self._chain()}.</p>'
                f'<table><tr><th>seq</th><th>Created (UTC)</th><th>Status</th><th>Layer / namespace</th><th>Configuration</th><th>Actor</th>'
                f'<th>Basis</th></tr>{"".join(rows) or "<tr><td colspan=7>No status entry for this target.</td></tr>"}</table>'
                f'<p class="muted">Read-only. Entries are only appended; a later entry supersedes an earlier one.</p></div>')
        self.send(page("Audit trail: one target", body, who))

    # --- blind review (T22.4, T22.5) -------------------------------------------------------------------------------------------------

    def _item(self, who: dict[str, str], batch_id: str, k: str) -> tuple[list[str], str]:
        order = self.store.order(batch_id, who["profile_id"])
        index = int(k) - 1
        if not 0 <= index < len(order):
            raise ContractError("ERR-SPEC", "no such item for this profile")
        return order, order[index]

    def _clip(self, who: dict[str, str], batch_id: str, target_id: str) -> dict[str, Any]:
        t = self.store.targets(batch_id)[target_id]
        token = self.server.clip_token(batch_id, target_id, who["profile_id"])
        return {"clip": f"/clip/{token}", "start_s": t["clip_start_s"], "end_s": t["clip_end_s"], "fps": t["fps"],
                "width": t["width"], "height": t["height"], "outlines": t["outlines"]}

    def _player(self, clip: dict[str, Any]) -> str:
        outlines = json.dumps(clip["outlines"]).replace("</", "<\\/")
        return (f'<div class="card"><div class="player"><video id="clip" src="{clip["clip"]}" preload="auto" playsinline muted '
                f'data-start="{clip["start_s"]}" data-end="{clip["end_s"]}" data-fps="{clip["fps"]}"></video><canvas id="overlay"></canvas></div>'
                '<div class="controls"><button type="button" id="play">Play / pause</button><button type="button" id="restart">Restart</button>'
                '<button type="button" id="back">◀ frame</button><button type="button" id="fwd">frame ▶</button>'
                '<input type="range" id="seek"><span id="t" class="muted"></span>'
                '<select id="rate"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option></select></div>'
                f'<script type="application/json" id="outlines">{outlines}</script><script>{PLAYER_JS}</script></div>')

    def get_review_next(self, batch_id: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        order = self.store.order(batch_id, who["profile_id"])
        for k, t in enumerate(order, 1):
            if who["profile_id"] not in self.store.latest(batch_id, t):
                return self.redirect(f"/review/{batch_id}/{k}")
        self.send(page("Blind review", f'<div class="card"><p>All {len(order)} items done. Thank you.</p></div>', who))

    def get_review_item(self, batch_id: str, k: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        order, target_id = self._item(who, batch_id, k)
        self.store.note_display(batch_id, target_id, who["profile_id"])
        mine = self.store.latest(batch_id, target_id).get(who["profile_id"])
        head = f'<p class="muted">Item {k} of {len(order)}. Judge from the video alone (T22.5).</p>'
        if mine:
            form = (f'<div class="card"><h2>Your assessment</h2><p><strong>{esc(mine["label"])}</strong>, confidence {esc(P.CONFIDENCE[mine["confidence"]])}</p>'
                    f'<p>{esc(mine["rationale"])}</p></div>'
                    f'<form class="card" method="post"><h2>Correction (replaces your assessment)</h2>{label_options()}<p>{confidence_options()}</p>'
                    f'<input type="hidden" name="replaces" value="{esc(mine["rva_id"])}">'
                    f'<p><textarea name="rationale" required>Replaces {esc(mine["rva_id"])}: </textarea></p><button>Submit correction</button></form>')
        else:
            form = (f'<form class="card" method="post"><h2>Label</h2>{label_options()}<h2>Confidence in this label</h2><p>{confidence_options()}</p>'
                    '<h2>What was seen</h2><p><textarea name="rationale" required placeholder="At least one sentence saying what was seen."></textarea></p>'
                    '<button>Submit</button></form>')
        nav = f'<p><a href="/review/{batch_id}">Next open item</a></p>'
        self.send(page("Blind review", head + self._player(self._clip(who, batch_id, target_id)) + form + nav, who))

    def get_api_item(self, batch_id: str, k: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        order, target_id = self._item(who, batch_id, k)
        self.store.note_display(batch_id, target_id, who["profile_id"])
        mine = self.store.latest(batch_id, target_id).get(who["profile_id"])
        data = {"item": int(k), "of": len(order), **self._clip(who, batch_id, target_id),
                "submitted": {"label": mine["label"], "confidence": mine["confidence"], "rationale": mine["rationale"]} if mine else None}
        self.send(json.dumps(data), ctype="application/json")

    def post_review_item(self, batch_id: str, k: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        _, target_id = self._item(who, batch_id, k)
        f = self.form()
        try:
            confidence = float(f.get("confidence", ""))
        except ValueError:
            raise ContractError("ERR-SPEC", "confidence must be low, medium or high (T22.5 b)") from None
        self.store.submit(batch_id, target_id, who["profile_id"], f.get("label", ""), confidence, f.get("rationale", ""),
                          shown_system_output=f.get("shown_system_output") == "true", replaces=f.get("replaces") or None)
        self.redirect(f"/review/{batch_id}")

    def get_clip(self, token: str) -> None:
        who = self.who()
        entry = self.server.clips.get(token)
        if not who or not entry or entry[2] != who["profile_id"]:
            return self.send(b"", HTTPStatus.NOT_FOUND, "text/plain")
        path = Path(self.store.targets(entry[0])[entry[1]]["video"])
        size = path.stat().st_size
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "").strip())
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1, start + CHUNK - 1)
            else:
                start, end = max(0, size - int(m.group(2))), size - 1
            if start >= size:
                return self.send(b"", HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "text/plain", {"Content-Range": f"bytes */{size}"})
            status, headers = HTTPStatus.PARTIAL_CONTENT, {"Content-Range": f"bytes {start}-{end}/{size}", "Accept-Ranges": "bytes"}
        else:
            start, end, status, headers = 0, size - 1, HTTPStatus.OK, {"Accept-Ranges": "bytes"}
        with open(path, "rb") as handle:
            handle.seek(start)
            data = handle.read(end - start + 1)
        self.send(data, status, "video/mp4", headers)

    # --- adjudication (T22.7) ----------------------------------------------------------------------------------------------------------

    def _may_decide(self, batch_id: str, who: dict[str, str]) -> bool:
        """The adjudicator; or, when the batch has none, its reviewers once both have finished the batch (T22.7 c)."""
        if self.store.manifest(batch_id)["pilot"]:
            return False
        adj = self.store.adjudicator(batch_id)
        if adj is not None:
            return who["profile_id"] == adj
        reviewers = self.store.reviewers(batch_id)
        ids = self.store.manifest(batch_id)["target_ids"]
        return who["profile_id"] in reviewers and all(r in self.store.latest(batch_id, t) for r in reviewers for t in ids)

    def _decide_order(self, batch_id: str, who: dict[str, str]) -> list[str]:
        m = self.store.manifest(batch_id)
        return P.reviewer_order(m["target_ids"], m["seed"], f"decide:{who['profile_id']}")

    def get_adjudicate_list(self, batch_id: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        if not self._may_decide(batch_id, who):
            return self.fail(HTTPStatus.FORBIDDEN, "Adjudication is not open to this profile for this batch.", who)
        waiting = set(self.store.needs_adjudication(batch_id))
        order = self._decide_order(batch_id, who)
        items = [f'<li><a href="/adjudicate/{batch_id}/{k}">Case {k}</a></li>' for k, t in enumerate(order, 1) if t in waiting]
        body = f'<div class="card"><p>{len(items)} case(s) waiting.</p><ul>{"".join(items)}</ul></div>'
        self.send(page("Adjudication", body, who))

    def get_adjudicate_item(self, batch_id: str, k: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        if not self._may_decide(batch_id, who):
            return self.fail(HTTPStatus.FORBIDDEN, "Adjudication is not open to this profile for this batch.", who)
        order = self._decide_order(batch_id, who)
        target_id = order[int(k) - 1] if 0 < int(k) <= len(order) else None
        if target_id not in self.store.needs_adjudication(batch_id):
            return self.fail(HTTPStatus.NOT_FOUND, "This case is not waiting for adjudication.", who)
        latest = self.store.latest(batch_id, target_id)
        shown = [latest[r] for r in self.store.reviewers(batch_id)]
        adj = self.store.adjudicator(batch_id)
        if adj and adj in latest:
            shown.append(latest[adj])
        cards = "".join(f'<div class="card"><h3>Assessment {n}{" (your blind audit)" if r["annotator_id"] == who["profile_id"] else ""}</h3>'
                        f'<p><strong>{esc(r["label"])}</strong>, confidence {esc(P.CONFIDENCE[r["confidence"]])}</p><p>{esc(r["rationale"])}</p></div>'
                        for n, r in enumerate(shown, 1))
        method = "adjudicator" if adj else "consensus meeting of both reviewers"
        form = (f'<form class="card" method="post"><h2>Final label ({method})</h2>{label_options("final_label")}<button>Record final label</button></form>')
        self.send(page(f"Adjudication, case {k}", self._player(self._clip(who, batch_id, target_id)) + cards + form, who))

    def post_adjudicate_item(self, batch_id: str, k: str) -> None:
        who = self.need("c_layer_reviewer", "adjudicator")
        if not who:
            return
        if not self._may_decide(batch_id, who):
            return self.fail(HTTPStatus.FORBIDDEN, "Adjudication is not open to this profile for this batch.", who)
        order = self._decide_order(batch_id, who)
        if not 0 < int(k) <= len(order):
            raise ContractError("ERR-SPEC", "no such case")
        final = self.form().get("final_label", "")
        if self.store.adjudicator(batch_id):
            self.store.adjudicate(batch_id, order[int(k) - 1], who["profile_id"], final)
        else:
            self.store.consensus(batch_id, order[int(k) - 1], who["profile_id"], final)
        self.redirect(f"/adjudicate/{batch_id}")


def _fmt(x: Any) -> str:
    return "not defined (one category only)" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def render_agreement(a: dict[str, Any]) -> str:
    times = "".join(f'<tr><td>{esc(k)}</td><td>{_fmt(v[0])}</td><td>{_fmt(v[1])}</td></tr>' for k, v in a["review_time_s_median_p90"].items())
    strata = ", ".join(f"{k} {v}" for k, v in a["targets_per_stratum"].items())
    counts = ", ".join(f"{k}: {v}" for k, v in a["counts_by_tier_method"].items())
    alpha = (f'not computed (n &lt; {P.ALPHA_MIN_UNITS})' if a["n_audited"] < P.ALPHA_MIN_UNITS else _fmt(a["alpha_audited"])) + f' (n = {a["n_audited"]})'
    rate = "no audit" if a["audit_agreement_rate"] is None else f'{a["audit_agree"]}/{a["n_audited"]} = {a["audit_agreement_rate"]:.3f}'
    return (f'<div class="card"><p>agreement_stat_ref: <code>{esc(a["agreement_stat_ref"])}</code> · configuration {esc(a["configuration"])} · '
            f'partition {esc(a["partition"])} · {a["n_targets"]} targets</p><p>Targets per stratum: {esc(strata)}</p>'
            f'<table><tr><th>Statistic</th><th>Value</th></tr>'
            f'<tr><td>Cohen\'s kappa, two reviewers, five labels</td><td>{_fmt(a["kappa_five_labels"])}</td></tr>'
            f'<tr><td>Cohen\'s kappa, four labels (targets where either said unsure left out; n = {a["n_four_label_targets"]})</td><td>{_fmt(a["kappa_four_labels"])}</td></tr>'
            f'<tr><td>Krippendorff\'s alpha (nominal), audited targets with three assessments (T22.14 b)</td><td>{alpha}</td></tr>'
            f'<tr><td>Tier-1 audit agreement rate</td><td>{esc(rate)}</td></tr>'
            f'<tr><td>Final adjudications by tier and method</td><td>{esc(counts)}</td></tr>'
            f'<tr><td>Tier-1 records superseded after the audit</td><td>{a["superseded_tier1"]}</td></tr>'
            f'<tr><td>Final label unsure (reported separately)</td><td>{a["final_unsure"]}</td></tr></table></div>'
            f'<div class="card"><h2>review_time_s</h2><table><tr><th>Reviewer</th><th>Median</th><th>P90</th></tr>{times}</table>'
            f'<p class="muted">Reported descriptively only (T22.5 d).</p></div>'
            f'<div class="card"><h2>Reviewer qualifications</h2><ul>{"".join(f"<li>{esc(q)}</li>" for q in a["qualifications"])}</ul>'
            f'<ul>{"".join(f"<li>{esc(s)}</li>" for s in a["statements"])}</ul></div>')


def make_server(store: Store, frames: dict[str, Any], port: int = 0, host: str = HOST) -> ReviewServer:
    return ReviewServer(store, frames, port=port, host=host)
