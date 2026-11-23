"""D-53 step 0: the v2 tuning subset and reporting cameras (D-50 item 3, `docs/preregistration/v2_notes.md`).

  PYTHONPATH=src .venv/bin/python research/m1b/v2_sets.py   -> research/m1b/v2_camera_sets.json

Population: the SDG validation cameras with an ORACLE-S3 (`m1a_common.Context.validation_cameras`, 226), as the pilot.
Tuning subset: every camera of a validation run that contains a T-22 probe camera (`zero_shot_probe.json` selection).
Reporting cameras: every camera of the other validation runs. Expected 116 and 110 (v2 notes, counted 19 Nov 2026).
No test partition (ERR-LEAKAGE from `Context.camera`).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

EXPECTED = {"tuning": 116, "reporting": 110}
PATH = pc.ROOT / "research/m1b/v2_camera_sets.json"


def split(cameras: list[dict], probe: set[str]) -> dict:
    """cameras: [{"rec_id", "run", "camera"}]; probe: rec_ids. Runs with a probe camera -> tuning; others -> reporting."""
    probe_runs = {c["run"] for c in cameras if c["rec_id"] in probe}
    missing = probe - {c["rec_id"] for c in cameras}
    if missing:
        raise ValueError(f"probe cameras outside the population: {sorted(missing)}")
    out = {}
    for name, keep in (("tuning", lambda r: r in probe_runs), ("reporting", lambda r: r not in probe_runs)):
        cs = sorted((c for c in cameras if keep(c["run"])), key=lambda c: c["rec_id"])
        out[name] = {"runs": sorted({c["run"] for c in cs}), "n_runs": len({c["run"] for c in cs}), "n_cameras": len(cs),
                     "by_viewpoint": {v: sum(1 for c in cs if pc.viewpoint(c["camera"]) == v) for v in ("ceiling", "eye_level")},
                     "cameras": [{"rec_id": c["rec_id"], "run": c["run"], "camera": c["camera"], "viewpoint": pc.viewpoint(c["camera"]),
                                  "probe_camera": c["rec_id"] in probe} for c in cs]}
    return out


def check(sets: dict) -> list[str]:
    problems = [f"{k}: {sets[k]['n_cameras']} cameras, expected {n}" for k, n in EXPECTED.items() if sets[k]["n_cameras"] != n]
    both = {c["rec_id"] for c in sets["tuning"]["cameras"]} & {c["rec_id"] for c in sets["reporting"]["cameras"]}
    if both:
        problems.append(f"cameras in both sets: {sorted(both)}")
    if set(sets["tuning"]["runs"]) & set(sets["reporting"]["runs"]):
        problems.append("a run is in both sets")
    return problems


def load() -> dict:
    import json
    return json.loads(PATH.read_text())


def tuning() -> list[str]:
    return [c["rec_id"] for c in load()["tuning"]["cameras"]]


def reporting() -> list[str]:
    return [c["rec_id"] for c in load()["reporting"]["cameras"]]


def main():  # pragma: no cover - driver over stored inputs
    ctx = pc.m.Context("sdg")
    cams = [{"rec_id": c["rec_id"], "run": c["run"], "camera": c["camera"]} for c in ctx.validation_cameras()]
    sets = split(cams, set(pc.probe_cameras()))
    problems = check(sets)
    out = {"status": "D-53 step 0: v2 camera sets (D-50 item 3); SDG validation partition only", "source": "docs/preregistration/v2_notes.md",
           "population": "SDG validation cameras with an ORACLE-S3 (m1a_common.Context.validation_cameras)", "population_cameras": len(cams),
           "probe_cameras": len(pc.probe_cameras()), "check": problems or "ok: 116 / 110, disjoint", **sets}
    pc.write_json(PATH, out)
    print(PATH, problems or "ok", {k: (sets[k]["n_runs"], sets[k]["n_cameras"], sets[k]["by_viewpoint"]) for k in sets})
    if problems:
        raise SystemExit("STOP: " + "; ".join(problems))


if __name__ == "__main__":
    main()
