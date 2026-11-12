"""Architect review of AR-7 (11 Nov 2026): event-time columns and the canonical UTC format."""
import json
from datetime import datetime, timezone

import pytest

from rq1.fixtures import identity_rows as rows
from rq1.ids import artifact, core
from rq1.ids.anchors import AnchorRegistry
from rq1.ids.artifact import Spec
from rq1.schema import files, registry, validate, vr_rules
from rq1.schema.errors import ContractError

T1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 6, 1, 12, 30, tzinfo=timezone.utc)
SPLIT = "spm_" + "a" * 26


def test_event_time_columns_are_classified():
    assert registry.event_columns("split_manifest") == ["frozen_utc"]
    assert registry.event_columns("sampling_plan") == ["frozen_utc"]
    assert registry.event_columns("acceptance_criterion") == ["frozen_utc"]
    assert registry.event_columns("reference_window") == ["locked_utc", "locked_utc_null_reason"]
    assert registry.event_columns("dataset_source") == [] and registry.event_columns("license_component") == []


def _split(at):
    return rows.row("split_manifest", split_label="v1", version="1", frozen_utc=at)


def test_refreezing_identical_split_keeps_ids():
    spec = Spec("X0b", "E-1.2.4", "f", "f", (), (), {})
    a, b = artifact.build_artifact(spec, {"split_manifest": [_split(T1)]}), artifact.build_artifact(spec, {"split_manifest": [_split(T2)]})
    assert a.artifact_id == b.artifact_id and a.tables["split_manifest"][0]["spm_id"] == b.tables["split_manifest"][0]["spm_id"]
    assert (a.tables["split_manifest"][0]["frozen_utc"], b.tables["split_manifest"][0]["frozen_utc"]) == (T1, T2)


def test_refreezing_identical_sampling_plan_keeps_ids():
    spec = Spec("V0", "E-1.2.4", "f", "f", (), (SPLIT,), {})
    plan = lambda at: rows.row("sampling_plan", plan_label="p", version="1", split_version_id=SPLIT, frozen_utc=at)
    a, b = artifact.build_artifact(spec, {"sampling_plan": [plan(T1)]}), artifact.build_artifact(spec, {"sampling_plan": [plan(T2)]})
    assert a.artifact_id == b.artifact_id and a.tables["sampling_plan"][0]["spl_id"] == b.tables["sampling_plan"][0]["spl_id"]


def test_refreezing_identical_acceptance_criterion_keeps_id():
    criterion = lambda at: rows.row("acceptance_criterion", criterion_label="c", version="1", frozen_utc=at)
    assert artifact.config_id("acceptance_criterion", criterion(T1)) == artifact.config_id("acceptance_criterion", criterion(T2))
    other = rows.row("acceptance_criterion", criterion_label="c", version="1", frozen_utc=T1, target=0.5)
    assert artifact.config_id("acceptance_criterion", other) != artifact.config_id("acceptance_criterion", criterion(T1))


def test_event_times_are_stored_and_dropped_by_reconstruction(tmp_path):
    spec = Spec("X0b", "E-1.2.4", "f", "f", (), (), {})
    built = artifact.build_artifact(spec, {"split_manifest": [_split(T2)]})
    directory = artifact.write_artifact(built, tmp_path / "x", "synthetic_rendered")
    stored = files.read_table(directory / "split_manifest.parquet", "split_manifest", "E-1.2.4")
    assert stored[0]["frozen_utc"] == T2
    assert artifact.verify(directory) == built.artifact_id
    assert "frozen_utc" not in json.dumps(built.payload["split_manifest"], default=str)


def _dataset(retrieved):
    return rows.row("dataset_source", name="ds", version="1", retrieved_utc=retrieved)


def test_supplied_retrieved_utc_is_hashed():
    spec = Spec("S0", "E-1.2.4", "f", "f", (), (), {})
    a, b = artifact.build_artifact(spec, {"dataset_source": [_dataset(T1)]}), artifact.build_artifact(spec, {"dataset_source": [_dataset(T2)]})
    assert a.payload_sha256 != b.payload_sha256 and a.artifact_id != b.artifact_id
    # F.1 A1.2: the anchor ID depends on the natural key (name, version) only, so it does not change;
    # the changed payload under the same anchor is an ANC-1 conflict. See CR-004.
    assert a.tables["dataset_source"][0]["dsr_id"] == b.tables["dataset_source"][0]["dsr_id"] == core.anchor_id("dsr", "dataset_source", ["ds", "1"])
    register = AnchorRegistry()
    register.add(a)
    with pytest.raises(ContractError) as exc:
        register.add(b)
    assert exc.value.code == "ERR-ANCHOR-CONFLICT"


@pytest.mark.parametrize("value,ok", [
    ("2026-01-01T00:00:00.000000Z", True), ("2026-01-01T00:00:00Z", False), ("2026-01-01T00:00:00.000+00:00", False),
    ("2026-01-01 00:00:00.000000Z", False), ("2026-01-01T00:00:00.000000z", False), ("2026-13-01T00:00:00.000000Z", False),
])
def test_utc_string_format(value, ok):
    row = _dataset(value)
    assert (validate.validate_row("dataset_source", row) == []) is ok


def test_non_canonical_timestamp_rejected_by_builder():
    spec = Spec("S0", "E-1.2.4", "f", "f", (), (), {})
    with pytest.raises(ContractError):
        artifact.build_artifact(spec, {"dataset_source": [_dataset("2026-01-01T00:00:00Z")]})


def test_canonical_string_and_datetime_hash_identically():
    spec = Spec("S0", "E-1.2.4", "f", "f", (), (), {})
    a = artifact.build_artifact(spec, {"dataset_source": [_dataset(T1)]})
    b = artifact.build_artifact(spec, {"dataset_source": [_dataset("2026-01-01T00:00:00.000000Z")]})
    assert a.artifact_id == b.artifact_id


def test_vr_e_054_reads_event_time_from_stored_windows(tmp_path):
    spec = Spec("V0", "E-1.2.4", "f", "f", (), (SPLIT,), {})
    window = rows.row("reference_window", plan_nk=["p", "1"], window_index=0, locked_utc=T2)
    plan = rows.row("sampling_plan", plan_label="p", version="1", split_version_id=SPLIT, frozen_utc=T1)
    built = artifact.build_artifact(spec, {"sampling_plan": [plan], "reference_window": [window]})
    directory = artifact.write_artifact(built, tmp_path / "v0", "synthetic_rendered")
    stored = files.read_table(directory / "reference_window.parquet", "reference_window", "E-1.2.4")
    run_start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert [i.rule for i in vr_rules.check_windows_locked(stored, run_start)] == ["VR-E-054"]  # locked after the S8 run
    assert vr_rules.check_windows_locked(stored, datetime(2026, 9, 1, tzinfo=timezone.utc)) == []


def test_vr_e_004_ignores_event_time_for_configuration_ids():
    criterion = rows.row("acceptance_criterion", criterion_label="c", version="1", frozen_utc=T1)
    criterion["acc_id"] = artifact.config_id("acceptance_criterion", {**criterion, "frozen_utc": T2})
    assert vr_rules.check_ids("acceptance_criterion", [criterion]) == []
