"""V-01 page data for one recording, from simulator truth through the T-18 adapters and the S4 functions, unchanged.

- Oracle points (T17-T19, T20.1): `adapters.oracle_truth.camera_tracks` at the frozen g_max, with its per-frame outcomes
  (tracked -> "V" visible; predicted -> "P" not visible, predicted point; lost -> "L" not visible, no point;
  no_point_ineligible -> "I" ineligible frame). Frames outside the object's visible span are not drawn.
- Positions, speeds, velocity and forklift yaw (T8.2 as corrected by T9.1): the S4 builder's per-track object states
  (`SubstrateBuilder._object_states`, simulator-truth positions), the same code an S4 build runs. No POW, pair series,
  exposure profile or activity segment is built, and nothing is written: the in-memory S3 artifact exists only because
  the object-state code reads its track points.
- Clearance: the S4 signed footprint distance, applied as the S4 builder applies it to a pair-frame (`geometry.clearance`
  on the prior rectangle; `geometry.disc_clearance` on the circumscribed disc when the forklift yaw is null, T8.2), on
  every eligible frame where both objects have a position.
- forklift_turning (T20.2): `evaluation.strata.forklift_turning`, a report-time function (Owner decision, V-01 session).
- Not-visible runs (T18 amendment 3, T19, T20.1): `oracle_truth.not_visible_spans` / `not_visible_runs`.
- The dataset 3D box footprint (dashed outline) is the convex hull of the floor projection of the dataset box corners.

Nothing here is a result, metric, flag, label or episode. Values used for drawing only (box outline, truth position of a
lost or ineligible object-frame) are rounded to 0.1 mm; measured values are kept at full precision.
"""
from __future__ import annotations

import math
from typing import Any, Hashable

from rq1.adapters import oracle_truth as ot
from rq1.evaluation.strata import forklift_turning
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.schema.errors import ContractError
from rq1.substrate import builder, geometry, oracle
from rq1.substrate.surrogate import hull

from . import settings

Row = dict[str, Any]
STATE = {"tracked": "V", "predicted": "P", "lost": "L", "no_point_ineligible": "I"}
TURN = {"true": "T", "false": "F", "unknown": "U"}
ORACLE_CONFIG = {"source": "simulator_truth", "rule": "Appendix T T17, T18, T19, T20.1", "g_max": settings.G_MAX, "use": "V-01 display only"}


def _r(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)


