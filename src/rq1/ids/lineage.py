"""Lineage trace (CT-I-08, CT-E-28): from any artifact back through `art_` IDs to `src_`."""
from __future__ import annotations

from .artifact import Artifact


def trace_sources(artifact_id: str, store: dict[str, Artifact]) -> set[str]:
    sources: set[str] = set()
    pending = [artifact_id]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current in visited or current not in store:
            continue
        visited.add(current)
        built = store[current]
        sources |= {row["src_id"] for row in built.tables.get("source_file", [])}
        pending.extend(built.spec["input_artifact_ids"])
    return sources
