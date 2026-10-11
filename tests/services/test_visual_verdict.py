# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""VisualVerdict: supermajority or silence. No slogans."""

from services.visual_verdict import (
    ASK_SCOPE,
    adjudicate,
    adjudicate_label,
    is_degenerate,
    repetition_score,
)


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


def test_identity_out_of_scope_locally():
    # Mechanism, not hope: nobody local is asked who-this-is.
    assert ASK_SCOPE["identity"] == ()


def test_degenerate_single_word_list_reply():
    # Real SmolVLM output on 001 (asked 3-word list, answered one).
    assert is_degenerate("Girl.", "For each character left to right: boy or girl?") is True


def test_degenerate_single_noun_describe_reply():
    # Real SmolVLM output on 001 (asked rightmost detail, answered "Hair.").
    assert is_degenerate("Hair.", "Describe only the rightmost character.") is True


def test_degenerate_copypaste_dupes():
    # Real SmolVLM shape on 001: numbered items, same sentence twice.
    ans = "1. Girl with dark hair. 2. Blonde haired boy with blonde hair. 3. Blonde haired boy with blonde hair."
    assert repetition_score(ans) >= 0.3
    assert is_degenerate(ans, "List each person.") is True


def test_fluent_answers_survive():
    ans = "Three characters stand side by side under cherry trees holding dango."
    assert is_degenerate(ans, "Describe the image.") is False
