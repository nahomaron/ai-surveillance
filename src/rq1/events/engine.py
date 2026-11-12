"""S5 episode lifecycle and episode-level quantities (E-1.2.1 section 6)."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import kleene, labels


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


def expand(run_lengths: str) -> list[int]:
    out: list[int] = []
    for part in run_lengths.split(","):
        value, count = part.split("×")
        out += [int(value)] * int(count)
    return out


def _windows(frames: list[FrameFlags], m_gap: int) -> list[tuple[int, int]]:
    """Open on T = 1; bridge non-true runs of at most m_gap frames (CR-008 item 6); close after the last true frame."""
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
            if run_end < len(frames) and run_end - j <= m_gap:
                j = run_end
            else:
                break
        out.append((start, last + 1))
        k = last + 1
    return out


def run_pow(frames: list[FrameFlags], params: Params, ca_inputs: labels.CaInputs | None = None) -> tuple[list[dict], list[dict]]:
    for f in frames:
        f.X = kleene.k_and(f.P, f.M)
        f.C_any = kleene.any_of(f.C_by.values())
        f.T = kleene.k_or(kleene.k_or(f.P, f.X), f.C_any)
    pow_end = frames[-1].t + frames[-1].support
    episodes, discarded = [], []
    for start, end in _windows(frames, params.m_gap):
        inside = frames[start:end]
        t0, t1 = inside[0].t, inside[-1].t + inside[-1].support
        span = t1 - t0
        if span < params.t_min - 1e-9:
            discarded.append({"start_frame": inside[0].frame_index, "end_frame_excl": inside[-1].frame_index + 1, "span_s": span, "discard_reason": "shorter_than_t_min"})
            continue
        attr_end_t = min(t1 + params.w_post, pow_end)
        plus = [f for f in frames[start:] if f.t < attr_end_t - 1e-9]
        episodes.append(_episode(inside, plus, span, t0, t1, params, ca_inputs))
    return episodes, discarded


def _episode(inside: list[FrameFlags], plus: list[FrameFlags], span: float, t0: float, t1: float, params: Params, ca: labels.CaInputs | None) -> dict:
    providers = sorted({p for f in inside for p in f.C_by})
    p_ep, x_ep, c_ep = (any(getattr(f, n) == 1 for f in inside) for n in ("P", "X", "C_any"))
    e_ep = kleene.any_of(f.E for f in plus)
    measured = [f for f in inside if f.clearance is not None]
    low = min(measured, key=lambda f: (f.clearance, f.frame_index)) if measured else None
    minclr = low.clearance if low else None
    k = labels.k_value(e_ep, minclr, params.d_nm)
    given = ca.frame_index if ca else None
    ca_index = given if given is not None else (low.frame_index if low else None)
    at = next((f for f in inside if f.frame_index == ca_index), None)
    if ca:
        overlap, cue, usable = ca.overlap, ca.cue, ca.usable_around
    else:
        overlap = 2 if (at is None or at.clearance is None) else (1 if at.clearance <= 0 else 0)
        cue, usable = False, at is not None
    q_at_ca = at is not None and at.Q == 1
    contact = labels.contact_state(usable, overlap, cue, q_at_ca, at.clearance if at else None, at.sigma if at else None, params.k_sigma)
    insufficient = sum(f.support for f in inside if f.Q != 1)
    h_or_pc = x_ep or c_ep
    ie = (not q_at_ca) or insufficient > params.o_max * span + 1e-12 or contact == "not_assessable" or (k == 2 and h_or_pc)
    out = {"start_frame": inside[0].frame_index, "end_frame_excl": inside[-1].frame_index + 1, "attr_end_frame_excl": plus[-1].frame_index + 1,
           "t_start_tl_s": t0, "t_end_tl_s": t1, "span_s": span, "P_ep": p_ep, "X_ep": x_ep, "C_ep": c_ep,
           "C_ep_by_provider": {p: any(f.C_by.get(p) == 1 for f in inside) for p in providers}, "E_ep": e_ep, "K": k,
           "minclr_m": minclr, "minclr_sigma_m": low.sigma if low else None, "minclr_frame": low.frame_index if low else None,
           "closest_approach_frame": ca_index, "contact_state": contact}
    out.update(labels.assign(p_ep, x_ep, c_ep, k, contact, ie))
    return out
