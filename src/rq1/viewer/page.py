"""V-01 page: one self-contained HTML file per recording (embedded JSON, plain JavaScript on a canvas; no server, no
network, no external file). The output is a pure function of the page data, so identical inputs give identical bytes."""
from __future__ import annotations

import html
import json
import re
from typing import Any

from . import settings

_DATA_OPEN = '<script id="rq1-data" type="application/json">'
_DATA_RE = re.compile(re.escape(_DATA_OPEN) + r"(.*?)</script>", re.S)


def _json(data: Any) -> str:
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return text.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")  # cannot close the script element


def embedded(page: str) -> Any:
    """The page data embedded in a page made by `render`."""
    match = _DATA_RE.search(page)
    if match is None:
        raise ValueError("no embedded page data")
    return json.loads(match.group(1))


def render(data: dict[str, Any]) -> str:
    h = data["header"]
    title = html.escape(f"Truth replay {h.get('run', '')} {h.get('camera', '')}".strip())
    banner = html.escape(settings.BANNER)
    return (_TEMPLATE.replace("@@TITLE@@", title).replace("@@BANNER@@", banner).replace("@@DATA@@", _json(data))
            .replace("@@SCRIPT@@", _SCRIPT).replace("@@STYLE@@", _STYLE))


def render_index(rows: list[dict[str, str]]) -> str:
    """A list of the generated pages (relative links only)."""
    items = "\n".join(
        f'<tr><td><a href="{html.escape(r["file"])}">{html.escape(r["run"])}</a></td><td>{html.escape(r["camera"])}</td>'
        f'<td>{html.escape(r["viewpoint_class"])}</td><td>{html.escape(r["low_light"])}</td><td>{html.escape(r["dataset_row"])}</td></tr>'
        for r in rows)
    return (_INDEX.replace("@@BANNER@@", html.escape(settings.BANNER)).replace("@@ROWS@@", items).replace("@@N@@", str(len(rows)))
            .replace("@@STYLE@@", _STYLE))


_STYLE = r"""
:root{--bg:#ffffff;--fg:#1d2329;--muted:#5f6b76;--line:#d9dee3;--panel:#f5f7f9;--person:#1f6fd1;--fork:#c2560c;--other:#6b7280;
--ring-p:#b45309;--ring-pc:#b91c1c;--turn-t:rgba(217,119,6,.22);--turn-f:rgba(22,163,74,.10);--turn-u:rgba(107,114,128,.22);--grid:#eceff2;--banner:#fff4d6;--banner-fg:#5b4100}
@media (prefers-color-scheme:dark){:root{--bg:#14181c;--fg:#e6e9ec;--muted:#9aa5b1;--line:#2c333a;--panel:#1b2025;--person:#5aa2ff;--fork:#f08a3e;
--other:#9ca3af;--ring-p:#f59e0b;--ring-pc:#f87171;--grid:#20262c;--banner:#3a2f12;--banner-fg:#ffe3a3}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.banner{background:var(--banner);color:var(--banner-fg);padding:8px 16px;font-weight:600;border-bottom:1px solid var(--line)}
header{padding:8px 16px;display:flex;flex-wrap:wrap;gap:4px 18px;border-bottom:1px solid var(--line);color:var(--muted)}
header b{color:var(--fg);font-weight:600}
#controls{padding:8px 16px;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;border-bottom:1px solid var(--line)}
#controls label{display:flex;gap:6px;align-items:center}#controls input[type=range]{width:120px}
#frame{width:min(520px,60vw)!important}button,select{font:inherit;padding:3px 8px}
#main{display:flex;gap:0;min-height:420px}#floor{flex:1 1 auto;width:100%;height:62vh;min-height:360px;display:block;cursor:grab}
aside{width:300px;flex:0 0 300px;border-left:1px solid var(--line);padding:8px 12px;overflow:auto;max-height:62vh;background:var(--panel)}
aside table{border-collapse:collapse;width:100%}aside td,aside th{padding:2px 4px;border-bottom:1px solid var(--line);text-align:left;font-variant-numeric:tabular-nums}
#timeline{width:100%;height:300px;display:block;border-top:1px solid var(--line);cursor:crosshair}
.note{color:var(--muted);padding:6px 16px 14px}.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
table.idx{border-collapse:collapse;margin:12px 16px}table.idx td,table.idx th{padding:3px 10px;border-bottom:1px solid var(--line);text-align:left}
a{color:var(--person)}
@media (max-width:760px){#main{flex-direction:column}aside{width:auto;flex:none;border-left:0;border-top:1px solid var(--line)}}
"""

