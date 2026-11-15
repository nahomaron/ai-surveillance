"""V-01 item 5b (D-36 follow-up, Owner, 14 Nov 2026): Owner marking mode.

Per clip: "Would you send this clip for review? yes / no / unsure" and a free-text note. Marks are kept in
out/viewer/owner_marks.json, labelled "exploratory, Owner impression, not a reference label", and read by no stage.
In marking mode the page hides every overlay (rings, clearance line and label, speed vectors, ghosts, timeline lines,
turning shading) and shows only the footprints, the scrubber and the time.
"""
import json
import re
from pathlib import Path

import pytest

from rq1.schema.errors import ContractError
from rq1.viewer import marks, page

from test_v01_viewer import _frames, _payload

ROOT = Path(__file__).resolve().parents[2]
SPLIT = {"leakage_groups": [{"leakage_group_id": g, "member_recording_ids": [f"rec_{g}"], "edge_types": []} for g in ("a", "b", "t")],
         "assignments": [{"leakage_group_id": "a", "partition": "validation"}, {"leakage_group_id": "b", "partition": "validation"},
                         {"leakage_group_id": "t", "partition": "test"}]}


def _doc(rec, answer, note=""):
    return {"label": marks.LABEL, "question": marks.QUESTION, "read_by": marks.READ_BY, "schema": marks.SCHEMA,
            "marks": {rec: {"answer": answer, "note": note, "run": "r", "camera": "c", "dataset_row": "d", "page_code_commit": "0" * 40}}}


def test_wording_is_the_owner_text():
    assert marks.QUESTION == "Would you send this clip for review? yes / no / unsure"
    assert marks.LABEL == "exploratory, Owner impression, not a reference label"
    assert marks.ANSWERS == ("yes", "no", "unsure")
    assert marks.FILE == Path("out") / "viewer" / "owner_marks.json"


def test_merge_keeps_one_mark_per_clip_and_the_last_one_wins(tmp_path):
    a, b, a2 = tmp_path / "1.json", tmp_path / "2.json", tmp_path / "3.json"
    a.write_text(json.dumps(_doc("rec_a", "yes", "turn at 4 s")))
    b.write_text(json.dumps(_doc("rec_b", "unsure")))
    a2.write_text(json.dumps(_doc("rec_a", "no", "second look")))
    doc = marks.merge(marks.empty(), [a, b, a2], SPLIT)
    assert sorted(doc["marks"]) == ["rec_a", "rec_b"]
    assert doc["marks"]["rec_a"]["answer"] == "no" and doc["marks"]["rec_a"]["note"] == "second look"
    assert doc["label"] == marks.LABEL and doc["read_by"] == marks.READ_BY


@pytest.mark.determinism
def test_written_file_is_deterministic_and_labelled(tmp_path):
    src = tmp_path / "m.json"
    src.write_text(json.dumps(_doc("rec_b", "yes", "ü note")))
    out1, out2 = tmp_path / "o1.json", tmp_path / "o2.json"
    marks.write(marks.merge(marks.empty(), [src], SPLIT), out1)
    marks.write(marks.merge(marks.empty(), [src], SPLIT), out2)
    assert out1.read_bytes() == out2.read_bytes()
    assert json.loads(out1.read_text())["label"] == marks.LABEL


@pytest.mark.parametrize("bad, why", [
    (lambda d: d["marks"]["rec_a"].update(answer="maybe"), "answer outside yes / no / unsure"),
    (lambda d: d.update(label="reference label"), "label changed"),
    (lambda d: d["marks"].update({"rec_t": d["marks"].pop("rec_a")}), "test-partition clip"),
    (lambda d: d["marks"].update({"rec_zz": d["marks"].pop("rec_a")}), "clip not in the split"),
    (lambda d: d["marks"]["rec_a"].update(note=7), "note not text"),
], ids=["answer", "label", "test_partition", "outside_split", "note"])
def test_refuses_a_bad_mark_file(tmp_path, bad, why):
    d = _doc("rec_a", "yes")
    bad(d)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(d))
    with pytest.raises(ContractError) as e:
        marks.merge(marks.empty(), [path], SPLIT)
    assert e.value.code == "ERR-SPEC", why


def test_page_carries_the_marking_mode_and_the_wording():
    html = page.render(_payload(_frames())[0])
    for text in (marks.QUESTION.split("?")[0], marks.LABEL, 'id="markmode"', 'id="markpanel"', "owner_marks.json"):
        assert text in html, text
    data = page.embedded(html)
    assert data["marks"] == {"label": marks.LABEL, "question": marks.QUESTION, "read_by": marks.READ_BY, "schema": marks.SCHEMA,
                             "answers": list(marks.ANSWERS), "file": "out/viewer/owner_marks.json"}
    assert "safe" not in html.lower() and "near miss" not in html.lower()


def test_marking_mode_gates_every_overlay_in_the_page_script():
    """Each overlay drawing step of the page script is behind the marking-mode switch (structural check; the rendering was
    also checked in a browser, see the viewer report)."""
    script = page._SCRIPT
    for name in ("drawRings", "drawClearance", "drawVectors", "drawGhosts", "drawTimelineLines", "drawTurningShading"):
        assert f"function {name}(" in script, name
        calls = [m.start() for m in re.finditer(rf"\b{name}\(", script) if not script[max(0, m.start() - 9):m.start()].endswith("function ")]
        assert calls, name
        for at in calls:
            line = script[script.rfind("\n", 0, at) + 1:script.find("\n", at)]
            assert "!MARKING" in line, (name, line.strip())


def test_marks_are_read_by_no_stage():
    """Only the viewer's marks module and CLI name the marks file; no other module of rq1 does, and the page builder does
    not read it."""
    hits = [p for p in (ROOT / "src" / "rq1").rglob("*.py") if "owner_marks" in p.read_text()]
    assert sorted(p.relative_to(ROOT / "src" / "rq1").as_posix() for p in hits) == ["viewer/marks.py"]
    for name in ("payload.py", "recordings.py", "guard.py", "settings.py"):
        assert "marks" not in (ROOT / "src" / "rq1" / "viewer" / name).read_text(), name
