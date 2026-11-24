"""D-47 item 5: every `.venv-det` command sets YOLO_CONFIG_DIR to a git-ignored folder in the repository."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))


def test_det_env_points_inside_the_repository_and_is_ignored():
    import pilot_common as pc
    d = Path(pc.DET_ENV["YOLO_CONFIG_DIR"])
    assert d.resolve() == (ROOT / "out/m1b/ultralytics_config").resolve()
    assert pc.DET_ENV["YOLO_AUTOINSTALL"] == "false"
    # D-52 amendment: check the deepest part of the path that lies inside the working tree: the settings path itself
    # where out/ is a real folder, out where out/ is a symlink (git refuses a path beyond a symbolic link).
    rel = Path("out/m1b/ultralytics_config/Ultralytics/settings.json")
    probe = Path()
    for part in rel.parts:
        probe = probe / part
        if (ROOT / probe).is_symlink():
            break
    r = subprocess.run(["git", "check-ignore", "-q", str(probe)], cwd=ROOT)
    assert r.returncode == 0, f"the settings folder must be git-ignored ({probe})"


def test_detector_entry_points_set_the_folder_before_importing_ultralytics():
    for rel in ("research/m1b/s2_yolo_world.py", "research/m1b/zero_shot_probe.py", "src/rq1/tracking/bytetrack.py", "research/m1b/botsort_keys.py"):
        text = (ROOT / rel).read_text()
        i, j = text.find("YOLO_CONFIG_DIR"), text.find("import ultralytics")
        assert i != -1, rel
        assert j == -1 or i < j, rel


def test_run_pilot_passes_det_env_to_every_detector_subprocess():
    text = (ROOT / "research/m1b/run_pilot.py").read_text()
    assert text.count("str(DET_PY)") == text.count("env=pc.DET_ENV") >= 2
