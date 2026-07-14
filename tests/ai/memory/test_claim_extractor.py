"""Tests for the factual-claim extractor (no network)."""

from ai.memory.claim_extractor import extract_claims, is_searchable_query


def test_extracts_factual_sentence_with_copula_and_anchor():
    text = "Hello! The speed of light is 299792458 meters per second. How are you?"
    claims = extract_claims(text)
    assert any("speed of light" in c for c in claims)
    # question excluded
    assert not any("How are you" in c for c in claims)


def test_extracts_chinese_factual_sentence():
    text = "水的化學式是 H2O。今天天氣好嗎？請幫我搜尋新聞。"
    claims = extract_claims(text)
    assert any("H2O" in c for c in claims)
    # question excluded
    assert not any("天氣好嗎" in c for c in claims)
    # imperative excluded
    assert not any("搜尋新聞" in c for c in claims)


def test_excludes_pure_chitchat():
    text = "你好啊，今天過得怎麼樣？我覺得蠻好的。"
    claims = extract_claims(text)
    assert claims == []


def test_excludes_question_only():
    text = "What is the capital of France?"
    assert extract_claims(text) == []


def test_caps_number_of_claims():
    sentences = ". ".join(
        f"Element number {i} is a real chemical substance discovered in history." for i in range(20)
    )
    claims = extract_claims(sentences)
    assert len(claims) <= 8


def test_empty_text():
    assert extract_claims("") == []


def test_is_searchable_query_factual_question():
    assert is_searchable_query("What is the capital of Taiwan?") is True
    assert is_searchable_query("東京的首都是哪裡？") is True


def test_is_searchable_query_excludes_chitchat():
    assert is_searchable_query("How are you today?") is False
    assert is_searchable_query("我覺得蠻好的。") is False


def test_is_searchable_query_excludes_explicit_search_intent():
    assert is_searchable_query("幫我搜尋最新新聞") is False
    assert is_searchable_query("Please search the web for this.") is False
