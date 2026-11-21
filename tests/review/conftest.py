"""Shared helpers for the V-02 tests: a fixture video, an HTTP client with a cookie jar, and a store + server built from
an Appendix T T22 fixture (FX-13 ... FX-13f)."""
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
from rq1.review import protocol as P
from rq1.review.frame import OUTLINE_COLOURS, FixtureFrame
from rq1.review.registry import StoreRegistry
from rq1.review.server import make_server
from rq1.review.store import Store

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "records"
SEED = 2026111901


def load_fixture(fixture_id: str) -> dict:
    return json.loads((FIX / f"{fixture_id}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def video(tmp_path_factory) -> Path:
    return review_video.write(tmp_path_factory.mktemp("video") / "fixture.mp4")


class Clock:
    """Deterministic clock: each call advances 1.5 s."""

    def __init__(self) -> None:
        self.t = datetime(2026, 11, 19, 9, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        self.t += timedelta(seconds=1.5)
        return self.t


def clip_target(t: dict, video: Path, onset: float = 3.0, iplus_end: float = 5.0) -> dict:
    """A fixture target with what the server needs to play it (T22.4)."""
    start, end = P.clip_window(onset, iplus_end, 0.0, 10.0, P.PARAMS["c_pad_s"])
    b = review_video.boxes()
    return {"target_type": t["target_type"], "target_id": t["target_id"], "recording_id": t["recording_id"],
            "config_id": t["config_id"], "g2_label": t["g2_label"], "stratum": t["summary_label"],
            "video": str(video), "clip_start_s": start, "clip_end_s": end, "fps": float(review_video.FPS),
            "width": review_video.W, "height": review_video.H,
            "outlines": [{"colour": OUTLINE_COLOURS["person"], "boxes": [x for x in b["person"] if start <= x[0] < end]},
                         {"colour": OUTLINE_COLOURS["forklift"], "boxes": [x for x in b["forklift"] if start <= x[0] < end]}]}


def filler(config_id: str, video: Path, n: int = 3, prefix: str = "pilot") -> list[dict]:
    out = []
    for k in range(n):
        tid = _pad("ep", prefix, k)
        out.append(clip_target({"target_type": "system_episode", "target_id": tid, "recording_id": _pad("rec", prefix, k),
                                "config_id": config_id, "g2_label": None, "summary_label": "PC"}, video))
    return out


def _pad(prefix: str, tag: str, k: int) -> str:
    """A 26-character ID body: the tag, then k zero-padded (so k = 1 and k = 10 differ)."""
    return f"{prefix}_{tag}{k:0{26 - len(tag)}d}"


class Client:
    def __init__(self, port: int) -> None:
        self.port, self.cookie = port, ""

    def request(self, method: str, path: str, data: dict | None = None, headers: dict | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = dict(headers or {})
        if self.cookie:
            h["Cookie"] = self.cookie
        body = None
        if data is not None:
            body = urlencode(data)
            h["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=h)
        resp = conn.getresponse()
        raw = resp.read()
        set_cookie = resp.getheader("Set-Cookie")
        if set_cookie:
            self.cookie = set_cookie.split(";")[0]
        conn.close()
        return resp.status, dict(resp.getheaders()), raw

    def get(self, path: str, **kw):
        return self.request("GET", path, **kw)

    def post(self, path: str, data: dict):
        return self.request("POST", path, data=data)

    def text(self, path: str) -> tuple[int, str]:
        status, _, raw = self.get(path)
        return status, raw.decode("utf-8", "replace")

    def login(self, profile_id: str, passphrase: str) -> None:
        status, headers, _ = self.post("/login", {"profile": profile_id, "passphrase": passphrase})
        assert status == 303 and headers["Location"] == "/home", status


class App:
    """A validation store and a running server for one T22 fixture."""

    def __init__(self, tmp: Path, video: Path, fixture: dict | None = None, targets: list[dict] | None = None,
                 annotators: list[dict] | None = None, with_pilot: bool = True) -> None:
        self.fixture = fixture
        self.registry = StoreRegistry(tmp / "registry.json")  # T23.25 (a): a store opens only when registered
        self.registry.register(tmp / "store")
        self.store = Store(tmp / "store", clock=Clock(), kdf_iterations=1000, registry=self.registry)
        self.store.create_owner("Owner", "owner-pass")
        fx_inputs = fixture["inputs"] if fixture else None
        annotators = annotators if annotators is not None else fx_inputs["annotators"]
        self.ids = {}
        for a in annotators:
            self.store.add_annotator(a["pseudonym"], a["role"], a["qualification_ref"], a["independence_attestation"],
                                     f"pw-{a['pseudonym']}", anr_id=a["anr_id"])
            self.ids[a["pseudonym"]] = a["anr_id"]
        if targets is None:
            targets = [clip_target(fx_inputs["target"], video)] + [clip_target(t, video) for t in fx_inputs.get("other_targets", [])]
        config_id = targets[0]["config_id"]
        self.frame = FixtureFrame(targets[:1] if fixture else targets, config_id=config_id)
        self.server = make_server(self.store, {"BL-6": self.frame})
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        reviewers = [a["anr_id"] for a in annotators if a["role"] == "c_layer_reviewer"]
        adjudicator = next((a["anr_id"] for a in annotators if a["role"] == "adjudicator"), None)
        if with_pilot:
            self.store.create_batch(FixtureFrame(filler(config_id, video), config_id=config_id), SEED, reviewers, adjudicator, pilot=True)
            self.batch = self.store.create_batch(self.frame, SEED, reviewers, adjudicator, pilot=False)["batch_id"]

    def client(self, pseudonym: str | None = None) -> Client:
        c = Client(self.port)
        if pseudonym == "Owner":
            c.login("owner", "owner-pass")
        elif pseudonym:
            c.login(self.ids[pseudonym], f"pw-{pseudonym}")
        return c

    def assess(self, pseudonym: str, label: str, confidence: float, rationale: str, extra: dict | None = None):
        """Open the person's next item and submit it through the app (returns the POST response)."""
        c = self.client(pseudonym)
        status, headers, _ = c.get(f"/review/{self.batch}")
        assert status == 303, status
        item = headers["Location"]
        assert c.get(item)[0] == 200
        return c.post(item, {"label": label, "confidence": f"{confidence:.1f}", "rationale": rationale, **(extra or {})})

    def decide(self, pseudonym: str, final_label: str):
        c = self.client(pseudonym)
        status, page = c.text(f"/adjudicate/{self.batch}")
        assert status == 200, page
        case = re.search(rf'href="(/adjudicate/{self.batch}/\d+)"', page).group(1)
        assert c.get(case)[0] == 200
        return c.post(case, {"final_label": final_label})

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def make_app(tmp_path, video):
    apps = []

    def build(fixture_id: str | None = None, **kw) -> App:
        app = App(tmp_path / f"app{len(apps)}", video, load_fixture(fixture_id) if fixture_id else None, **kw)
        apps.append(app)
        return app

    yield build
    for app in apps:
        app.close()


def registered_store(path: Path, **kw) -> Store:
    """A V-02 store registered in its own registry beside it (T23.25 a)."""
    reg = StoreRegistry(path.parent / f"{path.name}_registry.json")
    reg.register(path)
    return Store(path, registry=reg, **kw)
