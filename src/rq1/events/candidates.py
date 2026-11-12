"""Single-camera candidate events and count summaries (E-1.2.1 sections 5.6 and 7; Package F WP-06).

With one camera every scenario holds one-member events (section 5.6), so S_VIEW = S_LINK = S_POSS and no
edge is ever used. Linkage across cameras is milestone M2."""
from __future__ import annotations

from typing import Any

from rq1.schema.canonical import canonical_json

from . import labels

Row = dict[str, Any]
SCENARIOS = ("S_VIEW", "S_LINK", "S_POSS")
GROUPING_VERSION = "single_camera_v1"  # AR-38 item 5


def _jcs(value: Any) -> str:
    return canonical_json(value).decode("utf-8")


def episode_nk(ep: Row) -> list:
    return [ep["pow_id"], ep["start_frame"]]


def _order(ep: Row) -> tuple:
    """Section 7 order: (t_onset with nulls last, camera_id, episode natural key)."""
    t = ep.get("t_start_tl_s")
    return (t is None, t if t is not None else 0.0, ep["camera_id"], _jcs(episode_nk(ep)))


def candidate_events(episodes: list[Row]) -> list[Row]:
    out = []
    for scenario in SCENARIOS:
        for ep in sorted(episodes, key=_order):
            nk = episode_nk(ep)
            row = {"scenario": scenario, "member_episode_nks": [nk], "t_onset_tl_s": ep["t_start_tl_s"], "t_end_tl_s": ep["t_end_tl_s"],
                   "P_ev": ep["P_ep"], "X_ev": ep["X_ep"], "C_ev": ep["C_ep"], "E_ev": ep["E_ep"], "K_ev": ep["K"], "minclr_ev_m": ep["minclr_m"],
                   "contact_state_ev": ep["contact_state"], "grouping_algorithm_version": GROUPING_VERSION,
                   "join_sequence": [_jcs(nk)], "edges_used": [], "alternative_groups": {}, "ambiguous": False, "unresolved_members": []}
            for name in ("t_onset_tl_s", "t_end_tl_s", "minclr_ev_m"):
                row[f"{name}_null_reason"] = None if row[name] is not None else "not_observable"
            # Labels are recomputed from the event's own flags (VR-E-032); IE comes from the one member's evidence.
            labelled = labels.assign(row["P_ev"], row["X_ev"], row["C_ev"], row["K_ev"], row["contact_state_ev"], ep["lbl_IE"])
            out.append({**row, **labelled})
    return out


COUNT_LABELS = ("all", "O", "H", "PC", "NM", "UD", "CT", "IE")
SCOPE_FIELDS = {"recording": "recording_id", "timeline": "timeline_id"}


def count_summaries(events: list[Row], episodes: list[Row], scopes: list[tuple[str, str]]) -> list[Row]:
    """T10.6: one row per (scope, scenario, label), zero counts included. `all` counts every event; another label counts
    events with lbl_<label> true, so labels overlap. An event belongs to the scope of its onset, which in a single-camera
    run is its one member episode's recording and timeline. Discarded episodes are not events."""
    member = {_jcs(episode_nk(ep)): ep for ep in episodes}
    out = []
    for scope_type, scope_id in scopes:
        field = SCOPE_FIELDS[scope_type]
        for scenario in SCENARIOS:
            members = [e for e in events if e["scenario"] == scenario and member[_jcs(e["member_episode_nks"][0])][field] == scope_id]
            for label in COUNT_LABELS:
                chosen = members if label == "all" else [e for e in members if e[f"lbl_{label}"]]
                out.append({"scope_type": scope_type, "scope_id": scope_id, "scenario": scenario, "label": label, "n_events": len(chosen),
                            "n_ambiguous_groups": sum(1 for e in chosen if e["ambiguous"]),
                            "n_unresolved_identity_episodes": sum(len(e["unresolved_members"]) for e in chosen),
                            "assumptions": [{"assumption": a, "status": "unverified", "evidence_ref": None, "evidence_ref_null_reason": "not_applicable"}
                                            for a in ("A1", "A2", "A3")],
                            "wording": "scenario_count"})
    return out
