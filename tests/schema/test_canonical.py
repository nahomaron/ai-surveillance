"""E-1.2.1 section 1.5: RFC 8785 canonical JSON. Expected strings are hand-written from RFC 8785."""
from rq1.schema.canonical import canonical_json, sort_set


def test_float_uses_jcs_form_not_python_repr():
    # Section 1.5 names this exact case: 1e-07 (general encoders) versus 1e-7 (JCS).
    assert canonical_json({"x": 1e-7}) == b'{"x":1e-7}'


def test_integral_float_has_no_fraction():
    assert canonical_json([1.0, 2]) == b"[1,2]"


def test_keys_sorted_and_no_whitespace():
    assert canonical_json({"b": 1, "a": [True, None]}) == b'{"a":[true,null],"b":1}'


def test_contract_sets_sort_by_canonical_json_of_elements():
    assert sort_set([{"b": 2}, {"a": 1}, 10, 9]) == [10, 9, {"a": 1}, {"b": 2}]
