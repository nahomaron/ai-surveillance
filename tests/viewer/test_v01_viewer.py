"""V-01 Truth replay viewer (Owner tooling, read-only): acceptance tests of the V-01 task text (item 6).

The viewer produces no result, metric, flag, label, episode or artifact that enters any evaluation. These tests pin:
- the partition guard (frozen X0b split; validation only; ERR-SPEC otherwise, and ERR-SPEC when no frozen split exists);
- that the clearance and speeds embedded in the page are the S4 function outputs (geometry.clearance / disc_clearance as
  the S4 builder applies them; object_state speed_mps from the S4 builder) on the same frames, within 1e-9;
- a T20.1 case renders as one lost run of 20 frames;
- the four T20.2 cases (constant yaw, 75 deg/s, half-turn jump, null yaw) give the expected shading;
- byte-identical HTML for identical inputs;
- no network URL, no TEST-ONLY value, and the banner, in the page;
- the viewer package imports no S5 (rq1.events) module and no S8 (rq1.evaluation) module other than the T20.2 report-time
  function `rq1.evaluation.strata` (Owner decision, V-01 session of 14 Nov 2026; see the viewer report).

Fixture geometry (hand set-up, as in tests/events/test_t18_oracle_absence.py): camera straight down from 10 m, 1920 x 1080,
10 fps (dt = 0.1 s), 60 frames. Forklift on y = 0 at x(t) = -2.5 + t (1 m/s, yaw 0); person static at (1.0, 2.0).
Hand values: forklift speed 1 m/s on every frame whose T9.1 window has >= 3 frames; person speed 0. Clearance at frame k
(forklift centre x_f = -2.5 + 0.1 k, prior 2.0 x 1.0 m, person r = 0.30): the person centre lies 2.0 - 0.5 = 1.5 m beyond the
long side when |1.0 - x_f| <= 1.0, so clearance = 1.5 - 0.3 = 1.2 m on frames 25..45 (x_f in [0, 2]).
"""
import ast
import json
import math
import re
from pathlib import Path

import pytest

from rq1.adapters import oracle_truth as ot
from rq1.adapters import sdg_truth
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema.errors import ContractError
from rq1.substrate import builder, oracle
from rq1.viewer import guard, page, payload, settings

ROOT = Path(__file__).resolve().parents[2]
CAL = {"intrinsics_K": [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0], "R_cam_from_world": [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0],
       "t_cam_from_world_m": [0.0, 0.0, 10.0], "image_size_px": [1920, 1080]}
N = 60
FORK_PRIOR = (2.0, 1.0)
HEADER = {"dataset_row": "fixture", "run": "fixture-run", "camera": "fixture-cam", "recording_id": "rec_fixture", "viewpoint_class": "ceiling",
          "low_light": "no", "code_commit": "0" * 40, "contract": "E-1.2.18", "preregistration_sha256": "f" * 64,
          "split_artifact_id": "art_fixture", "partition": "validation"}


