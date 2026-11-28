"""`EventEngine.run` (S5): flag_series, episode, discarded_episode, candidate_event and event_count_summary
(E-1.2.1 sections 5.6, 6, 7; Appendix T T9 and T10). S5 reads S1 and S4 and never writes them (CT-E-12)."""
from __future__ import annotations

from collections.abc import Callable

import dataclasses
from dataclasses import dataclass
from typing import Any

from rq1.ids import core
from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError

from . import candidates, engine, providers

Row = dict[str, Any]


@dataclass(frozen=True)
class S5Config:
    rules: providers.RuleParams
    params: engine.Params
    substrate_config: Row  # the section 5.2 substrate_config record the S4 artifact was built with
    band_scheme_id: str
    version_label: str | None = None
    m_gap_s: float | None = None  # T25.3: lifecycle.m_gap_s; None = absent (m_gap_frames applies, E-1.2.25)
    join_across_pow: bool | None = None  # T25.2 (a): None = absent; absent or False = off


def substrate_config_id(record: Row) -> str:
    return core.make_id("sbc", record)


def rule_configuration(cfg: S5Config) -> Row:
    """The section 5.2 rule_configuration record of this run. Its content-addressed ID is the S5 configuration ID.
    T12.1: a provider's params hold only its exclusive parameters (R1 k_img, R2 d_p, R3 d_pc, R4 ttc_max, pet_max (T15.5),
    R5 e_turn, e_acc, e_dec).
    v_min and the prediction horizon tau come from substrate_config; w_e is in the classification block."""
    r, p = cfg.rules, cfg.params
    providers_list = [{"provider_id": "R1", "enabled": r.p_provider == "R1", "params": {"k_img": r.k_img}},
                      {"provider_id": "R2", "enabled": r.p_provider == "R2", "params": {"d_p": r.d_p}},
                      {"provider_id": "R3", "enabled": "R3" in r.conflict, "params": {"d_pc": r.d_pc}},
                      {"provider_id": "R4", "enabled": "R4" in r.conflict, "params": {"pet_max": r.pet_max, "ttc_max": r.ttc_max}},
                      {"provider_id": "R5", "enabled": r.r5, "params": {"e_turn": r.e_turn, "e_acc": r.e_acc, "e_dec": r.e_dec}}]
    row = {"experiment": "E1", "providers": providers_list,
           "lifecycle": lifecycle(cfg),
           "classification": {"d_nm_m": p.d_nm, "k_sigma": p.k_sigma, "k_c": p.k_c, "k_c_turn": p.k_c_turn, "o_max_frac": p.o_max, "w_e_s": p.w_e},
           "motion_models": ["constant_velocity"], "substrate_config_id": substrate_config_id(cfg.substrate_config), "band_scheme_id": cfg.band_scheme_id,
           "preregistration_ref": None, "preregistration_ref_null_reason": "not_applicable"}
    row["version_label"] = cfg.version_label
    row["version_label_null_reason"] = None if cfg.version_label is not None else "not_applicable"
    return row


def lifecycle(cfg: S5Config) -> Row:
    """Section 5.2 lifecycle block. T25.0: `m_gap_s` (T25.3) and `join_across_pow` (T25.2) enter only when present, so a
    configuration without them has its E-1.2.25 record and ID (AR-69 item 7)."""
    p = cfg.params
    out: Row = {"m_gap_frames": p.m_gap, "t_min_s": p.t_min, "w_post_s": p.w_post}
    if cfg.m_gap_s is not None:
        out["m_gap_s"] = cfg.m_gap_s
    if cfg.join_across_pow is not None:
        out["join_across_pow"] = cfg.join_across_pow
    return out


def config_id(cfg: S5Config) -> str:
    return core.make_id("rcf", rule_configuration(cfg))


def effective_rules(cfg: S5Config) -> providers.RuleParams:
    """T12.1 single sources: v_min and tau from substrate_config, w_e from the classification block. A runtime value that
    disagrees with its source is refused, so no output can depend on a value the configuration IDs do not carry."""
    sc, r = cfg.substrate_config, cfg.rules
    for name, runtime, source in (("v_min", r.v_min, sc["v_min"]), ("tau", r.tau, sc["prediction_horizon_s"]), ("w_e", r.w_e, cfg.params.w_e)):
        if runtime != source:
            raise ContractError("ERR-SPEC", f"T12.1: {name} = {runtime} differs from its single source ({source})")
    providers.check_r4(r.ttc_max, r.pet_max, r.tau)
    return r


def _pow_nk(p: Row) -> list:
    return [p["person_track_id"], p["forklift_track_id"], p["start_frame"]]


