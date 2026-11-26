"""D-60 (Owner decision, 25 Nov 2026; CR-036 closed): the D-59 SmartSpaces scenes, their tiers and their S0 lineage.

The Owner's values are written here once, as data. Scenes and map hashes: `research/datasets/part5/candidates.json`
(qualification Part 5, written before download); tiers: D-60 rulings 1 and 2.
- Tier 1 (held-out-layout test, ruling 1): 010, 011, 016, 017, 018, 019, 022 (45 cameras, 6 layouts never held before).
- Tier 2 (reserve, ruling 2): 002, 004, 006, 020 (73 cameras, the layout of `Warehouse_000`).
Every D-59 scene is `synthetic_rendered` (no re-render was taken, d59_report 3.1).
"""
from __future__ import annotations

from datetime import datetime, timezone

CONTRACT = "E-1.2.26"
DECISION = "D-60"
# scene -> published split folder (D-60 ruling 4: generation_batch carries it)
SCENES = {"Warehouse_002": "train", "Warehouse_004": "train", "Warehouse_006": "train", "Warehouse_010": "train", "Warehouse_011": "train",
          "Warehouse_016": "train", "Warehouse_017": "train", "Warehouse_018": "train", "Warehouse_019": "train",
          "Warehouse_020": "val", "Warehouse_022": "val"}
TIER1 = ("Warehouse_010", "Warehouse_011", "Warehouse_016", "Warehouse_017", "Warehouse_018", "Warehouse_019", "Warehouse_022")
TIER2 = ("Warehouse_002", "Warehouse_004", "Warehouse_006", "Warehouse_020")
TIER1_CAMERAS, TIER2_CAMERAS = 45, 73
DATA_ORIGIN = "synthetic_rendered"
# Arrival time of the last D-59 file (train/Warehouse_002/videos/Camera_0019.mp4, file mtime), taken once (as T-18 did).
RETRIEVED_UTC = datetime(2026, 11, 25, 3, 28, 56, tzinfo=timezone.utc)


def tier(scene: str) -> int:
    if scene in TIER1:
        return 1
    if scene in TIER2:
        return 2
    raise KeyError(f"{scene} is not a D-59 scene of D-60")
