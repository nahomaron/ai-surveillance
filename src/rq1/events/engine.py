"""S5 episode lifecycle and episode-level quantities (E-1.2.1 section 6; Appendix T section T9, E-1.2.7)."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import kleene, labels

EPS = 1e-9


@dataclass(frozen=True)
class Rates:
    """T9.2 rates at one frame. `turn_false`: the person's speed is below v_min at a or b, so the turn criterion is FALSE."""
    person_speed_change: float | None = None
    forklift_decel: float | None = None
    person_turn_rate: float | None = None
    turn_false: bool = False


@dataclass
class FrameFlags:
    frame_index: int
    t: float
    support: float
    P: int
    M: int
    C_by: dict[str, int]
    E: int = 2
    Q: int = 1
    clearance: float | None = None
    sigma: float | None = None
    G: int = 2
    closing_rate: float | None = None
    ttca: float | None = None
    image_gap_norm: float | None = None
    overlap: int = 2
    rates: Rates | None = None
    evidence_class: str = "detected"
    borderline: frozenset = frozenset()  # section 6.0 borderline P, M or C on this frame (enum names)
    extra_flags: frozenset = frozenset()  # pair-frame borderline flags from S4 (AR-35 item 3)
    X: int = field(default=2, init=False)
    C_any: int = field(default=0, init=False)
    T: int = field(default=0, init=False)


@dataclass(frozen=True)
class Params:
    m_gap: int
    t_min: float
    w_post: float
    d_nm: float
    k_sigma: float
    o_max: float
    g_max: int
    w_e: float
    k_c: float
    k_c_turn: float
    r5_enabled: bool
    e_turn: float
    e_acc: float
    e_dec: float


def expand(run_lengths: str) -> list[int]:
    out: list[int] = []
    for part in run_lengths.split(","):
        value, count = part.split("×")
        out += [int(value)] * int(count)
    return out


def _windows(frames: list[FrameFlags], m_gap: int, g_max: int) -> list[tuple[int, int]]:
    """Open on T = 1. T9.7: a maximal non-true run between true frames is bridged iff its length <= m_gap, or it has
    no T = 0 frame and its length <= g_max. Otherwise close after the last true frame."""
    out, k = [], 0
    while k < len(frames):
        if frames[k].T != 1:
            k += 1
            continue
        start = last = k
        j = k + 1
        while j < len(frames):
            if frames[j].T == 1:
                last, j = j, j + 1
                continue
            run_end = j
            while run_end < len(frames) and frames[run_end].T != 1:
                run_end += 1
            length = run_end - j
            bridged = length <= m_gap or (all(f.T == 2 for f in frames[j:run_end]) and length <= g_max)
            if run_end < len(frames) and bridged:
                j = run_end
            else:
                break
        out.append((start, last + 1))
        k = last + 1
    return out


def criteria(rates: Rates | None, e_turn: float, e_acc: float, e_dec: float) -> tuple[int, int, int]:
    """T9.2 criteria (turn, speed change, deceleration) as tri values: unknown when the required values are null."""
    if rates is None:
        return 2, 2, 2
    tri = lambda v, thr: 2 if v is None else int(v > thr)
    turn = 0 if rates.turn_false else tri(rates.person_turn_rate, e_turn)
    return turn, tri(rates.person_speed_change, e_acc), tri(rates.forklift_decel, e_dec)


def evasive(rates: Rates | None, e_turn: float, e_acc: float, e_dec: float) -> int:
    """T9.2: E(k) = turn > e_turn or speed change > e_acc or deceleration > e_dec, in Kleene logic."""
    return kleene.any_of(criteria(rates, e_turn, e_acc, e_dec))


def contact_cue(rates: Rates | None, k_c: float, k_c_turn: float) -> int:
    """T9.3: deceleration > k_c or person speed change > k_c or person turn rate > k_c_turn, in Kleene logic."""
    return kleene.any_of(criteria(rates, k_c_turn, k_c, k_c))


def evasive_ratio(rates: Rates | None, e_turn: float, e_acc: float, e_dec: float) -> float | None:
    """Largest ratio of observed value to threshold among the three criteria (T9.2); a FALSE turn has no value."""
    if rates is None:
        return None
    pairs = [(None if rates.turn_false else rates.person_turn_rate, e_turn), (rates.person_speed_change, e_acc), (rates.forklift_decel, e_dec)]
    values = [v / thr for v, thr in pairs if v is not None]
    return max(values) if values else None


def closest_approach(inside: list[FrameFlags]) -> tuple[FrameFlags | None, float | None, bool]:
    """T9.5: (CA frame, t_CA, ca_observed)."""
    measured = [f for f in inside if f.clearance is not None]
    if measured:
        m = min(measured, key=lambda f: (f.clearance, f.frame_index))
        pos = inside.index(m)
        following = inside[pos + 1] if pos + 1 < len(inside) else None
        if m is measured[-1] and following is not None and following.clearance is None and (m.closing_rate is None or m.closing_rate > 0):
            t_ca = m.t + m.ttca if m.ttca is not None else inside[-1].t + inside[-1].support
            ca = min(inside, key=lambda f: (round(abs(f.t - t_ca), 9), f.frame_index))
            return ca, t_ca, False
        return m, m.t, True
    boxed = [f for f in inside if f.image_gap_norm is not None]
    if boxed:
        ca = min(boxed, key=lambda f: (f.image_gap_norm, f.frame_index))
        return ca, ca.t, False
    return None, None, False


