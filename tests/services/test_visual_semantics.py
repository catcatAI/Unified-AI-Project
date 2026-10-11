# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""L4 semantics: probe plumbing + merge-by-decision (pure logic tested)."""

from services.visual_semantics import (
    MARGIN_BAR,
    crop_for_track,
    gate_decision,
    group_box,
    link_subjects,
    merge_by_decision,
    size_band,
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


def test_zoom_split_on_weak():
    # Fake probe: whole box weak, quadrants decisive. Recursion must surface
    # the sub-cell verdicts instead of one abstention.
    import io as _io

    from PIL import Image
    from services.visual_semantics import zoom_probe

    img = Image.new("RGB", (200, 200), (240, 240, 240))
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    calls = []

    def fake_probe(crop_png):
        calls.append(1)
        # First call = whole box (weak); rest = quadrants (decisive).
        if len(calls) == 1:
            return ("a mask", 0.05)
        return ("a hat", 0.6)

    leaves = zoom_probe(data, [0.0, 0.0, 1.0, 1.0], fake_probe, depth=1)
    assert len(calls) == 5  # 1 whole + 4 quadrants
    hats = [lf for lf in leaves if lf["decision"] == "a hat"]
    assert len(hats) == 4


def test_zoom_no_split_on_firm():
    import io as _io

    from PIL import Image
    from services.visual_semantics import zoom_probe

    img = Image.new("RGB", (200, 200), (240, 240, 240))
    buf = _io.BytesIO()
    img.save(buf, format="PNG")

    def firm_probe(crop_png):
        return ("a person", 0.8)

    leaves = zoom_probe(buf.getvalue(), [0.0, 0.0, 1.0, 1.0], firm_probe, depth=1)
    assert len(leaves) == 1 and leaves[0]["decision"] == "a person"


def test_same_looks_same_size_links():
    emb = [1.0, 0.0, 0.0]
    items = [
        {"box": [0.0, 0.0, 0.2, 0.2], "decision": "a mask", "emb": emb},
        {"box": [0.8, 0.8, 1.0, 1.0], "decision": "a mask", "emb": emb},
    ]
    groups = link_subjects(items)
    assert len(groups) == 1  # distant but same subject -> one


def test_person_vs_its_doll_stays_two():
    # Same looks, different size: a person and its mini version are two.
    emb = [1.0, 0.0, 0.0]
    items = [
        {"box": [0.0, 0.0, 0.4, 0.4], "decision": "a mask", "emb": emb},
        {"box": [0.0, 0.0, 0.1, 0.1], "decision": "a mask", "emb": emb},
    ]
    assert size_band(items[0]["box"]) != size_band(items[1]["box"])
    assert len(link_subjects(items)) == 2


def test_different_looks_do_not_link():
    items = [
        {"box": [0.0, 0.0, 0.2, 0.2], "decision": "a mask", "emb": [1.0, 0.0]},
        {"box": [0.05, 0.05, 0.25, 0.25], "decision": "a mask", "emb": [0.0, 1.0]},
    ]
    assert len(link_subjects(items)) == 2  # touching but different -> two


def test_abstained_never_links():
    items = [
        {"box": [0.0, 0.0, 0.2, 0.2], "decision": None, "emb": [1.0, 0.0]},
        {"box": [0.0, 0.0, 0.2, 0.2], "decision": None, "emb": [1.0, 0.0]},
    ]
    assert len(link_subjects(items)) == 2


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
