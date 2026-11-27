"""D-66 diagnostic: on every IE event of the oracle path (A) and the detector path (C), which rule input was undetermined.
Diagnostic and post hoc; tuning cameras only (the 116 of the v2 dev run, `out/v2/dev/`); selects nothing; no test data.
Synthetic-data evaluation; experimental.

  PYTHONPATH=src .venv/bin/python research/v2/ie_inputs_diag.py run [workers]   -> out/v2/diag_ie/cam/<rec>.json
  PYTHONPATH=src .venv/bin/python research/v2/ie_inputs_diag.py aggregate       -> research/v2/ie_inputs_diag_tune.json

Method. For each camera and each S5 baseline of A (BL-2..BL-6) and C (BL-2, BL-3, BL-6), the stored S4 (and, on C, the
stitched S3 for the CR-042 member map) of the dev run is read and its artifact ID verified; the per-frame inputs are
recomputed exactly as `s5.build` does (`providers.flag_frames`, `engine.run_pow`, the frozen v2 rule configuration,
whose ID must equal the freeze record). The recomputed episodes must equal the stored S5 episodes (bounds, K, contact
state, IE); otherwise STOP. Then, per stored IE event of scenario S_VIEW (the events the run's IE share counts,
`d58_events.event_rows`; one member episode under v2, limitation 16):
- clauses: which part of the IE rule held (engine._episode): coverage_at_ca (Q at the closest-approach frame not 1, or
  no CA frame), coverage_share (time with Q not 1 > o_max x span), contact_not_assessable, k_undetermined (K = 2 with H
  or PC; k_parts: E_ep unknown (R5) and / or no measured clearance);
- undetermined inputs (2 = unknown, Kleene) anywhere in the episode: M (frames of the episode), R4 (the R4 provider's
  C value), R5 (E over the attribution frames), contact_cue (T9.3 at the CA frame; unknown without a CA frame),
  coverage (Q not 1 on a frame of the episode). None = the input is not in that baseline's configuration.
The clauses are what made the event IE; the inputs say what else was unknown in it. Both are non-exclusive counts.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
DEV = ROOT / "out/v2/dev"
OUT = ROOT / "out/v2/diag_ie"
RESULT = HERE / "ie_inputs_diag_tune.json"
COLUMNS = {"A": ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6"), "C": ("BL-2", "BL-3", "BL-6")}
CLAUSES = ("coverage_at_ca", "coverage_share", "contact_not_assessable", "k_undetermined")
INPUTS = ("M", "R4", "R5", "contact_cue", "coverage")
STATUS = "diagnostic, post hoc (D-66); tuning cameras only; selects nothing; synthetic-data evaluation; experimental"


def attribute(frames, ep: dict, params) -> dict:
    """IE clauses and undetermined inputs of one episode; `frames` = its POW's FrameFlags after `engine.run_pow`."""
    from rq1.events import engine
    inside = [f for f in frames if ep["start_frame"] <= f.frame_index < ep["end_frame_excl"]]
    plus = [f for f in frames if ep["start_frame"] <= f.frame_index < ep["attr_end_frame_excl"]]
    at = next((f for f in inside if f.frame_index == ep["closest_approach_frame"]), None)
    h_or_pc = bool(ep["X_ep"] or ep["C_ep"])
    clauses = {"coverage_at_ca": at is None or at.Q != 1,
               "coverage_share": sum(f.support for f in inside if f.Q != 1) > params.o_max * ep["span_s"] + 1e-12,
               "contact_not_assessable": ep["contact_state"] == "not_assessable",
               "k_undetermined": ep["K"] == 2 and h_or_pc}
    if any(clauses.values()) != bool(ep["lbl_IE"]):
        raise SystemExit(f"STOP: IE clauses {clauses} disagree with the stored lbl_IE {ep['lbl_IE']}")
    k_parts = {"r5_unknown": ep["E_ep"] == 2, "clearance_unknown": ep["minclr_m"] is None} if clauses["k_undetermined"] else None
    r4 = any("R4" in f.C_by for f in inside)
    undetermined = {"M": any(f.M == 2 for f in inside),
                    "R4": any(f.C_by.get("R4") == 2 for f in inside) if r4 else None,
                    "R5": any(f.E == 2 for f in plus) if params.r5_enabled else None,
                    "contact_cue": at is None or engine.contact_cue(at.rates, params.k_c, params.k_c_turn) == 2,
                    "coverage": any(f.Q != 1 for f in inside)}
    return {"clauses": clauses, "k_parts": k_parts, "undetermined": undetermined}


def summarise(rows: list[dict]) -> dict:
    """Non-exclusive counts over IE events; an input absent from the configuration is 'not enabled'."""
    clauses, undet, combos, kp = Counter(), {}, Counter(), Counter()
    for r in rows:
        on = [k for k, v in r["clauses"].items() if v]
        clauses.update(on)
        combos[" + ".join(on)] += 1
        for k, v in (r.get("k_parts") or {}).items():
            kp[k] += bool(v)
        for k, v in r["undetermined"].items():
            undet[k] = "not enabled" if v is None else undet.get(k, 0) + bool(v)
    out = {"ie_events": len(rows), "clauses": {k: clauses[k] for k in r["clauses"]} if rows else {},
           "undetermined": undet, "clause_combinations": dict(sorted(combos.items()))}
    if kp:
        out["k_undetermined_parts"] = dict(sorted(kp.items()))
    return out


def _tables(art_id: str) -> dict:  # pragma: no cover - reads stored artifacts
    from rq1.ids import artifact as A
    from rq1.schema import files
    d = DEV / "artifacts" / art_id
    if A.verify(str(d)) != art_id:
        raise SystemExit(f"STOP: {art_id} does not verify")
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], A.SCHEMA_VERSION) for f in man["files"] if f["path"].endswith(".parquet")}


