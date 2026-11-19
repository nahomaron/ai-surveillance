"""T-25p population (D-45 items 0 and 3a): SDG validation cameras with an ORACLE-S3, minus the 20 T-22 probe cameras.
Expected 206 = 226 - 20 (D-45 item 3a). Needs the local dataset records; skipped without them."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
pytestmark = pytest.mark.skipif(not (ROOT / "out/s0_sdg/index.json").exists(), reason="local dataset records not present")


def test_population_excludes_probe_cameras():
    import pilot_common as pc
    ctx = pc.m.Context("sdg")
    cams = pc.pilot_cameras(ctx)
    probe = set(pc.probe_cameras())
    assert len(probe) == 20 and len(ctx.validation_cameras()) == 226
    assert len(cams) == 206
    assert not probe & {c["rec_id"] for c in cams}
    assert all(ctx.is_validation(c) for c in cams)
    assert [c["rec_id"] for c in cams] == sorted(c["rec_id"] for c in cams)


def test_test_partition_refused():
    import pilot_common as pc
    from rq1.schema.errors import ContractError
    ctx = pc.m.Context("sdg")
    other = next(c for c in ctx.counts["cameras"] if not ctx.is_validation(c))
    with pytest.raises(ContractError):
        ctx.camera(other["rec_id"])
