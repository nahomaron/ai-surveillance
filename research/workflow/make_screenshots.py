"""W-01 report screenshots, on fixtures only (no footage, no SDG data; D-48 step 4).

Builds a fixture workflow store under out/review/w01_fixtures/ from the T23 fixtures (FX-14c, FX-14f and a
human-started report), drives it through the application's own sign-in and form posts (the tests/workflow helpers), saves
the key pages, and renders each with headless Google Chrome (installed locally) into research/workflow/screenshots/.
Every manager decision here is a fixture step, not a decision on demo data.

Run from the repository root: PYTHONPATH=src:tests/workflow .venv/bin/python research/workflow/make_screenshots.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from conftest import WfApp, load_fixture  # tests/workflow/conftest.py
from rq1.fixtures import review_video
from rq1.workflow import rules as R

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/review/w01_fixtures"
SHOTS = ROOT / "research/workflow/screenshots"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    video = review_video.write(OUT / "fixture.mp4")
    pages: dict[str, str] = {}
    app = WfApp(OUT / "a", video, load_fixture("FX-14c"), params={"n_flag_min": 3})
    try:
        [ct] = app.intake()
        twelve = load_fixture("FX-14f")["inputs"]["episodes"][:4]
        nm_ids = app.intake(twelve)
        am, sm, ov, owner = app.client("AM-1"), app.client("SM-1"), app.client("OV-1"), app.client("OWNER")
        pages["01_area_manager_inbox"] = am.text("/wf/inbox")[1]
        pages["02_report_pending_ai"] = am.text(f"/wf/report/{nm_ids[0]}")[1]
        for k, rid in enumerate(nm_ids):
            if k < 3:
                app.act("AM-1", rid, "am_reject", reason="not_hazardous", rationale="The truck is parked with the forks down.")
            else:
                app.act("AM-1", rid, "am_approve", label="nm", rationale="The truck brakes hard as the person steps out.")
        pages["03_report_recorded"] = am.text(f"/wf/report/{nm_ids[3]}")[1]
        app.run_steps(ct)
        app.client("W-1").post("/wf/file", {"kind": "near_miss", "area_id": app.area_id, "occurred_at": "2026-11-16T08:30",
                                            "description": "A truck reversed out of aisle 3 while I was crossing; I stepped back."})
        pages["04_safety_manager_queue"] = sm.text("/wf/queue")[1]
        pages["05_incident_recordability"] = sm.text(f"/wf/report/{ct}")[1]
        pages["06_indicators_flags"] = sm.text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]
        pages["07_regulator_view"] = ov.text(f"/wf/regulator?est={app.est_id}&period={app.period}")[1]
        pages["08_file_a_report"] = app.client("W-1").text("/wf/file")[1]
        pages["09_owner_setup"] = owner.text("/wf/setup")[1]
        log = app.store.root / "wf_report_log.jsonl"
        data = bytearray(log.read_bytes())
        data[data.index(b'"state_after":"pending_am"') + 16] = ord("X")
        log.write_bytes(bytes(data))
        pages["10_broken_chain"] = sm.text(f"/wf/report/{nm_ids[3]}")[1]
    finally:
        app.close()
    for name, html in pages.items():
        assert R.lint_workflow(html) == [] or name == "10_broken_chain", name
    SHOTS.mkdir(parents=True, exist_ok=True)
    folder = OUT / "pages"
    folder.mkdir()
    for name, html in pages.items():
        html = re.sub(r'src="/wf/clip/[^"]+"', f'src="{video.as_uri()}"', html)  # static copy for the screenshot only
        path = folder / f"{name}.html"
        path.write_text(html, encoding="utf-8")
        tall = name in ("02_report_pending_ai", "03_report_recorded", "05_incident_recordability", "06_indicators_flags", "07_regulator_view", "09_owner_setup")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--window-size=1300,{2200 if tall else 1000}", "--virtual-time-budget=4000",
                        f"--screenshot={SHOTS / (name + '.png')}", path.as_uri()], check=True, capture_output=True, timeout=120)
    print(sorted(p.name for p in SHOTS.glob("*.png")))


if __name__ == "__main__":
    main()
