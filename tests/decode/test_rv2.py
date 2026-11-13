"""Frame-quality rules version `rv2` (synthetic M1a) and `rv2-real-provisional` (real footage), Architect ruling of
13 Nov 2026 on D-25 (Owner approval by forwarding it).

black iff P99(Y) <= 32 AND P99(Y) - P1(Y) <= 2 (nearest rank, as in rv2-provisional). overexposed and frozen unchanged.
low_light: recording-level tag, median P99 <= 32 over the recording's decoded frames that are not black (AR-51); a
stratum, never an exclusion. Expected values are hand calculations written beside each assertion."""
from fractions import Fraction

import numpy as np
import pytest

from rq1.decode import quality, timestamps
from rq1.decode.timestamps import DecodeConfig, PacketRecord

TB = Fraction(1, 1000)


def cfg(version):
    return DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=version, declared={})


def luma(values):
    return np.array(values, dtype=np.uint8).reshape(1, -1)


def flags(values, version=quality.RV2):
    return quality.frame_flags(quality.stats(luma(values)), version)


@pytest.mark.determinism
@pytest.mark.parametrize("version", [quality.RV2, quality.RV2_REAL])
def test_black_requires_dark_and_flat(version):
    # Flat at 16 (limited-range black): P99 = P1 = 16, spread 0 -> black.
    assert flags([16] * 100, version) == {"black"}
    # P99 = 18, P1 = 16 (spread 2) -> black. 100 px: 2 at 16, 98 at 18; ranks 1 and 99 -> 16, 18.
    assert flags([16] * 2 + [18] * 98, version) == {"black"}
    # Spread 3 (P1 16, P99 19) -> not black: a dark frame with content (red-lit range 3-16).
    assert flags([16] * 2 + [19] * 98, version) == set()
    # Dark ramp 0..31 x 4 (128 px): P1 = rank 2 -> 0, P99 = rank 127 -> 31; spread 31 -> not black.
    assert flags(list(range(32)) * 4, version) == set()
    # Flat but bright: P99 = 33 > 32 -> not black, whatever the spread.
    assert flags([33] * 100, version) == set()
    # Boundary: flat at 32 -> black; P1 30 / P99 32 (spread 2) -> black; P1 29 / P99 32 (spread 3) -> not.
    assert flags([32] * 100, version) == {"black"}
    assert flags([30] * 2 + [32] * 98, version) == {"black"}
    assert flags([29] * 2 + [32] * 98, version) == set()


@pytest.mark.determinism
def test_rv2_provisional_rule_is_unchanged():
    # The superseded provisional rule (P99 <= 32 only) stays reproducible for the recorded evidence files.
    assert flags(list(range(32)) * 4, quality.RV2_PROVISIONAL) == {"black"}
    assert flags([16] * 2 + [19] * 98, quality.RV2_PROVISIONAL) == {"black"}


@pytest.mark.determinism
@pytest.mark.parametrize("version", [quality.RV2, quality.RV2_REAL])
def test_overexposed_unchanged(version):
    assert flags([250] * 50 + [100] * 50, version) == {"overexposed"}
    assert flags([250] * 49 + [100] * 51, version) == set()


def packets(images, step=33):
    return [PacketRecord(i, i, i * step, i * step, True, quality.stats(img)) for i, img in enumerate(images)]


@pytest.mark.determinism
@pytest.mark.parametrize("version", [quality.RV2, quality.RV2_REAL])
def test_frozen_unchanged_and_flat_black_frames_excluded(version):
    # 30 identical flat frames at 16, 33 ms apart: all black; frames 1..29 also frozen (span 29 * 33 = 957 ms >= 500).
    r = timestamps.resolve(packets([luma([16] * 4)] * 30), TB, cfg(version), None)
    assert r.frames[0].quality_flags == ["black"] and r.frames[1].quality_flags == ["black", "frozen"]
    assert not any(f.eligible for f in r.frames)


@pytest.mark.determinism
@pytest.mark.parametrize("version", [quality.RV2, quality.RV2_REAL])
def test_dark_content_frames_stay_eligible(version):
    # 10 frames of a dark ramp (spread 31), each different (shifted by k): no flag, all eligible.
    images = [luma([(v + k) % 32 for v in range(32)] * 4) for k in range(10)]
    r = timestamps.resolve(packets(images), TB, cfg(version), None)
    assert all(f.quality_flags == [] and f.eligible for f in r.frames)


@pytest.mark.determinism
def test_low_light_tag():
    dark = quality.stats(luma(list(range(32)) * 4))  # P99 31, not black
    flat = quality.stats(luma([16] * 100))  # P99 16, black
    bright = quality.stats(luma([100] * 100))  # P99 100
    # All frames dark but not black: median P99 31 <= 32 -> low_light.
    assert quality.condition_tags([dark] * 5, quality.RV2) == ["low_light"]
    # 3 black + 2 bright frames: black frames are left out; median over the 2 bright frames = 100 -> no tag.
    assert quality.condition_tags([flat] * 3 + [bright] * 2, quality.RV2) == []
    # 3 dark + 2 bright: median over 5 = 31 -> low_light. 2 dark + 3 bright: median 100 -> no tag.
    assert quality.condition_tags([dark] * 3 + [bright] * 2, quality.RV2) == ["low_light"]
    assert quality.condition_tags([dark] * 2 + [bright] * 3, quality.RV2) == []
    # Even count: 2 dark (31) + 2 frames at P99 34 -> median (31 + 34) / 2 = 32.5 > 32 -> no tag.
    p34 = quality.stats(luma([34] * 100))
    assert quality.condition_tags([dark] * 2 + [p34] * 2, quality.RV2) == []
    # Every frame black: no frame left -> no tag (the frames are excluded, not low-light).
    assert quality.condition_tags([flat] * 4, quality.RV2) == []
    # rv1 and rv2-provisional give no condition tags.
    assert quality.condition_tags([dark] * 5, "rv1") == [] and quality.condition_tags([dark] * 5, quality.RV2_PROVISIONAL) == []


@pytest.mark.determinism
def test_low_light_is_never_an_exclusion():
    assert "low_light" not in quality.EXCLUSION_FLAGS[quality.RV2] | quality.EXCLUSION_FLAGS[quality.RV2_REAL]
    images = [luma([(v + k) % 32 for v in range(32)] * 4) for k in range(10)]
    r = timestamps.resolve(packets(images), TB, cfg(quality.RV2), None)
    assert r.condition_tags == ["low_light"] and all(f.eligible for f in r.frames)


@pytest.mark.determinism
def test_versions_and_labels():
    assert (quality.RV2, quality.RV2_REAL, quality.RV2_PROVISIONAL) == ("rv2", "rv2-real-provisional", "rv2-provisional")
    assert all(quality.needs_pixels(v) for v in (quality.RV2, quality.RV2_REAL, quality.RV2_PROVISIONAL))
    assert not quality.needs_pixels("rv1")
    r = timestamps.resolve([PacketRecord(i, i, i * 33, i * 33, True) for i in range(5)], TB, cfg("rv1"), None)
    assert r.condition_tags == []
