"""Appendix T T21 (contract E-1.2.19): interaction references from simulator truth, the four tests the ruling names, run
through the M1a driver's own reference unit and evaluation functions on a synthetic recording (TEST-ONLY geometry).

Scene: 30 frames at 10 fps. Person from (3.0, 0) moving at -0.5 m/s along x; forklift (3.03 x 1.13 m, yaw 0) from the
origin at +1 m/s. Footprint clearance at t = 0 is 3 - 1.515 - 0.30 = 1.185 m < d_p = 2 m, so BL-6 has P on every frame
and one episode per POW."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/m1a"))
import evaluate_m1a as ev  # noqa: E402
import m1a_common as m  # noqa: E402
import run_m1a  # noqa: E402
from rq1.adapters import oracle_truth as ot  # noqa: E402
from rq1.evaluation import association as assoc  # noqa: E402
from rq1.evaluation import matching as mt  # noqa: E402
from rq1.fixtures import synthetic_s1  # noqa: E402

N = 30
PROV = ("test", "test")
BOX_P, BOX_F = (100, 100, 139, 199), (300, 100, 499, 219)  # dataset pixel indices, inside the 1000 x 600 image


def scene(person_visible, fork_visible):
    s1 = synthetic_s1.build(N)
    frames = []
    for k in range(N):
        t = k / 10
        frames.append({"p": ot.Obs("person", BOX_P if k in person_visible else None, None, (3.0 - 0.5 * t, 0.0), None),
                       "f": ot.Obs("forklift", BOX_F if k in fork_visible else None, None, (t, 0.0), 0.0)})
    data = m.Loaded(s1, frames, {"p": "person", "f": "forklift"}, {k: k for k in range(N)}, None)
    rec = s1["frame"][0]["recording_id"]
    ctx = SimpleNamespace(ds="sdg", index={rec: {"calibration": None}})
    return ctx, rec, data


def reference(ctx, rec, data):
    unit = run_m1a.unit_reference(ctx, rec, data, PROV, "test", False, "synthetic_rendered")
    refs, groups = ev.references(SimpleNamespace(rec=rec, units={"reference": unit}))
    return unit, refs, groups


def oracle_events(ctx, rec, data, p5=None):
    s3, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], PROV)
    s4 = m.s4(ctx, data, s3, positions, "simulator_truth", m.S4_BASE, PROV)
    s5 = m.s5_build(ctx, data, s4, "BL-6", m.S4_BASE, p5 or m.S5_BASE, PROV)
    trk_key = ev.track_map(s3.tables, ev.oracle_keys(m.visible_frames(data)), data.classes)
    rows, _, _ = ev.association(s3.tables, trk_key)
    summaries, _ = assoc.summarize(rows, {f: 0.1 for f in {r["frame_index"] for r in rows}})
    return ev.system_events(s4.tables, s5.tables, rows, summaries)


@pytest.mark.determinism
def test_t21_visible_throughout_is_assessable_and_matched_by_bl6():
    ctx, rec, data = scene(range(N), range(N))
    unit, refs, groups = reference(ctx, rec, data)
    assert len(refs) == 1 and refs[0].assessable and unit["references"][0]["status"] == "assessable"
    assert groups[refs[0].ref_event_id] == frozenset({"G1"})
    records = mt.match_window(refs, oracle_events(ctx, rec, data), "G1", ev.S8["iou_m"], "rule_conformance", groups)
    assert [r["match_type"] for r in records] == ["matched"] and records[0]["temporal_iou"] == 1.0


@pytest.mark.determinism
def test_t21_never_jointly_visible_is_unobservable_reference():
    # Person visible on frames 0-14 only, forklift on 15-29 only: both exist in the truth on every frame, so the reference
    # interaction exists (T21.1), but no frame has both visible (T21.3) -> unobservable_reference, reported, not scored.
    ctx, rec, data = scene(range(0, 15), range(15, N))
    unit, refs, groups = reference(ctx, rec, data)
    assert len(refs) == 1 and not refs[0].assessable and unit["references"][0]["status"] == "unobservable_reference"
    records = mt.match_window(refs, [], "G1", ev.S8["iou_m"], "rule_conformance", groups)
    assert [r["match_type"] for r in records] == ["unobservable_reference"]


@pytest.mark.determinism
def test_t21_4_a_sweep_run_is_scored_against_the_same_reference_ids():
    ctx, rec, data = scene(range(N), range(N))
    _, refs, groups = reference(ctx, rec, data)
    ids = {r.ref_event_id for r in refs}
    for p5 in (dict(m.S5_BASE, d_p=1.5), dict(m.S5_BASE, d_p=3.0), dict(m.S5_BASE, m_gap=3)):
        records = mt.match_window(refs, oracle_events(ctx, rec, data, p5), "G1", ev.S8["iou_m"], "rule_conformance", groups)
        assert {r["ref_event_id"] for r in records if r["ref_event_id"]} <= ids
    # The reference ID does not depend on any swept value: rebuilding the reference gives the same IDs.
    assert {r.ref_event_id for r in reference(ctx, rec, data)[1]} == ids


@pytest.mark.determinism
def test_t21_2_no_g2_reference_is_produced():
    ctx, rec, data = scene(range(N), range(N))
    unit, refs, groups = reference(ctx, rec, data)
    assert all(g <= frozenset({"G1"}) for g in groups.values())
    assert not any(k.startswith("lbl_") and k[4:] in ("NM", "UD", "CT") for r in unit["references"] for k in r)
    records = mt.match_window(refs, oracle_events(ctx, rec, data), "G2", ev.S8["iou_m"], "rule_conformance", groups)
    assert not any(r["ref_event_id"] for r in records)  # no G2 reference to match or miss
