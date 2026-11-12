"""Contact state, K and the E1 labels (E-1.2.1 section 6; Appendix N1 note on null sigma)."""
from __future__ import annotations

from dataclasses import dataclass

PRECEDENCE = ("CT", "UD", "NM", "PC", "H", "O")


@dataclass(frozen=True)
class CaInputs:
    """Closest-approach inputs. In part A they are given (Appendix N1 states them per row); CR-008 items 2, 4 and 5."""
    frame_index: int
    overlap: int
    cue: bool
    usable_around: bool


def contact_state(usable_around: bool, overlap: int, cue: bool, q_at_ca: bool, clearance: float | None, sigma: float | None, k_sigma: float) -> str:
    if not usable_around:
        return "not_assessable"
    if overlap == 1 and cue:
        return "suspected"
    if overlap in (1, 2) or not q_at_ca:
        return "undetermined"
    if clearance is not None and clearance - k_sigma * (sigma or 0.0) <= 0:  # within k_sigma * sigma of 0; null sigma uses 0
        return "undetermined"
    return "none_observed"


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
