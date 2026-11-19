"""V-02 report screenshots, on fixtures only (no footage, no SDG data).

Builds a demo validation store under out/review/demo/ with the synthetic fixture video, the FX-13 annotators and eight
fixture targets; runs one pilot and one batch end to end through the running application (HTTP, as a browser would:
sign-in, blind review, adjudication, audit); saves the key pages; and renders each page with headless Google Chrome
(installed locally) into research/review_ui/screenshots/.

Run from the repository root:  PYTHONPATH=src .venv/bin/python research/review_ui/make_demo.py
"""
from __future__ import annotations

import http.client
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rq1.fixtures import review_video  # noqa: E402
from rq1.review import protocol as P  # noqa: E402
from rq1.review.frame import OUTLINE_COLOURS, FixtureFrame  # noqa: E402
from rq1.review.server import make_server  # noqa: E402
from rq1.review.store import Store  # noqa: E402

OUT = ROOT / "out/review/demo"
SHOTS = ROOT / "research/review_ui/screenshots"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CONFIG = "rcf_" + "demo".ljust(26, "0")
STRATA = ["CT", "UD", "NM", "NM", "PC", "PC", "H", "O"]
G2 = {"CT": "lbl_ct", "UD": "lbl_ud", "NM": "lbl_nm"}
# (reviewer A, reviewer B) labels per target, in target-ID order; the audit and adjudications follow from them.
LABELS = [("ct", "ct"), ("ud", "nm"), ("nm", "nm"), ("nm", "unsure"), ("not_hazardous", "not_hazardous"),
          ("nm", "not_hazardous"), ("not_hazardous", "not_hazardous"), ("not_hazardous", "not_hazardous")]


def target(k: int, video: Path, prefix: str = "demo") -> dict:
    s = STRATA[k % len(STRATA)]
    start, end = P.clip_window(3.0, 5.0, 0.0, 10.0, P.PARAMS["c_pad_s"])
    b = review_video.boxes()
    return {"target_type": "system_episode", "target_id": f"ep_{prefix}{k}".ljust(29, "0"), "recording_id": f"rec_{prefix}{k}".ljust(30, "0"),
            "config_id": CONFIG, "g2_label": G2.get(s), "stratum": s, "video": str(video), "clip_start_s": start, "clip_end_s": end,
            "fps": float(review_video.FPS), "width": review_video.W, "height": review_video.H,
            "outlines": [{"colour": OUTLINE_COLOURS["person"], "boxes": [x for x in b["person"] if start <= x[0] < end]},
                         {"colour": OUTLINE_COLOURS["forklift"], "boxes": [x for x in b["forklift"] if start <= x[0] < end]}]}


class Client:
    def __init__(self, port: int) -> None:
        self.port, self.cookie = port, ""

    def call(self, method: str, path: str, data: dict | None = None) -> tuple[int, dict, str]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        headers = {"Cookie": self.cookie} if self.cookie else {}
        body = urlencode(data) if data is not None else None
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=headers)
        r = conn.getresponse()
        text = r.read().decode("utf-8", "replace")
        if r.getheader("Set-Cookie"):
            self.cookie = r.getheader("Set-Cookie").split(";")[0]
        conn.close()
        return r.status, dict(r.getheaders()), text


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    video = review_video.write(OUT / "fixture.mp4")
    store = Store(OUT / "store", kdf_iterations=10_000)
    store.create_owner("Owner", "owner-demo")
    fx = json.loads((ROOT / "fixtures/records/FX-13.json").read_text())
    ids = {}
    for a in fx["inputs"]["annotators"]:
        ids[a["pseudonym"]] = store.add_annotator(a["pseudonym"], a["role"], a["qualification_ref"], True, f"pw-{a['pseudonym']}")["anr_id"]
    frame = FixtureFrame([target(k, video) for k in range(8)], config_id=CONFIG)
    pilot_frame = FixtureFrame([target(k, video, "pilot") for k in range(3)], config_id=CONFIG)
    server = make_server(store, {"BL-6": frame})
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def login(name: str) -> Client:
        c = Client(port)
        c.call("POST", "/login", {"profile": "owner" if name == "Owner" else ids[name], "passphrase": "owner-demo" if name == "Owner" else f"pw-{name}"})
        return c

    pages: dict[str, str] = {"01_sign_in": Client(port).call("GET", "/")[2]}
    owner = login("Owner")
    pages["02_owner_annotators"] = owner.call("GET", "/setup")[2]
    store.create_batch(pilot_frame, 20261119, [ids["R-A"], ids["R-B"]], ids["ADJ"], pilot=True)
    st, h, _ = owner.call("POST", "/batches", {"configuration": "BL-6", "seed": "2026111901", "reviewer1": ids["R-A"], "reviewer2": ids["R-B"],
                                              "adjudicator": ids["ADJ"]})
    batch = h["Location"].rsplit("/", 1)[1]
    pages["03_owner_batches"] = owner.call("GET", "/batches")[2]
    by_id = {t: k for k, t in enumerate(sorted(store.manifest(batch)["target_ids"]))}
    for col, name in enumerate(("R-A", "R-B")):
        c = login(name)
        for k, t in enumerate(store.order(batch, ids[name]), 1):
            if name == "R-B" and k == 1:
                pages["04_reviewer_item"] = c.call("GET", f"/review/{batch}/{k}")[2]
            c.call("GET", f"/review/{batch}/{k}")
            label = LABELS[by_id[t]][col]
            c.call("POST", f"/review/{batch}/{k}", {"label": label, "confidence": "2.0" if label != "unsure" else "1.0",
                                                    "rationale": f"Fixture rationale: the shapes pass each other ({label})."})
    adj = login("ADJ")
    for k, t in enumerate(store.order(batch, ids["ADJ"]), 1):  # blind tier-1 audit
        adj.call("GET", f"/review/{batch}/{k}")
        adj.call("POST", f"/review/{batch}/{k}", {"label": "ud", "confidence": "2.0", "rationale": "Fixture audit: the moment is hidden."})
    listing = adj.call("GET", f"/adjudicate/{batch}")[2]
    cases = re.findall(rf'href="(/adjudicate/{batch}/\d+)"', listing)
    pages["05_adjudication_case"] = adj.call("GET", cases[0])[2]
    for case in cases:
        adj.call("POST", case, {"final_label": "ud"})
    pages["06_owner_agreement"] = owner.call("GET", f"/batch/{batch}/agreement")[2]
    pages["07_owner_status_log"] = owner.call("GET", "/statuslog")[2]
    server.shutdown()

    SHOTS.mkdir(parents=True, exist_ok=True)
    folder = OUT / "pages"
    folder.mkdir()
    for name, html in pages.items():
        # Static copy for the screenshot only: the clip token URL becomes the local fixture video file.
        html = re.sub(r'src="/clip/[^"]+"', f'src="{video.as_uri()}"', html)
        path = folder / f"{name}.html"
        path.write_text(html, encoding="utf-8")
        tall = name in ("04_reviewer_item", "05_adjudication_case", "06_owner_agreement")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--autoplay-policy=no-user-gesture-required", f"--window-size=1100,{1750 if tall else 900}",
                        "--virtual-time-budget=4000", f"--screenshot={SHOTS / (name + '.png')}", path.as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(json.dumps({"batch": batch, "progress": store.progress(batch), "screenshots": sorted(p.name for p in SHOTS.glob("*.png"))}, indent=1))


if __name__ == "__main__":
    main()
