"""D-58 STEP 3: the stitching grid, the pre-declared selection rule, and the points-based tracking measures (equal to
`v2_tracker_measures.measures` when every track is its own unit). Hand-made inputs; expected values by hand beside each
assertion."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d58_stitch as st  # noqa: E402
import v2_tracker_measures as vm  # noqa: E402
from rq1.tracking import bridging  # noqa: E402


def test_grid_is_off_plus_twelve():
    g = st.grid()
    assert g[0] == {"name": "off", "params": None} and len(g) == 13
    assert {(c["params"]["stitch_max_gap_s"], c["params"]["stitch_r_gate_m"]) for c in g[1:]} == {(t, r) for t in (1.0, 2.0, 3.0, 5.0) for r in (0.5, 1.0, 2.0)}
    assert all(c["params"]["stitch_v_max_mps"] == {"person": 2.5, "forklift": 4.0} and c["params"]["stitch_img_gate"] == 1.0 for c in g[1:])


def _row(f_idf1, p_idf1, f_frag, f_prec=0.98, p_prec=0.99):
    return {"forklift": {"idf1": f_idf1, "precision": f_prec, "fragments_per_identity": f_frag}, "person": {"idf1": p_idf1, "precision": p_prec},
            "objective": f_idf1 + p_idf1}


def test_select_guard_within_and_order():
    table = {c["name"]: _row(0.70, 0.80, 1.20) for c in st.grid()}
    table["off"] = _row(0.70, 0.70, 1.30)  # objective 1.40, outside 0.01 of the best (1.50)
    table["Ts1_rg0.5"] = _row(0.75, 0.80, 1.10, p_prec=0.94)  # best objective 1.55, but fails the guard (0.94 < 0.95)
    table["Ts5_rg2"] = _row(0.70, 0.805, 1.05)  # 1.505: kept, and the fewest forklift fragments
    table["Ts2_rg1"] = _row(0.70, 0.80, 1.05)  # 1.50: kept, same fragments, smaller T_s than Ts5 -> chosen
    s = st.select(table)
    assert "Ts1_rg0.5" not in s["guarded"] and s["best_objective"] == 1.505
    assert "off" not in s["kept"] and s["chosen"] == "Ts2_rg1"
    assert s["status"] == "selected under D-58, not frozen"


def test_select_ties_break_on_smaller_r_g():
    table = {c["name"]: _row(0.70, 0.80, 1.20) for c in st.grid()}
    for n in ("Ts2_rg0.5", "Ts2_rg1", "Ts2_rg2"):
        table[n] = _row(0.70, 0.80, 1.00)
    assert st.select(table)["chosen"] == "Ts2_rg0.5"


def _log():
    """Two tracks: track 7 matched on frames 0-3 and 6 (gap 4-5 bridged by predicted boxes), track 9 on frames 8-9."""
    b = lambda x: [x, 0.0, x + 10.0, 20.0]
    log = []
    for i in range(10):
        e = {"frame_index": i, "tracked": [], "lost": []}
        if i in (0, 1, 2, 3, 6):
            e["tracked"].append([7, 0, b(float(i))])
        if i in (4, 5):
            e["lost"].append([7, b(float(i))])
        if i in (8, 9):
            e["tracked"].append([9, 0, b(float(i))])
        log.append(e)
    return log


def test_measures_units_equal_measures_with_tracks_as_units():
    log = _log()
    refs = {i: [("obj", [float(i), 0.0, i + 10.0, 20.0])] for i in range(10)}
    score = {(i, 0): 0.9 for i in range(10)}
    want = vm.measures(log, refs, refs, score, list(range(10)))
    pts = bridging.points_from_log(log, vm.G_MAX)
    units = {tid: [(p["frame_index"], p["state"], p["bbox"], score[(p["frame_index"], 0)] if p["state"] == "tracked" else 0.0) for p in tr["points"]]
             for tid, tr in pts.items()}
    got = st.measures_units(units, refs, refs, list(range(10)))
    strip = lambda d: {k: v for k, v in d.items() if k != "counts"}
    assert strip(got) == strip(want)
    assert want["fragments"]["obj"] == {"tracked": 2, "all": 2}  # two tracks match the one reference identity
    # The two tracks as one stitched unit: one fragment, and every box now carries the one system identity.
    merged = st.measures_units({7: units[7] + units[9]}, refs, refs, list(range(10)))
    assert merged["fragments"]["obj"] == {"tracked": 1, "all": 1}
    assert merged["idf1"]["IDTP"] == 9 and merged["idf1"]["IDFN"] == 1  # 9 system boxes (frames 0-6, 8, 9) of 10 references
