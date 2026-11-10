"""Small schema-valid rows for identity tests (T-02). Natural-key fields are set explicitly."""
from __future__ import annotations

from typing import Any

from rq1.schema import registry

REC = "rec_" + "a" * 26
PERSON = "trk_" + "p" * 26
FORKLIFT = "trk_" + "f" * 26


def row(table: str, **changes: Any) -> dict[str, Any]:
    out = registry.minimal_row(table)
    for key, value in changes.items():
        out[key] = value
        if value is not None and f"{key}_null_reason" in out:
            out[f"{key}_null_reason"] = None
    return out


def track(local_id: int, cls: str = "person") -> dict[str, Any]:
    return row("track", recording_id=REC, track_local_id=local_id, **{"class": cls})


def track_point(local_id: int, frame: int) -> dict[str, Any]:
    return row("track_point", track_nk=[REC, local_id], frame_index=frame)


def pow_row(start: int) -> dict[str, Any]:
    return row("pow", person_track_id=PERSON, forklift_track_id=FORKLIFT, start_frame=start, end_frame_excl=start + 5)


def pair(start: int, frame: int) -> dict[str, Any]:
    return row("pair_series", pow_nk=[PERSON, FORKLIFT, start], frame_index=frame)


def episode(pow_id: str, start: int) -> dict[str, Any]:
    return row("episode", pow_id=pow_id, start_frame=start, end_frame_excl=start + 3, attr_end_frame_excl=start + 3)


def event_link(a: list, b: list) -> dict[str, Any]:
    return row("event_link", episode_a_nk=a, episode_b_nk=b)


def candidate_event(members: list[list]) -> dict[str, Any]:
    return row("candidate_event", member_episode_nks=members)
