"""Frame-quality rules version `rv2-provisional` (D-25 proposal, applied provisionally under D-26; Architect review pending).

Rules (8-bit luma, integer arithmetic): black = nearest-rank P99 of luma <= 32; overexposed = at least half the pixels with
luma >= 250; frozen = luma byte-identical to the previous timed frame, inside a run whose span t(last) - t(first) >= 0.5 s,
every frame after the first in the run flagged. Excluding: decode_error, black, overexposed, frozen. Expected values are
hand calculations written beside each assertion."""
from fractions import Fraction

import av
import numpy as np
import pytest

from rq1.decode import quality, timestamps, video
from rq1.decode.timestamps import DecodeConfig, PacketRecord

TB = Fraction(1, 1000)


def cfg(version="rv2-provisional"):  # the superseded provisional rule, kept reproducible
    return DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=version, declared={})


def luma(values):
    return np.array(values, dtype=np.uint8).reshape(1, -1)


@pytest.mark.determinism
def test_black_nearest_rank_p99():
    # 100 pixels: 99 at 10, 1 at 200. Nearest rank ceil(0.99 * 100) = 99 -> the 99th smallest is 10 <= 32 -> black.
    assert quality.stats(luma([10] * 99 + [200])).p99 == 10
    assert "black" in quality.frame_flags(quality.stats(luma([10] * 99 + [200])), quality.RV2_PROVISIONAL)
    # 98 at 10, 2 at 200: the 99th smallest is 200 -> not black.
    assert quality.stats(luma([10] * 98 + [200] * 2)).p99 == 200
    assert "black" not in quality.frame_flags(quality.stats(luma([10] * 98 + [200] * 2)), quality.RV2_PROVISIONAL)
    # Boundary: P99 = 32 is black, 33 is not.
    assert "black" in quality.frame_flags(quality.stats(luma([32] * 100)), quality.RV2_PROVISIONAL)
    assert "black" not in quality.frame_flags(quality.stats(luma([33] * 100)), quality.RV2_PROVISIONAL)


@pytest.mark.determinism
def test_overexposed_half_of_pixels():
    # 50 of 100 pixels at 250 -> 2 * 50 >= 100 -> overexposed; 49 of 100 -> not. 249 never counts.
    assert quality.frame_flags(quality.stats(luma([250] * 50 + [100] * 50)), quality.RV2_PROVISIONAL) == {"overexposed"}
    assert quality.frame_flags(quality.stats(luma([250] * 49 + [100] * 51)), quality.RV2_PROVISIONAL) == set()
    assert quality.frame_flags(quality.stats(luma([249] * 100)), quality.RV2_PROVISIONAL) == set()


def packets(images, step=33):
    return [PacketRecord(i, i, i * step, i * step, True, quality.stats(img)) for i, img in enumerate(images)]


def varied(i):
    return luma([100 + (i % 50)] * 4)


@pytest.mark.determinism
def test_frozen_run_of_half_a_second():
    # 33 ms steps. Frames 2..17 identical: 16 frames, span (17 - 2) * 33 = 495 ms < 500 -> no frozen flag.
    images = [varied(i) for i in range(2)] + [luma([200, 210, 220, 230])] * 16 + [varied(i) for i in range(18, 25)]
    r = timestamps.resolve(packets(images), TB, cfg(), None)
    assert not any("frozen" in f.quality_flags for f in r.frames)
    # Frames 2..18 identical: 17 frames, span 16 * 33 = 528 ms >= 500 -> frames 3..18 flagged (16 frames), frame 2 not.
    images = [varied(i) for i in range(2)] + [luma([200, 210, 220, 230])] * 17 + [varied(i) for i in range(19, 25)]
    r = timestamps.resolve(packets(images), TB, cfg(), None)
    frozen = [f.seq for f in r.frames if "frozen" in f.quality_flags]
    assert frozen == list(range(3, 19))
    by_seq = {f.seq: f for f in r.frames}
    assert by_seq[2].eligible and not by_seq[3].eligible and by_seq[3].support_status == "excluded_own_support"
    # 16 excluded frames x 33 ms of support -> 528 ms unusable, reason excluded_frame + frozen.
    unusable = [p for p in r.pieces if p.state == "unusable"]
    assert sum(p.support for p in unusable) == Fraction(528, 1000)
    assert all(p.reasons == ("excluded_frame", "frozen") for p in unusable)


