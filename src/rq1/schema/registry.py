"""Registry and generators: Arrow schemas, JSON Schemas and row scaffolds from tables.py."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pyarrow as pa

from .tables import DEFINITIONS, ENUMS
from .types import Field, KeyPart, Table, Type, parse_type, with_reasons

REASON = Type("enum", values=ENUMS["null_reason"])
ID = Type("id")
# Section 5.7: forbidden quantities (VR-E-041), as normalized column-name fragments.
FORBIDDEN_FRAGMENTS = ("potential_energy", "fall_probability", "impact_energy", "falling_object_trajectory",
                       "trajectory", "severity", "risk_score")


def _parse_field(line: str) -> Field:
    tokens = line.split()
    provisional = tokens[-1] == "~"
    if provisional:
        tokens = tokens[:-1]
    constraints = frozenset(t[1:] for t in tokens if t.startswith("@"))
    tokens = [t for t in tokens if not t.startswith("@")]
    name, type_text = tokens[0], " ".join(tokens[1:])
    nullable = name.endswith("?")
    return Field(name.rstrip("?"), parse_type(type_text, ENUMS), nullable, constraints, provisional)


def _derived_for(field: Field) -> Field | None:
    """Section 2.2: each same-artifact `<table>_nk` resolves to a derived `<table>_id`."""
    if field.name.endswith("_nk") and field.type.kind == "nk":
        return Field(f"{field.name[:-3]}_id", ID, field.nullable, derived=True)
    if field.name.endswith("_nks") and field.type.kind == "list" and field.type.item.kind == "nk":
        return Field(f"{field.name[:-4]}_ids", Type("list", item=ID), derived=True)
    return None


def _key_parts(text: str) -> list[KeyPart]:
    parts = []
    for token in text.split():
        name, _, source = token.partition("=")
        parts.append(KeyPart(name, source or None))
    return parts


def _build(definition: tuple) -> Table:
    name, prefix, store, stage, cls, key, body, inferred = definition
    parsed = [_parse_field(line) for line in body.strip().splitlines()]
    expanded: list[Field] = []
    if prefix:
        expanded.append(Field(f"{prefix}_id", ID, derived=True))
    elif cls in ("human", "configuration") and not any(f.name.endswith("status_id") for f in parsed):
        expanded.append(Field(f"{name}_id", ID, derived=True, provisional=True))
    for field in parsed:
        expanded.append(field)
        derived = _derived_for(field)
        if derived:
            expanded.append(derived)
    return Table(name, prefix, store, stage, cls, _key_parts(key), with_reasons(expanded, REASON), inferred)


TABLES: dict[str, Table] = {d[0]: _build(d) for d in DEFINITIONS}
for _table in TABLES.values():
    _names = [f.name for f in _table.fields]
    if len(_names) != len(set(_names)):
        raise ValueError(f"duplicate column in {_table.name}")
    for _key in _table.key:
        if (_key.source or _key.name) not in _names:
            raise ValueError(f"key field missing in {_table.name}: {_key.name}")


def _arrow_type(t: Type) -> pa.DataType:
    if t.kind in ("str", "id", "nk"):
        return pa.utf8()
    simple = {"i32": pa.int32(), "i64": pa.int64(), "f64": pa.float64(), "bool": pa.bool_(), "tri": pa.int8(),
              "ts": pa.timestamp("us", tz="UTC")}
    if t.kind in simple:
        return simple[t.kind]
    if t.kind == "enum":
        return pa.dictionary(pa.int32(), pa.utf8())
    if t.kind == "list":
        item = _arrow_type(t.item)
        return pa.list_(item, t.size) if t.size else pa.list_(item)
    if t.kind == "map":
        key = pa.utf8() if t.key.kind == "enum" else _arrow_type(t.key)
        return pa.map_(key, _arrow_type(t.item))
    if t.kind == "struct":
        return pa.struct([pa.field(f.name, _arrow_type(f.type), f.nullable) for f in t.fields])
    raise ValueError(t.kind)


def arrow_schema(table: str) -> pa.Schema:
    return pa.schema([pa.field(f.name, _arrow_type(f.type), f.nullable) for f in TABLES[table].fields])


def _json_type(t: Type) -> dict[str, Any]:
    if t.kind == "id":
        return {"type": "string", "pattern": r"^[a-z0-9]{2,4}_([a-z0-9]{26}|[0-9a-f-]{36})$"}
    if t.kind in ("str", "nk"):
        return {"type": "string"}
    if t.kind in ("i32", "i64"):
        return {"type": "integer"}
    if t.kind == "f64":
        return {"type": "number"}
    if t.kind == "bool":
        return {"type": "boolean"}
    if t.kind == "tri":
        return {"enum": [0, 1, 2]}
    if t.kind == "ts":
        return {"type": "string", "format": "date-time"}
    if t.kind == "enum":
        return {"enum": list(t.values)}
    if t.kind == "list":
        schema: dict[str, Any] = {"type": "array", "items": _json_type(t.item)}
        if t.size:
            schema.update(minItems=t.size, maxItems=t.size)
        return schema
    if t.kind == "map":
        return {"type": "object", "additionalProperties": _json_type(t.item)}
    if t.kind == "struct":
        return _json_object(t.fields)
    raise ValueError(t.kind)


def _json_field(f: Field) -> dict[str, Any]:
    schema = _json_type(f.type)
    return {"anyOf": [schema, {"type": "null"}]} if f.nullable else schema


def _json_object(fields: tuple[Field, ...] | list[Field]) -> dict[str, Any]:
    pairs = [f for f in fields if f.nullable and f"{f.name}_null_reason" in {x.name for x in fields}]
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {f.name: _json_field(f) for f in fields},
        "required": [f.name for f in fields if not f.derived],
    }
    if pairs:
        schema["allOf"] = [{
            "oneOf": [
                {"properties": {f.name: {"type": "null"},
                                f"{f.name}_null_reason": {"enum": list(ENUMS["null_reason"])}}},
                {"properties": {f.name: {"not": {"type": "null"}}, f"{f.name}_null_reason": {"type": "null"}}},
            ]
        } for f in pairs]
    return schema


def json_schema(table: str) -> dict[str, Any]:
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": table,
            **_json_object(TABLES[table].fields)}


def forbidden_field_names(table: str) -> list[str]:
    return [f.name for f in TABLES[table].fields if any(x in f.name.lower() for x in FORBIDDEN_FRAGMENTS)]


def _minimal(f: Field) -> Any:
    if f.nullable:
        return None
    return _minimal_type(f.type, f.constraints)


def _minimal_type(t: Type, constraints: frozenset[str] = frozenset()) -> Any:
    if t.kind == "id":
        return "abc_" + "a" * 26
    if t.kind in ("str", "nk"):
        return "x"
    if t.kind in ("i32", "i64", "tri"):
        return 0
    if t.kind == "f64":
        return 0.0
    if t.kind == "bool":
        return False
    if t.kind == "ts":
        return datetime(2026, 1, 1, tzinfo=timezone.utc)
    if t.kind == "enum":
        return t.values[0]
    if t.kind == "list":
        if "bbox" in constraints:
            return [0.0, 0.0, 1.0, 1.0]
        return [_minimal_type(t.item) for _ in range(t.size)] if t.size else []
    if t.kind == "map":
        return {}
    if t.kind == "struct":
        return _minimal_struct(t.fields)
    raise ValueError(t.kind)


def _minimal_struct(fields) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for f in fields:
        row[f.name] = "not_applicable" if f.name.endswith("_null_reason") and row.get(f.name[:-12]) is None else _minimal(f)
    return row


def minimal_row(table: str) -> dict[str, Any]:
    """Smallest schema-valid row, used as a base for fixtures and tests."""
    row = _minimal_struct(TABLES[table].fields)
    if table == "site":
        row["data_origin"] = "synthetic_rendered"  # the first enum value is a real origin, which VR-E-070 restricts
    return row


def to_arrow(table: str, rows: list[dict[str, Any]]) -> pa.Table:
    """Load rows, encoding enums as dictionary columns (section 1.1)."""
    schema = arrow_schema(table)
    plain = pa.schema([pa.field(f.name, _undictionary(f.type), f.nullable) for f in schema])
    return pa.Table.from_pylist(rows, schema=plain).cast(schema)


def _undictionary(t: pa.DataType) -> pa.DataType:
    if pa.types.is_dictionary(t):
        return pa.utf8()
    if pa.types.is_fixed_size_list(t):
        return pa.list_(_undictionary(t.value_type), t.list_size)
    if pa.types.is_list(t):
        return pa.list_(_undictionary(t.value_type))
    if pa.types.is_map(t):
        return pa.map_(t.key_type, _undictionary(t.item_type))
    if pa.types.is_struct(t):
        return pa.struct([pa.field(x.name, _undictionary(x.type), x.nullable) for x in t])
    return t


__all__ = ["ENUMS", "TABLES", "arrow_schema", "json_schema", "forbidden_field_names", "minimal_row", "to_arrow"]
