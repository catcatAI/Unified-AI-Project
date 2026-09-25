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
