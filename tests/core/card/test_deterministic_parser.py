"""E6 — DeterministicParser unit tests"""

from core.card.parser.deterministic_parser import DeterministicParser


class TestDeterministicParser:

    def test_parse_card_id_cc(self):
        parser = DeterministicParser()
        card, conf = parser.parse("CC-43")
        assert card.card_id == "CC-43"
        assert conf["card_id"] == 0.98

    def test_parse_card_id_sl(self):
        parser = DeterministicParser()
        card, _ = parser.parse("SL-01")
        assert card.card_id == "SL-01"

    def test_parse_card_id_e(self):
        parser = DeterministicParser()
        card, _ = parser.parse("E-05")
        assert card.card_id == "E-05"

    def test_parse_card_id_rc(self):
        parser = DeterministicParser()
        card, _ = parser.parse("RC-12")
        assert card.card_id == "RC-12"

    def test_parse_world_line(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01\n世界線: W01")
        assert card.world_line == "W01"

    def test_parse_name(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01\n姓名: 林明")
        assert card.name == "林明"

    def test_parse_core_trait(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01\n核心特質: 務實")
        assert card.core_trait == "務實"

    def test_parse_tokens(self):
        parser = DeterministicParser()
        card, _ = parser.parse("Token: 領導力 (0.85)\nToken: 決斷力 (0.75)")
        assert len(card.tokens) == 2
        assert card.tokens[0].name == "領導力"
        assert card.tokens[0].strength == 0.85

    def test_parse_qualified_id(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01\n世界線: W01")
        assert card.qualified_id == "CC-01@W01"

    def test_classify_auto_stage(self):
        parser = DeterministicParser()
        _, conf = parser.parse("CC-01\n世界線: W01\n姓名: Test\n核心特質: A\nToken: B (0.5)")
        cls = parser.classify_confidence(conf)
        assert cls["stage"] == "auto"

    def test_classify_needs_llm_low_confidence(self):
        parser = DeterministicParser()
        cls = parser.classify_confidence({"card_id": 0.0, "name": 0.0})
        assert cls["needs_llm"] is True

    def test_empty_text_returns_defaults(self):
        parser = DeterministicParser()
        card, _ = parser.parse("")
        assert card.card_id == ""
        assert card.name == ""

    def test_custom_fields_stored(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01\n自訂欄位: 測試值")
        assert "自訂欄位" in card.custom_fields

    def test_card_type_character(self):
        parser = DeterministicParser()
        card, _ = parser.parse("CC-01")
        assert card.card_type.name == "CHARACTER"

    def test_card_type_rule(self):
        parser = DeterministicParser()
        card, _ = parser.parse("RC-01")
        assert card.card_type.name == "RULE"
