"""
Test ProjectCoordinator + DocumentBuilder isolation
Covers B7/B8/B9/B10/B11 from ANGELA_SYSTEM_AUDIT_v6.2.5.md

Uses importlib.util to bypass the slow ai.dialogue package import chain.

NOTE: Source modules (ai.dialogue.project_coordinator, ai.dialogue.document_builder)
were deleted during Phase 9-12 cleanup. Keeping this file with skip guard in case
modules are restored.
"""
import pytest

pytest.skip("Source modules removed (ai.dialogue.*)", allow_module_level=True)


@pytest.fixture(scope="module")
def preloaded_imports():
    """Pre-load slow dependencies once per module session."""
    import core.shared.types.common_types
    import networkx as nx
    return True


@pytest.fixture(scope="module")
def project_coordinator(preloaded_imports):
    """Load ProjectCoordinator via importlib.util (bypasses slow package init)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "project_coordinator",
        str(src / "ai" / "dialogue" / "project_coordinator.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ProjectCoordinator


@pytest.fixture(scope="module")
def document_builder(preloaded_imports):
    """Load DocumentBuilder via importlib.util."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "document_builder",
        str(src / "ai" / "dialogue" / "document_builder.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DocumentBuilder


class TestProjectCoordinator:
    """B7/B8: ProjectCoordinator decomposition and fallback."""

    def test_init(self, project_coordinator):
        from unittest.mock import MagicMock
        coord = project_coordinator(
            memory_manager=MagicMock(),
            personality_manager=MagicMock(),
            dialogue_manager_config={"turn_timeout_seconds": 60},
        )
        assert coord.turn_timeout_seconds == 60

    def test_fallback_decompose_character(self, project_coordinator):
        result = project_coordinator()._fallback_decompose("生成一個角色卡")
        assert len(result) >= 1
        assert result[0]["capability_needed"] == "creative_writing_v1"

    def test_fallback_decompose_search(self, project_coordinator):
        result = project_coordinator()._fallback_decompose("搜尋最新AI資訊")
        assert len(result) >= 1
        assert result[0]["capability_needed"] == "web_search_v1"

    def test_fallback_decompose_default(self, project_coordinator):
        result = project_coordinator()._fallback_decompose("隨便處理")
        assert len(result) >= 1
        assert result[0]["capability_needed"] == "creative_writing_v1"

    def test_detect_complex_task_positive(self, project_coordinator):
        coord = project_coordinator()
        assert coord._detect_complex_task("生成角色卡") == True
        assert coord._detect_complex_task("整理所有文件") == True
        assert coord._detect_complex_task("研究") == True
        assert coord._detect_complex_task("建立") == True

    def test_detect_complex_task_negative(self, project_coordinator):
        coord = project_coordinator()
        assert coord._detect_complex_task("你好") == False
        assert coord._detect_complex_task("嗨") == False

    def test_clean_json_response(self, project_coordinator):
        coord = project_coordinator()
        raw = '[{"task": "test"}]'
        cleaned = coord._clean_json_response(raw)
        assert cleaned[0] == "["

    def test_clean_json_no_match(self, project_coordinator):
        coord = project_coordinator()
        raw = "This is not JSON"
        result = coord._clean_json_response(raw)
        assert result == raw
    async def test_integrate_fallback(self, project_coordinator):
        from unittest.mock import AsyncMock
        coord = project_coordinator()
        coord.prompts = {}
        results = {0: "Result A", 1: "Result B"}
        llm_mock = AsyncMock()
        llm_mock.generate_text = AsyncMock(return_value="整合結果")
        result = await coord._integrate_subtask_results("原始", results, llm_mock)
        assert result == "整合結果"


class TestDocumentBuilder:
    """B9/B10/B11: DocumentBuilder build, type detection, format learning."""

    def test_init(self, document_builder):
        import asyncio
        async def mock_llm(prompt, **kwargs):
            return "test output"
        builder = document_builder(
            llm_generate_fn=mock_llm,
            max_segments=4,
            tokens_per_segment=256,
        )
        assert builder.max_segments == 4
        assert builder.tokens_per_segment == 256

    def test_detect_task_type(self, document_builder):
        async def ml(p, **k): pass
        builder = document_builder(llm_generate_fn=ml)
        assert builder._detect_task_type("生成一個角色卡") == "character_card"
        assert builder._detect_task_type("生成角色") == "character_card"
        assert builder._detect_task_type("整理所有文件") == "document"
        assert builder._detect_task_type("報告") == "document"
        assert builder._detect_task_type("搜尋最新資訊") == "research"
        assert builder._detect_task_type("規劃项目") == "plan"
        assert builder._detect_task_type("一般問答") == "general"

    def test_extract_keywords(self, document_builder):
        async def ml(p, **k): pass
        builder = document_builder(llm_generate_fn=ml)
        kw = builder._extract_keywords("生成一個測試角色卡")
        assert isinstance(kw, list)
        assert len(kw) <= 10

    def test_load_format_no_library(self, document_builder):
        async def ml(p, **k): pass
        builder = document_builder(llm_generate_fn=ml, template_library=None)
        result = builder._load_format_from_memory("character_card")
        assert result is None

    def test_load_format_with_mock_library(self, document_builder):
        from unittest.mock import MagicMock
        async def ml(p, **k): pass
        mock_lib = MagicMock()
        mock_lib.get_by_category = MagicMock(return_value=[
            MagicMock(id="fmt_001", content="格式內容", metadata={})
        ])
        builder = document_builder(llm_generate_fn=ml, template_library=mock_lib)
        result = builder._load_format_from_memory("character_card")
        assert result is not None
        assert result["format_id"] == "fmt_001"
    async def test_load_fantasy_codex_no_memory(self, document_builder):
        async def ml(p, **k): pass
        builder = document_builder(llm_generate_fn=ml, memory_manager=None)
        result = await builder._load_fantasy_codex("生成角色")
        assert result == {}
    async def test_build_basic(self, document_builder):
        async def slow_llm(prompt, **kwargs):
            import asyncio
            await asyncio.sleep(0.05)
            return "Generated content"
        builder = document_builder(llm_generate_fn=slow_llm, max_segments=2, tokens_per_segment=128)
        builder._update_eta = MagicMock()
        builder.eta_state = MagicMock()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            asyncio.wait_for(builder.build("生成測試", complexity=0.3), timeout=5.0)
        )
        loop.close()
        assert result is not None
        assert len(result.segments) >= 1
    async def test_build_with_user_feedback(self, document_builder):
        async def ml(p, **k): return "Generated"
        builder = document_builder(llm_generate_fn=ml)
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            builder.build("生成角色", complexity=0.5, user_feedback="自訂格式", learn_from_output=True)
        )
        loop.close()
        assert result is not None
    async def test_build_segment_failure_resilient(self, document_builder):
        attempt = {"count": 0}
        async def flaky_llm(prompt, **kwargs):
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise RuntimeError("Segment 0 failed")
            return "Recovery success"
        builder = document_builder(llm_generate_fn=flaky_llm, max_segments=4, tokens_per_segment=64)
        builder._update_eta = MagicMock()
        builder.eta_state = MagicMock()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            asyncio.wait_for(builder.build("測試", complexity=0.3), timeout=5.0)
        )
        loop.close()
        assert result.successful_segments >= 0
        assert result.successful_segments <= result.total_segments

    def test_learn_format_no_dup(self, document_builder):
        from unittest.mock import MagicMock
        async def ml(p, **k): pass
        builder = document_builder(llm_generate_fn=ml, template_library=MagicMock())
        builder._learn_format("character_card", "Query1", "Result", [])
        c1 = builder._format_counter
        builder._learn_format("character_card", "Query2", "Result", [])
        c2 = builder._format_counter
        assert c2 > c1


class TestIntegration:
    """Verify integration patterns between components."""

    def test_llm_chain_project_coordinator_to_document_builder(self, project_coordinator, document_builder):
        async def mock_llm(prompt, **kwargs):
            return "LLM output"
        builder = document_builder(llm_generate_fn=mock_llm)
        assert builder.llm_generate is not None

    def test_project_coordinator_standalone_no_hsp(self, project_coordinator):
        from unittest.mock import MagicMock
        coord = project_coordinator(memory_manager=None, hsp_connector=None)
        assert coord.hsp_connector is None
        assert coord._llm_service is None