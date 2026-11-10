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


def test_identity_reference_vector_appendix_t5():
    """Expected values copied from Appendix T section T5."""
    import hashlib

    from rq1.ids.core import b32, make_id, observation_id
    rows = [("track", {"recording_id": "rec_a", "track_local_id": 1, "class": "person", "start_frame": 10, "end_frame_excl": 13}),
            ("track", {"recording_id": "rec_a", "track_local_id": 2, "class": "forklift", "start_frame": 10, "end_frame_excl": 12})]
    rows += [("track_point", {"track_nk": ["rec_a", t], "frame_index": f, "state": st}) for t, f, st in
             [(1, 10, "tracked"), (1, 11, "predicted"), (1, 12, "tracked"), (2, 10, "tracked"), (2, 11, "tracked")]]
    stream = b"".join(t.encode() + b"\t" + canonical_json(r) + b"\n" for t, r in rows)
    payload = hashlib.sha256(stream).hexdigest()
    assert payload == "2b38d32502f58662b39c32bd796a2d24e4dfc3ecd87140f1dcc9ff9568fff068"
    art = make_id("art", ["asp_s3example0000000000000", payload])
    assert art == "art_pmpcesnhpbbgtw2f3fhb6zkqxk"
    assert observation_id("trk", "track", art, ["rec_a", 1]) == "trk_zr3hb5b6y2jjuw7ab7aml6ymtf"
    assert observation_id("tpt", "track_point", art, [["rec_a", 2], 11]) == "tpt_dbqp2kun3bv562njoyaz72zoy2"
    assert len(b32(b"\x00" * 32)) == 26
