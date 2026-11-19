"""Appendix T T22 (contract E-1.2.20; CR-027, D-44): the C-layer blind review rules as pure functions.

Nothing here reads data or writes records; `store.py` applies these rules to stored records. The readings of T22 are
T22.14 (contract E-1.2.21; CR-028, D-46); representation choices are AR-61 (accepted, D-46).
"""
from __future__ import annotations

import hashlib
import math
from typing import Any, Iterable

import numpy as np

from rq1.evaluation.estimators import cohen_kappa, krippendorff_alpha_nominal
from rq1.schema.errors import ContractError

PARAMS = {"c_pad_s": 3.0, "n_batch": 60, "n_pilot": 20, "a_audit": 0.10}  # T22.12
LABELS = ("ct", "nm", "ud", "not_hazardous", "unsure")  # T22.5 (a)
CONFIDENCE = {1.0: "low", 2.0: "medium", 3.0: "high"}  # T22.5 (b)
METHODS = ("agreement", "adjudicator", "consensus_meeting")  # T22.7 (e)
STRATA = ("CT", "UD", "NM", "PC", "H", "O")  # T22.6 (a): the episode's summary_label
G2_MAP = {"lbl_nm": "nm", "lbl_ud": "ud", "lbl_ct": "ct"}  # T22.8 (b)
STATUS_TARGETS = ("system_episode", "system_event")  # T22.8 (a)

# T22.5 (a), verbatim: the reviewer-facing definitions.
DEFINITIONS = {
    "ct": "the person and the forklift (including forks, mast or load) appear to touch, or the person is struck, pushed or "
          "pinned, or an abrupt reaction at the closest moment makes contact likely.",
    "nm": "no contact is seen, but the forklift (or its forks or load) was moving and came close enough that contact was "
          "avoided only by a reaction (sudden stop, swerve, step back, jump) or by a margin so small that slightly different "
          "timing could plausibly have led to contact.",
    "ud": "it may be nm or ct, but the video does not show the decisive moment (occluded, out of frame, or overlapping in the "
          "image so that contact cannot be ruled in or out).",
    "not_hazardous": "the person and the forklift are near each other but there is no conflict: forklift and forks stationary, "
                     "or paths that do not conflict, or separation clearly adequate, or a barrier between them.",
    "unsure": "the reviewer can see the interaction but cannot decide among the labels above. (ud describes the video; unsure "
              "describes the reviewer's decision.)",
}


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


def check_label(label: Any) -> str:
    if label not in LABELS:
        raise _spec(f"label {label!r} is not one of {', '.join(LABELS)} (T22.5 a)")
    return label


def check_confidence(value: Any) -> float:
    """T22.5 (b): f64 in {1.0, 2.0, 3.0}; other values are refused (an int or a string is not an f64)."""
    if type(value) is not float or value not in CONFIDENCE:
        raise _spec(f"confidence {value!r} is not 1.0, 2.0 or 3.0 (T22.5 b)")
    return value


def check_rationale(text: Any) -> str:
    """T22.5 (c): required; at least one sentence saying what was seen (here: some text with letters in it)."""
    if not isinstance(text, str) or not any(ch.isalpha() for ch in text):
        raise _spec("a rationale saying what was seen is required (T22.5 c)")
    return text.strip()


def g2_from_flags(*, lbl_NM: bool, lbl_UD: bool, lbl_CT: bool) -> str | None:
    """The episode's automated G2 label as T22.8 (b) names it, or None when it has none."""
    on = [name for name, flag in (("lbl_nm", lbl_NM), ("lbl_ud", lbl_UD), ("lbl_ct", lbl_CT)) if flag]
    if len(on) > 1:
        raise ContractError("ERR-INVARIANT", f"episode carries more than one G2 label: {on}")
    return on[0] if on else None


def map_g2(g2_label: str | None) -> str:
    """T22.8 (b): lbl_nm -> nm, lbl_ud -> ud, lbl_ct -> ct, none of the three -> not_hazardous."""
    return G2_MAP.get(g2_label, "not_hazardous")


def status_for(final_label: str, mapped: str) -> str:
    """T22.8 (b)."""
    if final_label == "unsure":
        return "disputed"
    return "confirmed" if final_label == mapped else "rejected"


def is_tier1(a: str, b: str) -> bool:
    """T22.7 (a): both assessments have the same label and neither is unsure."""
    return a == b and a != "unsure"


def clip_window(onset_s: float, iplus_end_s: float, rec_start_s: float, rec_end_s: float, c_pad_s: float) -> tuple[float, float]:
    """T22.4: from max(recording start, onset - c_pad_s) to min(recording end, I+ end + c_pad_s)."""
    return max(rec_start_s, onset_s - c_pad_s), min(rec_end_s, iplus_end_s + c_pad_s)


def _rng(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(seed))


