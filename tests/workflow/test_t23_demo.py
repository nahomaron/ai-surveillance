"""T23.11 demo draw (FX-14i) and the SDG source it reads."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import ROOT, Clock
from rq1.fixtures import review_video
from rq1.review.frame import FixtureFrame
from rq1.schema.errors import ContractError
from rq1.workflow import rules as R
from rq1.workflow.demo import CALENDAR_DAYS, RUNS_PER_FAMILY, SdgDemoSource, draw_demo
from rq1.workflow.store import WorkflowStore

CONFIG = "rcf_" + "fx14idemo".ljust(26, "0")


def _id(prefix: str, tag: str) -> str:
    return f"{prefix}_{tag.ljust(26, '0')}"


class FakeSource:
    """Two families of four runs, two cameras per run, one NM episode on the first camera."""

    configuration, path, source_root = "BL-6", "t21_oracle", "fixture"

    def __init__(self, video: Path) -> None:
        self.video = video

    def runs_by_family(self):
        return {f"fam{f}": [f"run{f}{k}" for k in range(1, 5)] for f in "ab"}

    def recordings(self, run):
        return [_id("rec", f"{run}c{c}") for c in (1, 2)]

    def camera(self, rec):
        tag = rec[4:].rstrip("0")
        eps = []
        if tag.endswith("c1"):
            eps = [{"ep_id": _id("ep", tag), "recording_id": rec, "camera_id": _id("cam", tag), "config_id": CONFIG, "g2_label": "lbl_nm",
                    "summary_label": "NM", "local_t_start_s": 4.0, "local_t_end_s": 5.0, "minclr_m": 0.6, "minclr_m_null_reason": None,
                    "geometry_method": "full_camera", "E_ep": 1, "video": str(self.video), "fps": 10.0, "clip_start_s": 1.0,
                    "clip_end_s": 8.0, "width": review_video.W, "height": review_video.H, "synthetic": True, "s5_artifact_id": "art_x"}]
        return {"rec_id": rec, "camera_id": _id("cam", tag), "s1": "art_s1", "segments": [{"t_start_tl_s": 0.0, "t_end_tl_s": 10.0, "coverage_state": "usable"}],
                "episodes": eps, "s5": "art_" + tag if eps else None, "has_source_output": True}


@pytest.fixture
def store(tmp_path):
    s = WorkflowStore(tmp_path / "store", clock=Clock(), kdf_iterations=1000)
    s.create_owner("Owner", "pw")
    return s


def _batch(store: WorkflowStore, recordings: list[str], pilot: bool = True):
    a = store.add_annotator("R-A", "c_layer_reviewer", "trained", True, "pw-a")
    b = store.add_annotator("R-B", "c_layer_reviewer", "trained", True, "pw-b")
    targets = [{"target_type": "system_episode", "target_id": _id("ep", f"t22{k:03d}"), "recording_id": r, "config_id": CONFIG,
                "g2_label": None, "stratum": "PC"} for k, r in enumerate(recordings)]
    return store.create_batch(FixtureFrame(targets, config_id=CONFIG), 7, [a["anr_id"], b["anr_id"]], None, pilot=pilot), targets


def test_fx14i_draw_refused_when_a_demo_run_is_in_a_t22_batch(store, video):
    src = FakeSource(video)
    all_recs = [r for runs in src.runs_by_family().values() for run in runs for r in src.recordings(run)]
    _batch(store, all_recs)
    before = sorted(p.name for p in store.root.iterdir())
    with pytest.raises(ContractError) as err:
        draw_demo(store, src, 2026111903)
    assert err.value.code == "ERR-SPEC" and "T23.11 (b)" in str(err.value)
    assert sorted(p.name for p in store.root.iterdir()) == before  # nothing written
    assert store.demo_manifest() is None and store.establishments() == {} and store.reports() == []


def test_fx14i_batch_after_draw_has_no_demo_episode(store, video):
    src = FakeSource(video)
    m = draw_demo(store, src, 2026111903, {"n_flag_min": 3, "n_flag_min_sm": 2})
    demo_recs = {r for run in m["runs"] for r in run["camera_rec_ids"]}
    all_recs = [r for runs in src.runs_by_family().values() for run in runs for r in src.recordings(run)]
    manifest, targets = _batch(store, all_recs)
    drawn = {t["target_id"]: t["recording_id"] for t in targets}
    assert manifest["target_ids"] and not {drawn[t] for t in manifest["target_ids"]} & demo_recs
    assert manifest["excluded_demo_targets"] == len(demo_recs)


def test_demo_draw_shape_manifest_and_reproducibility(tmp_path, video):
    out = []
    for k in range(2):
        s = WorkflowStore(tmp_path / f"s{k}", clock=Clock(), kdf_iterations=1000)
        m = draw_demo(s, FakeSource(video), 2026111903, {"n_flag_min": 3, "n_flag_min_sm": 2})
        assert s._check("demo_manifest", m) is None
        assert json.loads((s.root / "demo_manifest.json").read_text()) == m
        assert len(m["est_records"]) == 2 and len(m["runs"]) == 2 * RUNS_PER_FAMILY == len(m["areas"])
        assert all(0 <= r["calendar_offset_s"] < CALENDAR_DAYS * 86400 for r in m["runs"])
        assert all(e["demo"] for e in s.establishments().values())
        assert len(s.reports()) == 2 * RUNS_PER_FAMILY  # one NM episode per run -> one report per area
        assert (s.config()["n_flag_min"], s.config()["n_flag_min_sm"]) == (3, 2)
        r = s.reports()[0]
        assert "(simulated calendar)" in r.fields["description"] and r.fields["ai_label"] == "candidate near miss"
        with pytest.raises(ContractError):
            draw_demo(s, FakeSource(video), 1)  # the manifest is immutable
        out.append([(r["run"], r["calendar_offset_s"]) for r in m["runs"]])
    assert out[0] == out[1]


@pytest.mark.skipif(not (ROOT / "out/s0_sdg/index.json").exists(), reason="SDG outputs not present on this computer")
def test_sdg_source_families_match_d35():
    src = SdgDemoSource(ROOT)
    fam = src.runs_by_family()
    freeze = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())["split"]["families"]
    assert {k: len(v) for k, v in fam.items()} == {f["family"]: f["validation"] for f in freeze}
    assert src.path in ("detector_path_pilot_d45", "t21_oracle")