_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title><style>@@STYLE@@</style></head>
<body>
<div class="banner" id="banner">@@BANNER@@</div>
<header id="hdr"></header>
<div id="controls">
 <button id="play" title="space">Play</button>
 <label>rate <select id="rate"></select></label>
 <input type="range" id="frame" min="0" value="0" step="1">
 <span id="flabel"></span>
 <label>pair <select id="pair"></select></label>
 <label><input type="checkbox" id="follow" checked> follow pair</label>
 <label><input type="checkbox" id="allpairs" checked> lines for pairs within d_p</label>
 <button id="fit">fit view</button>
</div>
<div id="controls2" style="padding:6px 16px;display:flex;flex-wrap:wrap;gap:8px 18px;border-bottom:1px solid var(--line)"></div>
<div id="main"><canvas id="floor"></canvas><aside id="side"></aside></div>
<canvas id="timeline"></canvas>
<div class="note" id="note"></div>
<script id="rq1-data" type="application/json">@@DATA@@</script>
<script>@@SCRIPT@@</script>
</body></html>
"""

_INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Truth replay index</title><style>@@STYLE@@</style></head>
<body><div class="banner">@@BANNER@@</div>
<p class="note">@@N@@ validation-partition recordings. Each page is self-contained.</p>
<table class="idx"><tr><th>run</th><th>camera</th><th>viewpoint</th><th>low_light</th><th>dataset row</th></tr>
@@ROWS@@
</table></body></html>
"""