def run_pow(frames: list[FrameFlags], params: Params, ca_inputs: labels.CaInputs | None = None) -> tuple[list[dict], list[dict]]:
    for f in frames:
        if not params.r5_enabled:
            f.E = 0  # T9.4: R5 not enabled, so E is 0 and E_ep = 0 (AR-38 item 1)
        f.X = kleene.k_and(f.P, f.M)
        f.C_any = kleene.any_of(f.C_by.values())
        f.T = kleene.k_or(kleene.k_or(f.P, f.X), f.C_any)
    pow_end = frames[-1].t + frames[-1].support
    episodes, discarded = [], []
    for start, end in _windows(frames, params.m_gap, params.g_max):
        inside = frames[start:end]
        t0, t1 = inside[0].t, inside[-1].t + inside[-1].support
        span = t1 - t0
        if span < params.t_min - EPS:
            discarded.append({"start_frame": inside[0].frame_index, "end_frame_excl": inside[-1].frame_index + 1, "span_s": span, "discard_reason": "shorter_than_t_min"})
            continue
        attr_end_t = min(t1 + params.w_post, pow_end)
        plus = [f for f in frames[start:] if f.t < attr_end_t - EPS]
        before = frames[start - 1] if start > 0 else None
        episodes.append(_episode(inside, plus, before, span, t0, t1, params, ca_inputs))
    return episodes, discarded


def _episode(inside: list[FrameFlags], plus: list[FrameFlags], before: FrameFlags | None, span: float, t0: float, t1: float,
             params: Params, given: labels.CaInputs | None) -> dict:
    providers = sorted({p for f in inside for p in f.C_by})
    p_ep, x_ep, c_ep = (any(getattr(f, n) == 1 for f in inside) for n in ("P", "X", "C_any"))
    e_ep = kleene.any_of(f.E for f in plus) if params.r5_enabled else 0  # T9.4
    measured = [f for f in inside if f.clearance is not None]
    low = min(measured, key=lambda f: (f.clearance, f.frame_index)) if measured else None
    minclr = low.clearance if low else None
    k = labels.k_value(e_ep, minclr, params.d_nm)
    if given is not None:  # Appendix N1 is flag level: its rows state the CA frame, overlap and cue (AR-37)
        at = next((f for f in inside if f.frame_index == given.frame_index), None)
        if at is None:
            at, t_ca, observed = closest_approach(inside)
        else:
            t_ca, observed = at.t, at.clearance is not None
        overlap, cue = given.overlap, int(given.cue)
    else:
        at, t_ca, observed = closest_approach(inside)
        overlap = at.overlap if at else 2
        cue = contact_cue(at.rates, params.k_c, params.k_c_turn) if at else 2
    w_ca = [f for f in plus if abs(f.t - t_ca) <= params.w_e / 2 + EPS] if at is not None else []
    q_at_ca = at is not None and at.Q == 1
    contact = labels.contact_state(at is not None, any(f.Q == 1 for f in w_ca), q_at_ca, overlap, cue,
                                   at.clearance if at else None, at.sigma if at else None, params.k_sigma)
    insufficient_q = sum(f.support for f in inside if f.Q != 1)
    h_or_pc = x_ep or c_ep
    ie = (not q_at_ca) or insufficient_q > params.o_max * span + 1e-12 or contact == "not_assessable" or (k == 2 and h_or_pc)
    flags = set().union(*(f.borderline | f.extra_flags for f in plus))
    if inside[0].borderline or (before is not None and before.borderline):  # T9.8
        flags.add("onset_sensitive")
    ratios = [r for r in (evasive_ratio(f.rates, params.e_turn, params.e_acc, params.e_dec) for f in plus) if r is not None] if params.r5_enabled else []
    by_class = {c: sum(f.support for f in inside if f.evidence_class == c) for c in ("detected", "inferred", "insufficient")}
    out = {"start_frame": inside[0].frame_index, "end_frame_excl": inside[-1].frame_index + 1, "attr_end_frame_excl": plus[-1].frame_index + 1,
           "t_start_tl_s": t0, "t_end_tl_s": t1, "span_s": span,
           "duration_detected_s": by_class["detected"], "duration_inferred_s": by_class["inferred"], "duration_insufficient_s": by_class["insufficient"],
           "P_ep": p_ep, "X_ep": x_ep, "C_ep": c_ep,
           "C_ep_by_provider": {p: any(f.C_by.get(p) == 1 for f in inside) for p in providers}, "E_ep": e_ep, "K": k, "e_assessed": params.r5_enabled,
           "minclr_m": minclr, "minclr_sigma_m": low.sigma if low else None, "minclr_frame": low.frame_index if low else None,
           "closest_approach_frame": at.frame_index if at else None, "ca_observed": observed, "contact_state": contact,
           "borderline_flags": sorted(flags), "exp_evasive_score": max(ratios) if ratios else None}
    out.update(labels.assign(p_ep, x_ep, c_ep, k, contact, ie))
    return out


def flag_series_rows(pow_id: str, frames: list[FrameFlags]) -> list[dict]:
    """Section 5.6 flag_series rows for one POW, after `run_pow` has set X, C_any and T."""
    return [{"pow_id": pow_id, "frame_index": f.frame_index, "P": f.P, "M": f.M, "X": f.X, "E": f.E, "G": f.G, "Q": f.Q, "C_any": f.C_any, "T": f.T,
             "C_by_provider": dict(sorted(f.C_by.items()))} for f in frames]
