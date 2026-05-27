"""E6 — CardImportPipeline integration tests"""

from core.card.resolver.pipeline_orchestrator import CardImportPipeline


class TestCardImportPipeline:

    def test_pipeline_auto_stage_high_confidence(self):
        pipeline = CardImportPipeline()
        text = "CC-01\n世界線: W01\n姓名: Test\n核心特質: 勇敢\nToken: 勇氣 (0.9)"
        result = pipeline.process(text)
        assert result.stage == "auto"
        assert result.confidence >= 0.85
        assert result.card.qualified_id == "CC-01@W01"

    def test_pipeline_angela_stage_low_confidence(self):
        pipeline = CardImportPipeline()
        text = "姓名: Test\n核心特質: 謹慎"
        result = pipeline.process(text)
        assert result.stage in ("angela", "llm")

    def test_pipeline_registry_stores_card(self):
        pipeline = CardImportPipeline()
        text = "CC-02\n世界線: W01\n姓名: Second"
        pipeline.process(text)
        stored = pipeline.registry.get("CC-02@W01")
        assert stored is not None
        assert stored.name == "Second"

    def test_pipeline_multiple_cards_same_id_merged(self):
        pipeline = CardImportPipeline()
        text1 = "CC-03\n世界線: W01\n姓名: First\nToken: A (0.5)"
        text2 = "CC-03\n世界線: W01\nToken: B (0.8)"
        pipeline.process(text1)
        result = pipeline.process(text2)
        assert result.card.name == "First"
        assert len(result.card.tokens) >= 1

    def test_pipeline_no_duplicate_registry_after_merge(self):
        pipeline = CardImportPipeline()
        pipeline.process("CC-04\n世界線: W01\n姓名: X")
        pipeline.process("CC-04\n世界線: W01\n姓名: Y")
        assert pipeline.registry.count == 1

    def test_pipeline_handles_empty_text(self):
        pipeline = CardImportPipeline()
        result = pipeline.process("")
        assert result.card is not None

    def test_pipeline_custom_fields_preserved(self):
        pipeline = CardImportPipeline()
        text = "CC-05\n世界線: W01\n姓名: Z\n自訂欄位: 測試123"
        result = pipeline.process(text)
        assert "自訂欄位" in result.card.custom_fields

    def test_pipeline_stage_log_contains_entries(self):
        pipeline = CardImportPipeline()
        result = pipeline.process("CC-06\n世界線: W01\n姓名: Log")
        assert len(result.stage_log) >= 2

    def test_pipeline_multiple_runs_independent(self):
        pipeline = CardImportPipeline()
        r1 = pipeline.process("CC-10\n世界線: W01\n姓名: A")
        r2 = pipeline.process("CC-20\n世界線: W02\n姓名: B")
        assert r1.card.qualified_id != r2.card.qualified_id
        assert pipeline.registry.count == 2

    def test_pipeline_result_has_all_fields(self):
        pipeline = CardImportPipeline()
        result = pipeline.process("CC-07\n世界線: W01\n姓名: Full")
        assert hasattr(result, "card")
        assert hasattr(result, "stage")
        assert hasattr(result, "confidence")
        assert hasattr(result, "conflicts_resolved")
        assert hasattr(result, "conflicts_total")
