"""W-02 (D-49 step 2 d): re-render the demo views of out/review/demo_20261119 read-only, with the code before and after
E-1.2.23, and record what changed.

The demo store itself is never opened: it is copied twice into a scratch folder, and each copy gets a throwaway Owner
profile so the pages can be fetched (no manager decision is taken; a report page writes a first-display record into the
copy only). The SHA-256 of every file of the original store is taken before and after and must be equal.

  PYTHONPATH=src .venv/bin/python research/workflow/rerender_demo.py <scratch dir>

The pages (visible text) go to <scratch dir>/{old,new}/pages/; the summary is printed as JSON.
"""
from __future__ import annotations

import hashlib
import html
import http.client
import inspect
import json
import re
import shutil
import subprocess
import sys
import tarfile
import io
import threading
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "out/review/demo_20261119"
OLD_COMMIT = "42957f2"


def digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def render(src: str, copy: str, out: str) -> None:
    """Runs inside a subprocess with `src` first on sys.path (old or new code)."""
    sys.path.insert(0, src)
    from rq1.workflow import rules as R
    from rq1.workflow.server import make_server
    from rq1.workflow.store import WorkflowStore
    kw = {}
    if "registry" in inspect.signature(WorkflowStore.__init__).parameters:
        from rq1.review.registry import StoreRegistry
        reg = StoreRegistry(Path(out) / "registry.json")
        reg.register(Path(copy))
        kw["registry"] = reg
    store = WorkflowStore(Path(copy), kdf_iterations=1000, **kw)
    store.create_owner("Owner (re-render)", "pw")
    server = make_server(store, {})
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port, cookie = server.server_address[1], ""

    def get(path: str, body: dict | None = None) -> tuple[int, str]:
        nonlocal cookie
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
        h = {"Cookie": cookie} if cookie else {}
        if body is not None:
            h["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request("POST" if body is not None else "GET", path, body=urlencode(body) if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read().decode("utf-8", "replace")
        if r.getheader("Set-Cookie"):
            cookie = r.getheader("Set-Cookie").split(";")[0]
        return r.status, raw

    get("/login", {"profile": "owner", "passphrase": "pw"})
    pages = {"home": "/wf", "setup": "/wf/setup"}
    for rid in sorted(store.headers()):
        pages[f"report_{rid[-12:]}"] = f"/wf/report/{rid}"
    for est in store.establishments():
        for period in sorted({R.iso_week(r.fields["occurred_at"]) for r in store.reports() if r.fields.get("est_id") == est}):
            q = {"est": est, "period": period}
            pages[f"indicators_{est[-6:]}_{period}"] = "/wf/indicators?" + urlencode(q)
            pages[f"regulator_{est[-6:]}_{period}.json"] = "/wf/regulator.json?" + urlencode(q)
    folder = Path(out) / "pages"
    folder.mkdir(parents=True, exist_ok=True)
    status = {}
    for name, path in pages.items():
        code, text = get(path)
        status[name] = code
        if not name.endswith(".json"):  # every visible line, banners and user blocks included
            text = html.unescape(re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", "\n", text, flags=re.S | re.I))
        text = re.sub(r"/wf/clip/[A-Za-z0-9_-]+", "/wf/clip/<token>", text)
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        (folder / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
    (Path(out) / "status.json").write_text(json.dumps(status, indent=1, sort_keys=True))
    server.shutdown()


def main() -> None:
    if len(sys.argv) == 5 and sys.argv[1] == "--render":
        return render(*sys.argv[2:])
    scratch = Path(sys.argv[1]).resolve()
    before = digest(STORE)
    old_src = scratch / "old_src"
    if not old_src.exists():
        data = subprocess.run(["git", "archive", OLD_COMMIT, "src"], cwd=ROOT, capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(data)).extractall(scratch / "old_src_tmp")
        (scratch / "old_src_tmp" / "src").rename(old_src)
    summary = {"store": str(STORE), "files": len(before), "old_commit": OLD_COMMIT}
    for mode, src in (("old", old_src), ("new", ROOT / "src")):
        copy = scratch / mode / "store"
        if copy.parent.exists():
            shutil.rmtree(copy.parent)
        shutil.copytree(STORE, copy)
        subprocess.run([sys.executable, __file__, "--render", str(src), str(copy), str(scratch / mode)], check=True,
                       env={"PYTHONPATH": str(src), "PATH": "/usr/bin:/bin"})
        summary[mode] = json.loads((scratch / mode / "status.json").read_text())
    after = digest(STORE)
    summary["original_unchanged"] = before == after
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
