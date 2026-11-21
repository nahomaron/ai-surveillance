"""The V-02 validation store (Appendix T T22, contract E-1.2.20). Git-ignored, under out/review/<name>/.

Tables are written exactly as E-1.2.1 section 5.8 defines them (plus T22.13 `review_time_s`). Each row is wrapped in a
store envelope {"batch_id", "recording_id", "row"} (AR-61 item 5) so a record can be traced to its batch without adding
a field to a contract table. Files are append-only; nothing is updated or deleted. Every row is checked with
`validate.validate_row` and, in `reference`, with VR-E-053 before it is written.

Sign-in passphrases are stored salted and hashed (PBKDF2-SHA256) in `profiles.json`. This separates the sessions of
people who share one computer; it is not a security boundary.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from rq1.review import protocol as P
from rq1.review import registry as REG
from rq1.schema import validate, vr_rules
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.validation.reference import stored_adjudications
from rq1.validation.status_log import StatusLog

ROLES = ("c_layer_reviewer", "adjudicator")
KDF_ITERATIONS = 200_000
CONTRACT = "E-1.2.23"  # the contract this store code implements (D-49.1 section 4.2; AR-64 version guard)
WORKFLOW_QUAL = "workflow "  # T23.25 (d): annotator rows created for workflow managers


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in text.removeprefix("E-").split("."))


def _utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


def human_id(prefix: str) -> str:
    """E-1.2.1 section 2.1: human-entered records carry the table prefix and a UUIDv7 (as `StatusLog.append` does)."""
    return f"{prefix}_{uuid.uuid7()}"


class Store:
    def __init__(self, root: str | Path, clock: Callable[[], datetime] = _now, kdf_iterations: int = KDF_ITERATIONS,
                 registry: REG.StoreRegistry | None = None) -> None:
        self.root = Path(root)
        self.registry = registry or REG.StoreRegistry.default()
        if not self.registry.is_registered(self.root):  # T23.25 (a): nothing is created or read
            raise _spec(f"store {self.root} is not listed in the store registry {self.registry.path}; a store that is not "
                        "registered refuses to open; rule T23.25 (a)")
        meta = self.root / "store_contract.json"
        if meta.exists():
            recorded = json.loads(meta.read_text(encoding="utf-8"))["contract"]
            if _version(recorded) > _version(CONTRACT):
                raise _spec(f"this store was written under contract {recorded}; this code implements {CONTRACT} and refuses a "
                            "newer store (D-49.1 section 4.2)")
        elif not self.root.exists():  # a new store records its contract version; an existing store is not changed
            self.root.mkdir(parents=True)
            meta.write_bytes(canonical_json({"contract": CONTRACT}))
        (self.root / "batches").mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.kdf_iterations = kdf_iterations
        self.lock = threading.RLock()
        self.status_log = StatusLog(self.root / "validation_status_log.jsonl")

    # --- low-level files ----------------------------------------------------------------------------------------------

    def _read(self, name: str) -> list[dict[str, Any]]:
        path = self.root / name
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def _append(self, name: str, record: dict[str, Any]) -> None:
        with open(self.root / name, "ab") as handle:
            handle.write(canonical_json(record) + b"\n")

    @staticmethod
    def _check(table: str, row: dict[str, Any]) -> None:
        issues = validate.validate_row(table, row)
        if issues:
            raise ContractError(issues[0].code or "ERR-SPEC", f"{table}.{issues[0].field}: {issues[0].message}")

    # --- profiles and annotators (T22.2 c, d) ------------------------------------------------------------------------------

    def _profiles(self) -> dict[str, Any]:
        path = self.root / "profiles.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"owner": None, "annotators": {}}

    def _save_profiles(self, data: dict[str, Any]) -> None:
        path = self.root / "profiles.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(canonical_json(data))
        os.replace(tmp, path)

    def _hash(self, passphrase: str, salt: bytes | None = None) -> dict[str, Any]:
        if not passphrase:
            raise _spec("a passphrase is required")
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, self.kdf_iterations)
        return {"salt": salt.hex(), "hash": digest.hex(), "iterations": self.kdf_iterations, "kdf": "pbkdf2_sha256"}

    @staticmethod
    def _matches(secret: dict[str, Any], passphrase: str) -> bool:
        digest = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), bytes.fromhex(secret["salt"]), secret["iterations"])
        return hmac.compare_digest(digest.hex(), secret["hash"])

    def has_owner(self) -> bool:
        return self._profiles()["owner"] is not None

    def create_owner(self, pseudonym: str, passphrase: str) -> None:
        with self.lock:
            data = self._profiles()
            if data["owner"] is not None:
                raise _spec("the Owner profile already exists")
            if not pseudonym.strip():
                raise _spec("a pseudonym is required")
            data["owner"] = {"pseudonym": pseudonym.strip(), **self._hash(passphrase)}
            self._save_profiles(data)

    def annotators(self) -> dict[str, dict[str, Any]]:
        return {r["anr_id"]: r for r in self._read("annotator.jsonl")}

    def add_annotator(self, pseudonym: str, role: str, qualification_ref: str, independence_attestation: bool, passphrase: str,
                      anr_id: str | None = None) -> dict[str, Any]:
        """Owner setup. One annotator row per person and role (T22.2 d); the pseudonym identifies the person (AR-61 item 4)."""
        with self.lock:
            if role not in ROLES:
                raise _spec(f"role {role!r} is not c_layer_reviewer or adjudicator (T22.0)")
            pseudonym, qualification_ref = pseudonym.strip(), (qualification_ref or "").strip()
            if not pseudonym or not qualification_ref:
                raise _spec("pseudonym and qualification_ref are required (T22.2 c, d)")
            if any(a["pseudonym"] == pseudonym and a["role"] == role for a in self.annotators().values()):
                raise _spec(f"{pseudonym} already has a {role} row (one row per person and role, T22.2 d)")
            row = {"anr_id": anr_id or human_id("anr"), "role": role, "qualification_ref": qualification_ref,
                   "independence_attestation": bool(independence_attestation), "pseudonym": pseudonym}
            self._check("annotator", row)
            data = self._profiles()
            data["annotators"][row["anr_id"]] = self._hash(passphrase)
            self._append("annotator.jsonl", row)
            self._save_profiles(data)
            return row

    def profiles(self) -> list[dict[str, str]]:
        data = self._profiles()
        out = [{"profile_id": "owner", "pseudonym": data["owner"]["pseudonym"], "role": "owner"}] if data["owner"] else []
        out += [{"profile_id": a["anr_id"], "pseudonym": a["pseudonym"], "role": a["role"]}
                for a in sorted(self.annotators().values(), key=lambda a: (a["pseudonym"], a["role"]))]
        return out

    def login(self, profile_id: str, passphrase: str) -> dict[str, str] | None:
        data = self._profiles()
        secret = data["owner"] if profile_id == "owner" else data["annotators"].get(profile_id)
        if not secret or not self._matches(secret, passphrase or ""):
            return None
        return next(p for p in self.profiles() if p["profile_id"] == profile_id)

    def person(self, annotator_id: str) -> str:
        return self.annotators()[annotator_id]["pseudonym"]

    # --- records -----------------------------------------------------------------------------------------------------------

    def assessments(self) -> list[dict[str, Any]]:
        return self._read("reviewer_assessment.jsonl")

    def adjudications(self) -> list[dict[str, Any]]:
        """Stored adjudication envelopes, rows read under T23.16 (f) (never rewritten)."""
        return stored_adjudications(self.root)

    def refusals(self) -> list[dict[str, Any]]:
        return self._read("refusals.jsonl")

    def import_candidate_review(self, row: dict[str, Any], recording_id: str) -> dict[str, Any]:
        """Stores a candidate_review assessment (T22.1 b; its procedures are T23). Only used here so that the exposure rule
        (T22.2 b) can be enforced from stored assessments."""
        with self.lock:
            if row["namespace"] != "candidate_review" or row["blind"] is not False or row["shown_system_output"] is not True:
                raise _spec("a candidate_review assessment has blind = false and shown_system_output = true (T22.1 b)")
            self._check("reviewer_assessment", row)
            self._append("reviewer_assessment.jsonl", {"batch_id": None, "recording_id": recording_id, "row": row})
            return row

    def add_candidate_review_adjudication(self, target: dict[str, Any], final_label: str, assessment_ids: list[str],
                                          annotator_id: str, report_id: str | None) -> dict[str, Any]:
        """A candidate_review adjudication (T23.5 c): reference_class null with reason not_applicable (T23.16 b); every
        assessment it lists is a candidate_review assessment (T23.16 a). The envelope names the deciding annotator row and
        the report, so the T23.25 (c) exposure rule sees it."""
        with self.lock:
            rows = {e["row"]["rva_id"]: e["row"] for e in self.assessments()}
            if any(a not in rows or rows[a]["namespace"] != "candidate_review" for a in assessment_ids):
                raise _spec("an adjudication's namespace equals the namespace of every assessment it lists; rule T23.16 (a)")
            row = {"adj_id": human_id("adj"), "target_type": target["target_type"], "target_id": target["target_id"],
                   "namespace": "candidate_review", "final_label": P.check_label(final_label), "tier": "tier2", "method": "adjudicator",
                   "assessment_ids": list(assessment_ids), "agreement_stat_ref": None, "agreement_stat_ref_null_reason": "not_applicable",
                   "prov_class": "human_adjudicated", "reference_class": None, "reference_class_null_reason": "not_applicable"}
            self._check("adjudication", row)
            self._append("adjudication.jsonl", {"batch_id": None, "report_id": report_id, "recording_id": target["recording_id"],
                                                "annotator_id": annotator_id, "row": row})
            return row

    def exposure(self, annotator_id: str, recording_id: str) -> list[str]:
        """T23.25 (c): why this person (by pseudonym) is exposed for the recording, across every registered store."""
        return REG.exposure_reasons(self.registry, self.person(annotator_id), recording_id)

    def exposed(self, annotator_id: str, recording_id: str) -> bool:
        """T22.2 (b) applied to every person exposed under T23.25 (c), across stores."""
        return bool(self.exposure(annotator_id, recording_id))

    def _refuse_workflow_row(self, *annotator_ids: str) -> None:
        """T23.25 (d): annotator rows of workflow managers are refused at once for reference work, before T22.9 applies."""
        people = self.annotators()
        for anr in annotator_ids:
            if anr in people and people[anr]["qualification_ref"].startswith(WORKFLOW_QUAL):
                raise _spec("a workflow manager's annotator row is never used for a reference assessment or adjudication; rule T23.25 (d)")

    # --- batches (T22.6) -----------------------------------------------------------------------------------------------------

    def batch_ids(self) -> list[str]:
        return sorted(p.name for p in (self.root / "batches").iterdir() if (p / "manifest.json").exists())

    def manifest(self, batch_id: str) -> dict[str, Any]:
        path = self.root / "batches" / batch_id / "manifest.json"
        if not path.exists():
            raise _spec(f"no batch {batch_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def targets(self, batch_id: str) -> dict[str, dict[str, Any]]:
        """System-side description of the batch targets. Never sent to a reviewer page."""
        return json.loads((self.root / "batches" / batch_id / "targets.json").read_text(encoding="utf-8"))

    def create_batch(self, frame: Any, seed: int, reviewer_ids: list[str], adjudicator_id: str | None, pilot: bool) -> dict[str, Any]:
        with self.lock:
            if type(seed) is not int or seed < 0:
                raise _spec("the batch seed is a non-negative integer supplied by the Owner (T22.12)")
            people = self.annotators()
            if len(reviewer_ids) != 2 or len(set(reviewer_ids)) != 2 or any(people.get(r, {}).get("role") != "c_layer_reviewer" for r in reviewer_ids):
                raise _spec("a batch has exactly two c_layer_reviewer annotators (T22.6 b)")
            if len({people[r]["pseudonym"] for r in reviewer_ids}) != 2:
                raise _spec("the two reviewers must be two different people")
            if adjudicator_id is not None:
                if people.get(adjudicator_id, {}).get("role") != "adjudicator":
                    raise _spec("the adjudicator must have role adjudicator")
                if people[adjudicator_id]["pseudonym"] in {people[r]["pseudonym"] for r in reviewer_ids}:
                    raise _spec("a person never adjudicates a target they assessed (T22.2 d)")
            if frame.partition != "validation":
                raise ContractError("ERR-LEAKAGE", "reference batches use the validation partition while D-37 stands (T22.6 a, T22.11)")
            same = [self.manifest(b) for b in self.batch_ids()]
            same = [m for m in same if m["configuration"]["config_id"] == frame.config_id and m["partition"] == frame.partition]
            pilots = [m for m in same if m["pilot"]]
            if pilot and pilots:
                raise _spec("a pilot batch already exists for this configuration and partition (T22.6 c)")
            if not pilot and not pilots:
                raise _spec("a pilot batch is reviewed before the first batch (T22.6 c)")
            # T22.14 (c): a target drawn into any earlier batch (pilot or reference) on this configuration and partition
            # is excluded from every later batch.
            excluded = sorted({t for m in same for t in m["target_ids"]})
            # T23.25 (b), amending T22.6 (a) and T23.11 (b): every episode of every demo run of every registered store
            # (all of its cameras) leaves the sampling frame.
            demo_recs = self.demo_recordings()
            demo_targets = sorted(t["target_id"] for t in frame.episodes() if t.get("recording_id") in demo_recs)
            n = P.PARAMS["n_pilot"] if pilot else P.PARAMS["n_batch"]
            alloc, ids = P.draw(frame.episodes(), n, seed, exclude=excluded + demo_targets)
            if set(ids) & set(excluded):
                raise _spec("a target of an earlier batch was drawn again; each target is reviewed in at most one batch (T22.14 c)")
            if not ids:
                raise _spec("the sampling frame has no targets left")
            batch_id = human_id("rvb")
            annotators = [{"annotator_id": r, "role": "c_layer_reviewer"} for r in reviewer_ids]
            if adjudicator_id:
                annotators.append({"annotator_id": adjudicator_id, "role": "adjudicator"})
            manifest = {
                "batch_id": batch_id, "namespace": "reference", "pilot": pilot,
                "configuration": {"name": frame.name, "config_id": frame.config_id}, "partition": frame.partition,
                "dataset": frame.dataset, "strata_counts": alloc, "seed": seed, "target_ids": ids, "annotators": annotators,
                "c_pad_s": P.PARAMS["c_pad_s"], "parameters": dict(P.PARAMS), "excluded_earlier_targets": len(excluded),
                "n_requested": n, "n_drawn": len(ids), "frame_exhausted": len(ids) < n,  # T22.14 (e)
                "excluded_demo_targets": len(demo_targets),  # T23.11 (b), T23.25 (b)
                "readings": "Appendix T T22.14 (E-1.2.21)",
                "created_utc": _utc(self.clock()),
            }
            targets = {t: frame.describe(t) for t in ids}
            folder = self.root / "batches" / batch_id
            folder.mkdir()
            (folder / "targets.json").write_bytes(canonical_json(targets))
            (folder / "manifest.json").write_bytes(canonical_json(manifest))  # written last: the batch exists once this does
            return manifest

    def demo_recordings(self) -> set[str]:
        """T23.25 (b), amending T22.6 (a) and T23.11 (b): every recording of every demo run listed by any registered store."""
        return REG.demo_recordings(self.registry)

    def batch_recordings(self) -> set[str]:
        """T23.25 (b): recordings with a target in a batch of any registered store."""
        return REG.batch_recordings(self.registry)

    def role_in(self, batch_id: str, annotator_id: str) -> str | None:
        return next((a["role"] for a in self.manifest(batch_id)["annotators"] if a["annotator_id"] == annotator_id), None)

    def reviewers(self, batch_id: str) -> list[str]:
        return [a["annotator_id"] for a in self.manifest(batch_id)["annotators"] if a["role"] == "c_layer_reviewer"]

    def adjudicator(self, batch_id: str) -> str | None:
        return next((a["annotator_id"] for a in self.manifest(batch_id)["annotators"] if a["role"] == "adjudicator"), None)

    def order(self, batch_id: str, annotator_id: str) -> list[str]:
        """The targets this person assesses blind, in their own seeded order (T22.6 b). For the adjudicator: the audit sample."""
        m = self.manifest(batch_id)
        role = self.role_in(batch_id, annotator_id)
        if role == "c_layer_reviewer":
            return P.reviewer_order(m["target_ids"], m["seed"], annotator_id)
        if role == "adjudicator":
            audit = self.audit(batch_id)
            return P.reviewer_order(audit["target_ids"], m["seed"], annotator_id) if audit else []
        return []

    # --- assessments (T22.5) -------------------------------------------------------------------------------------------------

    def _batch_assessments(self, batch_id: str) -> list[dict[str, Any]]:
        return [e["row"] for e in self.assessments() if e["batch_id"] == batch_id]

    def latest(self, batch_id: str, target_id: str) -> dict[str, dict[str, Any]]:
        """T22.5 (e): the latest assessment per annotator (rows are appended in submission order)."""
        out: dict[str, dict[str, Any]] = {}
        for row in self._batch_assessments(batch_id):
            if row["target_id"] == target_id:
                out[row["annotator_id"]] = row
        return out

    def note_display(self, batch_id: str, target_id: str, annotator_id: str) -> None:
        """T22.5 (d): the first display of the clip, measured by the tool."""
        with self.lock:
            if not any(d["batch_id"] == batch_id and d["target_id"] == target_id and d["annotator_id"] == annotator_id
                       for d in self._read("displays.jsonl")):
                self._append("displays.jsonl", {"batch_id": batch_id, "target_id": target_id, "annotator_id": annotator_id,
                                                "first_display_utc": _utc(self.clock())})

    def _first_display(self, batch_id: str, target_id: str, annotator_id: str) -> datetime | None:
        for d in self._read("displays.jsonl"):
            if (d["batch_id"], d["target_id"], d["annotator_id"]) == (batch_id, target_id, annotator_id):
                return datetime.strptime(d["first_display_utc"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        return None

    def submit(self, batch_id: str, target_id: str, annotator_id: str, label: str, confidence: Any, rationale: str,
               shown_system_output: bool = False, replaces: str | None = None) -> dict[str, Any]:
        with self.lock:
            self._refuse_workflow_row(annotator_id)
            m = self.manifest(batch_id)
            target = self.targets(batch_id).get(target_id)
            if target is None:
                raise _spec("target is not in this batch")
            if target_id not in self.order(batch_id, annotator_id):
                raise _spec("this person has no blind assessment of this target in this batch (T22.6 b, T22.7 d)")
            label, confidence = P.check_label(label), P.check_confidence(confidence)
            rationale = P.check_rationale(rationale)
            why = self.exposure(annotator_id, target["recording_id"])
            if why:
                raise _spec(f"excluded from reference assessment of this recording ({', '.join(why)}, T23.25 c); rule T22.2 (b)")
            mine = self.latest(batch_id, target_id).get(annotator_id)
            if mine and not replaces:
                raise _spec("one assessment per (annotator, target, namespace); a correction names the replaced one (T22.5 e)")
            if replaces:
                if not mine or mine["rva_id"] != replaces or replaces not in rationale:
                    raise _spec("a correction names the replaced assessment in its rationale (T22.5 e)")
                if self.current(batch_id, target_id):
                    raise _spec("the target is adjudicated; corrections are taken before adjudication")
            now = self.clock()
            shown = self._first_display(batch_id, target_id, annotator_id)
            row = {"rva_id": human_id("rva"), "annotator_id": annotator_id, "namespace": "reference", "target_type": target["target_type"],
                   "target_id": target_id, "label": label, "confidence": confidence, "rationale": rationale, "blind": True,
                   "shown_system_output": bool(shown_system_output),
                   "review_time_s": (now - shown).total_seconds() if shown else None,
                   "review_time_s_null_reason": None if shown else "not_observable", "submitted_utc": _utc(now)}
            self._check("reviewer_assessment", row)
            if vr_rules.check_blind_reference("reviewer_assessment", [row]):
                raise ContractError("ERR-NAMESPACE", "reference assessments are blind and not shown system output (VR-E-053)")
            self._append("reviewer_assessment.jsonl", {"batch_id": batch_id, "recording_id": target["recording_id"], "row": row})
            if not m["pilot"]:
                self._after_assessment(batch_id, target_id, annotator_id)
            return row

    # --- adjudication (T22.7), reference class (T22.9) and status (T22.8) -----------------------------------------------------

    def _batch_adjudications(self, batch_id: str) -> list[dict[str, Any]]:
        return [e["row"] for e in self.adjudications() if e["batch_id"] == batch_id]

    def current(self, batch_id: str, target_id: str) -> dict[str, Any] | None:
        rows = [r for r in self._batch_adjudications(batch_id) if r["target_id"] == target_id]
        return rows[-1] if rows else None

    def _reference_class(self, batch_id: str, target: dict[str, Any], assessments: list[dict[str, Any]], people: list[str]) -> str:
        """T22.9: independent_expert_judgment, or refused in reference (ERR-SPEC)."""
        annotators = self.annotators()
        for row in assessments:
            if row["blind"] is not True or row["shown_system_output"] is not False:
                raise _spec("an assessment considered is not blind (T22.9)")
        for anr in people:
            a = annotators[anr]
            if a["independence_attestation"] is not True or not a["qualification_ref"]:
                raise _spec(f"an annotator involved ({a['role']}) lacks independence_attestation or qualification_ref (T22.9)")
            if self.exposed(anr, target["recording_id"]):
                raise _spec("an annotator involved is excluded under T22.2 (b) (T22.9)")
        return "independent_expert_judgment"

    def _write_adjudication(self, batch_id: str, target: dict[str, Any], final_label: str, tier: str, method: str,
                            assessments: list[dict[str, Any]], people: list[str], actor_id: str) -> dict[str, Any]:
        self._refuse_workflow_row(*people)
        if any(r["namespace"] != "reference" for r in assessments):
            raise _spec("an adjudication's namespace equals the namespace of every assessment it lists; rule T23.16 (a)")
        reference_class = self._reference_class(batch_id, target, assessments, people)
        row = {"adj_id": human_id("adj"), "target_type": target["target_type"], "target_id": target["target_id"], "namespace": "reference",
               "final_label": P.check_label(final_label), "tier": tier, "method": method,
               "assessment_ids": [r["rva_id"] for r in assessments], "agreement_stat_ref": batch_id,
               "agreement_stat_ref_null_reason": None, "prov_class": "human_adjudicated", "reference_class": reference_class,
               "reference_class_null_reason": None}
        self._check("adjudication", row)
        self._append("adjudication.jsonl", {"batch_id": batch_id, "recording_id": target["recording_id"], "row": row})
        if target["target_type"] in P.STATUS_TARGETS:  # T22.8 (a); ref_event writes no status entry (T22.3 c)
            self.status_log.append(target_type=target["target_type"], target_id=target["target_id"], config_id=target["config_id"],
                                   status=P.status_for(row["final_label"], P.map_g2(target["g2_label"])), layer="C",
                                   namespace="reference", basis_ids=[row["adj_id"]], actor_id=actor_id, created_utc=self.clock())
        return row

    def _reviewer_pair(self, batch_id: str, target_id: str) -> list[dict[str, Any]] | None:
        latest = self.latest(batch_id, target_id)
        rows = [latest.get(r) for r in self.reviewers(batch_id)]
        return rows if all(rows) else None

    def _after_assessment(self, batch_id: str, target_id: str, annotator_id: str) -> None:
        target = self.targets(batch_id)[target_id]
        pair = self._reviewer_pair(batch_id, target_id)
        if annotator_id in self.reviewers(batch_id) and pair and not self.current(batch_id, target_id) \
                and P.is_tier1(pair[0]["label"], pair[1]["label"]):
            try:  # T22.7 (a): written by the tool; the actor is the batch (AR-61 item 6)
                self._write_adjudication(batch_id, target, pair[0]["label"], "tier1", "agreement", pair,
                                         [r["annotator_id"] for r in pair], actor_id=batch_id)
            except ContractError as error:
                self._append("refusals.jsonl", {"batch_id": batch_id, "target_id": target_id, "code": error.code, "message": str(error)})
        self._maybe_draw_audit(batch_id)

    def needs_adjudication(self, batch_id: str) -> list[str]:
        """Targets waiting for a tier2 decision: reviewers disagree or one said unsure (T22.7 b), or the audit label differs
        from the tier1 label (T22.7 d)."""
        if self.manifest(batch_id)["pilot"]:
            return []
        out = []
        for t in self.manifest(batch_id)["target_ids"]:
            pair, cur = self._reviewer_pair(batch_id, t), self.current(batch_id, t)
            if pair is None:
                continue
            if cur is None and not P.is_tier1(pair[0]["label"], pair[1]["label"]):
                out.append(t)
            elif cur is not None and cur["tier"] == "tier1" and self._audit_disagrees(batch_id, t):
                out.append(t)
        return out

    def adjudicate(self, batch_id: str, target_id: str, adjudicator_id: str, final_label: str) -> dict[str, Any]:
        """T22.7 (b), and (d) re-adjudication after an audit disagreement."""
        with self.lock:
            self._refuse_workflow_row(adjudicator_id)
            if self.adjudicator(batch_id) != adjudicator_id:
                raise _spec("only the batch adjudicator adjudicates (T22.7 b)")
            if target_id not in self.needs_adjudication(batch_id):
                raise _spec("this target is not waiting for adjudication")
            target = self.targets(batch_id)[target_id]
            pair = self._reviewer_pair(batch_id, target_id)
            reviewer_people = {self.person(r["annotator_id"]) for r in pair}
            if self.person(adjudicator_id) in reviewer_people:
                raise _spec("a person never adjudicates a target they assessed (T22.2 d)")
            considered = list(pair)
            audit_row = self.latest(batch_id, target_id).get(adjudicator_id)
            if audit_row:
                considered.append(audit_row)  # T22.7 (e): every assessment considered
            return self._write_adjudication(batch_id, target, final_label, "tier2", "adjudicator", considered,
                                            [r["annotator_id"] for r in pair] + [adjudicator_id], actor_id=adjudicator_id)

    def consensus(self, batch_id: str, target_id: str, reviewer_id: str, final_label: str) -> dict[str, Any]:
        """T22.7 (c): no adjudicator available; the two reviewers agree a final label together."""
        with self.lock:
            self._refuse_workflow_row(reviewer_id)
            if self.adjudicator(batch_id) is not None:
                raise _spec("the batch has an adjudicator; a consensus meeting is only used when none is available (T22.7 c)")
            if reviewer_id not in self.reviewers(batch_id) or target_id not in self.needs_adjudication(batch_id):
                raise _spec("not a reviewer of this batch, or the target is not waiting for adjudication")
            target, pair = self.targets(batch_id)[target_id], self._reviewer_pair(batch_id, target_id)
            return self._write_adjudication(batch_id, target, final_label, "tier2", "consensus_meeting", pair,
                                            [r["annotator_id"] for r in pair], actor_id=reviewer_id)

    # --- tier-1 audit (T22.7 d) ----------------------------------------------------------------------------------------------

    def audit(self, batch_id: str) -> dict[str, Any] | None:
        path = self.root / "batches" / batch_id / "audit.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def _maybe_draw_audit(self, batch_id: str) -> None:
        m = self.manifest(batch_id)
        if m["pilot"] or self.adjudicator(batch_id) is None or self.audit(batch_id):
            return
        if any(self._reviewer_pair(batch_id, t) is None for t in m["target_ids"]):
            return
        tier1 = [t for t in m["target_ids"] if (c := self.current(batch_id, t)) and c["tier"] == "tier1"]
        record = {"batch_id": batch_id, "a_audit": P.PARAMS["a_audit"], "n_tier1": len(tier1),
                  "target_ids": P.audit_sample(tier1, P.PARAMS["a_audit"], m["seed"]), "drawn_utc": _utc(self.clock())}
        (self.root / "batches" / batch_id / "audit.json").write_bytes(canonical_json(record))

    def _tier1(self, batch_id: str, target_id: str) -> dict[str, Any] | None:
        return next((r for r in self._batch_adjudications(batch_id) if r["target_id"] == target_id and r["tier"] == "tier1"), None)

    def _audit_disagrees(self, batch_id: str, target_id: str) -> bool:
        adj = self.adjudicator(batch_id)
        audit = self.audit(batch_id)
        if not adj or not audit or target_id not in audit["target_ids"]:
            return False
        row, tier1 = self.latest(batch_id, target_id).get(adj), self._tier1(batch_id, target_id)
        return bool(row and tier1 and row["label"] != tier1["final_label"])

    # --- batch state and agreement (T22.10) -------------------------------------------------------------------------------------

    def progress(self, batch_id: str) -> dict[str, Any]:
        m = self.manifest(batch_id)
        ids = m["target_ids"]
        audit = self.audit(batch_id)
        adj = self.adjudicator(batch_id)
        return {
            "targets": len(ids),
            "assessed": {r: sum(1 for t in ids if r in self.latest(batch_id, t)) for r in self.reviewers(batch_id)},
            "adjudicated": sum(1 for t in ids if self.current(batch_id, t)),
            "waiting_for_adjudication": len(self.needs_adjudication(batch_id)),
            "audit_drawn": audit is not None,
            "audited": sum(1 for t in (audit or {}).get("target_ids", []) if adj in self.latest(batch_id, t)),
            "audit_size": len((audit or {}).get("target_ids", [])),
            "refusals": [r for r in self.refusals() if r["batch_id"] == batch_id],
        }

    def fully_adjudicated(self, batch_id: str) -> bool:
        m = self.manifest(batch_id)
        if m["pilot"] or any(self.current(batch_id, t) is None for t in m["target_ids"]):
            return False
        adj = self.adjudicator(batch_id)
        if adj is None:
            return True
        audit = self.audit(batch_id)
        if audit is None:
            return False
        return all(adj in self.latest(batch_id, t) and not (t in self.needs_adjudication(batch_id)) for t in audit["target_ids"])

    def agreement(self, batch_id: str) -> dict[str, Any]:
        """T22.10 (a) and (c). Shown to the Owner only, and only once the batch is fully adjudicated."""
        if not self.fully_adjudicated(batch_id):
            raise _spec("agreement statistics are shown only after the batch is fully adjudicated")
        m = self.manifest(batch_id)
        ids, reviewers, adj = m["target_ids"], self.reviewers(batch_id), self.adjudicator(batch_id)
        pairs = [self._reviewer_pair(batch_id, t) for t in ids]
        k5, k4 = P.kappas([p[0]["label"] for p in pairs], [p[1]["label"] for p in pairs])
        audit = self.audit(batch_id) or {"target_ids": []}
        audited = audit["target_ids"]
        agree = sum(1 for t in audited if not self._audit_disagrees(batch_id, t))
        units = [[r["label"] for r in self._reviewer_pair(batch_id, t)] + [self.latest(batch_id, t)[adj]["label"]] for t in audited]
        finals = [self.current(batch_id, t) for t in ids]
        counts: dict[str, int] = {}
        for f in finals:
            key = f"{f['tier']} / {f['method']}"
            counts[key] = counts.get(key, 0) + 1
        times = {f"reviewer {k + 1}": P.median_p90([self.latest(batch_id, t)[r]["review_time_s"] for t in ids])
                 for k, r in enumerate(reviewers)}
        people = self.annotators()
        quals = sorted({f"{people[a['annotator_id']]['role']}: {people[a['annotator_id']]['qualification_ref']}" for a in m["annotators"]})
        return {
            "agreement_stat_ref": batch_id, "namespace": m["namespace"], "configuration": m["configuration"]["name"],
            "partition": m["partition"], "targets_per_stratum": m["strata_counts"], "n_targets": len(ids),
            "kappa_five_labels": k5, "kappa_four_labels": k4,
            "n_four_label_targets": sum(1 for p in pairs if "unsure" not in (p[0]["label"], p[1]["label"])),
            "alpha_audited": P.alpha(units), "n_audited": len(audited), "audit_agree": agree,
            "audit_agreement_rate": (agree / len(audited)) if audited else None,
            "counts_by_tier_method": dict(sorted(counts.items())),
            "superseded_tier1": sum(1 for t in ids if self._tier1(batch_id, t) and self.current(batch_id, t)["tier"] == "tier2"),
            "final_unsure": sum(1 for f in finals if f["final_label"] == "unsure"),
            "review_time_s_median_p90": times, "qualifications": quals,
            "statements": [
                "Namespace: reference (blind review).",
                "The sample is stratified by the system's episode summary label, so kappa describes agreement on this batch, not on all episodes.",
                "Synthetic data: results are at most experimental (T12.5).",
                "Labels are printed as codes.",
            ],
        }