def priors(fork_prior: tuple[float, float], classes: set[str] = frozenset({"person", "forklift"})) -> tuple[dict[str, Row], dict[str, str]]:
    """Footprint priors (section 4.2). Non-person classes other than forklift (SmartSpaces pallet_truck) get the forklift
    prior only so that their object states can be computed; they are drawn by their dataset box and pair with nobody."""
    length, width = fork_prior
    person = {"class": "person", "shape": "disc", "radius_m": settings.PERSON_RADIUS_M, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
    fork = {"class": "forklift", "shape": "oriented_rect", "length_m": length, "width_m": width, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
    out = {"person": person, "forklift": fork}
    for cls in sorted(set(classes) - {"person", "forklift"}):
        out[cls] = dict(fork, **{"class": cls})
    return out, {k: core.make_id("fpp", p) for k, p in out.items()}


def _footprint(o: ot.Obs) -> list[list[float]] | None:
    corners = o.corners() if callable(o.corners) else o.corners
    if corners is None:
        return None
    poly = hull([(float(c[0]), float(c[1])) for c in corners])
    return [[_r(x), _r(y)] for x, y in poly] if len(poly) >= 3 else None


def build(header: Row, s1: dict[str, list[Row]], frames: list[dict[Hashable, ot.Obs]], classes: dict[Hashable, str], calibration: Row,
          fork_prior: tuple[float, float]) -> Row:
    """Page data for one recording. `frames[k]`: object key -> observation on decoded frame k (the T-18 adapters);
    `s1`: the recording's S1 tables (frame, coverage_segment, decode_summary)."""
    recording = s1["frame"][0]["recording_id"]
    frame_rows = sorted((f for f in s1["frame"] if f["recording_id"] == recording), key=lambda f: f["decode_seq"])
    n = len(frame_rows)
    if [f["decode_seq"] for f in frame_rows] != list(range(n)) or len(frames) != n:
        raise ContractError("ERR-SPEC", f"{recording}: {len(frames)} truth frames for {n} decoded frames")
    seq_to_index = {f["decode_seq"]: f["frame_index"] for f in frame_rows}
    index_to_seq = {i: k for k, i in seq_to_index.items() if i is not None}
    ineligible = frozenset(k for k, i in seq_to_index.items() if i is None)

    outcomes: dict = {}
    tracks, _ = ot.camera_tracks(calibration, frames, settings.G_MAX, ineligible, outcomes=outcomes)
    truth, positions = ot.s3_truth(tracks, classes, seq_to_index)
    spec = Spec("S3", settings.CONTRACT, "viewer", "viewer", (core.make_id("orc", ORACLE_CONFIG),), (), {})
    s3 = oracle.OracleTrackSource().tracks(recording, truth, frame_rows, spec)
    key_of = {str(k): k for k in tracks}
    local_key = {t["local_id"]: key_of[t["physical_identity_id"]] for t in truth}

    eligible = {f["frame_index"]: f for f in frame_rows if f["eligible"]}
    own = [c for c in s1["coverage_segment"] if c.get("recording_id") == recording]
    coverage = [c for c in s1["coverage_segment"] if c["timeline_id"] == own[0]["timeline_id"] and c["camera_id"] == own[0]["camera_id"]]
    summary = next(d for d in s1["decode_summary"] if d["recording_id"] == recording)
    size = (summary["width_px"], summary["height_px"])
    prior_rows, prior_ids = priors(fork_prior, set(classes.values()))
    cfg = builder.SubstrateConfig(settings.G_MAX, settings.V_MIN, settings.W_V, settings.TAU_S, {"forklift"}, prior_rows, prior_ids, {}, settings.V_PART)
    points = {(p["track_nk"][1], p["frame_index"]): p for p in s3.tables["track_point"]}
    spans = ot.not_visible_spans(frames, ineligible)
    run_lengths = ot.not_visible_runs(frames, ineligible)
    s4 = builder.SubstrateBuilder()

    objects, states = [], {}
    for track in sorted(s3.tables["track"], key=lambda t: t["track_local_id"]):
        local, cls = track["track_local_id"], track["class"]
        key = local_key[local]
        rows = {r["frame_index"]: r for r in s4._object_states(track, local, points, positions, None, eligible, coverage, size, cfg)}
        states[local] = rows
        span = sorted(k for (obj, k) in outcomes if obj == key)
        first, last = span[0], span[-1]
        o: Row = {"id": local, "key": str(key), "cls": cls, "s0": first, "st": "", "x": [], "y": [], "vx": [], "vy": [], "speed": [], "ax": [], "ay": [],
                  "runs": [[s, m, e] for (s, m), e in zip(spans.get(key, []), run_lengths.get(key, []))]}
        if cls != "person":
            o.update(yaw=[], box=[])
        turning = {}
        if cls == "forklift":
            o.update(yr=[], turn="")
            turning = forklift_turning(list(rows.values()), eligible, coverage, settings.W_TURN_S, settings.E_FTURN_RAD_S)
        for k in range(first, last + 1):
            state = STATE[outcomes[(key, k)]] if (key, k) in outcomes else "-"
            row = rows.get(seq_to_index[k]) if seq_to_index[k] is not None else None
            obs = frames[k].get(key)
            o["st"] += state
            has = row is not None and row["x_m"] is not None
            o["x"].append(row["x_m"] if has else None)
            o["y"].append(row["y_m"] if has else None)
            v = row.get("_v") if row is not None else None
            o["vx"].append(v[0] if v else None)
            o["vy"].append(v[1] if v else None)
            o["speed"].append(row["speed_mps"] if row is not None else None)
            o["ax"].append(_r(obs.xy[0]) if (obs is not None and not has) else None)  # truth position, drawn for L / I only
            o["ay"].append(_r(obs.xy[1]) if (obs is not None and not has) else None)
            if cls != "person":
                o["yaw"].append(row["yaw_rad"] if row is not None else None)
                o["box"].append(_footprint(obs) if obs is not None else None)
            if cls == "forklift":
                t = turning.get(seq_to_index[k]) if seq_to_index[k] is not None else None
                o["yr"].append(None if t is None or t.yaw_rate_rad_s is None else math.degrees(t.yaw_rate_rad_s))
                o["turn"] += "-" if t is None else TURN[t.state]
        objects.append(o)

    length, width = fork_prior
    radius = settings.PERSON_RADIUS_M
    pairs = []
    persons = [o for o in objects if o["cls"] == "person"]
    forks = [o for o in objects if o["cls"] == "forklift"]
    for p in persons:
        for f in forks:
            c: list[float | None] = [None] * n
            for i, k in sorted(index_to_seq.items()):
                ps, fs = states[p["id"]].get(i), states[f["id"]].get(i)
                if ps is None or fs is None or ps["x_m"] is None or fs["x_m"] is None:
                    continue
                person_xy, fork_xy, yaw = (ps["x_m"], ps["y_m"]), (fs["x_m"], fs["y_m"]), fs["yaw_rad"]
                if yaw is None:  # T8.2: unknown yaw -> circumscribed disc (as the S4 builder's pair-frame)
                    c[k] = geometry.disc_clearance(person_xy, radius, fork_xy, geometry.circumscribed_radius(length, width))
                else:
                    c[k] = geometry.clearance(person_xy, radius, fork_xy, yaw, length, width)
            pairs.append({"p": p["id"], "f": f["id"], "c": c})

    return {
        "header": dict(header, n_frames=n),
        "settings": {"banner": settings.BANNER, "display": dict(settings.DISPLAY), "ranges": {k: list(v) for k, v in settings.RANGES.items()},
                     "person_radius_m": radius, "fork_prior_m": [length, width], "v_min_mps": settings.V_MIN, "w_v_s": settings.W_V,
                     "w_turn_s": settings.W_TURN_S, "play_rates": list(settings.PLAY_RATES)},
        "frames": {"t": [f["t_resolved_s"] for f in frame_rows], "el": "".join("1" if f["eligible"] else "0" for f in frame_rows),
                   "dt": summary.get("delta_nom_s")},
        "objects": objects,
        "pairs": pairs,
    }