def _derived_seed(seed: int, *parts: str) -> int:
    """A seed derived from the batch seed and labels (AR-61 item 3): first 8 bytes of SHA-256, big-endian."""
    text = ":".join([str(int(seed)), *parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(text).digest()[:8], "big")


def allocate(sizes: dict[str, int], n: int, seed: int) -> dict[str, int]:
    """T22.6 (a): equal across the strata present, capped at stratum size, remainder by largest remainder with ties
    broken by the batch seed. T22.14 (e): water-filling; capping is applied until no remaining stratum is below the
    equal share; the integer remainder then goes to the largest fractional shares, which are equal, so the seed decides."""
    present = [s for s in STRATA if sizes.get(s, 0) > 0] + sorted(s for s in sizes if s not in STRATA and sizes[s] > 0)
    alloc: dict[str, int] = {}
    open_strata, remaining = list(present), n
    while open_strata:
        share = remaining / len(open_strata)
        capped = [s for s in open_strata if sizes[s] <= share]
        if not capped:
            break
        for s in capped:
            alloc[s] = sizes[s]
            remaining -= sizes[s]
        open_strata = [s for s in open_strata if s not in capped]
    if open_strata:
        share = remaining / len(open_strata)
        floors = {s: math.floor(share) for s in open_strata}
        left = remaining - sum(floors.values())
        fractions = {s: share - floors[s] for s in open_strata}
        order = list(open_strata)
        tie_rank = {s: k for k, s in enumerate(_rng(seed).permutation(order).tolist())}
        winners = sorted(open_strata, key=lambda s: (-fractions[s], tie_rank[s]))[:left]
        for s in open_strata:
            alloc[s] = floors[s] + (1 if s in winners else 0)
    return {s: alloc[s] for s in present}


def draw(frame: list[dict[str, Any]], n: int, seed: int, exclude: Iterable[str] = ()) -> tuple[dict[str, int], list[str]]:
    """T22.6 (a): allocate, then draw without replacement inside each stratum from episodes sorted by episode ID, with
    numpy PCG64 seeded by the batch seed (strata in T22.6 order; AR-61 item 2). Returns the allocation and the target IDs
    sorted by ID."""
    excluded = set(exclude)
    by_stratum: dict[str, list[str]] = {}
    for t in frame:
        if t["target_id"] not in excluded:
            by_stratum.setdefault(t["stratum"], []).append(t["target_id"])
    alloc = allocate({s: len(v) for s, v in by_stratum.items()}, n, seed)
    rng = _rng(_derived_seed(seed, "draw"))
    chosen: list[str] = []
    for s, k in alloc.items():
        pool = sorted(by_stratum[s])
        chosen += [pool[i] for i in sorted(rng.choice(len(pool), size=k, replace=False).tolist())]
    return alloc, sorted(chosen)


def reviewer_order(target_ids: list[str], seed: int, annotator_id: str) -> list[str]:
    """T22.6 (b): a seeded shuffle whose seed is derived from the batch seed and the annotator ID."""
    ids = sorted(target_ids)
    return [ids[i] for i in _rng(_derived_seed(seed, "order", annotator_id)).permutation(len(ids)).tolist()]


def audit_count(n_tier1: int, a_audit: float) -> int:
    """T22.14 (a): ceil(a_audit x n_tier1), with a 1e-9 guard so 0.1 x 10 is 1, not 2."""
    return math.ceil(a_audit * n_tier1 - 1e-9) if n_tier1 else 0


def audit_sample(tier1_ids: list[str], a_audit: float, seed: int) -> list[str]:
    """T22.7 (d): a seeded share a_audit of the batch's tier1 targets, drawn without replacement, returned sorted."""
    ids = sorted(tier1_ids)
    k = audit_count(len(ids), a_audit)
    if not k:
        return []
    return sorted(ids[i] for i in _rng(_derived_seed(seed, "audit")).choice(len(ids), size=k, replace=False).tolist())


def kappas(r1: list[str], r2: list[str]) -> tuple[float | None, float | None]:
    """T22.10 (a): Cohen's kappa over the five labels, and over the four labels without targets where either said unsure."""
    k5 = cohen_kappa(r1, r2) if r1 else None
    pairs = [(a, b) for a, b in zip(r1, r2) if "unsure" not in (a, b)]
    k4 = cohen_kappa([a for a, _ in pairs], [b for _, b in pairs]) if pairs else None
    return k5, k4


ALPHA_MIN_UNITS = 5  # T22.14 (b)


def alpha(units: list[list[str]]) -> float | None:
    """T22.14 (b): Krippendorff's alpha (nominal) over the audited targets only, three assessments each; not computed
    (None) with fewer than 5 audited targets."""
    return krippendorff_alpha_nominal(units) if len(units) >= ALPHA_MIN_UNITS else None


def median_p90(values: list[float | None]) -> tuple[float | None, float | None]:
    """review_time_s median and P90 (numpy linear interpolation), ignoring null times."""
    xs = [v for v in values if v is not None]
    if not xs:
        return None, None
    return float(np.percentile(xs, 50)), float(np.percentile(xs, 90))
