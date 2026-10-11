# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""L4 semantics: probe plumbing + merge-by-decision (pure logic tested)."""

from services.visual_semantics import (
    MARGIN_BAR,
    crop_for_track,
    gate_decision,
    group_box,
    merge_by_decision,
)


def _track(i, box, decision):
    return {"id": i, "box": box, "decision": decision, "fixations": 2}


def test_touching_same_decision_merges():
    # The straddler case: two adjacent crops, both person -> one group.
    groups = merge_by_decision(
        [_track(1, [0.0, 0.3, 0.4, 0.7], "person"), _track(2, [0.3, 0.3, 0.7, 0.7], "person")]
    )
    assert len(groups) == 1 and len(groups[0]) == 2


def test_separated_same_decision_stays_two():
    groups = merge_by_decision(
        [_track(1, [0.0, 0.0, 0.2, 0.5], "person"), _track(2, [0.8, 0.0, 1.0, 0.5], "person")]
    )
    assert len(groups) == 2


def test_different_decisions_do_not_merge():
    groups = merge_by_decision(
        [_track(1, [0.0, 0.3, 0.4, 0.7], "person"), _track(2, [0.3, 0.3, 0.7, 0.7], "background")]
    )
    assert len(groups) == 2


def test_weak_probes_abstain():
    assert gate_decision("person", 0.02) is None  # real 001 id=3 shape
    assert gate_decision("person", 0.84) == "person"
    assert gate_decision(None, 0.9) is None


def test_abstained_tracks_never_merge():
    tracks = [
        {"id": 1, "box": [0.0, 0.3, 0.4, 0.7], "decision": "person"},
        {"id": 2, "box": [0.3, 0.3, 0.7, 0.7], "decision": None},
    ]
    groups = merge_by_decision(tracks)
    assert len(groups) == 2


def test_group_box_unions():
    box = group_box([{"box": [0.0, 0.0, 0.3, 0.3]}, {"box": [0.2, 0.2, 0.5, 0.6]}])
    assert box == [0.0, 0.0, 0.5, 0.6]


def test_crop_roundtrip():
    import io as _io

    from PIL import Image

    img = Image.new("RGB", (200, 100), (200, 30, 30))
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    out = crop_for_track(buf.getvalue(), [0.25, 0.0, 0.75, 1.0])
    assert out is not None
    back = Image.open(_io.BytesIO(out))
    assert back.size == (100, 100)