def run_camera(rec: str) -> tuple[str, str]:  # pragma: no cover - driver over stored artifacts
    import dataclasses
    import run_v2 as rv
    import run_pilot as rp
    from rq1.events import engine, providers, s5
    path = OUT / "cam" / f"{rec}.json"
    if path.exists():
        return rec, "skipped"
    cam = json.loads((DEV / "cam" / f"{rec}.json").read_text())
    if cam["partition"] != "dev":
        raise SystemExit(f"STOP: {rec} is not a tuning camera")
    ctx = rv.m.Context("sdg")
    _, s1, _ = rp.load_s1(ctx, rec)  # ERR-LEAKAGE unless validation (D-37)
    want = rv.expected_configs(json.loads(rv.FREEZE.read_text()))["rcf"]
    frames = sorted((f for f in s1["frame"] if f["recording_id"] == s1["frame"][0]["recording_id"]),
                    key=lambda f: (f["frame_index"] is None, f["frame_index"] if f["frame_index"] is not None else f["decode_seq"]))
    delta_nom = next(x for x in s1["decode_summary"] if x["recording_id"] == frames[0]["recording_id"])["delta_nom_s"]
    out = {"rec_id": rec, "viewpoint": cam["viewpoint"], "columns": {}}
    for col, bls in COLUMNS.items():
        s4 = _tables(cam["artifacts"][f"{col}.S4"]["id"])
        members = providers.stitch_members(_tables(cam["artifacts"]["C.S3.stitched"]["id"])) if col == "C" else None
        index = providers.S4Index(s4, frames, s1["coverage_segment"], members=members)
        for bl in bls:
            c5 = rv.v2.s5_config(ctx, bl, rv.LABEL, True)
            if s5.config_id(c5) != want[bl]:
                raise SystemExit(f"STOP: {rec} {bl}: rule configuration differs from the freeze record")
            rules = s5.effective_rules(c5)
            params = dataclasses.replace(c5.params, m_gap=engine.m_gap_frames(c5.m_gap_s, delta_nom))
            stored = _tables(cam["artifacts"][f"{col}.S5.{bl}"]["id"])
            eps = {(e["pow_id"], e["start_frame"]): e for e in stored["episode"]}
            flags_of, seen = {}, set()
            for pw in s4["pow"]:
                nk = [pw["person_track_id"], pw["forklift_track_id"], pw["start_frame"]]
                fl = providers.flag_frames(s4, rules, frames, s1["coverage_segment"], pow_nk=nk, index=index)
                for e in engine.run_pow(fl, params)[0]:
                    s = eps.get((pw["pow_id"], e["start_frame"]))
                    keys = ("end_frame_excl", "K", "contact_state", "lbl_IE", "closest_approach_frame")
                    if s is None or any(s[k] != e[k] for k in keys):
                        raise SystemExit(f"STOP: {rec} {col}|{bl}: recomputed episode differs from the stored S5 at {pw['pow_id']} {e['start_frame']}")
                    seen.add((pw["pow_id"], e["start_frame"]))
                flags_of[pw["pow_id"]] = fl
            if seen != set(eps):
                raise SystemExit(f"STOP: {rec} {col}|{bl}: recomputed episodes do not cover the stored S5")
            by_id = {e["ep_id"]: e for e in stored["episode"]}
            rows, view = [], [ev for ev in stored["candidate_event"] if ev["scenario"] == "S_VIEW"]
            for ev in view:
                if not ev["lbl_IE"]:
                    continue
                if ev["n_members"] != 1:
                    raise SystemExit(f"STOP: {rec}: event with {ev['n_members']} members (limitation 16)")
                e = by_id[ev["member_episode_ids"][0]]
                rows.append({"evt_id": ev["evt_id"], **attribute(flags_of[e["pow_id"]], e, params)})
            out["columns"][f"{col}|{bl}"] = {"events": len(view), "ie": rows}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, sort_keys=True, indent=1))
    return rec, "done"


def aggregate() -> dict:  # pragma: no cover - reads the per-camera files
    import subprocess
    cams = [json.loads(p.read_text()) for p in sorted((OUT / "cam").glob("*.json"))]
    if len(cams) != 116:
        raise SystemExit(f"STOP: {len(cams)} cameras (116 expected)")
    res = {"status": STATUS, "cameras": len(cams), "source": "out/v2/dev (v2 dev run; S4 / S5 artifact IDs verified)",
           "code_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
           "method": __doc__.split("Method. ")[1].strip(), "results": {}}
    for key in sorted({k for c in cams for k in c["columns"]}):
        res["results"][key] = {}
        for view in ("all", "ceiling", "eye_level"):
            sel = [c for c in cams if view == "all" or c["viewpoint"] == view]
            rows = [r for c in sel for r in c["columns"][key]["ie"]]
            events = sum(c["columns"][key]["events"] for c in sel)
            res["results"][key][view] = {"events": events, "ie_share": len(rows) / events if events else None, **summarise(rows)}
    RESULT.write_text(json.dumps(res, sort_keys=True, indent=1) + "\n")
    return res


def main():  # pragma: no cover
    if sys.argv[1] == "run":
        recs = sorted(p.stem for p in (DEV / "cam").glob("*.json"))
        t0 = time.time()
        with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 3) as pool:
            for i, (rec, st) in enumerate(pool.imap_unordered(run_camera, recs), 1):
                print(i, rec, st, round(time.time() - t0), flush=True)
    elif sys.argv[1] == "aggregate":
        r = aggregate()
        for k, v in r["results"].items():
            print(k, v["all"]["events"], v["all"]["ie_events"], v["all"]["clauses"], v["all"]["undetermined"])


if __name__ == "__main__":
    main()
