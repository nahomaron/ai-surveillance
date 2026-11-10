"""ANC-1 (F.1 A1.2): the same anchor ID must always carry the same payload."""
from __future__ import annotations

from rq1.schema import registry
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError

from .artifact import Artifact


class AnchorRegistry:
    def __init__(self) -> None:
        self._payloads: dict[str, bytes] = {}

    def add(self, built: Artifact) -> None:
        for table, rows in built.tables.items():
            spec = registry.TABLES[table]
            if spec.identity_class != "anchor":
                continue
            payload_rows = built.payload[table]
            for row, payload in zip(rows, payload_rows):
                anchor = row[f"{spec.prefix}_id"]
                encoded = canonical_json(payload)
                if self._payloads.setdefault(anchor, encoded) != encoded:
                    raise ContractError("ERR-ANCHOR-CONFLICT", f"{table}: {anchor}")
