"""`EventEngine.run` (S5): flag_series, episode, discarded_episode, candidate_event and event_count_summary
(E-1.2.1 sections 5.6, 6, 7; Appendix T T9 and T10). S5 reads S1 and S4 and never writes them (CT-E-12)."""
from __future__ import annotations

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


def substrate_config_id(record: Row) -> str:
    return core.make_id("sbc", record)


def rule_configuration(cfg: S5Config) -> Row:
    """The section 5.2 rule_configuration record of this run. Its content-addressed ID is the S5 configuration ID.
    T12.1: a provider's params hold only its exclusive parameters (R1 k_img, R2 d_p, R3 d_pc, R5 e_turn, e_acc, e_dec).
    v_min and the prediction horizon tau come from substrate_config; w_e is in the classification block."""
    r, p = cfg.rules, cfg.params
    providers_list = [{"provider_id": "R1", "enabled": r.p_provider == "R1", "params": {"k_img": r.k_img}},
                      {"provider_id": "R2", "enabled": r.p_provider == "R2", "params": {"d_p": r.d_p}},
                      {"provider_id": "R3", "enabled": "R3" in r.conflict, "params": {"d_pc": r.d_pc}},
                      {"provider_id": "R5", "enabled": r.r5, "params": {"e_turn": r.e_turn, "e_acc": r.e_acc, "e_dec": r.e_dec}}]
    row = {"experiment": "E1", "providers": providers_list,
           "lifecycle": {"m_gap_frames": p.m_gap, "t_min_s": p.t_min, "w_post_s": p.w_post},
           "classification": {"d_nm_m": p.d_nm, "k_sigma": p.k_sigma, "k_c": p.k_c, "k_c_turn": p.k_c_turn, "o_max_frac": p.o_max, "w_e_s": p.w_e},
           "motion_models": ["constant_velocity"], "substrate_config_id": substrate_config_id(cfg.substrate_config), "band_scheme_id": cfg.band_scheme_id,
           "preregistration_ref": None, "preregistration_ref_null_reason": "not_applicable"}
    row["version_label"] = cfg.version_label
    row["version_label_null_reason"] = None if cfg.version_label is not None else "not_applicable"
    return row


def config_id(cfg: S5Config) -> str:
    return core.make_id("rcf", rule_configuration(cfg))


def effective_rules(cfg: S5Config) -> providers.RuleParams:
    """T12.1 single sources: v_min and tau from substrate_config, w_e from the classification block. A runtime value that
    disagrees with its source is refused, so no output can depend on a value the configuration IDs do not carry."""
    sc, r = cfg.substrate_config, cfg.rules
    for name, runtime, source in (("v_min", r.v_min, sc["v_min"]), ("tau", r.tau, sc["prediction_horizon_s"]), ("w_e", r.w_e, cfg.params.w_e)):
        if runtime != source:
            raise ContractError("ERR-SPEC", f"T12.1: {name} = {runtime} differs from its single source ({source})")
    return r


def _pow_nk(p: Row) -> list:
    return [p["person_track_id"], p["forklift_track_id"], p["start_frame"]]


def build(s1: dict[str, list[Row]], s4: Artifact, cfg: S5Config, spec: Spec) -> Artifact:
    frames = sorted((f for f in s1["frame"] if f["recording_id"] == s1["frame"][0]["recording_id"]), key=lambda f: f["frame_index"])
    recording = frames[0]["recording_id"]
    own = sorted((c for c in s1["coverage_segment"] if c.get("recording_id") == recording), key=lambda c: c["t_start_tl_s"])
    timeline_id = own[0]["timeline_id"]
    rules = effective_rules(cfg)
    if substrate_config_id(cfg.substrate_config) not in (s4.spec or {}).get("config_ids", []):
        raise ContractError("ERR-SPEC", "the S4 artifact was not built with this substrate_config (T12.1 single source)")
    pows = sorted(s4.tables["pow"], key=lambda p: canonical_json(_pow_nk(p)))
    flag_rows: list[Row] = []
    episodes: list[Row] = []
    discarded: list[Row] = []
    last_episode: dict[str, Row] = {}  # pow_id -> episode that ends at the POW end
    by_pow_id = {p["pow_id"]: p for p in pows}
    for pw in pows:
        flags = providers.flag_frames(s4.tables, rules, frames, s1["coverage_segment"], pow_nk=_pow_nk(pw))
        eps, disc = engine.run_pow(flags, cfg.params)
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
    events = candidates.candidate_events(episodes)
    counts = candidates.count_summaries(events, episodes, [("recording", recording), ("timeline", timeline_id)])
    return build_artifact(spec, {"flag_series": flag_rows, "episode": episodes, "discarded_episode": discarded,
                                 "candidate_event": events, "event_count_summary": counts})
