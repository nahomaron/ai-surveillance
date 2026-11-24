"""D-55 step 5: the Owner-approved tracker selection rule, applied exactly (pure; main `.venv`).

  PYTHONPATH=src .venv/bin/python research/m1b/v2_tracker_select.py   -> research/m1b/v2_tracker_selection.json

1. Drop the configurations with forklift point precision < 0.95, or with person IDF1 below the column C
   configuration's person IDF1 on the same 116 cameras.
2. Among the rest, keep those within 0.01 of the best forklift IDF1 (IDF1 >= best - 0.01; a 1e-12 allowance absorbs
   floating-point rounding of the subtraction only).
3. Highest coverage, then fewest fragments per identity, then fewest parameters changed from the installed defaults,
   then the lowest configuration ID (string order). Each tie-break keeps the rows equal to the best on its key.
4. T1 and T2 separately; then the two winners compared by the same rule from step 2 on: the package.
If no configuration passes the guards: STOP (no guard is loosened).
Inputs per row: config_id, family, idf1_forklift, coverage, fragments_per_identity, parameters_changed, precision,
idf1_person (the primary reading of `v2_tracker_measures`).
"""
from __future__ import annotations

import json
import os
import sys

PRECISION_MIN = 0.95
BAND = 0.01
EPS = 1e-12
TIE_BREAKS = (("coverage", "max"), ("fragments_per_identity", "min"), ("parameters_changed", "min"), ("config_id", "min"))
STOP = "STOP: no configuration passes the guards"


def parameters_changed(params: dict, installed: dict) -> int:
    """Keys whose value differs from the tracker's installed default (`tracker_type` never differs)."""
    if set(params) != set(installed):
        raise ValueError("parameter keys differ from the installed keys")
    return sum(1 for k in installed if params[k] != installed[k])


def guards(rows: list[dict], person_idf1_c: float) -> dict:
    out = {}
    for r in rows:
        g = {"precision_ge_0.95": r["precision"] is not None and r["precision"] >= PRECISION_MIN,
             "person_idf1_ge_column_c": r["idf1_person"] >= person_idf1_c}
        out[r["config_id"]] = {**g, "pass": all(g.values())}
    return out


def choose(rows: list[dict]) -> dict:
    """Steps 2 and 3 on rows that passed the guards."""
    if not rows:
        return {"band": None, "path": [], "winner": None}
    best = max(rows, key=lambda r: (r["idf1_forklift"], [-ord(ch) for ch in r["config_id"]]))
    lo = best["idf1_forklift"] - BAND - EPS
    band = sorted((r for r in rows if r["idf1_forklift"] >= lo), key=lambda r: r["config_id"])
    path, left = [], band
    for key, how in TIE_BREAKS:
        if len(left) == 1:
            break
        vals = [r[key] for r in left]
        target = max(vals) if how == "max" else min(vals)
        left = [r for r in left if r[key] == target]
        path.append({"key": key, "remaining": [r["config_id"] for r in left]})
    return {"band": {"best_idf1": best["idf1_forklift"], "best_config_id": best["config_id"], "lower_edge": best["idf1_forklift"] - BAND,
                     "members": [r["config_id"] for r in band]}, "path": path, "winner": left[0]["config_id"]}


def select_family(rows: list[dict], family: str, person_idf1_c: float) -> dict:
    fam = [r for r in rows if r["family"] == family]
    g = guards(fam, person_idf1_c)
    passed = [r for r in fam if g[r["config_id"]]["pass"]]
    return {"family": family, "configurations": len(fam), "passed_guards": len(passed), **choose(passed)}


def select(rows: list[dict], person_idf1_c: float) -> dict:
    out = {"guards": guards(rows, person_idf1_c)}
    for fam in ("T1", "T2"):
        out[fam] = select_family(rows, fam, person_idf1_c)
    winners = [r for r in rows if r["config_id"] in {out["T1"]["winner"], out["T2"]["winner"]}]
    out["package"] = choose(winners)
    out["status"] = STOP if out["package"]["winner"] is None else "selected (D-55), not frozen"
    return out


def main() -> None:  # pragma: no cover - driver over the stored grid
    sys.path.insert(0, os.path.dirname(__file__))
    import v2_tracker_grid as vg
    grid = json.loads(vg.GRID_PATH.read_text())
    rows = [vg.selection_row(r) for r in grid["rows"]]
    c = vg.selection_row(grid["column_c"])
    out = select(rows, c["idf1_person"])
    alt = select([vg.selection_row(r, "all") for r in grid["rows"]], vg.selection_row(grid["column_c"], "all")["idf1_person"])
    doc = {"status": "D-55 step 5: tuning subset, synthetic SDG, selection evidence, not a reported result; selected, not frozen",
           "rule": {"precision_min": PRECISION_MIN, "person_idf1_min": "column C configuration's person IDF1", "band": BAND,
                    "tie_breaks": [k for k, _ in TIE_BREAKS], "reading": "primary (CR-033 item 2): tracked point = state `tracked`"},
           "column_c": {**c, "person_idf1_reference": c["idf1_person"]}, "inputs": rows, **out,
           "package_configuration": next((r for r in grid["rows"] if r["config_id"] == out["package"]["winner"]), None),
           "sensitivity_secondary_reading": {"note": "the same rule on the secondary reading (tracked and predicted points); not the selection",
                                             "T1": alt["T1"]["winner"], "T2": alt["T2"]["winner"], "package": alt["package"]["winner"]}}
    for _ in range(2):
        vg.write(vg.SELECTION_PATH, doc)
    print(json.dumps({k: out[k]["winner"] for k in ("T1", "T2", "package")}), out["status"])
    if out["package"]["winner"] is None:
        raise SystemExit(STOP)


if __name__ == "__main__":
    main()
