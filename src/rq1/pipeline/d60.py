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


# --- STEP 3: split addendum X0b-A1 (rulings 1-3) -------------------------------------------------------------------------
X0B_ARTIFACT_ID = "art_w5v3ldr43xdsqc6l4zifmjkuuj"  # docs/preregistration/freeze_record.json
X0B_PAYLOAD_SHA256 = "c01ad60be4ae42a9e986ab1ec8461dae55b7c3d0d0b57c2a5b342fb056465382"
X0B_SPM_ID = "spm_uvjw4v4mygzvtvwqrbjjhambh5"
SPLIT_LABEL, SPLIT_VERSION, TIER = "X0b-A1", "1", "T1"
PARTITION = {1: "test_layout_holdout", 2: "reserve"}
LAYOUT_EDGE = "same_layout"  # AR-70 item 3
ADDENDUM_RECORD = {"rule": "D-60 rulings 1-3 and STEP 3", "parent_split": X0B_SPM_ID, "x0b_assignments": "unchanged",
                   "grouping": "metadata edges (E-1.2.1 section 8, T14, T16.2) plus one edge chain per layout_id (D-60 STEP 3: one group per layout)",
                   "partitions": {"tier 1": PARTITION[1], "tier 2": PARTITION[2]}, "tier": TIER, "basis": "metadata_only",
                   "layout_id": "SHA-256 of map.png (ruling 4)"}


def addendum_rows(s0_tables: list[dict]) -> list[dict]:
    """Recordings of the D-59 S0 artifacts as `builder.freeze` takes them, with the partition of their scene's tier."""
    rows = []
    for t in s0_tables:
        d, ses = t["dataset_source"][0], {s["ses_id"]: s for s in t["session"]}
        for r in t["recording"]:
            lin = ses[r["session_id"]]["lineage"]
            rows.append({"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": d["dsr_id"], "dataset_name": d["name"],
                         "lineage": lin, "partition": PARTITION[tier(lin["ext_run_id"])]})
    return sorted(rows, key=lambda r: r["recording_id"])


def layout_edges(rows: list[dict]) -> list[tuple[str, str, str]]:
    """One chain of `same_layout` edges per layout_id over the sorted recording IDs (D-60 STEP 3)."""
    by_layout: dict[str, list[str]] = {}
    for r in rows:
        lid = r["lineage"].get("layout_id")
        if lid is None:
            raise ValueError(f"{r['recording_id']}: no layout_id")
        by_layout.setdefault(lid, []).append(r["recording_id"])
    return [(a, b, LAYOUT_EDGE) for lid in sorted(by_layout) for a, b in zip(sorted(by_layout[lid]), sorted(by_layout[lid])[1:])]


def freeze_addendum(rows: list[dict], frozen_utc: datetime) -> dict:
    from rq1.splits import builder
    return builder.freeze(rows, SPLIT_LABEL, SPLIT_VERSION, TIER, frozen_utc, extra_edges=tuple(layout_edges(rows)))


def audit_edges(rows: list[dict]) -> list[dict]:
    """X0c input: every metadata edge and every layout edge among the addendum's recordings, with its evidence."""
    from rq1.splits import leakage
    meta = [(a, b, k, "S0 lineage (E-1.2.1 section 8)") for a, b, k in leakage.metadata_edges(rows)]
    lay = [(a, b, k, "S0 lineage.layout_id (D-60 STEP 3)") for a, b, k in layout_edges(rows)]
    return [{"recording_a": a, "recording_b": b, "edge_type": k, "evidence_ref": e} for a, b, k, e in sorted(meta + lay)]


def check_disjoint_from_x0b(addendum: dict, x0b: dict, addendum_shas: set[str], x0b_shas: set[str]) -> dict:
    """The addendum leaves X0b as it is: no recording and no source file in both (X0b assignments are then untouched)."""
    a = {m for g in addendum["leakage_groups"] for m in g["member_recording_ids"]}
    b = {m for g in x0b["leakage_groups"] for m in g["member_recording_ids"]}
    return {"recordings_in_both": sorted(a & b), "source_files_in_both": sorted(addendum_shas & x0b_shas),
            "addendum_recordings": len(a), "x0b_recordings": len(b)}
