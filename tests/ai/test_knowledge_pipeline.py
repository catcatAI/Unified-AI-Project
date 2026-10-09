# ANGELA-MATRIX: L2 [βγδ] [A] [L3+]

import pytest
from ai.meta.knowledge_pipeline import KnowledgePipeline


@pytest.mark.asyncio
async def test_identity_question_does_not_enter_knowledge_pipeline():
    pipeline = KnowledgePipeline()

    assert await pipeline.query("自我介紹一下") is None
    assert await pipeline.query("你有啥能力？") is None
    assert await pipeline.query("高興的意思") is None


def test_identity_question_is_not_a_dictionary_lookup():
    pipeline = KnowledgePipeline()

    assert pipeline._detect_dictionary_query("自我介紹一下") == (False, "")


def test_long_cjk_sentence_is_not_a_bare_dictionary_lookup():
    pipeline = KnowledgePipeline()

    assert pipeline._detect_dictionary_query("今天天氣真不錯") == (False, "")


def test_explicit_meaning_lookup_still_works():
    pipeline = KnowledgePipeline()

    is_dictionary, query = pipeline._detect_dictionary_query("高興的意思")
    assert is_dictionary is True
    assert query == "高興"


@pytest.mark.parametrize(
    "query",
    [
        "現在幾點",
        "今天幾號",
        "水的沸點是幾度",
        "一百加二十是多少",
        "誰是孔子",
        "哪裡有好吃的",
        "為什麼天是藍的",
    ],
)
def test_interrogatives_are_not_bare_dictionary_lookups(query):
    """Questions must not hijack to translation (live: 現在幾點→the present)."""
    pipeline = KnowledgePipeline()

    assert pipeline._detect_dictionary_query(query) == (False, "")


@pytest.mark.parametrize("query", ["蘋果", "computer", "光合作用"])
def test_bare_words_still_translate(query):
    pipeline = KnowledgePipeline()

    is_dictionary, lookup = pipeline._detect_dictionary_query(query)
    assert is_dictionary is True
    assert lookup == query
