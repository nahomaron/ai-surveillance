"""CT-ID-01-07, CT-FK-01-07 and CT-I-01/03-08 (Appendix T), at builder level.

Pipeline-level re-runs of CT-I-03, 04, 07 and 08 happen when S4, S5 and S8 exist (T-08, T-09, T-14, T-16).
"""
import json
import random
from datetime import datetime, timedelta, timezone

import pytest

from rq1.fixtures import identity_rows as rows
from rq1.ids import artifact, core, lineage
from rq1.ids.artifact import Spec
from rq1.schema import files, registry, vr_rules
from rq1.schema.errors import ContractError

MODEL, INFER = "mdl_" + "a" * 26, "inf_" + "a" * 26
TRK = "trc_" + "a" * 26


def spec(stage="S3", configs=(TRK,), inputs=()):
    return Spec(stage=stage, schema_bundle="E-1.2.3", code_commit="fixture", environment_digest="fixture",
                config_ids=tuple(configs), input_artifact_ids=tuple(inputs), seeds={})


def s3_tables():
    return {"track": [rows.track(1), rows.track(2, "forklift")],
            "track_point": [rows.track_point(1, f) for f in (10, 11, 12)] + [rows.track_point(2, f) for f in (10, 11)]}


def s5_tables():
    a, b = rows.episode("pow_" + "a" * 26, 0), rows.episode("pow_" + "b" * 26, 0)
    ka, kb = ["pow_" + "a" * 26, 0], ["pow_" + "b" * 26, 0]
    return {"episode": [a, b], "event_link": [rows.event_link(ka, kb)], "candidate_event": [rows.candidate_event([ka, kb])]}


RCF = "rcf_" + "a" * 26


def s5_spec():
    return spec("S5", (RCF,))


def ids_of(built):
    return {t: sorted(r[registry.TABLES[t].prefix + "_id"] for r in rs) for t, rs in built.tables.items() if registry.TABLES[t].prefix}


@pytest.mark.determinism
def test_ct_id_01_builds_with_id_library_disabled(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("ID derivation called before step 5 finished")
    monkeypatch.setattr(core, "observation_id", boom)
    identity = artifact.compute_identity(spec(), s3_tables())
    assert identity.artifact_id.startswith("art_")


@pytest.mark.determinism
def test_ct_fk_01_same_as_ct_id_01_for_payload_without_own_ids():
    tables = s3_tables()
    for name, table_rows in tables.items():
        derived = {f.name for f in registry.TABLES[name].fields if f.derived}
        for row in table_rows:
            row.update({k: "corrupted" for k in derived if row.get(k) is not None})
    assert artifact.compute_identity(spec(), tables).artifact_id == artifact.compute_identity(spec(), s3_tables()).artifact_id


@pytest.mark.determinism
def test_ct_id_02_ct_fk_04_exact_rerun():
    a, b = artifact.build_artifact(spec(), s3_tables()), artifact.build_artifact(spec(), s3_tables())
    assert (a.payload_sha256, a.artifact_id, ids_of(a)) == (b.payload_sha256, b.artifact_id, ids_of(b))


@pytest.mark.determinism
def test_ct_id_03_clock_and_host_only_affect_execution(tmp_path):
    built = artifact.build_artifact(spec(), s3_tables())
    d1 = artifact.write_artifact(built, tmp_path / "a", "synthetic_rendered", clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc), host="h1")
    d2 = artifact.write_artifact(built, tmp_path / "b", "synthetic_rendered", clock=lambda: datetime(2030, 1, 1, tzinfo=timezone.utc), host="h2")
    assert (d1 / "manifest.json").read_bytes() == (d2 / "manifest.json").read_bytes()
    assert (d1 / "execution.json").read_bytes() != (d2 / "execution.json").read_bytes()


@pytest.mark.determinism
def test_ct_id_04_perturbed_value_changes_artifact_and_records():
    tables = {"detection": [rows.row("detection", recording_id=rows.REC, frame_index=0, det_index=0, score=0.5)]}
    changed = {"detection": [rows.row("detection", recording_id=rows.REC, frame_index=0, det_index=0, score=0.5 + 1e-9)]}
    s = spec("S2", (MODEL, INFER))
    a, b = artifact.build_artifact(s, tables), artifact.build_artifact(s, changed)
    assert a.artifact_id != b.artifact_id and ids_of(a) != ids_of(b)


