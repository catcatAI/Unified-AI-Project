"""Tests for CulturalContextModule — culture-aware response enhancement."""

import pytest


@pytest.fixture
def cultural_context():
    from ai.context.cultural_context import CulturalContextModule
    return CulturalContextModule()


class TestDetectCulture:

    def test_detect_western_by_code(self, cultural_context):
        assert cultural_context.detect(language_code="en") == "western"
        assert cultural_context.detect(language_code="fr") == "western"

    def test_detect_east_asian_by_code(self, cultural_context):
        assert cultural_context.detect(language_code="zh") == "east_asian"
        assert cultural_context.detect(language_code="ja") == "east_asian"
        assert cultural_context.detect(language_code="ko") == "east_asian"

    def test_detect_by_text_cjk(self, cultural_context):
        assert cultural_context.detect(text="你好世界") == "east_asian"

    def test_detect_by_text_hangul(self, cultural_context):
        assert cultural_context.detect(text="안녕하세요 세계") == "east_asian"

    def test_detect_arabic_by_text(self, cultural_context):
        assert cultural_context.detect(text="مرحبا بالعالم") == "middle_eastern"

    def test_detect_default_western(self, cultural_context):
        assert cultural_context.detect() == "western"


class TestCulturalNotes:

    def test_get_notes_returns_list(self, cultural_context):
        notes = cultural_context.get_notes("east_asian")
        assert len(notes) >= 4
        concepts = {n["concept"] for n in notes}
        assert "greeting" in concepts
        assert "respect" in concepts

    def test_get_notes_unknown_returns_empty(self, cultural_context):
        assert cultural_context.get_notes("atlantean") == []

    def test_get_greeting_advice(self, cultural_context):
        advice = cultural_context.get_greeting_advice("east_asian")
        assert "Bowing" in advice
        assert len(advice) > 10


class TestEnrichContext:

    def test_enrich_context_injects_region(self, cultural_context):
        result = cultural_context.enrich_context({}, "hello world", language_code="en")
        assert "cultural_context" in result
        assert result["cultural_context"]["region"] == "western"

    def test_enrich_context_injects_notes(self, cultural_context):
        result = cultural_context.enrich_context({}, "你好", language_code="zh")
        notes = result["cultural_context"]["notes"]
        assert len(notes) >= 1
        assert "concept" in notes[0]
        assert "note" in notes[0]

    def test_enrich_context_preserves_existing_keys(self, cultural_context):
        result = cultural_context.enrich_context(
            {"existing_key": "keep_me"}, "test"
        )
        assert result["existing_key"] == "keep_me"

    def test_enrich_context_without_text(self, cultural_context):
        result = cultural_context.enrich_context({}, "")
        assert "cultural_context" not in result or result["cultural_context"]["region"] == "western"
