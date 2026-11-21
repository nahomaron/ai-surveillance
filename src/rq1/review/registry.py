"""Appendix T T23.25 (contract E-1.2.23; D-49): the registry of V-02/T23 stores and the cross-store reference protection.

`out/review/registry.json` (git-ignored, JCS) lists every store. A store that is not registered refuses to open
(`Store.__init__`). The functions below read the registered stores' files directly (read-only) for:
- T23.25 (b): the recordings of every demo run of every registered store, and the recordings with a target in any batch;
- T23.25 (c): why a person (by pseudonym) is exposed for a recording, across stores and all recorded actions.

Representation (AR-64): a registry entry is {"path"}; a path inside the registry's folder is stored relative to it, any
other path as an absolute POSIX path. Registering is idempotent and never removes an entry.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from rq1.schema.canonical import canonical_json

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "out" / "review" / "registry.json"
REASONS = ("candidate_review records", "report log", "wf_displays", "owner of a demo store")


class StoreRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @classmethod
    def default(cls) -> "StoreRegistry":
        return cls(DEFAULT_PATH)

    def _data(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"registry": "Appendix T T23.25 (a), contract E-1.2.23", "stores": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _key(self, root: str | Path) -> str:
        r = Path(root).resolve()
        base = self.path.parent.resolve()
        try:
            return r.relative_to(base).as_posix()
        except ValueError:
            return r.as_posix()

    def _resolve(self, key: str) -> Path:
        p = Path(key)
        return (p if p.is_absolute() else self.path.parent / p).resolve()

    def roots(self) -> list[Path]:
        return [self._resolve(e["path"]) for e in self._data()["stores"]]

    def is_registered(self, root: str | Path) -> bool:
        return Path(root).resolve() in self.roots()

    def register(self, root: str | Path) -> None:
        data = self._data()
        key = self._key(root)
        if any(e["path"] == key for e in data["stores"]):
            return
        data["stores"].append({"path": key})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_bytes(canonical_json(data))
        os.replace(tmp, self.path)


# --- read-only views of the registered stores ----------------------------------------------------------------------------

def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def manifest_recordings(root: Path) -> set[str]:
    m = _json(root / "demo_manifest.json")
    return {r for run in (m or {}).get("runs", []) for r in run["camera_rec_ids"]}


def demo_recordings(registry: StoreRegistry) -> set[str]:
    """T23.25 (b): every recording of every demo run listed by any registered store."""
    return {r for root in registry.roots() for r in manifest_recordings(root)}


def batch_recordings(registry: StoreRegistry) -> set[str]:
    """T23.25 (b): every recording with a target in a batch of any registered store."""
    out: set[str] = set()
    for root in registry.roots():
        folder = root / "batches"
        if not folder.exists():
            continue
        for b in sorted(folder.iterdir()):
            targets = _json(b / "targets.json")
            if targets and (b / "manifest.json").exists():
                out |= {t["recording_id"] for t in targets.values()}
    return out


def _people(root: Path) -> dict[str, str]:
    """IDs that act in a store -> the pseudonym of the person (annotator rows, workflow users, the Owner)."""
    out = {a["anr_id"]: a["pseudonym"] for a in _jsonl(root / "annotator.jsonl")}
    out.update({u["user_id"]: u["pseudonym"] for u in _jsonl(root / "wf_user.jsonl")})
    owner = (_json(root / "profiles.json") or {}).get("owner")
    if owner:
        out["owner"] = owner["pseudonym"]
    return out


def _reports_with(root: Path, recording_id: str) -> set[str]:
    eps = {e["ep_id"]: e.get("recording_id") for e in _jsonl(root / "wf_episode.jsonl")}
    return {h["report_id"] for h in _jsonl(root / "wf_report.jsonl")
            if any(eps.get(m) == recording_id for m in (h.get("member_episode_ids") or []))}


def exposure_reasons(registry: StoreRegistry, pseudonym: str, recording_id: str) -> list[str]:
    """T23.25 (c): the recorded reasons why the person is exposed for the recording, in the order of T23.25 (c) 1-4."""
    found: set[str] = set()
    for root in registry.roots():
        people = _people(root)
        mine = {k for k, v in people.items() if v == pseudonym}
        if not mine and people.get("owner") != pseudonym:
            continue
        for name in ("reviewer_assessment.jsonl", "adjudication.jsonl"):
            for e in _jsonl(root / name):
                row = e["row"]
                who = row.get("annotator_id") if name == "reviewer_assessment.jsonl" else e.get("annotator_id")
                if row["namespace"] == "candidate_review" and e.get("recording_id") == recording_id and who in mine:
                    found.add(REASONS[0])
        reports = _reports_with(root, recording_id)
        if reports:
            if any(e.get("report_id") in reports and e.get("actor_user_id") in mine for e in _jsonl(root / "wf_report_log.jsonl")):
                found.add(REASONS[1])
            if any(d["report_id"] in reports and d["user_id"] in mine for d in _jsonl(root / "wf_displays.jsonl")):
                found.add(REASONS[2])
        if people.get("owner") == pseudonym and recording_id in manifest_recordings(root):
            found.add(REASONS[3])
    return [r for r in REASONS if r in found]


def stores_summary(registry: StoreRegistry, roots: Iterable[Path] | None = None) -> list[dict[str, Any]]:
    """Read-only summary of stores (registered or given): batches with their manifests' key fields (section 6.3)."""
    out = []
    for root in (roots if roots is not None else registry.roots()):
        batches = []
        folder = root / "batches"
        if folder.exists():
            for b in sorted(folder.iterdir()):
                m = _json(b / "manifest.json")
                if m:
                    t = _json(b / "targets.json") or {}
                    batches.append({"batch_id": m["batch_id"], "pilot": m.get("pilot"), "configuration": m.get("configuration"),
                                    "partition": m.get("partition"), "dataset": m.get("dataset"), "n_drawn": m.get("n_drawn"),
                                    "annotators": m.get("annotators"), "recordings": sorted({x["recording_id"] for x in t.values()}),
                                    "target_ids": m.get("target_ids", [])})
        out.append({"root": str(root), "exists": root.exists(), "registered": registry.is_registered(root), "batches": batches,
                    "demo_recordings": sorted(manifest_recordings(root))})
    return out