@pytest.mark.determinism
def test_ct_id_05_same_rows_different_config():
    a = artifact.build_artifact(spec(configs=("trc_" + "b" * 26,)), s3_tables())
    assert a.artifact_id != artifact.build_artifact(spec(), s3_tables()).artifact_id


@pytest.mark.determinism
@pytest.mark.parametrize("table", ["track"])
def test_ct_id_06_ct_fk_07_duplicate_key(table):
    tables = s3_tables()
    tables["track"].append(rows.track(1))
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(spec(), tables)
    assert exc.value.code == "ERR-NATURAL-KEY"


@pytest.mark.determinism
def test_ct_id_07_ct_fk_05_reconstruction_after_rewriting_row_groups(tmp_path):
    built = artifact.build_artifact(spec(), s3_tables())
    directory = artifact.write_artifact(built, tmp_path / "x", "synthetic_rendered")
    assert artifact.verify(directory) == built.artifact_id
    manifest = json.loads((directory / "manifest.json").read_text())
    path = directory / "track_point.parquet"
    rows_back = files.read_table(path, "track_point", "E-1.2.3")
    meta = {"schema_id": "track_point", "schema_version": "E-1.2.3", "artifact_id": built.artifact_id,
            "data_origin": "synthetic_rendered", "payload_sha256": built.payload_sha256}
    files.write_table("track_point", rows_back, path, meta, row_group_size=1)
    assert artifact.verify(directory, check_file_hashes=False) == built.artifact_id
    assert manifest["artifact_id"] == built.artifact_id


@pytest.mark.determinism
def test_ct_fk_02_shuffled_rows_give_identical_ids():
    for make, make_spec in ((s3_tables, spec), (s5_tables, s5_spec)):
        tables = make()
        shuffled = {k: random.Random(7).sample(v, len(v)) for k, v in reversed(tables.items())}
        assert ids_of(artifact.build_artifact(make_spec(), tables)) == ids_of(artifact.build_artifact(make_spec(), shuffled))


@pytest.mark.determinism
def test_ct_fk_03_foreign_keys_resolve_and_dangling_rejected(tmp_path):
    built = artifact.build_artifact(spec(), s3_tables())
    track_ids = {r["trk_id"] for r in built.tables["track"]}
    assert {r["track_id"] for r in built.tables["track_point"]} <= track_ids
    tables = s3_tables()
    tables["track_point"].append(rows.track_point(99, 1))
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(spec(), tables)
    assert exc.value.code == "ERR-FK"
    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.determinism
def test_ct_fk_06_nested_keys():
    built = artifact.build_artifact(s5_spec(), s5_tables())
    ep_ids = {tuple([r["pow_id"], r["start_frame"]]): r["ep_id"] for r in built.tables["episode"]}
    link = built.tables["event_link"][0]
    assert link["episode_a_id"] == ep_ids[("pow_" + "a" * 26, 0)] and link["episode_b_id"] == ep_ids[("pow_" + "b" * 26, 0)]
    event = built.tables["candidate_event"][0]
    assert sorted(event["member_episode_ids"]) == sorted(ep_ids.values())
    permuted = s5_tables()
    permuted["candidate_event"][0]["member_episode_nks"].reverse()
    assert artifact.build_artifact(s5_spec(), permuted).tables["candidate_event"][0]["evt_id"] == event["evt_id"]


@pytest.mark.determinism
def test_ct_i_01_exact_rerun_different_run_id(tmp_path):
    built = artifact.build_artifact(spec(), s3_tables())
    runs = [json.loads((artifact.write_artifact(built, tmp_path / n, "synthetic_rendered") / "execution.json").read_text())["run_id"] for n in "ab"]
    assert runs[0] != runs[1] and all(r.startswith("run_") for r in runs)


@pytest.mark.determinism
def test_ct_i_03_g_max_change_changes_all_pow_ids():
    tables = {"pow": [rows.pow_row(0), rows.pow_row(10)]}
    gcf, a, b = "gcf_" + "a" * 26, "sbc_" + "a" * 26, "sbc_" + "b" * 26
    one = ids_of(artifact.build_artifact(spec("S4", (gcf, a)), tables))["pow"]
    two = ids_of(artifact.build_artifact(spec("S4", (gcf, b)), tables))["pow"]
    assert not set(one) & set(two)


