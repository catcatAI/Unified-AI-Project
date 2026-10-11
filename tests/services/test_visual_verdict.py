# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""VisualVerdict: supermajority or silence. No slogans."""

from services.visual_verdict import adjudicate, adjudicate_label


def test_unanimous_decides():
    r = adjudicate([3, 3, 3])
    assert r["status"] == "decided" and r["answer"] == 3


def test_supermajority_decides_with_dissent_on_record():
    # The 001 count case, one-model-one-vote: SmolVLM 3, Qwen 3, CLIP 4.
    r = adjudicate([3, 3, 4])
    assert r["status"] == "decided" and r["answer"] == 3
    assert r["dissent"] == [4]


def test_split_abstains():
    r = adjudicate([3, 4])
    assert r["status"] == "abstained" and r["answer"] is None
    assert set(r["dissent"]) == {3, 4}


def test_empty_abstains():
    r = adjudicate([])
    assert r["status"] == "abstained" and r["answer"] is None


def test_identity_franchise_soup_abstains():
    # 001 identity case: SAO vs FGO — no supermajority, must not pick one.
    r = adjudicate_label(["Sword Art Online", "Fate/Grand Order"])
    assert r["status"] == "abstained" and r["answer"] is None


def test_identity_normalizes_case_and_space():
    r = adjudicate_label(["Fate/Grand Order", "fate/grand  order", "Fate/Grand Order"])
    assert r["status"] == "decided"
