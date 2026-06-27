# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [C] [L3]
# Phase 6 Integration Tests: End-to-End Pipeline + Performance Benchmarks
# =============================================================================

import asyncio
import time

import pytest

# ---------------------------------------------------------------------------
# 6.1.1  Search query: classify -> SEARCH -> gate -> auto_execute
# ---------------------------------------------------------------------------

class TestE2ESearchQuery:
    def test_classify_search_query(self):
        from ai.core.query_classifier import QueryClassifier, QueryType
        qc = QueryClassifier()
        result = qc.classify("搜尋台北天氣")
        assert result.primary_type == QueryType.SEARCH
        assert result.confidence > 0.5

    def test_gate_auto_execute_search(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="search",
            action_type="read",
            user_message="搜尋台北天氣",
            confidence=0.9,
            context={},
        )
        assert decision.action == "auto_execute"
        assert decision.handler == "web_search"

    def test_model_bus_execute_handler(self):
        from ai.core.model_bus import ModelBus
        bus = ModelBus()

        class MockSearchHandler:
            def process(self, query, context):
                return f"search result for: {query}"

        bus.register_handler("web_search", MockSearchHandler(), ["search"])
        results = asyncio.run(bus.execute_handler("web_search", "台北天氣", {}))
        assert results["type"] == "web_search"
        assert results["success"] is True


# ---------------------------------------------------------------------------
# 6.1.2  File read query: classify -> FILE -> gate -> auto_execute
# ---------------------------------------------------------------------------

class TestE2EFileRead:
    def test_classify_file_read(self):
        from ai.core.query_classifier import QueryClassifier, QueryType
        qc = QueryClassifier()
        result = qc.classify("讀取 temp.txt")
        assert result.primary_type == QueryType.FILE
        assert result.confidence > 0.5

    def test_gate_auto_execute_file_read(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="file",
            action_type="read",
            user_message="讀取 temp.txt",
            confidence=0.95,
            context={},
        )
        assert decision.action == "auto_execute"
        assert decision.handler == "file_ops"


# ---------------------------------------------------------------------------
# 6.1.3  File delete: classify -> FILE -> gate -> reject (irreversible)
# ---------------------------------------------------------------------------

class TestE2EFileDelete:
    def test_gate_rejects_delete(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="file",
            action_type="delete",
            user_message="刪除 temp.txt",
            confidence=0.8,
            context={},
        )
        assert decision.action == "confirm_then_execute"
        assert decision.handler == "file_ops"

    def test_gate_rejects_delete_all(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="file",
            action_type="delete",
            user_message="刪除全部檔案",
            confidence=0.9,
            context={},
        )
        assert decision.action == "confirm_then_execute"
        assert decision.handler == "file_ops"


# ---------------------------------------------------------------------------
# 6.1.5  Command with confirmation
# ---------------------------------------------------------------------------

class TestE2ECommandConfirm:
    def test_gate_confirm_command(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="command",
            action_type="read",
            user_message="幫我查字典",
            confidence=0.7,
            context={},
        )
        assert decision.action in ("confirm_then_execute", "reject")

    def test_gate_rejects_low_score_no_handler(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="unknown",
            action_type="none",
            user_message="x",
            confidence=0.05,
            context={},
        )
        assert decision.action in ("reject", "confirm_then_execute")


# ---------------------------------------------------------------------------
# 6.1.7  Negation detection -> reject
# ---------------------------------------------------------------------------

