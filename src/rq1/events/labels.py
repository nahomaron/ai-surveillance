"""Contact state, K and the E1 labels (E-1.2.1 section 6; Appendix N1 note on null sigma)."""
from __future__ import annotations

from dataclasses import dataclass

PRECEDENCE = ("CT", "UD", "NM", "PC", "H", "O")


@dataclass(frozen=True)
class CaInputs:
    """Closest-approach inputs stated by an Appendix N1 row (flag level, AR-37). Pipeline runs derive them by T9.5 and T9.3."""
    frame_index: int
    overlap: int
    cue: bool


def contact_state(ca_exists: bool, usable_in_w_ca: bool, q_at_ca: bool, overlap: int, cue: int,
                  clearance: float | None, sigma: float | None, k_sigma: float) -> str:
    """Appendix T T10.1: evaluate in order, stop at the first match."""
    if not ca_exists or not usable_in_w_ca:
        return "not_assessable"  # 1 (T9.6 step 1)
    if not q_at_ca:
        return "undetermined"  # 2
    if overlap == 1 and cue == 1:
        return "suspected"  # 3
    if overlap in (1, 2) or clearance is None or clearance - k_sigma * (sigma or 0.0) <= 0:
        return "undetermined"  # 4: overlap 1 or unknown; within k_sigma*sigma of 0 (sigma 0 if null); clearance null
    return "none_observed"  # 5


def k_value(e_ep: int, minclr: float | None, d_nm: float) -> int:
    """K = E_ep or (minclr < d_nm), Kleene; no measurable clearance makes the second term unknown."""
    from .kleene import k_or

    return k_or(e_ep, 2 if minclr is None else (1 if minclr < d_nm else 0))


def assign(p_ep: bool, x_ep: bool, c_ep: bool, k: int, contact: str, ie: bool) -> dict:
    h, pc = x_ep, c_ep
    out = {"lbl_O": p_ep and not h and not pc, "lbl_H": h, "lbl_PC": pc,
           "lbl_NM": (h or pc) and k == 1 and contact == "none_observed", "lbl_UD": (h or pc) and k == 1 and contact == "undetermined",
           "lbl_CT": contact == "suspected", "lbl_IE": ie}
    out["summary_label"] = next(x for x in PRECEDENCE if out[f"lbl_{x}"]) if any(out[f"lbl_{x}"] for x in PRECEDENCE) else None
    out["review_route"] = contact in ("undetermined", "suspected") or any(out[f"lbl_{x}"] for x in ("NM", "UD", "CT", "IE"))
    return out
