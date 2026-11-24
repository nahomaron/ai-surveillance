"""D-55 steps 6 and 7: fragmentation check (tracking level only) and the tracker report.

  PYTHONPATH=src .venv/bin/python research/m1b/v2_tracker_report.py
      -> research/m1b/v2_tracker_fragmentation.json and research/m1b/v2_tracker_report.md (each written twice)

Step 6, for the package and the column C configuration, on the 116 tuning cameras, from the per-camera grid files:
fragments per forklift reference identity (identities covered by >= 1 track): median, P90 (nearest rank), max; the
number of identities covered by two or more tracks; the longest gap bridged (eligible frames). Primary reading
(tracked points); the secondary reading (tracked and predicted points) beside it. Nothing is recommended.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import v2_tracker_grid as vg  # noqa: E402
import v2_tracker_measures as vm  # noqa: E402

FRAG_PATH = vg.ROOT / "research/m1b/v2_tracker_fragmentation.json"
REPORT_PATH = vg.ROOT / "research/m1b/v2_tracker_report.md"
VIEWS = ("all", "ceiling", "eye_level")


def fragmentation(per: dict, config_id: str) -> dict:
    out = {}
    for view in VIEWS:
        recs = [r for r in sorted(per) if view == "all" or per[r]["viewpoint"] == view]
        block = {}
        for v in vm.VARIANTS:
            n = [f[v] for r in recs for f in per[r]["configs"][config_id]["fragments"].values()]
            cov = [x for x in n if x >= 1]
            block[v] = {"identities": len(n), "identities_covered": len(cov), "median": vm.median(cov), "p90": vm.quantile(cov, 90),
                        "max": max(cov, default=None), "identities_two_or_more": sum(1 for x in cov if x >= 2)}
        block["longest_bridged_frames"] = max((per[r]["configs"][config_id]["counts"]["longest_bridged"] for r in recs), default=0)
        out[view] = block
    return out


def f3(x):
    return "–" if x is None else f"{x:.3f}"


def table_rows(rows: list[dict], view: str = "all") -> list[str]:
    out = ["| config_id | fam | high/new | fuse | buffer | IDF1 F | coverage | precision | frag/id | IDF1 P | tracks | predicted | bridged | changed |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = r["forklift"][view]
        g = r["grid"] or {"track_high_thresh": r["params"]["track_high_thresh"], "new_track_thresh": r["params"]["new_track_thresh"],
                          "fuse_score": r["params"]["fuse_score"], "track_buffer": r["params"]["track_buffer"]}
        out.append(f"| `{r['config_id']}` | {r['family']} | {g['track_high_thresh']}/{g['new_track_thresh']} | {str(g['fuse_score']).lower()} | "
                   f"{g['track_buffer']} | {f3(f['idf1'])} | {f3(f['tracked']['coverage'])} | {f3(f['tracked']['precision'])} | "
                   f"{f3(f['tracked']['fragments_per_identity'])} | {f3(r['person_idf1'][view])} | {f['counts']['tracks']} | {f['counts']['predicted']} | "
                   f"{f['counts']['runs_bridged']} | {r['parameters_changed']} |")
    return out


def report(grid: dict, sel: dict, frag: dict) -> str:
    rows = {r["config_id"]: r for r in [grid["column_c"]] + grid["rows"]}
    c = grid["column_c"]
    pkg_id = sel["package"]["winner"]
    pkg = rows.get(pkg_id)
    L = [f"# D-55 tracker selection (v2 detector + tracker package)", "",
         f"Status: {vg.STATUS}. Selected under D-55, **not frozen** (frozen later in pre-registration v2). Contract {grid['contract']} unchanged.", "",
         "No event evaluation of any kind: no S4, S5 or S8 run and no EV metric. Tuning cameras only (116; "
         f"{grid['by_viewpoint']['ceiling']} ceiling, {grid['by_viewpoint']['eye_level']} eye-level); nothing on the 110 reporting cameras or the test partition. "
         "Detector as frozen in D-45 (YOLO-World v2-s, person 0.20, forklift 0.05). Columns A, B, C and C′ unchanged.", "",
         "## Summary (plain language)", ""]
    if pkg is None:
        L += ["No configuration passed the guards; nothing is selected (STOP)."]
    else:
        fc, fp = c["forklift"]["all"], pkg["forklift"]["all"]
        won = "BoT-SORT (T2)" if pkg["family"] == "T2" else "ByteTrack (T1)"
        L += [f"- Forklift coverage by tracked points: column C settings {f3(fc['tracked']['coverage'])}, selected package {f3(fp['tracked']['coverage'])}.",
              f"- Forklift IDF1: column C {f3(fc['idf1'])}, package {f3(fp['idf1'])}. Person IDF1 is unchanged ({f3(c['person_idf1']['all'])}): the person tracker is the same.",
              f"- The package is {won}. T1 winner `{sel['T1']['winner']}`, T2 winner `{sel['T2']['winner']}`."
              + (" BoT-SORT won." if pkg["family"] == "T2" else " BoT-SORT did not win."),
              f"- Fragmentation remains: package {f3(fp['tracked']['fragments_per_identity'])} tracks per covered forklift identity "
              f"({frag['package']['all']['tracked']['identities_two_or_more']} of {frag['package']['all']['tracked']['identities_covered']} covered identities have two or more), "
              f"column C {f3(fc['tracked']['fragments_per_identity'])} ({frag['column_c']['all']['tracked']['identities_two_or_more']} of {frag['column_c']['all']['tracked']['identities_covered']}).",
              f"- Under the secondary reading (tracked and predicted points) the same rule selects `{sel['sensitivity_secondary_reading']['package']}` "
              + ("(the same package)." if sel["sensitivity_secondary_reading"]["package"] == pkg_id else "(a different package; see CR-033 item 2)."),
              "- These are tracking measures on synthetic SDG tuning cameras: selection evidence, not a reported result, nothing validated."]
    L += ["", "## Selected package", ""]
    if pkg is not None:
        L += [f"Configuration ID `{pkg_id}` (S3 tracker configuration ID, F.1 A1.2 configuration class).", "",
              "| class | tracker | parameter | value |", "|---|---|---|---|"]
        for cls, v in pkg["run_config"]["classes"].items() if "run_config" in pkg else []:
            for k, val in v["params"].items():
                L.append(f"| {cls} | {v['tracker']} (`{v['tracker_id']}`) | {k} | `{json.dumps(val)}` |")
        L += ["", f"Bridging g_max {vm.G_MAX} (frozen v1), tracked box = detection box (AR-62 item 3), NumPy assignment path (AR-62 item 5)."]
    L += ["", "## Selection (STEP 5)", "",
          f"Rule as approved: guards precision ≥ 0.95 and person IDF1 ≥ column C's ({f3(c['person_idf1']['all'])}); band 0.01 below the best forklift IDF1; "
          "then coverage, fragments per identity, parameters changed from the installed defaults, configuration ID. Primary reading (CR-033 item 2).", ""]
    for fam in ("T1", "T2", "package"):
        s = sel[fam]
        if s.get("band") is None:
            L.append(f"- **{fam}**: no configuration passed the guards.")
            continue
        extra = f" ({s['passed_guards']} of {s['configurations']} passed the guards)" if fam != "package" else ""
        L.append(f"- **{fam}**{extra}: best IDF1 {f3(s['band']['best_idf1'])} (`{s['band']['best_config_id']}`); band ≥ {f3(s['band']['lower_edge'])}: "
                 f"{len(s['band']['members'])} configurations; path: "
                 + (", ".join(f"{p['key']} → {len(p['remaining'])}" for p in s["path"]) or "single member") + f"; winner `{s['winner']}`.")
    failed = {k: v for k, v in sel["guards"].items() if not v["pass"]}
    L += ["", f"Guard failures: {len(failed)} of {len(sel['guards'])} configurations "
          f"(precision: {sum(1 for v in failed.values() if not v['precision_ge_0.95'])}; person IDF1: {sum(1 for v in failed.values() if not v['person_idf1_ge_column_c'])})."
          " Per-configuration guard results: `v2_tracker_selection.json`."]
    L += ["", "## Grid (STEP 4), all 116 tuning cameras", "",
          "IDF1 F / P: forklift / person IDF1 (TrackEval port, iou_cm 0.5, pooled IDTP/IDFP/IDFN). Coverage, precision and frag/id: primary reading, "
          "probe matcher IoU ≥ 0.3 on clipped reference-visible boxes. Counts: tracks started, predicted points, bridged gaps.", ""]
    L += table_rows([c] + grid["rows"])
    for view in ("ceiling", "eye_level"):
        L += ["", f"### {view} ({grid['by_viewpoint'][view]} cameras)", ""]
        L += table_rows([c] + grid["rows"], view)
    L += ["", "Person tracker: ByteTrack, column C configuration, one job per camera shared by every configuration, so person IDF1 is identical in every row "
          f"by construction. Column C's tracker run reproduced the stored column C tracker log on {grid['column_c_reproduction']['cameras_with_stored_log']} cameras "
          f"(all identical: {grid['column_c_reproduction']['all_identical']}).", "",
          "## Fragmentation (STEP 6), tracking level only", "",
          "| configuration | view | identities covered | median | P90 | max | covered by ≥ 2 tracks | longest bridged gap (frames) |", "|---|---|---|---|---|---|---|---|"]
    for name in ("package", "column_c"):
        for view in VIEWS:
            b = frag[name][view]
            t = b["tracked"]
            L.append(f"| {name} `{frag[name + '_id']}` | {view} | {t['identities_covered']} / {t['identities']} | {t['median']} | {t['p90']} | {t['max']} | "
                     f"{t['identities_two_or_more']} | {b['longest_bridged_frames']} |")
    L += ["", "Secondary reading (tracked and predicted points) in `v2_tracker_fragmentation.json`. No recommendation is made; this informs the later stitching decision.", "",
          "## Files", "", "- `research/m1b/botsort_keys.json`: installed BoT-SORT keys and the D-55 settings.",
          "- `research/m1b/v2_tracker_grid.json`: one row per configuration (overall and by viewpoint, both readings).",
          "- `research/m1b/v2_tracker_selection.json`: guards, band, tie-break path, winners, column C row, sensitivity.",
          "- `research/m1b/v2_tracker_fragmentation.json`: STEP 6.", "- CR-033: the `tracker_id` field for column C, and the readings used.", ""]
    return "\n".join(L)


def main() -> None:  # pragma: no cover
    grid = json.loads(vg.GRID_PATH.read_text())
    sel = json.loads(vg.SELECTION_PATH.read_text())
    per = {c["rec_id"]: json.loads((vg.GRID_DIR / f"{c['rec_id']}.json").read_text()) for c in vg.tuning()}
    pkg = sel["package"]["winner"]
    frag = {"status": vg.STATUS + "; D-55 step 6, tracking level only, no recommendation", "package_id": pkg, "column_c_id": grid["column_c"]["config_id"],
            "package": fragmentation(per, pkg) if pkg else None, "column_c": fragmentation(per, grid["column_c"]["config_id"])}
    cfgs = {c["config_id"]: c for c in vg.configurations()}
    for r in [grid["column_c"]] + grid["rows"]:
        r["run_config"] = cfgs[r["config_id"]]["run_config"]
    text = report(grid, sel, frag)
    for _ in range(2):
        vg.write(FRAG_PATH, frag)
        REPORT_PATH.write_text(text)
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
