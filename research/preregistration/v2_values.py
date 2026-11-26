"""Pre-registration v2 base values (Owner decision D-61, 26 Nov 2026, section 1.3-1.5; verbatim in
`docs/preregistration/v2_notes.md`). One source for the D-61 STEP 4 diagnostic check and the STEP 5 freeze.

Values only; every rule, label and matching definition is unchanged (contract E-1.2.26). The v1 dicts in
`research/m1a/m1a_common.py` (S4_BASE, S5_BASE, BAND_EDGES_M) stay as they are: v1 records are never changed.

Representation (AR-71):
- `m_gap_s` 1.5 s is the event definition (T25.3). The section 5.2 lifecycle record also carries `m_gap_frames`; it holds
  45 = floor(1.5 / (1/30) + 1e-9), the value T25.3 gives at delta_nom 1/30 s, which every recording v2 covers has
  (D-61 STEP 0). At run time S5 derives the frame count from m_gap_s and the recording's delta_nom (T25.3).
- g_max is a frame count (T8.1): 45 frames (1.5 s at 30 fps). For a recording that is not 30 fps see CR-038.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1a"))
import m1a_common as m  # noqa: E402

DECISION = "D-61 (26 Nov 2026)"
CONTRACT = "E-1.2.26"
DELTA_NOM_S = 1.0 / 30.0  # every recording v2 covers (D-61 STEP 0)

# Section 1.3, S4 values (v1 keys). Changed from v1: g_max 15 -> 45 frames.
S4_V2 = dict(m.S4_BASE, g_max=45)
# Section 1.3, S5 values (v1 keys). Changed from v1: pet_max 1.0 -> 1.5 s, d_p 2.0 -> 3.0 m, w_post 1.0 -> 1.5 s,
# e_dec 2.0 -> 1.0 m/s^2, k_c 3.0 -> 1.5 m/s^2; m_gap 5 frames -> m_gap_s 1.5 s (m_gap_frames 45 in the record, AR-71).
M_GAP_S = 1.5
S5_V2 = dict(m.S5_BASE, pet_max=1.5, d_p=3.0, w_post=1.5, e_dec=1.0, k_c=1.5, m_gap=45)
# Clearance band edges: 3 m added (descriptive only).
BAND_EDGES_V2 = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0]
# T25.2 on with m_gap_s (section 1.5).
JOIN_ACROSS_POW = True
# Section 1.6: N4 iou_m 0.3 (unchanged); 0.5 and 0.7 reported beside it.
IOU_M = 0.3
IOU_M_REPORTED = (0.3, 0.5, 0.7)

# Section 1.5, engineering selections (tuning-subset selections, not literature values).
DETECTOR = {"model": "YOLO-World v2-s", "mode": "zero-shot", "thresholds": {"person": 0.20, "forklift": 0.05}, "decision": "D-45"}
TRACKER_PACKAGE = "trc_7flfpx52d2siiljxkqwcorr7nz"  # D-55 / D-56; its ID hashes g_max 15 (AR-71 item 3)
T24 = {"anchor": "box_bottom_centre", "anchor_offset_m": 1.00, "anchor_taper_m": 2.0, "smartspaces_offset_scale": 0.923, "s_max_m_per_px": 0.1}
STITCH_GRID = ROOT / "research/m1b/d58_stitch_grid.json"


def stitch_selection() -> dict:
    """T25.1 values: the D-58 STEP 3 selection (D-61 STEP 3 = D-58 STEP 3, done at 66809cd)."""
    sel = json.loads(STITCH_GRID.read_text())["selection"]
    return {"chosen": sel["chosen"], "params": sel["chosen_params"]}


def stitch_params():
    from rq1.tracking import stitching
    return stitching.params_from(stitch_selection()["params"])


def changed_from_v1() -> dict:
    """{key: (v1, v2)} for every S4 / S5 value that D-61 changes (a check against section 1.3)."""
    out = {k: (m.S4_BASE[k], v) for k, v in S4_V2.items() if m.S4_BASE[k] != v}
    out.update({k: (m.S5_BASE[k], v) for k, v in S5_V2.items() if m.S5_BASE[k] != v})
    out["band_edges_m"] = (list(m.BAND_EDGES_M), list(BAND_EDGES_V2))
    return out


def s4_values(g_max: int | None = None) -> dict:
    return S4_V2 if g_max is None else dict(S4_V2, g_max=g_max)


def substrate_config(ctx, label: str, g_max: int | None = None):
    """(record, SubstrateConfig, band scheme ID, bands) at the v2 base values; `g_max` overrides (counterfactual only)."""
    return m.substrate_config(ctx, s4_values(g_max), BAND_EDGES_V2, label)


def s5_config(ctx, bl: str, label: str, join: bool, g_max: int | None = None):
    """BL configuration at the v2 base values; `join` = T25.2 on. `g_max` overrides S4 g_max (counterfactual only)."""
    return m.s5_config(ctx, bl, s4_values(g_max), S5_V2, BAND_EDGES_V2, label, m_gap_s=M_GAP_S, join_across_pow=True if join else None)