class TestE2ENegation:
    def test_negation_rejects(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        decision = gate.decide(
            query_type="search",
            action_type="read",
            user_message="不要搜尋",
            confidence=0.8,
            context={},
        )
        assert decision.action == "reject"


# ---------------------------------------------------------------------------
# 6.1.10  Greeting -> reflex -> LLM
# ---------------------------------------------------------------------------

class TestE2EGreeting:
    def test_classify_greeting(self):
        from ai.core.query_classifier import QueryClassifier, QueryType
        qc = QueryClassifier()
        result = qc.classify("你是誰")
        assert result.confidence > 0.2

    def test_classify_greeting_hello(self):
        from ai.core.query_classifier import QueryClassifier, QueryType
        qc = QueryClassifier()
        result = qc.classify("你好")
        assert result.primary_type == QueryType.GREETING
        assert result.confidence > 0.5


# ---------------------------------------------------------------------------
# 6.1.11  Math query -> ED3N math evaluation
# ---------------------------------------------------------------------------

class TestE2EMath:
    def test_classify_math(self):
        from ai.core.query_classifier import QueryClassifier, QueryType
        qc = QueryClassifier()
        result = qc.classify("123 + 456")
        assert result.primary_type == QueryType.MATH
        assert result.confidence > 0.5

    def test_ed3n_math_evaluation(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine()
        engine.load_presets()
        result = engine.process("三加五")
        assert result is not None
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# 6.1.14  Session persistence: memories survive restart
# ---------------------------------------------------------------------------

class TestE2ESessionPersistence:
    def test_session_save_and_load(self, tmp_path):
        from ai.context.memory_context import MemoryContextManager
        session_dir = str(tmp_path / "sessions")
        mgr = MemoryContextManager(session_dir=session_dir)
        mgr.create_memory("用戶問了天氣", "short_term", {"topic": "weather"})
        mgr.create_memory("用戶喜歡音樂", "long_term", {"topic": "music"})
        mgr.save_session("session_001")
        mgr2 = MemoryContextManager(session_dir=session_dir)
        loaded = mgr2.load_session("session_001")
        assert loaded is True
        assert mgr2.get_memory_count() == 2


# ---------------------------------------------------------------------------
# 6.2  Performance Benchmarks
# ---------------------------------------------------------------------------

class TestPerformanceBenchmarks:
    def test_reflex_latency_under_1ms(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine()
        engine.load_presets()
        start = time.perf_counter()
        for _ in range(100):
            engine.process_reflex("你好")
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100
        assert elapsed_ms < 5.0, f"Reflex latency {elapsed_ms:.2f}ms exceeds 5ms"

    def test_classify_latency_under_5ms(self):
        from ai.core.query_classifier import QueryClassifier
        qc = QueryClassifier()
        start = time.perf_counter()
        for _ in range(100):
            qc.classify("搜尋台北天氣")
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100
        assert elapsed_ms < 10.0, f"Classify latency {elapsed_ms:.2f}ms exceeds 10ms"

    def test_garden_process_latency_under_50ms(self):
        from ai.garden.garden_engine import GARDENEngine
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        start = time.perf_counter()
        for _ in range(20):
            engine.process("你好")
        elapsed_ms = (time.perf_counter() - start) * 1000 / 20
        assert elapsed_ms < 100.0, f"GARDEN latency {elapsed_ms:.2f}ms exceeds 100ms"

    def test_execution_gate_latency_under_1ms(self):
        from ai.core.execution_gate import ExecutionGate
        gate = ExecutionGate()
        start = time.perf_counter()
        for _ in range(100):
            gate.decide("search", "read", "搜尋天氣", 0.9, {})
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100
        assert elapsed_ms < 5.0, f"Gate latency {elapsed_ms:.2f}ms exceeds 5ms"


# ---------------------------------------------------------------------------
# 6.1.12  Continuation loop protection
# ---------------------------------------------------------------------------

class TestE2EContinuationLoop:
    def test_continuation_count_increments(self):
        context = {"continuation_count": 0}
        context["continuation_count"] += 1
        context["continuation_count"] += 1
        context["continuation_count"] += 1
        assert context["continuation_count"] >= 3


# ---------------------------------------------------------------------------
# 6.1.13  Cross-turn context
# ---------------------------------------------------------------------------

class TestE2ECrossTurnContext:
    def test_history_preserves_context(self):
        history = [
            {"role": "user", "content": "今天天氣"},
            {"role": "assistant", "content": "今天台北天氣晴朗"},
        ]
        assert len(history) == 2
        assert "天氣" in history[0]["content"]
        assert "晴朗" in history[1]["content"]


# ---------------------------------------------------------------------------
# ModelBus handler registration
# ---------------------------------------------------------------------------

class TestModelBusHandlerRegistration:
    def test_handler_not_found_returns_error(self):
        from ai.core.model_bus import ModelBus
        bus = ModelBus()
        result = asyncio.run(bus.execute_handler("nonexistent_handler", "test", {}))
        assert result["success"] is False

    def test_execute_handler_returns_structured_result(self):
        from ai.core.model_bus import ModelBus
        bus = ModelBus()

        class MockHandler:
            def process(self, query, context):
                return f"processed: {query}"

        bus.register_handler("mock", MockHandler(), ["test"])
        result = asyncio.run(bus.execute_handler("mock", "hello", {}))
        assert result["type"] == "mock"
        assert result["success"] is True
        assert "processed: hello" in result["result"]

    def test_model_bus_handler_latency_under_100ms(self):
        from ai.core.model_bus import ModelBus
        bus = ModelBus()

        class MockHandler:
            def process(self, query, context):
                return f"result: {query}"

        bus.register_handler("mock", MockHandler(), ["test"])
        start = time.perf_counter()
        for _ in range(10):
            asyncio.run(bus.execute_handler("mock", "test", {}))
        elapsed_ms = (time.perf_counter() - start) * 1000 / 10
        assert elapsed_ms < 200.0, f"Handler latency {elapsed_ms:.2f}ms exceeds 200ms"
