"""Reports from OBX exports (F.1 A2 EXP-4; A5.1 RV-02, RV-04; E-1.2.1 sections 7, 9.5; Appendix T T12.2, T12.4, T14; CLAUDE.md wording).

Reports are Markdown text built only from fixed section builders, then checked by `lint`. A fixture export uses the
fixture template, which starts with the fixed banner; a research template on a fixture export is refused (CT-X-04)."""
from __future__ import annotations

import re

from rq1.evaluation.event_metrics import EV_M10_NOTE, SENSITIVITY_LABEL
from rq1.schema.errors import ContractError
from rq1.schema.vr_rules import OBSERVED_CONTACT
from rq1.splits.builder import ORDER, recording_partitions
from rq1.validation.namespace import check_rv_02

BANNER = "FIXTURE VERIFICATION — NOT RESEARCH RESULTS"
CONFORMANCE_TITLE = "Implementation conformance"  # RV-02
RV04_CAVEAT = "These results compare the system with its own rules applied to reference data. They show that the definitions are implemented as written; they are not hazard identification and not construct evidence."
VISIBILITY_NOTE = "reference visibility assumed"  # T12.4 and the Architect's ruling on AR-36 item 4
T14_SCOPE = "held-out runs of the same synthetic layout"  # T14.2
STATUS_LABELS = {"implemented": "Implemented", "verified": "Verified", "empirically_validated": "Empirically validated (scope)"}
FIXED_LINES = {RV04_CAVEAT, EV_M10_NOTE, BANNER}

# Wording rules (CLAUDE.md "Never"; LK-07; RV-04; the Architect's ruling on AR-40 item 4).
WORDING = [
    ("W1 collision", re.compile(r"\bcollisions?\b", re.I)),
    ("W2 near miss", re.compile(r"(?<!candidate )(?<!\bno )\bnear[- ]miss(es)?\b", re.I)),  # "no near misses" claims none (AR-46 item 4 ruling)
    ("W3 contact claim", OBSERVED_CONTACT),
    ("W3 contact claim", re.compile(r"\bcontact (occurred|detected|happened)\b", re.I)),
    ("W4 validated", re.compile(r"(?<!technically_)(?<!empirically )\bvalidated\b", re.I)),
    ("W5 interaction count", re.compile(r"\bphysical interactions?\b|\b\d+\s+interactions?\b", re.I)),
    ("W6 score or ranking", re.compile(r"\b(safety|risk) score\b|\branking\b|\bOSHA\b|\bNAICS\b|\bestablishment rate\b", re.I)),
]
# T14.2: a report scoped to held-out runs of the same synthetic layout makes no unseen-camera, -layout or -site claim.
T14_UNSEEN = re.compile(r"\bunseen[- ](cameras?|layouts?|sites?)\b", re.I)
RV04 = re.compile(r"\bhazard identification\b|\bidentif(y|ies) hazards?\b|\bconstruct\b|\bvalidity\b", re.I)


def lint(text: str) -> list[str]:
    """Wording-rule violations as 'rule: line'. Fixed sentences written by this module are exempt."""
    issues, section = [], ""
    t14_scoped = T14_SCOPE in text
    for line in text.splitlines():
        if line.startswith("#"):
            section = line.lstrip("# ").strip()
        if line.strip() in FIXED_LINES:
            continue
        for rule, pattern in WORDING:
            if pattern.search(line):
                issues.append(f"{rule}: {line.strip()}")
        if t14_scoped and T14_UNSEEN.search(line):
            issues.append(f"T14.2 unseen claim: {line.strip()}")
        if section == CONFORMANCE_TITLE and RV04.search(line):
            issues.append(f"RV-04: {line.strip()}")
    return issues


def render(manifest: dict, template: str, title: str, sections: list[tuple[str, list[str]]]) -> str:
    """Assemble a report and enforce EXP-4 and the wording rules (ERR-INVARIANT on a wording violation, AR-46 item 1)."""
    fixture = manifest["export_class"] == "fixture_verification"
    if template not in ("fixture", "research"):
        raise ContractError("ERR-SPEC", f"template {template}")
    if fixture != (template == "fixture"):
        raise ContractError("ERR-EXPORT-CLASS", f"EXP-4: {template} template on a {manifest['export_class']} export")
    lines = ([BANNER, ""] if fixture else []) + [f"# {title}", "", f"Export class: {manifest['export_class']}; contract {manifest['contract']}.", ""]
    for heading, body in sections:
        lines += [f"## {heading}", "", *body, ""]
    text = "\n".join(lines)
    issues = lint(text)
    if issues:
        raise ContractError("ERR-INVARIANT", "wording rules: " + "; ".join(issues))
    return text


def conformance_section(metric_rows: list[dict]) -> tuple[str, list[str]]:
    """RV-02 and RV-04: results against rule-conformance references, under the fixed title and caveat, claim level none."""
    rows = [r for r in metric_rows if r.get("reference_class") == "rule_conformance"]
    issues = check_rv_02(rows)
    if issues:
        raise ContractError("ERR-INVARIANT", issues[0].message)
    body = [RV04_CAVEAT, ""] + [f"- {r['metric_id']}: {r.get('value')} (claim level none)" for r in sorted(rows, key=lambda r: r["metric_id"])]
    return CONFORMANCE_TITLE, body


