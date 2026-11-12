"""T-04. Expected timestamps are hand-written from E-1.2.1 section 3, Appendix N3 and Appendix T CT-T rows."""
import hashlib
import json
from pathlib import Path

import av
import pytest

from rq1.fixtures import clips

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CLIPS = {"fx_clip_a", "fx_clip_b", "fx_clip_c", "fx_clip_d", "ct_t_01_vfr", "ct_t_02_bframes", "ct_t_02_all_intra", "ct_t_03_dup_pts",
                  "ct_t_04_dropout", "ct_t_05_corrupt", "ct_t_07_file_a", "ct_t_07_file_b", "ct_t_08_untimed", "fx_10",
                  "fx_m0_pipeline"}  # added at T-16 for the M0 integration run (AR-47 item 1)


def test_fx_m0_pipeline_clip_is_50_frames_at_100_ms():
    assert clips.CLIPS["fx_m0_pipeline"].times_ms == [100 * i for i in range(50)]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("clips")
    clips.build_all(out)
    return out


def states(directory, name):
    """Decode with the fault overlay: one (pts, dts, ok) tuple per packet in decode order, plus delayed frames."""
    faults = clips.read_faults(directory / f"{name}.faults.json")
    rows, frames = [], []
    with av.open(str(directory / f"{name}.mkv")) as container:
        stream = container.streams.video[0]
        for index, packet in enumerate(container.demux(stream)):
            if packet.size == 0:
                frames += [(f.pts, f.dts) for f in packet.decode()]
                continue
            clips.apply_faults(index, packet, faults)
            try:
                decoded = packet.decode()
                ok = True
            except av.error.InvalidDataError:
                decoded, ok = [], False
            rows.append((packet.pts, packet.dts, ok))
            frames += [(f.pts, f.dts) for f in decoded]
    return rows, frames


@pytest.mark.determinism
def test_catalogue_is_complete():
    assert set(clips.CLIPS) == EXPECTED_CLIPS


@pytest.mark.determinism
def test_deterministic_bytes(tmp_path, built):
    clips.build_all(tmp_path)
    for name in EXPECTED_CLIPS:
        for suffix in (".mkv", ".faults.json"):
            assert (tmp_path / f"{name}{suffix}").read_bytes() == (built / f"{name}{suffix}").read_bytes(), name


@pytest.mark.determinism
def test_committed_manifest_matches_this_decoder_build(built):
    manifest = json.loads((ROOT / "fixtures" / "clips_manifest.json").read_text())
    assert manifest["pyav"] == av.__version__
    assert set(manifest["clips"]) == EXPECTED_CLIPS
    for name, entry in manifest["clips"].items():
        assert hashlib.sha256((built / f"{name}.mkv").read_bytes()).hexdigest() == entry["sha256"], name
        assert hashlib.sha256((built / f"{name}.faults.json").read_bytes()).hexdigest() == entry["faults_sha256"], name
        assert entry["source"].strip()


@pytest.mark.determinism
def test_case_a_corrupt_but_timed(built):
    rows, frames = states(built, "fx_clip_a")
    assert rows == [(0, 0, True), (33, 33, False), (66, 66, True), (100, 100, True)]
    assert frames == [(0, 0), (66, 66), (100, 100)]


@pytest.mark.determinism
def test_case_b_untimed_depth_zero(built):
    rows, frames = states(built, "fx_clip_b")
    assert rows == [(0, 0, True), (None, None, True), (66, 66, True), (100, 100, True)]
    assert frames[1] == (None, None)


@pytest.mark.determinism
def test_case_c_dts_only_with_b_frames_depth_2(built):
    rows, frames = states(built, "fx_clip_c")
    assert [r[0] for r in rows] == [0, 100, None, 66]  # decode order I0 P100 B33 B66, f1 PTS stripped
    assert rows[2][1] == 33
    presentation = [0, 3, 2]  # index of 0, 100, 66 among 0, 33, 66, 100
    decode = [0, 1, 3]
    assert max(abs(p - d) for p, d in zip(presentation, decode)) == 2
    assert (None, 33) in frames


@pytest.mark.determinism
def test_case_d_dts_only_depth_zero(built):
    rows, frames = states(built, "fx_clip_d")
    assert rows == [(0, 0, True), (None, 33, True), (66, 66, True), (100, 100, True)]
    assert frames[1] == (None, 33)


@pytest.mark.determinism
def test_ct_t_01_vfr_alternates_33_and_50_ms(built):
    rows, _ = states(built, "ct_t_01_vfr")
    deltas = [b[0] - a[0] for a, b in zip(rows, rows[1:])]
    assert set(deltas[::2]) == {33} and set(deltas[1::2]) == {50}
    assert rows[-1][0] < 10000 <= rows[-1][0] + 50


@pytest.mark.determinism
def test_ct_t_02_b_frames_reorder_and_all_intra_copy_has_same_times(built):
    b_rows, _ = states(built, "ct_t_02_bframes")
    i_rows, _ = states(built, "ct_t_02_all_intra")
    assert [r[0] for r in b_rows] != sorted(r[0] for r in b_rows)
    assert sorted(r[0] for r in b_rows) == [r[0] for r in i_rows]


@pytest.mark.determinism
def test_ct_t_03_two_frames_share_a_pts(built):
    rows, _ = states(built, "ct_t_03_dup_pts")
    pts = [r[0] for r in rows]
    assert pts[9] == pts[10] and len(pts) - len(set(pts)) == 1


@pytest.mark.determinism
def test_ct_t_04_four_second_dropout(built):
    rows, _ = states(built, "ct_t_04_dropout")
    deltas = [b[0] - a[0] for a, b in zip(rows, rows[1:])]
    assert deltas.count(4000) == 1 and set(deltas) == {33, 4000}


@pytest.mark.determinism
def test_ct_t_05_fifteen_undecodable_frames(built):
    rows, _ = states(built, "ct_t_05_corrupt")
    assert [i for i, r in enumerate(rows) if not r[2]] == list(range(20, 35))
    assert all(r[0] is not None for r in rows)


@pytest.mark.determinism
def test_ct_t_07_two_files(built):
    a, _ = states(built, "ct_t_07_file_a")
    b, _ = states(built, "ct_t_07_file_b")
    assert len(a) == len(b) == 60 and a[0][0] == b[0][0] == 0
    assert (built / "ct_t_07_file_a.mkv").read_bytes() != (built / "ct_t_07_file_b.mkv").read_bytes()


@pytest.mark.determinism
def test_ct_t_08_untimed_stream(built):
    rows, _ = states(built, "ct_t_08_untimed")
    assert len(rows) == 20 and all(r[0] is None and r[1] is None for r in rows)


@pytest.mark.determinism
def test_fx_10_vfr_gap_and_one_corrupt_frame(built):
    rows, _ = states(built, "fx_10")
    assert sum(1 for r in rows if not r[2]) == 1
    deltas = [b[0] - a[0] for a, b in zip(rows, rows[1:])]
    assert deltas.count(500) == 1 and {33, 50} < set(deltas)


@pytest.mark.determinism
def test_no_video_is_tracked_by_git():
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "*.mkv", "*.mp4"], cwd=ROOT, capture_output=True, text=True).stdout
    assert tracked == ""
