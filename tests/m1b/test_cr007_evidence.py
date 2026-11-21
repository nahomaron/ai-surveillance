"""D-47 item 2: decomposition of a floor-position error along and across the camera's viewing direction (diagnosis only).

Definitions (stated in the report and in CR-007):
- line of sight: the unit vector on the floor from the camera centre's floor point C to the true position T;
  along = (E - T) . u (positive: the estimate lies beyond the truth, farther from the camera); across = |(E - T) x u|;
- optical axis: the same with u = the camera's optical axis (third row of R_cam_from_world) projected on the floor.
- camera centre: C = -R^T t (R_cam_from_world, t_cam_from_world_m).
Hand values:
  C = (0, 0); T = (10, 0); E = (9, 0.5)   -> u = (1, 0); E - T = (-1, 0.5); along = -1.0, across = 0.5
  C = (0, 0); T = (3, 4);  E = (3.6, 4.8) -> u = (0.6, 0.8); E - T = (0.6, 0.8); along = 0.6*0.6 + 0.8*0.8 = 1.0, across = 0
  R = identity rotated so the camera's z axis is world (0, 1, -1)/sqrt2 -> floor axis (0, 1)
  camera centre: R = I, t = (1, 2, 3) -> C = (-1, -2, -3)
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import cr007_evidence as ce  # noqa: E402


def test_line_of_sight_case_1():
    a, c = ce.decompose((9.0, 0.5), (10.0, 0.0), ce.unit((10.0, 0.0), (0.0, 0.0)))
    assert math.isclose(a, -1.0) and math.isclose(c, 0.5)


def test_line_of_sight_case_2():
    a, c = ce.decompose((3.6, 4.8), (3.0, 4.0), ce.unit((3.0, 4.0), (0.0, 0.0)))
    assert math.isclose(a, 1.0) and math.isclose(c, 0.0, abs_tol=1e-12)


def test_camera_centre():
    R = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert ce.camera_centre(R, [1.0, 2.0, 3.0]) == (-1.0, -2.0, -3.0)


def test_optical_axis_on_floor():
    s = 1 / math.sqrt(2)
    R = [1, 0, 0, 0, s, s, 0, s, -s]  # third row = camera z axis in world = (0, s, -s)
    ax = ce.optical_axis_floor(R)
    assert math.isclose(ax[0], 0.0, abs_tol=1e-12) and math.isclose(ax[1], 1.0)
