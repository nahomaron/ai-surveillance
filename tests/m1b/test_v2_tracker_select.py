"""D-55 step 5: the Owner-approved selection rule on a hand-built table (expected values by hand).

Rule: (1) drop precision < 0.95 or person IDF1 below column C's; (2) keep IDF1 within 0.01 of the best remaining;
(3) highest coverage, then fewest fragments per identity, then fewest parameters changed, then lowest configuration ID;
(4) per family, then the two winners compared from step 2 on.

Table T (person IDF1 of column C = 0.700):
  id    fam  idf1   cov   frag  changed  prec   pIDF1
  c01   T1   0.900  0.80  1.5   3        0.94   0.70   guard: precision          -> dropped (best IDF1 of all, not kept)
  c02   T1   0.890  0.70  1.2   3        0.96   0.69   guard: person IDF1        -> dropped
  c03   T1   0.880  0.75  1.4   4        0.96   0.70   best remaining T1 IDF1; band [0.870, 0.880]
  c04   T1   0.875  0.75  1.3   4        0.97   0.70   in band (tie inside the band: 0.875 vs 0.880)
  c05   T1   0.871  0.75  1.3   2        0.97   0.70   in band
  c06   T1   0.869  0.90  1.0   1        0.99   0.70   just outside the band (0.880 - 0.869 = 0.011) despite best coverage
  c07   T1   0.870  0.75  1.3   2        0.95   0.70   in band (exactly 0.010 below; precision exactly 0.95 passes)
  T1: band {c03, c04, c05, c07}; coverage 0.75 all -> fragments: c03 1.4 out -> {c04, c05, c07};
      changed: c04 4 out -> {c05, c07}; lowest ID -> c05.  Path: coverage (4 left), fragments (3), changed (2), id (1).
  b01   T2   0.860  0.85  1.1   5        0.96   0.70   best T2
  b02   T2   0.855  0.86  1.1   5        0.96   0.70   in band, higher coverage -> T2 winner b02 (decided at coverage)
  Package: best of {c05 0.871, b02 0.855} = 0.871, band [0.861, 0.871] -> b02 out (0.855) -> c05.
Table U (every row fails a guard) -> no winner, status "no configuration passes the guards".
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import v2_tracker_select as sel  # noqa: E402


def row(cid, fam, idf1, cov, frag, changed, prec, pidf1):
    return {"config_id": cid, "family": fam, "idf1_forklift": idf1, "coverage": cov, "fragments_per_identity": frag,
            "parameters_changed": changed, "precision": prec, "idf1_person": pidf1}


T = [row("c01", "T1", 0.900, 0.80, 1.5, 3, 0.94, 0.70), row("c02", "T1", 0.890, 0.70, 1.2, 3, 0.96, 0.69),
     row("c03", "T1", 0.880, 0.75, 1.4, 4, 0.96, 0.70), row("c04", "T1", 0.875, 0.75, 1.3, 4, 0.97, 0.70),
     row("c05", "T1", 0.871, 0.75, 1.3, 2, 0.97, 0.70), row("c06", "T1", 0.869, 0.90, 1.0, 1, 0.99, 0.70),
     row("c07", "T1", 0.870, 0.75, 1.3, 2, 0.95, 0.70),
     row("b01", "T2", 0.860, 0.85, 1.1, 5, 0.96, 0.70), row("b02", "T2", 0.855, 0.86, 1.1, 5, 0.96, 0.70)]


def test_guards():
    g = sel.guards(T, 0.70)
    assert g["c01"] == {"precision_ge_0.95": False, "person_idf1_ge_column_c": True, "pass": False}
    assert g["c02"] == {"precision_ge_0.95": True, "person_idf1_ge_column_c": False, "pass": False}
    assert g["c07"]["pass"] is True  # precision exactly 0.95 passes
    assert sorted(k for k, v in g.items() if v["pass"]) == ["b01", "b02", "c03", "c04", "c05", "c06", "c07"]


def test_family_t1_band_and_every_tie_break():
    r = sel.select_family(T, "T1", 0.70)
    assert r["band"]["best_idf1"] == 0.880 and r["band"]["best_config_id"] == "c03"
    assert r["band"]["members"] == ["c03", "c04", "c05", "c07"]
    assert [(s["key"], s["remaining"]) for s in r["path"]] == [
        ("coverage", ["c03", "c04", "c05", "c07"]), ("fragments_per_identity", ["c04", "c05", "c07"]),
        ("parameters_changed", ["c05", "c07"]), ("config_id", ["c05"])]
    assert r["winner"] == "c05"


def test_family_t2_decided_at_coverage():
    r = sel.select_family(T, "T2", 0.70)
    assert r["band"]["members"] == ["b01", "b02"]
    assert r["path"] == [{"key": "coverage", "remaining": ["b02"]}]
    assert r["winner"] == "b02"


def test_package_compares_winners_from_step_2():
    out = sel.select(T, 0.70)
    assert out["T1"]["winner"] == "c05" and out["T2"]["winner"] == "b02"
    assert out["package"]["band"]["members"] == ["c05"] and out["package"]["winner"] == "c05"


def test_no_configuration_passes():
    u = [row("u1", "T1", 0.9, 0.9, 1.0, 1, 0.90, 0.70), row("u2", "T2", 0.9, 0.9, 1.0, 1, 0.99, 0.60)]
    out = sel.select(u, 0.70)
    assert out["T1"]["winner"] is None and out["T2"]["winner"] is None
    assert out["package"]["winner"] is None and out["status"] == "STOP: no configuration passes the guards"


def test_one_family_empty_package_is_the_other():
    u = [row("u1", "T1", 0.9, 0.9, 1.0, 1, 0.90, 0.70), row("u2", "T2", 0.8, 0.9, 1.0, 1, 0.99, 0.70)]
    out = sel.select(u, 0.70)
    assert out["T1"]["winner"] is None and out["package"]["winner"] == "u2"


def test_parameters_changed_counts_against_installed_defaults():
    byte = {"fuse_score": True, "match_thresh": 0.8, "new_track_thresh": 0.25, "track_buffer": 30, "track_high_thresh": 0.25,
            "track_low_thresh": 0.1, "tracker_type": "bytetrack"}
    assert sel.parameters_changed({**byte, "track_low_thresh": 0.05}, byte) == 1
    assert sel.parameters_changed({**byte, "track_low_thresh": 0.05, "fuse_score": False, "track_buffer": 90}, byte) == 3
    bot = {**byte, "tracker_type": "botsort", "gmc_method": "sparseOptFlow", "with_reid": False}
    assert sel.parameters_changed({**bot, "gmc_method": "none", "track_low_thresh": 0.05}, bot) == 2