def build(s1: dict[str, list[Row]], s4: Artifact, cfg: S5Config, spec: Spec, members: dict[str, list[str]] | None = None,
          *, check_inputs: Callable[[Row, providers.RuleParams, list[engine.FrameFlags]], None] | None = None) -> Artifact:
    """`members`: stitched identity -> member track IDs (`providers.stitch_members` of the S4 input's S3), so that M, R4, R5
    and the contact cue read each member's stored S4 state on its own frames (CR-042, reading 1). Omit it for unstitched S4."""
    # Ineligible frames have no frame_index; they sort after the eligible ones (by decode_seq). Only eligibility and the
    # recording are read from this list, so the order of ineligible frames changes nothing (AR-58 item 6, crash fix).
    frames = sorted((f for f in s1["frame"] if f["recording_id"] == s1["frame"][0]["recording_id"]),
                    key=lambda f: (f["frame_index"] is None, f["frame_index"] if f["frame_index"] is not None else f["decode_seq"]))
    recording = frames[0]["recording_id"]
    own = sorted((c for c in s1["coverage_segment"] if c.get("recording_id") == recording), key=lambda c: c["t_start_tl_s"])
    timeline_id = own[0]["timeline_id"]
    rules = effective_rules(cfg)
    if substrate_config_id(cfg.substrate_config) not in (s4.spec or {}).get("config_ids", []):
        raise ContractError("ERR-SPEC", "the S4 artifact was not built with this substrate_config (T12.1 single source)")
    pows = sorted(s4.tables["pow"], key=lambda p: canonical_json(_pow_nk(p)))
    params, delta_nom = cfg.params, None
    if cfg.m_gap_s is not None or cfg.join_across_pow:
        delta_nom = next(d for d in s1["decode_summary"] if d["recording_id"] == recording)["delta_nom_s"]
    if cfg.m_gap_s is not None:  # T25.3: m_gap_frames for a POW from m_gap_s and the recording's delta_nom (S1)
        params = dataclasses.replace(params, m_gap=engine.m_gap_frames(cfg.m_gap_s, delta_nom))
    flag_rows: list[Row] = []
    episodes: list[Row] = []
    discarded: list[Row] = []
    last_episode: dict[str, Row] = {}  # pow_id -> episode that ends at the POW end
    by_pow_id = {p["pow_id"]: p for p in pows}
    index = providers.S4Index(s4.tables, frames, s1["coverage_segment"], members=members)  # AR-58 item 5; CR-042 members
    for pw in pows:
        flags = providers.flag_frames(s4.tables, rules, frames, s1["coverage_segment"], pow_nk=_pow_nk(pw), index=index)
        if check_inputs is not None:
            check_inputs(pw, rules, flags)
        eps, disc = engine.run_pow(flags, params)
        flag_rows += engine.flag_series_rows(pw["pow_id"], flags)
        discarded += [{"pow_id": pw["pow_id"], **d} for d in disc]
        for ep in eps:
            row = {"pow_id": pw["pow_id"], "experiment": "E1", "classification_contract": "E1_v1", "recording_id": pw["recording_id"],
                   "camera_id": pw["camera_id"], "timeline_id": pw["timeline_id"], **ep,
                   "label_stability_frac": None, "label_stability_frac_null_reason": "not_computed_by_config"}  # MR-08 computes it (AR-40 item 2)
            row["continuation_of_nk"], row["continuation_of_nk_null_reason"] = None, "not_applicable"
            # Lifecycle step 6: an episode split at a POW break is linked to the part that ran to the end of the previous POW.
            prev = by_pow_id.get(pw.get("continuation_of_id")) if pw.get("continuation_of_id") else None
            if prev is not None and ep["start_frame"] == pw["start_frame"] and prev["pow_id"] in last_episode:
                row["continuation_of_nk"], row["continuation_of_nk_null_reason"] = [prev["pow_id"], last_episode[prev["pow_id"]]["start_frame"]], None
            if ep["end_frame_excl"] == pw["end_frame_excl"]:
                last_episode[pw["pow_id"]] = row
            episodes.append(row)
    extra: dict[str, list[Row]] = {}
    if cfg.join_across_pow:  # T25.2: episodes are unchanged; events are chains of them
        max_gap = cfg.m_gap_s if cfg.m_gap_s is not None else cfg.params.m_gap * delta_nom
        t_by_pow: dict[str, dict[int, int]] = {}
        for r in flag_rows:
            t_by_pow.setdefault(r["pow_id"], {})[r["frame_index"]] = r["T"]
        camera = own[0]["camera_id"]
        coverage = [c for c in s1["coverage_segment"] if c["timeline_id"] == timeline_id and c["camera_id"] == camera]
        chains = candidates.join_chains(episodes, by_pow_id, t_by_pow, coverage, max_gap)
        events = candidates.joined_events(chains, params.d_nm)
        extra["event_link"] = candidates.continuity_links(chains)
    else:
        events = candidates.candidate_events(episodes)
    counts = candidates.count_summaries(events, episodes, [("recording", recording), ("timeline", timeline_id)])
    return build_artifact(spec, {"flag_series": flag_rows, "episode": episodes, "discarded_episode": discarded,
                                 "candidate_event": events, "event_count_summary": counts, **extra})