def _obs(cls, xy, visible, yaw=0.0):
    box3d = {"x_min": -0.2, "x_max": 0.2, "y_min": -0.2, "y_max": 0.2, "z_min": 0.0, "z_max": 1.0,
             "transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [xy[0], xy[1], 0.0, 1]]}
    if cls == "forklift":
        box3d.update(x_min=-1.0, x_max=1.0, y_min=-0.5, y_max=0.5)
    return ot.sdg_obs(CAL, sdg_truth.ObjectTruth(cls, cls, xy, yaw if cls == "forklift" else None, None, visible, box3d))[0]


def _frames(person_visible=lambda k: True, fork_yaw=lambda k: 0.0, fork_xy=lambda k: (-2.5 + k / 10, 0.0)):
    return [{"p": _obs("person", (1.0, 2.0), (1045, 300, 1090, 355) if person_visible(k) else None),
             "f": _obs("forklift", fork_xy(k), (300, 600, 500, 720), yaw=fork_yaw(k))} for k in range(N)]


def _payload(frames, s1=None):
    s1 = s1 or synthetic_s1.build(N, width=1920, height=1080)
    return payload.build(HEADER, s1, frames, {"p": "person", "f": "forklift"}, CAL, FORK_PRIOR), s1


def _obj(p, cls):
    (o,) = [o for o in p["objects"] if o["cls"] == cls]
    return o


def _at(o, seq, name):
    i = seq - o["s0"]
    return o[name][i] if 0 <= i < len(o[name]) else None


# --- partition guard ------------------------------------------------------------------------------------------------

def _split(partition_of_group):
    return {"leakage_groups": [{"leakage_group_id": g, "member_recording_ids": [f"rec_{g}"], "edge_types": ["same_session"]} for g in partition_of_group],
            "assignments": [{"leakage_group_id": g, "partition": p} for g, p in partition_of_group.items()], "frozen_utc": "2026-11-15T01:47:59Z"}


def test_refuses_a_test_partition_recording():
    split = _split({"a": "validation", "b": "test"})
    assert guard.require_validation(split, "rec_a") == "validation"
    with pytest.raises(ContractError) as e:
        guard.require_validation(split, "rec_b")
    assert e.value.code == "ERR-SPEC"


def test_refuses_a_recording_absent_from_the_split():
    with pytest.raises(ContractError) as e:
        guard.require_validation(_split({"a": "validation"}), "rec_warehouse_001")
    assert e.value.code == "ERR-SPEC"


def test_refuses_everything_when_no_frozen_split_exists(tmp_path):
    with pytest.raises(ContractError) as e:
        guard.load_frozen_split(tmp_path)
    assert e.value.code == "ERR-SPEC"


def test_refuses_when_the_freeze_record_names_a_split_artifact_that_is_missing(tmp_path):
    (tmp_path / "docs" / "preregistration").mkdir(parents=True)
    (tmp_path / "docs" / "preregistration" / "freeze_record.json").write_text(json.dumps({"split": {"artifact_id": "art_" + "a" * 26}}))
    with pytest.raises(ContractError) as e:
        guard.load_frozen_split(tmp_path)
    assert e.value.code == "ERR-SPEC"


@pytest.mark.skipif(not (ROOT / "out" / "prereg").exists(), reason="frozen split artifact not on this machine (git-ignored out/)")
@pytest.mark.determinism
def test_frozen_split_on_disk_refuses_a_test_recording_and_accepts_a_validation_one():
    split, art = guard.load_frozen_split(ROOT)
    record = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())
    assert art == record["split"]["artifact_id"]
    parts = guard.partitions(split)
    test_rec = min(r for r, p in parts.items() if p == "test")
    val_rec = min(r for r, p in parts.items() if p == "validation")
    assert guard.require_validation(split, val_rec) == "validation"
    with pytest.raises(ContractError) as e:
        guard.require_validation(split, test_rec)
    assert e.value.code == "ERR-SPEC"


def test_s1_decode_record_must_carry_the_frozen_values():
    """S1 reuse (Owner decision, V-01 session): accepted only when its decode configuration ID rebuilds from the frozen
    section 4.1 values (k_sup 1.5, f_untimed 0.05, f_sub 0.10, rv2)."""
    guard.check_decode_config(["dcf_xv2ryouaw22oljgqmrpylb4uqz"])  # the ID of every S1 artifact held for validation recordings
    with pytest.raises(ContractError) as e:
        guard.check_decode_config(["dcf_" + "a" * 26])
    assert e.value.code == "ERR-SPEC"


# --- display settings equal the frozen pre-registration ---------------------------------------------------------------

def _frozen_value(row_label):
    text = (ROOT / "docs" / "preregistration_FROZEN.md").read_text()
    line = next(l for l in text.splitlines() if l.startswith("| ") and row_label in l.split("|")[1])
    return line.split("|")[2]


def test_slider_start_values_are_the_frozen_values():
    d = settings.DISPLAY
    assert "2.0 m" in _frozen_value("*d_p* (R2)") and d["d_p_m"] == 2.0
    assert "1.0 m" in _frozen_value("*d_pc* (R3)") and d["d_pc_m"] == 1.0
    assert "2.0 s" in _frozen_value("τ (prediction horizon)") and d["tau_s"] == 2.0
    assert "**15**" in _frozen_value("***g_max***") and d["g_max_frames"] == 15
    assert d["e_fturn_deg_s"] == 5.0 and "e_fturn = 5°/s" in (ROOT / "docs" / "preregistration_FROZEN.md").read_text()
    assert "r = 0.30 m" in _frozen_value("Person footprint prior") and settings.PERSON_RADIUS_M == 0.30
    assert "3.03 × 1.13 m" in _frozen_value("Forklift footprint prior (SDG)") and settings.FORK_PRIOR["sdg"] == (3.03, 1.13)
    assert "2.68 × 1.16 m" in _frozen_value("Forklift footprint prior (SmartSpaces)") and settings.FORK_PRIOR["smartspaces"] == (2.68, 1.16)
    assert "0.3 m/s" in _frozen_value("*v_min*") and settings.V_MIN == 0.3
    assert "0.5 s" in _frozen_value("*w_v*") and settings.W_V == 0.5