_SCRIPT = r"""
"use strict";
const D = JSON.parse(document.getElementById("rq1-data").textContent);
const S = D.settings, H = D.header, N = H.n_frames, FR = D.frames;
const FROZEN = Object.assign({}, S.display), disp = Object.assign({}, S.display);
const R = S.person_radius_m, FL = S.fork_prior_m[0], FW = S.fork_prior_m[1];
const OBJ = D.objects, BY = {}; OBJ.forEach(o => { BY[o.id] = o; });
const DT = FR.dt || 1 / 30;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const $ = id => document.getElementById(id);
const fmt = (v, d) => (v === null || v === undefined) ? "n/a" : v.toFixed(d);
const STATE_TEXT = {V: "visible", P: "not visible (predicted point)", L: "not visible (lost, no point)", I: "ineligible frame", "-": "outside span"};
const TURN_TEXT = {T: "true", F: "false", U: "unknown", "-": "ineligible frame"};
function at(o, k, name) { const i = k - o.s0; if (i < 0 || i >= o.st.length) return null; const a = o[name]; return a === undefined ? null : a[i]; }
function label(o) { return (o.cls === "person" ? "P" : o.cls === "forklift" ? "F" : "O") + o.id; }

/* header */
const hdr = [["dataset row", H.dataset_row], ["run", H.run], ["camera", H.camera], ["recording", H.recording_id], ["viewpoint", H.viewpoint_class],
  ["low_light", H.low_light], ["partition", H.partition], ["split", H.split_artifact_id], ["code commit", H.code_commit], ["contract", H.contract],
  ["pre-registration sha256", H.preregistration_sha256], ["frames", String(N)]];
$("hdr").innerHTML = "";
hdr.forEach(([k, v]) => { const s = document.createElement("span"); s.append(k + ": "); const b = document.createElement("b"); b.textContent = v; s.append(b); $("hdr").append(s); });

/* pairs: default = the pair with the smallest clearance over the recording (a display choice only) */
const PAIRS = D.pairs;
let pairIdx = -1, best = Infinity;
PAIRS.forEach((p, i) => { p.c.forEach(v => { if (v !== null && v < best) { best = v; pairIdx = i; } }); });
if (pairIdx < 0 && PAIRS.length) pairIdx = 0;
PAIRS.forEach((p, i) => { const o = document.createElement("option"); o.value = i; o.textContent = label(BY[p.p]) + " / " + label(BY[p.f]); $("pair").append(o); });
if (!PAIRS.length) { const o = document.createElement("option"); o.textContent = "no person / forklift pair"; $("pair").append(o); }
$("pair").value = String(pairIdx);
S.play_rates.forEach(r => { const o = document.createElement("option"); o.value = r; o.textContent = r + "x"; $("rate").append(o); });
$("rate").value = "1";

/* display sliders */
const SL = [["d_p_m", "d_p (m)", 1], ["d_pc_m", "d_pc (m)", 1], ["tau_s", "tau (s)", 1], ["g_max_frames", "g_max (frames)", 0], ["e_fturn_deg_s", "e_fturn (deg/s)", 1]];
SL.forEach(([k, name, d]) => {
  const l = document.createElement("label"), r = S.ranges[k], inp = document.createElement("input"), v = document.createElement("span");
  inp.type = "range"; inp.min = r[0]; inp.max = r[1]; inp.step = r[2]; inp.value = disp[k]; inp.id = "s_" + k; v.textContent = disp[k].toFixed(d);
  inp.addEventListener("input", () => { disp[k] = parseFloat(inp.value); v.textContent = disp[k].toFixed(d); timelineDirty = true; draw(); });
  l.append(name, inp, v); $("controls2").append(l);
});
const reset = document.createElement("button"); reset.textContent = "reset to pre-registered values";
reset.addEventListener("click", () => { SL.forEach(([k, , d]) => { disp[k] = FROZEN[k]; const i = $("s_" + k); i.value = FROZEN[k]; i.nextSibling.textContent = FROZEN[k].toFixed(d); }); timelineDirty = true; draw(); });
$("controls2").append(reset);
const tip = document.createElement("span"); tip.style.color = "var(--muted)"; tip.textContent = "Display settings only: nothing is written to any configuration.";
$("controls2").append(tip);

function turnAt(o, k) {
  const i = k - o.s0; if (i < 0 || i >= o.st.length || o.turn === undefined) return null;
  if (disp.e_fturn_deg_s === FROZEN.e_fturn_deg_s) return o.turn[i];
  if (o.turn[i] === "-") return "-";
  const yr = o.yr[i]; return yr === null ? "U" : (yr > disp.e_fturn_deg_s ? "T" : "F");
}

/* floor view */
const cv = $("floor"), ctx = cv.getContext("2d");
let view = {cx: 0, cy: 0, s: 20}, frame = 0, playing = false, timelineDirty = true;
function bounds() {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  OBJ.forEach(o => { for (let i = 0; i < o.st.length; i++) { const x = o.x[i] !== null ? o.x[i] : o.ax[i], y = o.y[i] !== null ? o.y[i] : o.ay[i];
    if (x === null || y === null) continue; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); } });
  if (!isFinite(x0)) { x0 = -5; x1 = 5; y0 = -5; y1 = 5; }
  return [x0 - 3, x1 + 3, y0 - 3, y1 + 3];
}
function fit() { const [x0, x1, y0, y1] = bounds(), w = cv.clientWidth, h = cv.clientHeight; view.cx = (x0 + x1) / 2; view.cy = (y0 + y1) / 2;
  view.s = Math.max(2, Math.min(w / (x1 - x0), h / (y1 - y0))); }
function resize() { const r = window.devicePixelRatio || 1; cv.width = cv.clientWidth * r; cv.height = cv.clientHeight * r;
  tl.width = tl.clientWidth * r; tl.height = tl.clientHeight * r; timelineDirty = true; }
const W2S = (x, y) => [cv.clientWidth / 2 + (x - view.cx) * view.s, cv.clientHeight / 2 - (y - view.cy) * view.s];
function rectPts(x, y, yaw, l, w, grow) {
  const c = Math.cos(yaw), s = Math.sin(yaw), a = l / 2, b = w / 2, out = [];
  if (!grow) { [[a, b], [-a, b], [-a, -b], [a, -b]].forEach(([u, v]) => out.push([x + c * u - s * v, y + s * u + c * v])); return out; }
  const corners = [[a, b, 0], [-a, b, Math.PI / 2], [-a, -b, Math.PI], [a, -b, 1.5 * Math.PI]];
  corners.forEach(([u, v, start]) => { for (let j = 0; j <= 8; j++) { const t = start + j * Math.PI / 16, pu = u + grow * Math.cos(t), pv = v + grow * Math.sin(t);
    out.push([x + c * pu - s * pv, y + s * pu + c * pv]); } });
  return out;
}
function poly(pts, stroke, fill, dash, width) {
  ctx.beginPath(); pts.forEach((p, i) => { const q = W2S(p[0], p[1]); if (i) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]); }); ctx.closePath();
  ctx.setLineDash(dash || []); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width || 1.5; ctx.stroke(); }
  ctx.setLineDash([]);
}
function circle(x, y, r, stroke, fill, dash, width) {
  const q = W2S(x, y); ctx.beginPath(); ctx.arc(q[0], q[1], Math.max(1, r * view.s), 0, 2 * Math.PI); ctx.setLineDash(dash || []);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width || 1.5; ctx.stroke(); } ctx.setLineDash([]);
}
function text(x, y, t, color, dx, dy) { const q = W2S(x, y); ctx.fillStyle = color; ctx.font = "12px system-ui,sans-serif"; ctx.fillText(t, q[0] + (dx || 0), q[1] + (dy || 0)); }
function arrow(x, y, vx, vy, color) {
  const a = W2S(x, y), b = W2S(x + vx, y + vy); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0]); ctx.beginPath(); ctx.moveTo(b[0], b[1]);
  ctx.lineTo(b[0] - 8 * Math.cos(ang - 0.4), b[1] - 8 * Math.sin(ang - 0.4)); ctx.lineTo(b[0] - 8 * Math.cos(ang + 0.4), b[1] - 8 * Math.sin(ang + 0.4)); ctx.fill();
}
function nearestOnFootprint(px, py, fx, fy, yaw) {
  if (yaw === null) { const d = Math.hypot(px - fx, py - fy) || 1, rr = Math.hypot(FL, FW) / 2; return [fx + (px - fx) / d * rr, fy + (py - fy) / d * rr]; }
  const c = Math.cos(yaw), s = Math.sin(yaw), dx = px - fx, dy = py - fy, a = FL / 2, b = FW / 2;
  let u = c * dx + s * dy, v = -s * dx + c * dy;
  if (Math.abs(u) <= a && Math.abs(v) <= b) { if (a - Math.abs(u) < b - Math.abs(v)) u = Math.sign(u || 1) * a; else v = Math.sign(v || 1) * b; }
  else { u = Math.max(-a, Math.min(a, u)); v = Math.max(-b, Math.min(b, v)); }
  return [fx + c * u - s * v, fy + s * u + c * v];
}
function grid() {
  const w = cv.clientWidth, h = cv.clientHeight, step = view.s >= 6 ? 1 : view.s >= 1.5 ? 5 : 10;
  const x0 = view.cx - w / 2 / view.s, x1 = view.cx + w / 2 / view.s, y0 = view.cy - h / 2 / view.s, y1 = view.cy + h / 2 / view.s;
  ctx.strokeStyle = css("--grid"); ctx.lineWidth = 1; ctx.beginPath();
  for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) { const q = W2S(x, 0)[0]; ctx.moveTo(q, 0); ctx.lineTo(q, h); }
  for (let y = Math.ceil(y0 / step) * step; y <= y1; y += step) { const q = W2S(0, y)[1]; ctx.moveTo(0, q); ctx.lineTo(w, q); }
  ctx.stroke();
  const nice = [1, 2, 5, 10, 20, 50].find(m => m * view.s >= 80) || 50, bx = 16, by = h - 18;
  ctx.strokeStyle = css("--fg"); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + nice * view.s, by); ctx.moveTo(bx, by - 5); ctx.lineTo(bx, by + 5);
  ctx.moveTo(bx + nice * view.s, by - 5); ctx.lineTo(bx + nice * view.s, by + 5); ctx.stroke();
  ctx.fillStyle = css("--fg"); ctx.font = "12px system-ui,sans-serif"; ctx.fillText(nice + " m", bx + 4, by - 8);
  ctx.fillStyle = css("--muted"); ctx.fillText("grid " + step + " m, world frame (x right, y up)", bx, 16);
}
function pos(o, k) { const x = at(o, k, "x"), y = at(o, k, "y"); return x === null ? null : [x, y]; }
function vel(o, k) { const vx = at(o, k, "vx"), vy = at(o, k, "vy"); return vx === null ? null : [vx, vy]; }

function drawFloor() {
  const r = window.devicePixelRatio || 1; ctx.setTransform(r, 0, 0, r, 0, 0); ctx.clearRect(0, 0, cv.clientWidth, cv.clientHeight);
  const pair = PAIRS[pairIdx];
  if ($("follow").checked && pair) { const a = pos(BY[pair.p], frame), b = pos(BY[pair.f], frame); if (a && b) { view.cx = (a[0] + b[0]) / 2; view.cy = (a[1] + b[1]) / 2; } }
  grid();
  const k = frame, cP = css("--person"), cF = css("--fork"), cO = css("--other"), tau = disp.tau_s;
  OBJ.forEach(o => {
    const st = at(o, k, "st"); if (st === null || st === "-") return;
    const col = o.cls === "person" ? cP : o.cls === "forklift" ? cF : cO;
    const p = pos(o, k);
    if (!p) { const ax = at(o, k, "ax"), ay = at(o, k, "ay"); if (ax === null) return;
      if (st === "L") { circle(ax, ay, o.cls === "person" ? R : 0.6, col, null, [3, 4], 1); text(ax, ay, label(o) + " lost", col, 8, -8); }
      else { const q = W2S(ax, ay); ctx.strokeStyle = cO; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(q[0] - 5, q[1] - 5); ctx.lineTo(q[0] + 5, q[1] + 5);
        ctx.moveTo(q[0] + 5, q[1] - 5); ctx.lineTo(q[0] - 5, q[1] + 5); ctx.stroke(); text(ax, ay, label(o) + " ineligible frame", cO, 8, -8); }
      return; }
    const v = vel(o, k), pred = st === "P", fill = pred ? null : col + "33", dash = pred ? [6, 4] : [];
    if (o.cls === "person") {
      circle(p[0], p[1], R, col, fill, dash, 2);
      if (v && tau > 0) circle(p[0] + v[0] * tau, p[1] + v[1] * tau, R, col, null, [2, 3], 1);
    } else {
      const box = at(o, k, "box"); if (box) poly(box, col, null, [4, 3], 1);
      if (o.cls === "forklift") {
        const yaw = at(o, k, "yaw");
        if (yaw === null) circle(p[0], p[1], Math.hypot(FL, FW) / 2, col, fill, dash, 2); else poly(rectPts(p[0], p[1], yaw, FL, FW, 0), col, fill, dash, 2);
        const ring = (d, c2) => { if (yaw === null) circle(p[0], p[1], Math.hypot(FL, FW) / 2 + d, c2, null, [1, 3], 1); else poly(rectPts(p[0], p[1], yaw, FL, FW, d), c2, null, [1, 3], 1); };
        if (disp.d_p_m > 0) ring(disp.d_p_m, css("--ring-p")); if (disp.d_pc_m > 0) ring(disp.d_pc_m, css("--ring-pc"));
        if (v && tau > 0) { const gx = p[0] + v[0] * tau, gy = p[1] + v[1] * tau;
          if (yaw === null) circle(gx, gy, Math.hypot(FL, FW) / 2, col, null, [2, 3], 1); else poly(rectPts(gx, gy, yaw, FL, FW, 0), col, null, [2, 3], 1); }
      }
    }
    if (v) { arrow(p[0], p[1], v[0], v[1], col); }
    const sp = at(o, k, "speed");
    text(p[0], p[1], label(o) + (pred ? " pred" : "") + (sp !== null ? "  " + sp.toFixed(2) + " m/s" : ""), col, 10, 14);
  });
  PAIRS.forEach((pr, i) => {
    const c = pr.c[k]; if (c === null) return;
    if (i !== pairIdx && !($("allpairs").checked && c <= disp.d_p_m)) return;
    const pp = pos(BY[pr.p], k), fp = pos(BY[pr.f], k); if (!pp || !fp) return;
    const yaw = at(BY[pr.f], k, "yaw"), q = nearestOnFootprint(pp[0], pp[1], fp[0], fp[1], yaw);
    const d = Math.hypot(pp[0] - q[0], pp[1] - q[1]) || 1, e = [pp[0] + (q[0] - pp[0]) / d * R, pp[1] + (q[1] - pp[1]) / d * R];
    const a = W2S(q[0], q[1]), b = W2S(e[0], e[1]); ctx.strokeStyle = css("--fg"); ctx.lineWidth = i === pairIdx ? 2 : 1; ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    ctx.fillStyle = css("--fg"); ctx.font = (i === pairIdx ? "600 " : "") + "12px system-ui,sans-serif"; ctx.fillText(c.toFixed(2) + " m", (a[0] + b[0]) / 2 + 6, (a[1] + b[1]) / 2 - 6);
  });
}

function side() {
  const k = frame, t = FR.t[k], pair = PAIRS[pairIdx];
  let h = "<p><b>frame " + k + "</b> &middot; t = " + (t === null ? "n/a" : t.toFixed(3) + " s") + " &middot; " + (FR.el[k] === "1" ? "eligible" : "ineligible") + "</p>";
  if (pair) { const f = BY[pair.f], tr = turnAt(f, k);
    h += "<p>pair " + label(BY[pair.p]) + " / " + label(f) + "<br>clearance " + fmt(pair.c[k], 3) + " m<br>forklift yaw rate " + fmt(at(f, k, "yr"), 2) +
      " deg/s<br>forklift_turning: " + (tr === null ? "outside span" : TURN_TEXT[tr]) + "</p>"; }
  h += "<table><tr><th>object</th><th>state</th><th>m/s</th></tr>";
  OBJ.forEach(o => { const st = at(o, k, "st"); if (st === null || st === "-") return;
    h += "<tr><td>" + label(o) + " " + o.cls + "</td><td>" + STATE_TEXT[st] + "</td><td>" + fmt(at(o, k, "speed"), 2) + "</td></tr>"; });
  h += "</table><p style='margin-top:10px;color:var(--muted)'><span class='sw' style='background:var(--person)'></span>person disc r = " + R +
    " m &middot; <span class='sw' style='background:var(--fork)'></span>forklift prior " + FL + " &times; " + FW +
    " m (solid), dataset 3D box footprint (dashed). Dashed outline: predicted oracle point. Dotted rings: d_p, d_pc (clearance). Thin dashed shapes: " +
    "constant-velocity position at t + tau. Arrows: velocity (length = 1 s of travel).</p>";
  $("side").innerHTML = h;
  $("flabel").textContent = "frame " + k + " / " + (N - 1);
}

/* timeline */
const tl = $("timeline"), tx = tl.getContext("2d"), off = document.createElement("canvas");
const PANELS = [["clearance (m)", 0.3], ["speed (m/s)", 0.22], ["forklift yaw rate (deg/s)", 0.24], ["oracle state", 0.24]];
function panelRects() { const h = tl.clientHeight, top = 6; let y = top; return PANELS.map(([n, f]) => { const ph = (h - top - 6) * f; const r = [y, ph - 6, n]; y += ph; return r; }); }
const XL = 54;
const xOf = k => XL + (tl.clientWidth - XL - 10) * k / Math.max(1, N - 1);
function series(c, arr, y0, ph, lo, hi, color) {
  c.strokeStyle = color; c.lineWidth = 1.2; c.beginPath(); let pen = false;
  for (let k = 0; k < N; k++) { const v = arr(k); if (v === null) { pen = false; continue; } const y = y0 + ph - (Math.min(hi, Math.max(lo, v)) - lo) / (hi - lo) * ph;
    if (pen) c.lineTo(xOf(k), y); else c.moveTo(xOf(k), y); pen = true; }
  c.stroke();
}
function hline(c, y0, ph, lo, hi, v, color, name) {
  if (v < lo || v > hi) return; const y = y0 + ph - (v - lo) / (hi - lo) * ph; c.strokeStyle = color; c.setLineDash([4, 3]); c.beginPath(); c.moveTo(XL, y);
  c.lineTo(tl.clientWidth - 10, y); c.stroke(); c.setLineDash([]); c.fillStyle = color; c.fillText(name, tl.clientWidth - 90, y - 3);
}
function renderTimeline() {
  const r = window.devicePixelRatio || 1; off.width = tl.width; off.height = tl.height; const c = off.getContext("2d"); c.setTransform(r, 0, 0, r, 0, 0);
  c.clearRect(0, 0, tl.clientWidth, tl.clientHeight); c.font = "11px system-ui,sans-serif";
  const pair = PAIRS[pairIdx], P = pair ? BY[pair.p] : null, F = pair ? BY[pair.f] : null, rects = panelRects();
  rects.forEach(([y0, ph, n]) => { c.strokeStyle = css("--line"); c.strokeRect(XL, y0, tl.clientWidth - XL - 10, ph); c.fillStyle = css("--muted"); c.fillText(n, XL + 4, y0 + 11); });
  if (pair) {
    let [y0, ph] = rects[0]; let hi = 0.5; pair.c.forEach(v => { if (v !== null) hi = Math.max(hi, Math.min(10, v)); }); hi = Math.max(hi, disp.d_p_m + 0.5); const lo = Math.min(0, ...pair.c.filter(v => v !== null));
    series(c, k => pair.c[k], y0, ph, lo, hi, css("--fg")); hline(c, y0, ph, lo, hi, disp.d_p_m, css("--ring-p"), "d_p " + disp.d_p_m.toFixed(1)); hline(c, y0, ph, lo, hi, disp.d_pc_m, css("--ring-pc"), "d_pc " + disp.d_pc_m.toFixed(1));
    hline(c, y0, ph, lo, hi, 0, css("--muted"), "0"); c.fillStyle = css("--muted"); c.fillText(hi.toFixed(1), 4, y0 + 10); c.fillText(lo.toFixed(1), 4, y0 + ph);
    [y0, ph] = rects[1]; let smax = 0.5; [P, F].forEach(o => o.speed.forEach(v => { if (v !== null) smax = Math.max(smax, v); }));
    series(c, k => at(P, k, "speed"), y0, ph, 0, smax, css("--person")); series(c, k => at(F, k, "speed"), y0, ph, 0, smax, css("--fork"));
    c.fillStyle = css("--muted"); c.fillText(smax.toFixed(1), 4, y0 + 10); c.fillText("0", 4, y0 + ph);
    [y0, ph] = rects[2]; let ymax = Math.max(disp.e_fturn_deg_s * 2, 10); F.yr.forEach(v => { if (v !== null) ymax = Math.max(ymax, Math.min(180, v)); });
    const shade = {T: css("--turn-t"), F: css("--turn-f"), U: css("--turn-u")};
    for (let k = 0; k < N; k++) { const s = turnAt(F, k); if (!s || s === "-") continue; c.fillStyle = shade[s]; c.fillRect(xOf(k), y0, Math.max(1, xOf(k + 1) - xOf(k)), ph); }
    series(c, k => at(F, k, "yr"), y0, ph, 0, ymax, css("--fork")); hline(c, y0, ph, 0, ymax, disp.e_fturn_deg_s, css("--ring-p"), "e_fturn " + disp.e_fturn_deg_s.toFixed(1));
    c.fillStyle = css("--muted"); c.fillText(ymax.toFixed(0), 4, y0 + 10); c.fillText("0", 4, y0 + ph);
    [y0, ph] = rects[3]; const lane = ph / 3, col = {V: css("--fg"), P: css("--ring-p"), L: css("--ring-pc"), I: css("--other")};
    [[P, 0], [F, 1]].forEach(([o, j]) => { const y = y0 + 4 + j * lane; c.fillStyle = css("--muted"); c.fillText(label(o), 4, y + lane * 0.6);
      for (let k = 0; k < N; k++) { const s = at(o, k, "st"); if (!s || s === "-") continue; c.fillStyle = col[s]; c.fillRect(xOf(k), y, Math.max(1, xOf(k + 1) - xOf(k)), lane - 6); }
      o.runs.forEach(([s0, m, e]) => { if (e > disp.g_max_frames) { c.strokeStyle = css("--ring-pc"); c.lineWidth = 1.5; c.strokeRect(xOf(s0), y - 1, Math.max(2, xOf(s0 + m) - xOf(s0)), lane - 4); } }); });
    const y = y0 + 4 + 2 * lane; c.fillStyle = css("--muted"); c.fillText("frame", 4, y + lane * 0.6);
    for (let k = 0; k < N; k++) if (FR.el[k] === "0") { c.fillStyle = css("--other"); c.fillRect(xOf(k), y, Math.max(1, xOf(k + 1) - xOf(k)), lane - 6); }
  } else { c.fillStyle = css("--muted"); c.fillText("no person / forklift pair in this recording", XL + 10, 40); }
  timelineDirty = false;
}
function drawTimeline() {
  if (timelineDirty) renderTimeline();
  const r = window.devicePixelRatio || 1; tx.setTransform(1, 0, 0, 1, 0, 0); tx.clearRect(0, 0, tl.width, tl.height); tx.drawImage(off, 0, 0); tx.setTransform(r, 0, 0, r, 0, 0);
  tx.strokeStyle = css("--fg"); tx.lineWidth = 1; tx.beginPath(); tx.moveTo(xOf(frame), 0); tx.lineTo(xOf(frame), tl.clientHeight); tx.stroke();
}
function draw() { drawFloor(); side(); drawTimeline(); $("frame").value = frame; }

/* interaction */
$("frame").max = N - 1;
$("frame").addEventListener("input", e => { frame = parseInt(e.target.value, 10); draw(); });
$("pair").addEventListener("change", e => { pairIdx = parseInt(e.target.value, 10); timelineDirty = true; draw(); });
["follow", "allpairs"].forEach(id => $(id).addEventListener("change", draw));
$("fit").addEventListener("click", () => { $("follow").checked = false; fit(); draw(); });
tl.addEventListener("click", e => { const b = tl.getBoundingClientRect(), x = e.clientX - b.left;
  frame = Math.max(0, Math.min(N - 1, Math.round((x - XL) / (tl.clientWidth - XL - 10) * (N - 1)))); draw(); });
let drag = null;
cv.addEventListener("mousedown", e => { drag = [e.clientX, e.clientY, view.cx, view.cy]; $("follow").checked = false; });
window.addEventListener("mouseup", () => { drag = null; });
window.addEventListener("mousemove", e => { if (!drag) return; view.cx = drag[2] - (e.clientX - drag[0]) / view.s; view.cy = drag[3] + (e.clientY - drag[1]) / view.s; drawFloor(); });
cv.addEventListener("wheel", e => { e.preventDefault(); view.s = Math.max(1, Math.min(400, view.s * (e.deltaY < 0 ? 1.15 : 1 / 1.15))); drawFloor(); }, {passive: false});
let last = null, acc = 0;
function tick(ts) { if (!playing) { last = null; return; } if (last !== null) { acc += (ts - last) / 1000 * parseFloat($("rate").value);
    const steps = Math.floor(acc / DT); if (steps > 0) { acc -= steps * DT; frame = Math.min(N - 1, frame + steps); draw(); if (frame === N - 1) { playing = false; $("play").textContent = "Play"; } } }
  last = ts; requestAnimationFrame(tick); }
$("play").addEventListener("click", () => { playing = !playing; $("play").textContent = playing ? "Pause" : "Play"; if (playing) { if (frame >= N - 1) frame = 0; acc = 0; requestAnimationFrame(tick); } });
window.addEventListener("keydown", e => { if (e.target.tagName === "SELECT") return;
  if (e.key === " ") { e.preventDefault(); $("play").click(); } else if (e.key === "ArrowRight") { frame = Math.min(N - 1, frame + 1); draw(); }
  else if (e.key === "ArrowLeft") { frame = Math.max(0, frame - 1); draw(); } });
window.addEventListener("resize", () => { resize(); draw(); });
$("note").textContent = "Oracle points were built at the pre-registered g_max = " + FROZEN.g_max_frames + " eligible frames; the g_max slider only outlines (red) " +
  "not-visible runs longer than the slider value. Timeline shading: forklift_turning true (amber), false (green), unknown (grey), at the e_fturn slider value " +
  "(T20.2, w_turn = " + S.w_turn_s + " s). Speeds and velocities: the S4 estimate (w_v = " + S.w_v_s + " s). Clearance: the S4 signed footprint distance " +
  "between the forklift prior footprint and the person disc. Click the timeline to jump; drag and scroll the floor view to pan and zoom.";
resize(); fit(); draw();
"""