def counts_section(count_rows: list[dict]) -> tuple[str, list[str]]:
    """Event counts as scenario_count with their assumptions (LK-07). One count is a number of candidate events of a
    scenario, never a number of physical interactions; parts linked by continuation_of are one episode chain."""
    body = ["Counts are scenario_count values of candidate events (assumptions A1–A3 as listed). Episodes linked by continuation_of are parts of one chain.", ""]
    for r in sorted(count_rows, key=lambda r: (r["scope_type"], r["scope_id"], r["scenario"], r["label"])):
        assumptions = ", ".join(f"{a['assumption']} {a['status']}" for a in r["assumptions"])
        body.append(f"- {r['scope_type']} {r['scope_id']}, {r['scenario']}, label {r['label']}: {r['n_events']} candidate events ({r['wording']}; {assumptions})")
    return "Candidate event counts", body


def ev_m10_section(headline: dict, sensitivity: dict, table: dict) -> tuple[str, list[str]]:
    """T12.2: EV-M10 with the sensitivity values under their label, beside (never instead of) the headline values."""
    w = table["weighted"]
    body = [f"- Headline EV-M2: {headline['EV-M2']}; EV-M7: {headline['EV-M7']}",
            f"- {SENSITIVITY_LABEL}: EV-M2 {sensitivity['EV-M2']}; EV-M7 {sensitivity['EV-M7']}",
            f"- EV-M10 (weighted): non-abstained {w['non_abstained']}, abstained {w['abstained']}",
            "", EV_M10_NOTE]
    return "System decisions on unobservable references (EV-M10)", body


def completeness_section(records: list[dict], visibility_assumed: bool) -> tuple[str, list[str]]:
    """Completeness on both bases; prints the visibility note where reference visible support is used without visibility truth."""
    body = []
    uses_visibility = any(r["metric_id"] in ("CM-01", "CM-02", "CM-03", "CM-10") for r in records)
    if visibility_assumed and uses_visibility:
        body += [f"Note: {VISIBILITY_NOTE}.", ""]
    for r in sorted(records, key=lambda r: (r["metric_id"], r["support_basis"], str(sorted(r["stratum"].items())))):
        basis = "basis-independent" if r["metric_id"] == "CM-10" else r["support_basis"]  # T13.1: stored under detected as a placeholder
        unit = {"CM-06": "sum (s)", "CM-07": "count"}.get(r["metric_id"], "value")  # T13.3: never a proportion
        body.append(f"- {r['metric_id']} ({basis}, {dict(sorted(r['stratum'].items()))}): {unit} {r['value']}")
    return "Completeness", body


def target_b_section(metric_rows: list[dict], split: dict, recording_origin: dict[str, str]) -> tuple[str, list[str]]:
    """T14.2 and T14.3: Target B (cluster bootstrap) intervals, each with the number of leakage groups per partition and data
    origin beside it. A group whose members differ in origin is counted once under the joined origin set. A split with
    shared_scene_content is scoped as held-out runs of the same synthetic layout."""
    partition_of = recording_partitions(split)
    counts: dict[str, dict[str, int]] = {}
    for group in split["leakage_groups"]:
        members = group["member_recording_ids"]
        missing = [m for m in members if m not in recording_origin]
        if missing:
            raise ContractError("ERR-INVARIANT", f"T14.3: no data origin for {missing}")
        origin = "+".join(sorted({recording_origin[m] for m in members}))
        part = partition_of[members[0]]
        counts.setdefault(part, {}).setdefault(origin, 0)
        counts[part][origin] += 1
    groups = "; ".join(f"{p}: " + ", ".join(f"{o} {n}" for o, n in sorted(counts[p].items())) for p in sorted(counts, key=ORDER.get))
    body = [f"Scope: {T14_SCOPE}.", ""] if split.get("shared_scene_content") else []
    for r in sorted((r for r in metric_rows if r.get("interval_method") == "cluster_bootstrap"), key=lambda r: (r["metric_id"], r["slice"].get("partition", ""))):
        level = f"{round(r['ci_level'] * 100):d} %"
        body.append(f"- {r['metric_id']} ({r['slice'].get('partition')}): {r.get('value')} [{r.get('ci_low')}, {r.get('ci_high')}] "
                    f"({level} cluster bootstrap); leakage groups by partition and data origin: {groups}")
    return "Target B intervals (new sessions)", body


def status_board(items: list[dict]) -> tuple[str, list[str]]:
    """The three statuses: implemented / verified / empirically validated (with scope). Empirical validation needs a scope
    and real data; fixtures and synthetic data never reach it (CLAUDE.md)."""
    body = ["| Item | Status | Scope |", "|---|---|---|"]
    for item in items:
        status = item["status"]
        if status not in STATUS_LABELS:
            raise ContractError("ERR-UNKNOWN-ENUM", f"status {status}")
        if status == "empirically_validated" and (not item.get("scope") or item.get("data_origin") not in ("real_natural", "real_staged")):
            raise ContractError("ERR-INVARIANT", f"{item['item']}: empirically validated needs a scope on real data")
        body.append(f"| {item['item']} | {STATUS_LABELS[status]} | {item.get('scope') or '—'} |")
    return "Status board", body