# --- embedded values equal the S4 function outputs ------------------------------------------------------------------

@pytest.mark.determinism
def test_clearance_and_speeds_equal_the_s4_outputs_on_the_same_frames():
    frames = _frames(person_visible=lambda k: not 20 <= k < 30)  # a 10-frame occlusion: predicted points (<= g_max)
    p, s1 = _payload(frames)
    # S4 built by the S4 builder from the same oracle tracks
    seq = {f["decode_seq"]: f["frame_index"] for f in s1["frame"]}
    tracks, _ = ot.camera_tracks(CAL, frames, settings.DISPLAY["g_max_frames"], frozenset())
    truth, positions = ot.s3_truth(tracks, {"p": "person", "f": "forklift"}, seq)
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.18", "v", "v", ("orc_" + "a" * 26,), (), {}))
    priors, ids = payload.priors(FORK_PRIOR)
    edges = [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]
    cfg = builder.SubstrateConfig(15, 0.3, 0.5, 2.0, {"forklift"}, priors, ids, {"bsc_" + "a" * 26: edges}, 0.5)
    s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, Spec("S4", "E-1.2.18", "v", "v", ("gcf_" + "a" * 26, "sbc_" + "a" * 26), (s3.artifact_id,), {}))
    trk = {t["trk_id"]: t["class"] for t in s3.tables["track"]}
    by_index = {i: k for k, i in seq.items()}
    compared = 0
    for row in s4.tables["object_state"]:
        o = _obj(p, trk[row["track_id"]])
        got = _at(o, by_index[row["frame_index"]], "speed")
        assert (got is None) == (row["speed_mps"] is None)
        if got is not None:
            assert abs(got - row["speed_mps"]) <= 1e-9
            compared += 1
    assert compared > 80
    (pair,) = p["pairs"]
    measured = [r for r in s4.tables["pair_series"] if r["clearance_m"] is not None]
    assert len(measured) == N  # one POW over all frames, the person predicted on its 10 occluded frames
    for r in measured:
        assert abs(pair["c"][by_index[r["frame_index"]]] - r["clearance_m"]) <= 1e-9
    # hand values
    fork = _obj(p, "forklift")
    assert all(abs(_at(fork, k, "speed") - 1.0) <= 1e-9 for k in range(2, N - 2))
    assert all(abs(pair["c"][k] - 1.2) <= 1e-9 for k in range(25, 46))


# --- T20.1: one lost run of 20 frames ---------------------------------------------------------------------------------

def test_t20_1_case_renders_as_one_lost_run_of_20_frames():
    """Person dataset-visible on 0..9, on 10 (but frame 10 is not eligible in S1), not visible on 11..29, visible on 30..59.
    T20.1: frame 10 is not a visible frame, so the run is 10..29, 20 frames, of which 19 are eligible > g_max = 15: lost on
    all 20 frames (no points). Under the E-1.2.17 reading frame 10 would be visible and the run 11..29 (19 frames).
    Forklift: visible on every frame; frame 10 is not eligible -> a run of 0 eligible frames -> no point, state ineligible."""
    frames = _frames(person_visible=lambda k: k <= 10 or k >= 30)
    s1 = synthetic_s1.build(N, width=1920, height=1080, excluded=frozenset({10}))
    p, _ = _payload(frames, s1)
    person, fork = _obj(p, "person"), _obj(p, "forklift")
    states = person["st"]
    assert person["s0"] == 0 and states[:10] == "V" * 10 and states[10:30] == "L" * 20 and states[30:] == "V" * 30
    assert re.findall("L+", states) == ["L" * 20]
    assert all(_at(person, k, "x") is None for k in range(10, 30))  # lost: no oracle point, no position
    assert fork["st"][10] == "I" and fork["st"].count("I") == 1
    assert [(r[0], r[1], r[2]) for r in person["runs"]] == [(10, 20, 19)]  # (first frame, camera frames, eligible frames)


