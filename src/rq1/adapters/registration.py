"""S0 registration metadata for the qualified synthetic datasets (T-18 part C, WP-13; E-1.2.1 section 3.1; T14.1).

Builds the `Registrar.register` input from facts the caller has read from disk (file hashes, sizes, codecs, SDG run index
rows, calibrations), so the mapping itself is pure and testable. Facts and their sources: research/datasets/qualification.md
Parts 1-3. Choices that are representation only: AR-52.

SDG-Warehouse (one S0 artifact, data_origin synthetic_rendered):
- site: the release's one warehouse layout family (`synthetic_scene`). Camera poses differ between runs (ceiling_00 at 10.0,
  10.03 or 10.5 m), so a camera is one view of one run: camera_label `<rgb run id>.<view>`; `ceiling_*` -> ceiling,
  `eye_*` -> eye_level. World frame: the dataset's declared stage frame (metres, metersPerSceneUnit 1.0; AR-35 item 7).
- session = one run (T14.1: a rendered scene instance). Lineage: ext_run_id = scene_id = the RGB-tier run id (the artifact
  folder name without its leading hash, the tier-join suffix rule); seed from the run index; generation_batch = the run
  index's source path without bucket and run folder; layout_id = the layout family (shared scene content: no edge on its
  own, T14.1); render_parent null not_applicable.
- calibration: full_camera from `camera_params.jsonl` (sdg_camera); a camera without camera parameters gets none.
SmartSpaces S0 waits for CR-020 (which data_origin its dataset_source row carries when its scenes differ in origin); its
licence row and identity constants are defined here, its calibration and truth are read by `adapters/smartspaces.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from rq1.ids import core
from rq1.schema.errors import ContractError

Row = dict[str, Any]

SDG_NAME = "nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes"
SDG_VERSION = "v1.0@d5b88d3abcf659f304a107f4336b71b4e2159133"
SDG_LAYOUT = "sdg-warehouse-v1-layout-family"  # card: one warehouse layout family for the whole release
SDG_WORLD_FRAME = ("sdg_stage_world", "v1.0")
SS_NAME = "nvidia/PhysicalAI-SmartSpaces"
SS_VERSION = "MTMC_Tracking_2026@d38193be60906679124732a4be9a6516821e2bed"

LICENSES = {  # qualification 1.2
    "sdg": {"component": SDG_NAME, "version": SDG_VERSION, "component_type": "dataset", "license_label": "OpenMDW-1.1", "terms_location": "website",
            "obligations": ["keep the licence text and notices of origin in any redistribution",
                            "rights terminate on a patent or copyright suit alleging the materials infringe",
                            "cite the dataset and the Cosmos 3 report (card request)"],
            "license_status": "verified", "decision_ref": "research/datasets/qualification.md 1.2"},
    "smartspaces": {"component": SS_NAME, "version": SS_VERSION, "component_type": "dataset", "license_label": "CC-BY-4.0", "terms_location": "website",
                    "obligations": ["attribution with a licence link and an indication of changes when sharing the material or adapted material",
                                    "no additional restrictions on recipients"],
                    "license_status": "verified", "decision_ref": "research/datasets/qualification.md 1.2"},
}

RETENTION_SYNTHETIC = {"label": "rp_synthetic_public_v1", "applies_to": "public synthetic datasets held under data/raw and data/derived (git-ignored)",
                       "retain_days": None, "deletion_method": "delete the local copy", "legal_basis_ref": "dataset licence (qualification 1.2)"}


def retention_policy_id(policy: Row = RETENTION_SYNTHETIC) -> str:
    return core.make_id("rtp", policy)


@dataclass(frozen=True)
class Video:
    uri: str  # relative to the data root
    sha256: str
    size_bytes: int
    container: str
    codec: str


@dataclass(frozen=True)
class SdgRun:
    artifact_run: str  # artifact-tier run folder name, `<hash>_<rgb run id>`
    index_row: Row  # the run's row of metadata/runs.parquet
    cameras: dict[str, tuple[Video, Row | None]]  # view -> (video, calibration or None)


def rgb_run_id(artifact_run: str) -> str:
    """Tier-join suffix rule (qualification 2.4): the artifact run id is `<hash>_` + the RGB-tier run id."""
    head, sep, rest = artifact_run.partition("_")
    if not sep or not rest or len(head) != 20:
        raise ContractError("ERR-SPEC", f"SDG artifact run id {artifact_run}: expected <20-character hash>_<run id>")
    return rest


def viewpoint(view: str) -> str:
    if view.startswith("ceiling_"):
        return "ceiling"
    if view.startswith("eye_"):
        return "eye_level"
    raise ContractError("ERR-SPEC", f"SDG view {view} is not known")


def generation_batch(source_run_s3: str, run_folder: str) -> str:
    """`s3://<bucket>/<batch path>/<run folder>/` -> `<batch path>`."""
    if not source_run_s3.startswith("s3://"):
        raise ContractError("ERR-SPEC", f"SDG source path {source_run_s3}: s3:// expected")
    parts = source_run_s3[len("s3://"):].strip("/").split("/")
    if len(parts) < 3 or parts[-1] != run_folder:
        raise ContractError("ERR-SPEC", f"SDG source path {source_run_s3} does not end in the run folder {run_folder}")
    return "/".join(parts[1:-1])


def sdg_session(run: SdgRun) -> Row:
    ext = rgb_run_id(run.artifact_run)
    row = run.index_row
    if row["run_id"] != ext or row["source_kind"] != "multi_camera_run":
        raise ContractError("ERR-INVARIANT", f"SDG run index row {row['run_id']} ({row['source_kind']}) does not match run {ext}")
    seed = row["seed"]
    if seed is None or seed != int(seed) or not ext.endswith(f"_seed_{int(seed)}"):
        raise ContractError("ERR-INVARIANT", f"SDG run {ext}: index seed {seed} disagrees with the run id")
    run_folder = ext.split("_", 1)[1]  # `run_<n>_seed_<s>`
    return {"session_label": ext, "scripted": True, "scenario_ref": row["scenario"], "extent": None,
            "lineage": {"ext_run_id": ext, "scene_id": ext, "seed": int(seed), "generation_batch": generation_batch(row["source_run_s3"], run_folder),
                        "layout_id": SDG_LAYOUT, "render_parent": None, "render_parent_null_reason": "not_applicable"}}


def _source(video: Video, privacy_state: str = "synthetic_no_persons") -> Row:
    return {"sha256": video.sha256, "size_bytes": video.size_bytes, "container": video.container, "codec": video.codec, "uri": video.uri,
            "privacy_state": privacy_state, "retention_policy_id": retention_policy_id()}


def sdg_metadata(runs: list[SdgRun], retrieved_utc: datetime) -> Row:
    """`Registrar.register` input for SDG runs (one site, one world frame, per-run cameras and sessions)."""
    key = [SDG_NAME, SDG_VERSION]
    site_label = SDG_LAYOUT
    cameras, sessions, sources, recordings, calibrations = [], [], [], [], []
    for run in sorted(runs, key=lambda r: rgb_run_id(r.artifact_run)):
        session = sdg_session(run)
        sessions.append(session)
        for view, (video, cal) in sorted(run.cameras.items()):
            label = f"{session['session_label']}.{view}"
            cameras.append({"camera_label": label, "viewpoint_class": viewpoint(view), "declared_overlap_camera_ids": []})
            sources.append(_source(video))
            recordings.append({"dataset": key, "site": site_label, "session": session["session_label"], "camera": label, "sha256": video.sha256,
                               "registration_label": label, "alignment": None})
            if cal is not None:
                calibrations.append({**cal, "dataset": key, "site": site_label, "camera": label, "world_frame": list(SDG_WORLD_FRAME),
                                     "version": SDG_VERSION, "valid_from_us": 0, "height_reference_ids": []})
    shas = [s["sha256"] for s in sources]
    if len(set(shas)) != len(shas):
        raise ContractError("ERR-INVARIANT", "two SDG recordings have identical bytes")
    return {"licenses": [LICENSES["sdg"]],
            "datasets": [{"name": SDG_NAME, "version": SDG_VERSION, "data_origin": "synthetic_rendered", "dataset_kind": "research",
                          "source_url": f"https://huggingface.co/datasets/{SDG_NAME}", "retrieved_utc": retrieved_utc, "license": [SDG_NAME, SDG_VERSION],
                          "annotation_levels": ["objects", "tracks", "world_geometry"], "unit_status": "verified",
                          "notes_ref": "research/datasets/qualification.md",
                          "sites": [{"site_label": site_label, "data_origin": "synthetic_rendered", "site_kind": "synthetic_scene",
                                     "independent_of_development": False, "cameras": cameras, "sessions": sessions,
                                     "world_frames": [{"label": SDG_WORLD_FRAME[0], "version": SDG_WORLD_FRAME[1],
                                                       "origin_description": "Isaac Sim stage world frame of the release (z up, metres, metersPerSceneUnit 1.0)",
                                                       "transform_from_dataset": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                                       "unit_status": "verified", "prov_class": "dataset_supplied"}]}]}],
            "source_files": sources, "recordings": recordings, "calibrations": calibrations}


@dataclass(frozen=True)
class SmartSpacesScene:
    name: str  # e.g. Warehouse_001
    data_origin: str  # synthetic_rendered | synthetic_transferred
    render_parent: str | None  # the scene this one re-renders (Warehouse_001 <- Warehouse_000), else None
    cameras: dict[str, tuple[Video, Row | None]]  # camera id -> (video, calibration or None)


SS_WORLD_FRAME = ("smartspaces_scene_world", "MTMC_Tracking_2026")


def smartspaces_version(data_origin: str) -> str:
    """CR-020 option (a) (Architect rulings of 13 Nov 2026, second set, item C): `<edition>@<revision>/<data_origin>`."""
    return f"{SS_VERSION}/{data_origin}"


def smartspaces_metadata(scene: SmartSpacesScene, retrieved_utc: datetime) -> Row:
    """`Registrar.register` input for one SmartSpaces synthetic scene: one S0 artifact per scene, single data_origin
    (VR-E-005). Site = the scene; session = the scene; scene_id = the scene asset (the render parent when there is one,
    T14.1: a scene asset together with all its re-renderings)."""
    if scene.data_origin not in ("synthetic_rendered", "synthetic_transferred"):
        raise ContractError("ERR-SPEC", f"SmartSpaces scene {scene.name}: {scene.data_origin} is not a synthetic origin (real scenes are registered under D-26)")
    if (scene.data_origin == "synthetic_transferred") != (scene.render_parent is not None):
        raise ContractError("ERR-INVARIANT", f"SmartSpaces scene {scene.name}: a transferred scene has a render parent, a rendered one has none")
    version = smartspaces_version(scene.data_origin)
    key = [SS_NAME, version]
    lineage = {"ext_run_id": scene.name, "scene_id": scene.render_parent or scene.name, "generation_batch": "MTMC_Tracking_2026/train",
               "layout_id": scene.render_parent or scene.name, "seed": None, "seed_null_reason": "not_supplied"}
    if scene.render_parent is None:
        lineage.update({"render_parent": None, "render_parent_null_reason": "not_applicable"})
    else:
        lineage["render_parent"] = scene.render_parent
    cameras, sources, recordings, calibrations = [], [], [], []
    for cam, (video, cal) in sorted(scene.cameras.items()):
        cameras.append({"camera_label": cam, "viewpoint_class": "other", "declared_overlap_camera_ids": []})
        sources.append(_source(video))
        recordings.append({"dataset": key, "site": scene.name, "session": scene.name, "camera": cam, "sha256": video.sha256,
                           "registration_label": f"{scene.name}.{cam}", "alignment": None})
        if cal is not None:
            calibrations.append({**cal, "dataset": key, "site": scene.name, "camera": cam, "world_frame": list(SS_WORLD_FRAME),
                                 "version": SS_VERSION, "valid_from_us": 0, "height_reference_ids": []})
    return {"licenses": [LICENSES["smartspaces"]],
            "datasets": [{"name": SS_NAME, "version": version, "data_origin": scene.data_origin, "dataset_kind": "research",
                          "source_url": f"https://huggingface.co/datasets/{SS_NAME}", "retrieved_utc": retrieved_utc, "license": [SS_NAME, SS_VERSION],
                          "annotation_levels": ["objects", "tracks", "world_geometry"], "unit_status": "verified",
                          "notes_ref": "research/datasets/qualification.md",
                          "sites": [{"site_label": scene.name, "data_origin": scene.data_origin, "site_kind": "synthetic_scene",
                                     "independent_of_development": False, "cameras": cameras,
                                     "sessions": [{"session_label": scene.name, "scripted": True, "extent": None, "lineage": lineage}],
                                     "world_frames": [{"label": SS_WORLD_FRAME[0], "version": SS_WORLD_FRAME[1],
                                                       "origin_description": "scene world frame of calibration.json and ground_truth.json (z up, metres)",
                                                       "transform_from_dataset": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                                                       "unit_status": "verified", "prov_class": "dataset_supplied"}]}]}],
            "source_files": sources, "recordings": recordings, "calibrations": calibrations}
