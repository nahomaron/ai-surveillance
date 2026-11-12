"""Type notation of E-1.2.1 section 1.1, parsed from the table definitions in tables.py."""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

SCALARS = {"str", "id", "i32", "i64", "f64", "bool", "tri", "ts", "nk"}


@dataclass(frozen=True)
class Type:
    kind: str  # scalar name, or enum, list, struct, map
    values: tuple[str, ...] = ()  # enum values
    item: "Type | None" = None  # list item or map value
    key: "Type | None" = None  # map key
    size: int | None = None  # fixed list length
    fields: tuple["Field", ...] = ()  # struct members


@dataclass(frozen=True)
class Field:
    name: str
    type: Type
    nullable: bool = False
    constraints: frozenset[str] = frozenset()
    provisional: bool = False  # type or existence inferred; recorded in CR-002
    derived: bool = False  # section 2.2 derived ID column, not hashed


def _split_top(text: str, sep: str = ",") -> list[str]:
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch in "<{[":
            depth += 1
        elif ch in ">}]":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


def with_reasons(fields: list[Field], reason_type: Type) -> list[Field]:
    """Section 1.1: a nullable field requires a nullable <field>_null_reason sibling."""
    out: list[Field] = []
    for f in fields:
        out.append(f)
        if f.nullable:
            marks = frozenset({"event"}) & f.constraints  # a reason column shares its field's column class
            out.append(Field(f"{f.name}_null_reason", reason_type, nullable=True, constraints=marks, derived=f.derived))
    return out


def parse_type(text: str, enums: dict[str, tuple[str, ...]]) -> Type:
    text = text.strip()
    if text in SCALARS:
        return Type(text)
    if text in enums:
        return Type("enum", values=enums[text])
    if text.startswith("enum{") and text.endswith("}"):
        return Type("enum", values=tuple(_split_top(text[5:-1])))
    if text.startswith("list<"):
        depth, end = 0, -1
        for i, ch in enumerate(text):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        rest = text[end + 1:]
        size = int(rest[1:-1]) if rest else None
        return Type("list", item=parse_type(text[5:end], enums), size=size)
    if text.startswith("map<") and text.endswith(">"):
        key, value = _split_top(text[4:-1])
        return Type("map", key=parse_type(key, enums), item=parse_type(value, enums))
    if text.startswith("struct{") and text.endswith("}"):
        members = []
        for part in _split_top(text[7:-1]):
            name, type_text = part.split(":", 1)
            nullable = name.endswith("?")
            members.append(Field(name.rstrip("?"), parse_type(type_text, enums), nullable))
        reason = Type("enum", values=enums["null_reason"])
        return Type("struct", fields=tuple(with_reasons(members, reason)))
    raise ValueError(f"unknown type: {text!r}")


@dataclass
class KeyPart:
    name: str
    source: str | None = None  # field in integer microseconds, per CN-2


@dataclass
class Table:
    name: str
    prefix: str | None
    store: str
    stage: str
    identity_class: str
    key: list[KeyPart]
    fields: list[Field]
    types_inferred: bool = False  # contract lists fields without types; see CR-002
    notes: list[str] = dc_field(default_factory=list)

    def key_names(self) -> list[str]:
        return [k.name for k in self.key]
