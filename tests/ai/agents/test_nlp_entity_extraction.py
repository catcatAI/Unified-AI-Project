"""
ANGELA-MATRIX: [L6] [β] [A] [L2]
Rule-based named entity recognition.

The NLP agent advertised entity extraction but only found URLs and emails —
every other type came back empty. These tests pin the coverage and, more
importantly, the *precision*: a wrong entity is worse than a missing one
for an agent that quotes its findings.
"""

import pytest
from ai.agents.specialized.nlp_processing_agent import extract_named_entities


def _by_type(entities, kind):
    return [e["value"] for e in entities if e["type"] == kind]


class TestNamedEntityRecognition:
    def test_empty_text(self):
        assert extract_named_entities("") == []

    def test_url_and_email(self):
        entities = extract_named_entities("see https://example.com/a and a@b.co")
        assert _by_type(entities, "URL") == ["https://example.com/a"]
        assert _by_type(entities, "EMAIL") == ["a@b.co"]

    def test_a_url_does_not_swallow_the_following_punctuation(self):
        entities = extract_named_entities("網址 https://example.com/x，預算")
        assert _by_type(entities, "URL") == ["https://example.com/x"]

    def test_dates_and_times(self):
        entities = extract_named_entities("2026年10月20日 14:30 開會")
        assert _by_type(entities, "DATE") == ["2026年10月20日"]
        assert _by_type(entities, "TIME") == ["14:30"]

    def test_money_and_percent(self):
        entities = extract_named_entities("預算 NT$12,500，成長率 15%")
        assert _by_type(entities, "MONEY") == ["NT$12,500"]
        assert _by_type(entities, "PERCENT") == ["15%"]

    def test_locations_from_the_gazetteer(self):
        entities = extract_named_entities("他在台北工作，搬到台灣")
        assert _by_type(entities, "LOCATION") == ["台北", "台灣"]

    def test_organisation_suffix(self):
        entities = extract_named_entities("台灣大學的研究")
        assert _by_type(entities, "ORG") == ["台灣大學"]

    def test_person_by_honorific(self):
        entities = extract_named_entities("李小姐和 Dr. Smith 一起")
        assert "李小姐" in _by_type(entities, "PERSON")
        assert "Smith" in _by_type(entities, "PERSON")

    def test_a_person_name_does_not_swallow_the_preceding_words(self):
        """「夥伴是李小姐」 — the name is 李, not 伴是李."""
        entities = extract_named_entities("夥伴是李小姐")
        assert _by_type(entities, "PERSON") == ["李小姐"]

    def test_numbers_are_reported_when_nothing_else_claims_them(self):
        entities = extract_named_entities("總共 42 個")
        assert _by_type(entities, "NUMBER") == ["42"]

    def test_a_date_is_not_also_reported_as_numbers(self):
        entities = extract_named_entities("2026年10月20日")
        assert _by_type(entities, "DATE") == ["2026年10月20日"]
        assert _by_type(entities, "NUMBER") == []

    def test_the_spans_point_at_the_text(self):
        text = "預算 NT$12,500"
        for entity in extract_named_entities(text):
            assert text[entity["start"] : entity["end"]] == entity["value"]


class TestAgentIntegration:
    def test_the_agent_reports_the_entities(self):
        from ai.agents.specialized.nlp_processing_agent import NLPProcessingAgent

        agent = NLPProcessingAgent()
        result = agent.extract_entities("王小明在台北，email: wang@example.com")
        assert result["status"] == "success"
        kinds = {e["type"] for e in result["entities"]}
        assert "EMAIL" in kinds
        assert "LOCATION" in kinds
