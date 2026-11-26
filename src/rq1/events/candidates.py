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


# --- T25.2 episode continuity across POW breaks (E-1.2.26; D-58) -------------------------------------------------------

CONTINUITY_VERSION = "T25.2_pow_continuity_v1"  # event_link.linkage_version of a T25.2 join (AR-69 item 5)
JOINED_GROUPING_VERSION = "single_camera_t25_2_v1"  # grouping_algorithm_version with T25.2 on (AR-69 item 6)
BREAKS = {"not_recorded", "gap_unobserved", "unusable"}
EPS = 1e-9


def _pair_key(ep: Row, pows: dict[str, Row]) -> tuple:
    p = pows[ep["pow_id"]]
    return (p["person_track_id"], p["forklift_track_id"], p["timeline_id"], p["camera_id"])


def _joinable(e1: Row, e2: Row, t_by_pow: dict[str, dict[int, int]], coverage: list[Row], max_gap_s: float) -> bool:
    if e1["pow_id"] == e2["pow_id"]:
        return False  # T25.2 joins across POWs only; within a POW the lifecycle (m_gap) decides
    a, b = e1["t_end_tl_s"], e2["t_start_tl_s"]
    gap = b - a
    if gap < -EPS or gap > max_gap_s + EPS:
        return False
    for pid in {e1["pow_id"], e2["pow_id"]}:
        flags = t_by_pow.get(pid, {})
        if any(flags.get(i) == 1 for i in range(e1["end_frame_excl"], e2["start_frame"])):
            return False  # a T = 1 frame of either POW lies in the gap
    return not any(s["coverage_state"] in BREAKS and s["t_start_tl_s"] < b - EPS and s["t_end_tl_s"] > a + EPS for s in coverage)


def join_chains(episodes: list[Row], pows: dict[str, Row], t_by_pow: dict[str, dict[int, int]], coverage: list[Row], max_gap_s: float) -> list[list[Row]]:
    """T25.2 (b): chains of episodes of the same pair (stitched identities under T25.1, otherwise tracks) in the same camera
    timeline, consecutive in time, each joined to the next iff the gap rule holds. Every episode is in exactly one chain.
    `t_by_pow`: pow_id -> frame_index -> T (the flag series); `coverage`: the timeline's coverage segments."""
    groups: dict[tuple, list[Row]] = {}
    for ep in episodes:
        groups.setdefault(_pair_key(ep, pows), []).append(ep)
    chains = []
    for key in sorted(groups, key=_jcs):
        run = sorted(groups[key], key=lambda e: (e["t_start_tl_s"], e["start_frame"], _jcs(episode_nk(e))))
        chain = [run[0]]
        for prev, nxt in zip(run, run[1:]):
            if _joinable(prev, nxt, t_by_pow, coverage, max_gap_s):
                chain.append(nxt)
            else:
                chains.append(chain)
                chain = [nxt]
        chains.append(chain)
    return sorted(chains, key=lambda c: _order(c[0]))


def _ca_member(chain: list[Row]) -> Row:
    """CR-037 primary reading: the member holding the event's closest approach is the one with the lowest measured minclr
    (ties: earliest); without a measured clearance, the earliest member with a closest-approach frame; else the first."""
    measured = [(e["minclr_m"], k) for k, e in enumerate(chain) if e.get("minclr_m") is not None]
    if measured:
        return chain[min(measured)[1]]
    return next((e for e in chain if e.get("closest_approach_frame") is not None), chain[0])


def joined_events(chains: list[list[Row]], d_nm: float) -> list[Row]:
    """T25.2 (c): one candidate_event per chain and scenario (single camera: S_VIEW = S_LINK = S_POSS). Event flags are
    taken over the members and the labels recomputed with section 6 (VR-E-032), never unioned:
    P_ev, X_ev, C_ev = any member; E_ev = Kleene OR; minclr_ev = min of the measured member values; K_ev = E_ev or
    (minclr_ev < d_nm). contact_state_ev and the IE evidence come from the closest-approach member (CR-037 primary
    reading); IE also holds when K_ev is unknown with H or PC (CL-INV-08)."""
    from .kleene import any_of
    out = []
    for scenario in SCENARIOS:
        for chain in chains:
            nks = [episode_nk(e) for e in chain]
            ca = _ca_member(chain)
            measured = [e["minclr_m"] for e in chain if e.get("minclr_m") is not None]
            p_ev, x_ev, c_ev = (any(e[n] for e in chain) for n in ("P_ep", "X_ep", "C_ep"))
            e_ev = any_of([e["E_ep"] for e in chain])
            minclr = min(measured) if measured else None
            k_ev = labels.k_value(e_ev, minclr, d_nm)
            row = {"scenario": scenario, "member_episode_nks": nks, "t_onset_tl_s": chain[0]["t_start_tl_s"], "t_end_tl_s": chain[-1]["t_end_tl_s"],
                   "P_ev": p_ev, "X_ev": x_ev, "C_ev": c_ev, "E_ev": e_ev, "K_ev": k_ev, "minclr_ev_m": minclr,
                   "contact_state_ev": ca["contact_state"], "grouping_algorithm_version": JOINED_GROUPING_VERSION,
                   "join_sequence": [_jcs(nk) for nk in nks], "edges_used": [], "alternative_groups": {}, "ambiguous": False, "unresolved_members": [],
                   "n_members": len(chain),
                   "unobserved_gap_s": sum(max(0.0, b["t_start_tl_s"] - a["t_end_tl_s"]) for a, b in zip(chain, chain[1:]))}
            for name in ("t_onset_tl_s", "t_end_tl_s", "minclr_ev_m"):
                row[f"{name}_null_reason"] = None if row[name] is not None else "not_observable"
            ie = bool(ca["lbl_IE"]) or (k_ev == 2 and (x_ev or c_ev))
            out.append({**row, **labels.assign(p_ev, x_ev, c_ev, k_ev, row["contact_state_ev"], ie)})
    return out


def continuity_links(chains: list[list[Row]]) -> list[Row]:
    """T25.2 (c): one event_link per consecutive member pair (AR-69 item 5): episode_a_nk < episode_b_nk by JCS (section
    5.6), edge `U` (no section 7 linkage claim; never an allowed edge of S_LINK or S_POSS), basis same_camera, no clock or
    geometry values, linkage_version CONTINUITY_VERSION."""
    out = []
    for chain in chains:
        for a, b in zip(chain, chain[1:]):
            x, y = sorted([episode_nk(a), episode_nk(b)], key=_jcs)
            out.append({"episode_a_nk": x, "episode_b_nk": y, "edge": "U", "time_offset_s": None, "time_offset_s_null_reason": "not_applicable",
                        "clock_sigma_s": None, "clock_sigma_s_null_reason": "not_applicable", "median_mahalanobis": None,
                        "median_mahalanobis_null_reason": "not_applicable", "n_overlap_frames": 0, "basis": ["same_camera"], "link_conflict": False,
                        "linkage_version": CONTINUITY_VERSION})
    return sorted(out, key=lambda r: _jcs([r["episode_a_nk"], r["episode_b_nk"]]))