# --- T20.2 shading ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("yaw, expected", [
    (lambda k: 0.4, "F"),                                              # constant yaw: rate 0 -> false
    (lambda k: math.radians(75.0) * k / 30, "T"),                      # 75 deg/s at 30 fps (frames 0..59) -> true
    (lambda k: 0.2 + (math.pi if k >= 30 else 0.0), "F"),              # half-turn jump: fold(pi) = 0 -> false
    (lambda k: None, "U"),                                             # null yaw -> unknown
], ids=["constant", "75deg_s", "half_turn", "null_yaw"])
def test_t20_2_cases_give_the_expected_shading(yaw, expected):
    """The Architect set-up of tests/evaluation/test_t20_forklift_turning.py: 30 fps, frames 0..59, forklift static at
    (1, 2) and tracked on every frame, w_turn 0.5 s, e_fturn 5 deg/s; frame 30 (t = 1.0 s), window frames 23..37."""
    s1 = synthetic_s1.build(N, dt=1 / 30, width=1920, height=1080)
    frames = [{"f": _obs("forklift", (1.0, 2.0), (300, 600, 500, 720), yaw=yaw(k))} for k in range(N)]  # static: no heading fallback
    p = payload.build(HEADER, s1, frames, {"f": "forklift"}, CAL, FORK_PRIOR)
    fork = _obj(p, "forklift")
    assert _at(fork, 30, "turn") == expected
    if expected == "T":
        assert abs(_at(fork, 30, "yr") - 75.0) <= 1e-5  # deg/s; the S1 fixture rounds timestamps to 1e-9 s
    if expected == "U":
        assert _at(fork, 30, "yr") is None


# --- page -------------------------------------------------------------------------------------------------------------

@pytest.mark.determinism
def test_same_inputs_give_byte_identical_html():
    a = page.render(_payload(_frames(person_visible=lambda k: not 20 <= k < 30))[0])
    b = page.render(_payload(_frames(person_visible=lambda k: not 20 <= k < 30))[0])
    assert a.encode() == b.encode()


def test_html_has_no_network_url_no_test_only_value_and_the_banner():
    html = page.render(_payload(_frames())[0])
    assert settings.BANNER == "Truth replay, validation partition, simulator truth. Not a system output. Thresholds are display settings."
    assert html.count(settings.BANNER) >= 1
    assert not re.search(r"(https?:|wss?:|ftp:)//|//cdn|\bwww\.", html, re.I)
    assert not re.search(r"<(script|link|img|iframe)[^>]+(src|href)=", html, re.I)
    assert "TEST-ONLY" not in html and "TEST_ONLY" not in html
    for word in ("validated", "near miss", "near-miss", "collision", "contact", "safe"):
        assert word not in html.lower(), word
    data = page.embedded(html)
    assert data == json.loads(json.dumps(data))  # the embedded JSON parses back
    assert data["settings"]["display"] == settings.DISPLAY


def test_embedded_json_cannot_close_the_script_element():
    h = dict(HEADER, run="</script><b>x")
    html = page.render(payload.build(h, synthetic_s1.build(N, width=1920, height=1080), _frames(), {"p": "person", "f": "forklift"}, CAL, FORK_PRIOR))
    assert "</script><b>" not in html and page.embedded(html)["header"]["run"] == "</script><b>x"


# --- static check -----------------------------------------------------------------------------------------------------

def test_viewer_imports_no_s5_or_s8_module():
    allowed_s8 = {"rq1.evaluation.strata"}  # T20.2 report-time function only (Owner decision, V-01)
    pkg = ROOT / "src" / "rq1" / "viewer"
    files = sorted(pkg.glob("*.py"))
    assert files
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                # `from rq1 import events` / `from rq1.evaluation import strata` name a module; `from m import f` names m
                modules = [f"{node.module}.{a.name}" if node.module in ("rq1", "rq1.evaluation") else node.module for a in node.names]
            for name in modules:
                assert not (name == "rq1.events" or name.startswith("rq1.events.")), (path.name, name)
                if name == "rq1.evaluation" or name.startswith("rq1.evaluation."):
                    assert name in allowed_s8, (path.name, name)
    source = "\n".join(p.read_text() for p in files)
    assert "SubstrateBuilder().build(" not in source  # no POW or pair series built, nothing an S5 run could read
    assert not re.search(r"import_module\([\"']rq1\.(events|evaluation)", source)
