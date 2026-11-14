"""Leakage edges and groups (E-1.2.1 section 8; AR-31; Appendix T T14, T16.2)."""
from __future__ import annotations

from itertools import combinations
from typing import Any

from rq1.ids import core

Row = dict[str, Any]
SCENE_FIELDS = ("scene_id", "ext_run_id", "render_parent", "seed")
SCRIPT_FIELDS = ("actor_roster_ref", "layout_id", "script_id", "collection_day")


def _dataset(r: Row) -> str:
    """T16.2: "within one dataset" means dataset_source rows with the same dataset name (a release registered as one row
    per data origin, T16.1). A recording without `dataset_name` is compared by its dataset row."""
    return r.get("dataset_name") or r["dataset_id"]


def _edge_type(a: Row, b: Row) -> str | None:
    if a["session_id"] == b["session_id"]:
        return "same_session"
    la, lb = a.get("lineage", {}), b.get("lineage", {})
    if _dataset(a) == _dataset(b):
        if any(la.get(f) is not None and la.get(f) == lb.get(f) for f in SCENE_FIELDS):
            return "same_scene_or_run"
        if (la.get("render_parent") is not None and la.get("render_parent") == lb.get("scene_id")) or \
           (lb.get("render_parent") is not None and lb.get("render_parent") == la.get("scene_id")):
            return "same_scene_or_run"
    if all(la.get(f) is not None and la.get(f) == lb.get(f) for f in SCRIPT_FIELDS):
        return "same_scripted_instance"
    return None


def metadata_edges(recordings: list[Row], excluded_sessions: set[str] = frozenset()) -> list[tuple[str, str, str]]:
    """Edges from R-1 metadata. Same-session edges of declared T2b shared sessions are left out."""
    edges = []
    for a, b in combinations(sorted(recordings, key=lambda r: r["recording_id"]), 2):
        kind = _edge_type(a, b)
        if kind == "same_session" and a["session_id"] in excluded_sessions:
            continue
        if kind:
            edges.append((a["recording_id"], b["recording_id"], kind))
    return edges


def components(nodes: list[str], edges: list[tuple[str, str, str]]) -> list[tuple[list[str], list[str]]]:
    """Connected components, each with its sorted members and sorted edge types."""
    parent = {n: n for n in nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _ in edges:
        parent[find(a)] = find(b)
    groups: dict[str, list[str]] = {}
    for n in nodes:
        groups.setdefault(find(n), []).append(n)
    kinds: dict[str, set[str]] = {}
    for a, b, kind in edges:
        kinds.setdefault(find(a), set()).add(kind)
    return sorted((sorted(m), sorted(kinds.get(root, set()))) for root, m in groups.items())


def group_id(members: list[str]) -> str:
    return core.make_id("lkg", sorted(members))
