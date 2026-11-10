"""Identity primitives: E-1.2.1 sections 2.1 and 2.3, F.1 A1.2."""
from __future__ import annotations

import base64
import hashlib
import re
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from rq1.schema.canonical import canonical_json

UUID7 = re.compile(r"^[a-z0-9]{2,4}_[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def b32(digest: bytes) -> str:
    """Lowercase RFC 4648 base32 of a digest, padding removed, first 26 characters."""
    return base64.b32encode(digest).decode("ascii").lower().rstrip("=")[:26]


def make_id(prefix: str, value: Any) -> str:
    """`id(prefix, x)` of section 2.1."""
    return f"{prefix}_{b32(hashlib.sha256(canonical_json(value)).digest())}"


def anchor_id(prefix: str, table: str, natural_key: Any) -> str:
    """F.1 A1.2: `id(prefix, [table, nk])`."""
    return make_id(prefix, [table, natural_key])


def source_id(sha256_hex: str) -> str:
    """Section 2.1: `src_` is `b32(SHA-256(file bytes))`."""
    return f"src_{b32(bytes.fromhex(sha256_hex))}"


def observation_id(prefix: str, table: str, artifact_id: str, natural_key: Any) -> str:
    """Section 2.1: `b32(SHA-256(JCS([table, art_id, natural_key])))`."""
    return make_id(prefix, [table, artifact_id, natural_key])


def to_us(seconds: float) -> int:
    """CN-2: integer microseconds, round half to even on the exact binary value (AR-15)."""
    return int((Decimal(seconds) * 1_000_000).to_integral_value(rounding=ROUND_HALF_EVEN))