@pytest.mark.determinism
def test_ct_i_04_recalibration_changes_substrate_ids():
    tables = {"pow": [rows.pow_row(0)], "pair_series": [rows.pair(0, 0)],
              "object_state": [rows.row("object_state", track_id=rows.PERSON, frame_index=0)]}
    cfg = ("gcf_" + "a" * 26, "sbc_" + "a" * 26)
    one = artifact.build_artifact(spec("S4", cfg, ("art_" + "a" * 26,)), tables)
    two = artifact.build_artifact(spec("S4", cfg, ("art_" + "c" * 26,)), tables)
    for table, values in ids_of(one).items():
        assert not set(values) & set(ids_of(two)[table]), table


@pytest.mark.determinism
def test_ct_i_05_same_file_two_cameras():
    src = core.source_id("ab" * 32)
    session = "ses_" + "a" * 26
    a = core.anchor_id("rec", "recording", [src, session, "cam_" + "a" * 26, "r"])
    b = core.anchor_id("rec", "recording", [src, session, "cam_" + "b" * 26, "r"])
    assert a != b and core.source_id("ab" * 32) == src


@pytest.mark.determinism
def test_ct_i_06_duplicate_natural_key_in_s0():
    row = rows.row("license_component", component="x", version="1")
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(spec("S0", ()), {"license_component": [row, dict(row)]})
    assert exc.value.code == "ERR-NATURAL-KEY"


@pytest.mark.determinism
def test_ct_i_07_id_07_rule_change_leaves_substrate_unchanged():
    subs = {"pow": [rows.pow_row(0)]}
    cfg = ("gcf_" + "a" * 26, "sbc_" + "a" * 26)
    s4 = artifact.build_artifact(spec("S4", cfg), subs)
    ep = {"episode": [rows.episode("pow_" + "a" * 26, 0)]}
    one = artifact.build_artifact(spec("S5", (RCF,), (s4.artifact_id,)), ep)
    two = artifact.build_artifact(spec("S5", ("rcf_" + "b" * 26,), (s4.artifact_id,)), ep)
    assert artifact.build_artifact(spec("S4", cfg), subs).artifact_id == s4.artifact_id
    assert one.artifact_id != two.artifact_id and not set(ids_of(one)["episode"]) & set(ids_of(two)["episode"])


@pytest.mark.determinism
def test_ct_i_08_lineage_reaches_source():
    sha = "cd" * 32
    src = rows.row("source_file", sha256=sha)
    s0 = artifact.build_artifact(spec("S0", ()), {"source_file": [src]})
    s3 = artifact.build_artifact(spec("S3", (TRK,), (s0.artifact_id,)), s3_tables())
    s5 = artifact.build_artifact(spec("S5", (RCF,), (s3.artifact_id,)), {"episode": [rows.episode("pow_" + "a" * 26, 0)]})
    store = {x.artifact_id: x for x in (s0, s3, s5)}
    assert lineage.trace_sources(s5.artifact_id, store) == {core.source_id(sha)}


@pytest.mark.determinism
def test_id_05_global_uniqueness_and_id_08():
    built = artifact.build_artifact(spec(), s3_tables())
    assert artifact.duplicate_ids([built]) == []
    assert artifact.duplicate_ids([built, built])
    assert "run_id" not in vars(spec())


@pytest.mark.determinism
def test_vr_e_004_ids_recompute_from_artifact():
    built = artifact.build_artifact(spec(), s3_tables())
    for table, table_rows in built.tables.items():
        assert vr_rules.check_ids(table, table_rows, built.artifact_id) == []


@pytest.mark.determinism
def test_write_is_refused_when_rows_are_invalid():
    tables = s3_tables()
    tables["track"][0]["class"] = "bicycle"
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(spec(), tables)
    assert exc.value.code == "ERR-UNKNOWN-ENUM"


@pytest.mark.determinism
def test_manifest_fields_section_2_5(tmp_path):
    built = artifact.build_artifact(spec(), s3_tables())
    directory = artifact.write_artifact(built, tmp_path / "x", "synthetic_rendered")
    manifest = json.loads((directory / "manifest.json").read_text())
    assert set(manifest) == {"artifact_spec_id", "spec", "payload_sha256", "artifact_id", "files", "data_origin", "reproducibility_class", "complete"}
    assert manifest["complete"] is True and manifest["reproducibility_class"] == "exact"
    assert {f["path"] for f in manifest["files"]} == {"track.parquet", "track_point.parquet"}


@pytest.mark.determinism
def test_ar16_schema_violation_uses_err_invariant():
    tables = s3_tables()
    tables["track"][0]["span_s"] = float("nan")
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(spec(), tables)
    assert exc.value.code == "ERR-INVARIANT"
