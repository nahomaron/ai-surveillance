"""T25.1 track stitching (Appendix T, contract E-1.2.26; D-58): joins track fragments of one physical object.

S3, detector and other non-oracle track sources only (T25.1 f). Off unless all four parameters are present (T25.0).

- `params_from(package)`: the four tracker-package parameters, all or none (T25.1 a).
- `links(tracks, frames, coverage, params, floor)`: the accepted links, in acceptance order (T25.1 b-d).
  - t_A is A's last `tracked` point, t_B is B's first `tracked` point (frame timeline time `t_tl_s`).
  - (A, B) is a candidate iff same class, 0 < t_B - t_A <= T_s, no point of A after t_A in state `tracked` or `predicted`,
    the tracks do not overlap in time (every point of A precedes every point of B), and no coverage segment of state
    not_recorded, gap_unobserved or unusable lies between the two endpoint frames (the T8.1 test, `pows._break_between`).
  - Gate: floor (both endpoint points have a floor position in `floor`) or image (otherwise), with the T25.1 (c) costs.
  - Assignment: ascending cost, then ascending t_B - t_A, then JCS of [A, B]; one successor and one predecessor per track.
- `chains`, `stitch_ids`: chains of accepted links; `stitch_id` = id("sti", [member track natural keys in chain order])
  (AR-69).
- `apply(s3, stitch_of, spec)`: the S3 artifact with `stitch_id` on every track point; nothing else changes (T25.1 e).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rq1.ids import core
from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.substrate import pows

Row = dict[str, Any]
EPS = 1e-9
KEYS = ("stitch_max_gap_s", "stitch_v_max_mps", "stitch_r_gate_m", "stitch_img_gate")
LIVE = {"tracked", "predicted"}


@dataclass(frozen=True)
class StitchParams:
    max_gap_s: float  # T_s
    v_max_mps: dict  # class -> v_max
    r_gate_m: float  # r_g
    img_gate: float  # k_img

    def as_record(self) -> dict:
        return {"stitch_max_gap_s": self.max_gap_s, "stitch_v_max_mps": dict(sorted(self.v_max_mps.items())), "stitch_r_gate_m": self.r_gate_m,
                "stitch_img_gate": self.img_gate}


@dataclass(frozen=True)
class Track:
    track_id: str
    cls: str
    points: list  # [(frame_index, state, [x1, y1, x2, y2])]


def params_from(package: dict) -> StitchParams | None:
    present = [k for k in KEYS if package.get(k) is not None]
    if not present:
        return None
    if len(present) != len(KEYS):
        raise ContractError("ERR-SPEC", f"T25.1 (a): the stitching parameters are all present or none; missing {sorted(set(KEYS) - set(present))}")
    p = StitchParams(float(package["stitch_max_gap_s"]), {str(k): float(v) for k, v in package["stitch_v_max_mps"].items()},
                     float(package["stitch_r_gate_m"]), float(package["stitch_img_gate"]))
    if not p.max_gap_s > 0 or not p.r_gate_m >= 0 or not p.img_gate > 0 or not p.v_max_mps or any(not v > 0 for v in p.v_max_mps.values()):
        raise ContractError("ERR-SPEC", "T25.1 (a): T_s > 0, r_g >= 0, k_img > 0 and v_max > 0 per class required")
    return p


def require_non_oracle(track_config_id: str) -> None:
    """T25.1 (f): stitching is off for oracle tracks (S3 configuration prefix `orc`)."""
    if track_config_id.split("_", 1)[0] == "orc":
        raise ContractError("ERR-SPEC", "T25.1 (f): track stitching is off for oracle tracks")


def _centre(box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


def _diag(box) -> float:
    return math.hypot(box[2] - box[0], box[3] - box[1])


def _ends(track: Track):
    pts = sorted(track.points, key=lambda p: p[0])
    tracked = [p for p in pts if p[1] == "tracked"]
    if not tracked:
        return None
    return {"first_point": pts[0][0], "last_point": pts[-1][0], "a": tracked[-1], "b": tracked[0],
            "live_after_a": any(p[0] > tracked[-1][0] and p[1] in LIVE for p in pts)}


def links(tracks: list[Track], frames: dict[int, Row], coverage: list[Row], params: StitchParams,
          floor: dict[tuple[str, int], tuple[float, float]]) -> list[dict]:
    ends = {t.track_id: _ends(t) for t in tracks}
    cls = {t.track_id: t.cls for t in tracks}
    cands = []
    for a in sorted(ends):
        ea = ends[a]
        if ea is None or ea["live_after_a"]:
            continue
        fa, _, box_a = ea["a"]
        for b in sorted(ends):
            eb = ends[b]
            if b == a or eb is None or cls[a] != cls[b]:
                continue
            fb, _, box_b = eb["b"]
            if not ea["last_point"] < eb["first_point"]:  # overlapping tracks are never stitched
                continue
            dt = frames[fb]["t_tl_s"] - frames[fa]["t_tl_s"]
            if not (dt > EPS and dt <= params.max_gap_s + EPS):
                continue
            if pows._break_between(frames, coverage, fa, fb, pows.BRIDGE_BREAKS):
                continue
            pa, pb = floor.get((a, fa)), floor.get((b, fb))
            if pa is not None and pb is not None:
                if cls[a] not in params.v_max_mps:
                    raise ContractError("ERR-SPEC", f"T25.1 (a): no stitch_v_max_mps for class {cls[a]}")
                dist, limit, gate = math.hypot(pb[0] - pa[0], pb[1] - pa[1]), params.v_max_mps[cls[a]] * dt + params.r_gate_m, "floor"
            else:
                ca, cb = _centre(box_a), _centre(box_b)
                dist, limit, gate = math.hypot(cb[0] - ca[0], cb[1] - ca[1]), params.img_gate * max(_diag(box_a), _diag(box_b)), "image"
            if limit <= 0 or dist > limit + EPS:
                continue
            cands.append({"a": a, "b": b, "cost": dist / limit, "dt_s": dt, "gate": gate, "distance": dist, "limit": limit})
    cands.sort(key=lambda c: (c["cost"], c["dt_s"], canonical_json([c["a"], c["b"]])))
    has_succ, has_pred, out = set(), set(), []
    for c in cands:
        if c["a"] in has_succ or c["b"] in has_pred:
            continue
        has_succ.add(c["a"])
        has_pred.add(c["b"])
        out.append(c)
    return out


def chains(track_ids: list[str], accepted: list[dict]) -> list[list[str]]:
    """Chains of accepted links, each in time order; every track is in exactly one chain. Sorted by JCS of the chain."""
    succ = {c["a"]: c["b"] for c in accepted}
    pred = {c["b"] for c in accepted}
    out = []
    for t in sorted(set(track_ids)):
        if t in pred:
            continue
        chain = [t]
        while chain[-1] in succ:
            chain.append(succ[chain[-1]])
        out.append(chain)
    return sorted(out, key=canonical_json)


def stitch_ids(chain_list: list[list[str]], nk_of: dict[str, list] | None = None) -> dict[str, str]:
    """AR-69 item 1: stitch_id = id("sti", [member track keys in chain order]); a single-track chain gets one too. With
    `nk_of`, the keys are the member tracks' natural keys [recording_id, track_local_id], which stay the same in the
    stitched S3 artifact (a track's `trk_` ID is artifact-scoped and changes with any new S3 artifact)."""
    out = {}
    for chain in chain_list:
        sid = core.make_id("sti", [nk_of[t] for t in chain] if nk_of is not None else list(chain))
        for t in chain:
            out[t] = sid
    return out


def apply(s3: Artifact, stitch_of: dict[str, str], spec: Spec) -> Artifact:
    """T25.1 (e): track points keep their tracks (natural keys) and each carries `stitch_id`; no point is created or
    removed. `stitch_of` maps the input artifact's track IDs to stitched identities."""
    trk_of = {t["track_local_id"]: t["trk_id"] for t in s3.tables["track"]}
    strip = lambda row, *names: {k: v for k, v in row.items() if k not in names}  # derived IDs are recomputed
    missing = sorted(set(trk_of.values()) - set(stitch_of))
    if missing:
        raise ContractError("ERR-SPEC", f"T25.1 (e): tracks without a stitched identity: {missing[:3]}")
    points = [{**strip(p, "tpt_id", "track_id"), "stitch_id": stitch_of[trk_of[p["track_nk"][1]]]} for p in s3.tables["track_point"]]
    return build_artifact(spec, {"track": [strip(t, "trk_id") for t in s3.tables["track"]], "track_point": points})


def natural_keys(s3_tables: dict[str, list[Row]]) -> dict[str, list]:
    return {t["trk_id"]: [t["recording_id"], t["track_local_id"]] for t in s3_tables["track"]}


def tracks_of(s3_tables: dict[str, list[Row]]) -> list[Track]:
    """`Track` inputs from S3 tables (track IDs, classes, points in frame order)."""
    trk_of = {t["track_local_id"]: t["trk_id"] for t in s3_tables["track"]}
    cls = {t["track_local_id"]: t["class"] for t in s3_tables["track"]}
    pts: dict[int, list] = {}
    for p in s3_tables["track_point"]:
        pts.setdefault(p["track_nk"][1], []).append((p["frame_index"], p["state"], list(p["bbox_xyxy_px"])))
    return [Track(trk_of[k], cls[k], sorted(v, key=lambda x: x[0])) for k, v in sorted(pts.items())]
