"""V-01 display settings: start values of the viewer's rings and sliders, and the page banner.

Every value is the frozen pre-registration value (`docs/preregistration_FROZEN.md`, version 1; pinned by
tests/viewer/test_v01_viewer.py). In the viewer they are DISPLAY settings only: moving a slider changes the drawing and
nothing else; nothing is written to any configuration.
"""
from __future__ import annotations

from rq1.pipeline import prereg

BANNER = "Truth replay, validation partition, simulator truth. Not a system output. Thresholds are display settings."
CONTRACT = prereg.CONTRACT
PREREGISTRATION_PATH = "docs/preregistration_FROZEN.md"

# Slider start values (preregistration_FROZEN.md sections 4.2, 4.3, 6)
DISPLAY = {"d_p_m": 2.0, "d_pc_m": 1.0, "tau_s": 2.0, "g_max_frames": 15, "e_fturn_deg_s": prereg.E_FTURN_DEG_S}
# Slider ranges (display only)
RANGES = {"d_p_m": (0.0, 6.0, 0.1), "d_pc_m": (0.0, 4.0, 0.1), "tau_s": (0.0, 6.0, 0.1), "g_max_frames": (0, 120, 1), "e_fturn_deg_s": (0.0, 30.0, 0.5)}

# S4 inputs used to call the S4 functions (section 4.2)
G_MAX = DISPLAY["g_max_frames"]
V_MIN, W_V, TAU_S, V_PART = 0.3, 0.5, 2.0, 0.5
PERSON_RADIUS_M = 0.30
FORK_PRIOR = {"sdg": (3.03, 1.13), "smartspaces": (2.68, 1.16)}  # length x width, anchor centre
W_TURN_S, E_FTURN_RAD_S = prereg.W_TURN_S, prereg.E_FTURN_RAD_S  # T20.2 (section 6)

# Section 4.1: the decode values an S1 artifact must carry to be read by the viewer
FROZEN_DECODE = {"k_sup": 1.5, "f_untimed": 0.05, "f_sub": 0.10, "rules_version": "rv2"}

PLAY_RATES = (0.25, 0.5, 1.0, 2.0)
