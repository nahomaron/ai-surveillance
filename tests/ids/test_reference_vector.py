"""Appendix T section T5. Every expected value is copied from that table."""
from rq1.ids import artifact

ASP = "asp_s3example0000000000000"
TRACK = [
    {"recording_id": "rec_a", "track_local_id": 2, "class": "forklift", "start_frame": 10, "end_frame_excl": 12},
    {"recording_id": "rec_a", "track_local_id": 1, "class": "person", "start_frame": 10, "end_frame_excl": 13},
]
POINTS = [{"track_nk": ["rec_a", t], "frame_index": f, "state": s} for t, f, s in
          [(2, 11, "tracked"), (1, 12, "tracked"), (1, 10, "tracked"), (2, 10, "tracked"), (1, 11, "predicted")]]


def build():
    return artifact.build_artifact(ASP, {"track_point": POINTS, "track": TRACK}, validate=False)


def test_payload_hash_and_artifact_id():
    built = build()
    assert built.payload_sha256 == "2b38d32502f58662b39c32bd796a2d24e4dfc3ecd87140f1dcc9ff9568fff068"
    assert built.artifact_id == "art_pmpcesnhpbbgtw2f3fhb6zkqxk"


def test_canonical_stream_appendix_t5():
    expected = (
        'track\t{"class":"person","end_frame_excl":13,"recording_id":"rec_a","start_frame":10,"track_local_id":1}\n'
        'track\t{"class":"forklift","end_frame_excl":12,"recording_id":"rec_a","start_frame":10,"track_local_id":2}\n'
        'track_point\t{"frame_index":10,"state":"tracked","track_nk":["rec_a",1]}\n'
        'track_point\t{"frame_index":11,"state":"predicted","track_nk":["rec_a",1]}\n'
        'track_point\t{"frame_index":12,"state":"tracked","track_nk":["rec_a",1]}\n'
        'track_point\t{"frame_index":10,"state":"tracked","track_nk":["rec_a",2]}\n'
        'track_point\t{"frame_index":11,"state":"tracked","track_nk":["rec_a",2]}\n'
    )
    assert artifact.payload_stream({"track_point": POINTS, "track": TRACK}).decode("utf-8") == expected


def test_record_ids():
    built = build()
    by_key = {tuple(map(str, [r["recording_id"], r["track_local_id"]])): r["trk_id"] for r in built.tables["track"]}
    assert by_key[("rec_a", "1")] == "trk_zr3hb5b6y2jjuw7ab7aml6ymtf"
    assert by_key[("rec_a", "2")] == "trk_kwwpqd3ie7pk73ai5tvu2mevrq"
    points = {(r["track_nk"][1], r["frame_index"]): r for r in built.tables["track_point"]}
    assert points[(1, 10)]["tpt_id"] == "tpt_f3lfwb6nyvogr3qwgwiv3gl6zn"
    assert points[(1, 11)]["tpt_id"] == "tpt_zclgpfkf4k7j52hftbgoilotyu"
    assert points[(1, 12)]["tpt_id"] == "tpt_46omowvb74tg5fe4u7zwsdj6or"
    assert points[(2, 10)]["tpt_id"] == "tpt_mzpwebvgdvlqaxls3rwuf2ddp7"
    assert points[(2, 11)]["tpt_id"] == "tpt_dbqp2kun3bv562njoyaz72zoy2"
    assert {points[(1, f)]["track_id"] for f in (10, 11, 12)} == {"trk_zr3hb5b6y2jjuw7ab7aml6ymtf"}
    assert {points[(2, f)]["track_id"] for f in (10, 11)} == {"trk_kwwpqd3ie7pk73ai5tvu2mevrq"}


def test_ordering_is_bytewise_not_numeric():
    # Appendix T T5: [["rec_a",1],10] sorts before [["rec_a",1],9].
    rows = [{"track_nk": ["rec_a", 1], "frame_index": f, "state": "tracked"} for f in (9, 10)]
    stream = artifact.payload_stream({"track_point": rows}).decode().splitlines()
    assert '"frame_index":10' in stream[0] and '"frame_index":9' in stream[1]