@pytest.mark.determinism
def test_rv1_ignores_pixel_statistics():
    images = [luma([0] * 4)] * 30  # black and frozen throughout
    r1 = timestamps.resolve(packets(images), TB, cfg("rv1"), None)
    assert all(f.quality_flags == [] and f.eligible for f in r1.frames)
    r2 = timestamps.resolve(packets(images), TB, cfg(), None)
    assert all("black" in f.quality_flags for f in r2.frames)
    # Frame 0 is black only; frames 1..29 are black and frozen (span 29 * 33 = 957 ms).
    assert r2.frames[0].quality_flags == ["black"] and r2.frames[1].quality_flags == ["black", "frozen"]


@pytest.mark.determinism
def test_rv2_needs_pixel_statistics():
    with pytest.raises(Exception):
        timestamps.resolve([PacketRecord(i, i, i * 33, i * 33, True) for i in range(5)], TB, cfg(), None)


@pytest.mark.determinism
def test_pyav_reader_supplies_luma_statistics(tmp_path):
    # Encode 6 frames: 3 black (Y = 16 everywhere after yuv conversion of RGB 0) and 3 white (Y = 235 limited range).
    path = tmp_path / "q.mp4"
    with av.open(str(path), "w") as out:
        stream = out.add_stream("mpeg4", rate=30)
        stream.width, stream.height, stream.pix_fmt = 64, 64, "yuv420p"
        stream.codec_context.qscale = 1
        for k in range(6):
            frame = av.VideoFrame.from_ndarray(np.full((64, 64, 3), 0 if k < 3 else 255, np.uint8), format="rgb24")
            for p in stream.encode(frame):
                out.mux(p)
        for p in stream.encode():
            out.mux(p)
    records, _ = video.read_packets(path, luma_stats=True)
    assert [r.luma is not None for r in records] == [True] * 6
    p99 = [r.luma.p99 for r in sorted(records, key=lambda r: r.seq)]
    assert all(v <= 32 for v in p99[:3]) and all(v > 200 for v in p99[3:])
    records, _ = video.read_packets(path)
    assert all(r.luma is None for r in records)  # rv1 runs decode no pixels


@pytest.mark.determinism
def test_needs_pixels_by_version():
    assert quality.needs_pixels("rv2-provisional") and not quality.needs_pixels("rv1")


@pytest.mark.determinism
def test_p1_nearest_rank_is_statistics_only():
    # D-25 Architect review item 1a: P1 by the same nearest-rank method as P99, the ceil(0.01 n)-th smallest value.
    # 100 pixels, 1 at 0 and 99 at 50: rank ceil(1.00) = 1 -> 0. 101 pixels, 1 at 0 and 100 at 50: rank ceil(1.01) = 2 -> 50.
    assert quality.stats(luma([0] + [50] * 99)).p1 == 0
    assert quality.stats(luma([0] + [50] * 100)).p1 == 50
    # A single pixel: rank 1 for both -> P1 = P99 = the value.
    s = quality.stats(luma([7]))
    assert (s.p1, s.p99) == (7, 7)
    # P1 changes no flag: a flat frame at 16 (spread 0) and a dark ramp 0..31 (spread > 0) are both black under rv2-provisional.
    assert quality.frame_flags(quality.stats(luma([16] * 100)), quality.RV2_PROVISIONAL) == {"black"}
    assert quality.frame_flags(quality.stats(luma(list(range(32)) * 4)), quality.RV2_PROVISIONAL) == {"black"}
