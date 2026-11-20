"""Helpers for the T23 workflow tests: a workflow store and running server built from an Appendix T T23 fixture
(FX-14 ... FX-14i), and an HTTP client with a cookie jar. Everything goes through the app's sign-in and form posts."""
from __future__ import annotations

import http.client
import json
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import pytest

from rq1.fixtures import review_video
from rq1.workflow import rules as R
from rq1.workflow.server import make_server
from rq1.workflow.store import WorkflowStore

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "records"


def load_fixture(fixture_id: str) -> dict:
    return json.loads((FIX / f"{fixture_id}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def video(tmp_path_factory) -> Path:
    return review_video.write(tmp_path_factory.mktemp("wfvideo") / "fixture.mp4")


class Clock:
    """Deterministic clock: each call advances 1.5 s."""

    def __init__(self, start: datetime | None = None) -> None:
        self.t = start or datetime(2026, 11, 19, 9, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        self.t += timedelta(seconds=1.5)
        return self.t


class Client:
    def __init__(self, port: int) -> None:
        self.port, self.cookie = port, ""

    def request(self, method: str, path: str, body: str | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        h = {"Cookie": self.cookie} if self.cookie else {}
        if body is not None:
            h["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=h)
        resp = conn.getresponse()
        raw = resp.read()
        if resp.getheader("Set-Cookie"):
            self.cookie = resp.getheader("Set-Cookie").split(";")[0]
        conn.close()
        return resp.status, dict(resp.getheaders()), raw

    def get(self, path: str):
        return self.request("GET", path)

    def text(self, path: str) -> tuple[int, str]:
        status, _, raw = self.get(path)
        return status, raw.decode("utf-8", "replace")

    def post(self, path: str, data: dict | list):
        return self.request("POST", path, urlencode(data, doseq=True))


def episode(e: dict, video: Path) -> dict:
    """A fixture episode with what the server needs to play its clip (the fixture video stands in for the recording)."""
    return {**e, "timeline_id": "tl_" + "fx14".ljust(26, "0"), "video": str(video), "fps": float(review_video.FPS),
            "clip_start_s": 1.0, "clip_end_s": 6.0, "width": review_video.W, "height": review_video.H, "synthetic": True}


class WfApp:
    def __init__(self, tmp: Path, video: Path, fixture: dict, params: dict | None = None, demo_source=None) -> None:
        self.fixture, self.video = fixture, video
        w = fixture["inputs"]["world"]
        self.calendar = R.parse_utc(w["calendar_start_utc"])
        self.store = WorkflowStore(tmp / "store", clock=Clock(), kdf_iterations=1000)
        self.store.create_owner("Owner", "owner-pass")
        self.store.set_config({**R.PARAMS, **(params or {})})
        self.store.add_establishment(w["establishment"]["name"], w["establishment"]["demo"], est_id=w["establishment"]["est_id"])
        a = w["area"]
        self.store.add_area(a["est_id"], a["name"], a["camera_ids"], area_id=a["area_id"])
        self.ids = {}
        for u in w["users"]:
            self.ids[u["pseudonym"]] = self.store.add_user(u["pseudonym"], u["roles"], u["est_id"], u["area_ids"], f"pw-{u['pseudonym']}")["user_id"]
        for m in w["monitoring"]:
            self.store.set_monitoring(m["camera_id"], [{"start_utc": R.utc(self.calendar + timedelta(seconds=s["t_start_s"])),
                                                        "end_utc": R.utc(self.calendar + timedelta(seconds=s["t_end_s"])),
                                                        "coverage_state": s["coverage_state"]} for s in m["segments"]], True, "fixture")
        self.server = make_server(self.store, {}, demo_source=demo_source)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.area_id, self.est_id, self.period = a["area_id"], a["est_id"], w["period"]

    def intake(self, episodes: list[dict] | None = None) -> list[str]:
        eps = [episode(e, self.video) for e in (self.fixture["inputs"]["episodes"] if episodes is None else episodes)]
        return self.store.intake(self.area_id, eps, self.calendar)

    def client(self, pseudonym: str | None = None) -> Client:
        c = Client(self.port)
        if pseudonym in (None, "OWNER", "Owner"):
            if pseudonym:
                c.post("/login", {"profile": "owner", "passphrase": "owner-pass"})
            return c
        status, headers, _ = c.post("/login", {"profile": self.ids[pseudonym], "passphrase": f"pw-{pseudonym}"})
        assert status == 303, status
        return c

    def act(self, pseudonym: str, report_id: str, action: str, **form):
        c = self.client(pseudonym)
        status, page = c.text(f"/wf/report/{report_id}")
        assert status == 200, page
        return c.post(f"/wf/report/{report_id}/act", {"action": action, **form})

    def run_steps(self, report_id: str | None = None) -> str | None:
        for step in self.fixture["inputs"]["steps"]:
            who, action = step["as"], step["action"]
            if action == "create_human":
                when = R.utc(self.calendar + timedelta(seconds=step["offset_s"]))[:19]
                status, headers, _ = self.client(who).post("/wf/file", {"kind": step["kind"], "area_id": self.area_id,
                                                                        "occurred_at": when, "description": step["description"]})
                assert status == 303, status
                report_id = headers["Location"].rsplit("/", 1)[1]
            elif action == "hours":
                status, _, _ = self.client("OWNER").post("/wf/setup/hours", {"est_id": self.est_id, "period": self.period,
                                                                            "hours_worked": str(step["hours_worked"])})
                assert status == 303
            elif action == "edit_fields":
                status, _, body = self.act(who, report_id, "edit_fields", **step["fields"])
                assert status == 303, body
            else:
                form = {k: v for k, v in step.items() if k not in ("as", "action")}
                status, _, body = self.act(who, report_id, action, **form)
                assert status == 303, body
        return report_id

    def indicators(self, area_id: str | None = None, **params) -> dict:
        cfg = {**self.store.config(), **params}
        ind = R.indicators(self.store.reports(), self.est_id, area_id, self.period, self.store.areas(), self.store.monitoring(),
                           self.store.hours(self.est_id, self.period), cfg, self.store.clock())
        return {"ind": ind, "flags": R.flags(ind, cfg)}

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def make_wf(tmp_path, video):
    apps = []

    def build(fixture_id: str, **kw) -> WfApp:
        app = WfApp(tmp_path / f"wf{len(apps)}", video, load_fixture(fixture_id), **kw)
        apps.append(app)
        return app

    yield build
    for app in apps:
        app.close()


def links(page: str) -> list[str]:
    return sorted(set(re.findall(r'href="(/[^"#]*)"', page)))
