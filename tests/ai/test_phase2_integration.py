"""
Phase 2 Intelligence Layer Integration Tests — AgentOrchestrator, PlanningEngine, ReasoningEngines
Tests for end-to-end orchestration, planning, and reasoning
"""

from unittest.mock import MagicMock

import pytest

# Lazy imports for optional modules
try:
    from ai.agents.agent_orchestrator import AgentOrchestrator
    from ai.reasoning.planning_engine import PlanningEngine
    from ai.reasoning.reasoning_engines import (
        AbductiveReasoner,
        AnalogicalReasoner,
        ChainOfThoughtReasoner,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="Phase 2 modules not available"
)


class TestAgentOrchestratorIntegration:
    """Integration tests for AgentOrchestrator"""

    def test_file_read_routes_correctly(self):
        ao = AgentOrchestrator()
        intent = ao.classify_intent("讀取文件 report.txt")
        assert intent == "file_read"

    def test_file_write_routes_correctly(self):
        ao = AgentOrchestrator()
        intent = ao.classify_intent("寫入文件 report.txt")
        assert intent == "file_write"

    def test_code_execute_routes_correctly(self):
        ao = AgentOrchestrator()
        intent = ao.classify_intent("執行代碼 print('hello')")
        assert intent == "code_execute"

    def test_web_search_routes_correctly(self):
        ao = AgentOrchestrator()
        intent = ao.classify_intent("搜尋天氣")
        # Regex sub-classification is the source of truth (the old IntentRegistry
        # gate returned "general" for every confident hit, killing the agent path)
        assert intent == "web_search"
        assert ao.select_agent(intent) == "web_search"

    def test_select_agent_returns_correct_type(self):
        """H10: handler-backed intents map to registered ModelBus handler ids."""
        ao = AgentOrchestrator()
        assert ao.select_agent("file_read") == "file_ops"
        assert ao.select_agent("code_execute") == "code_exec"
        assert ao.select_agent("web_search") == "web_search"
        assert ao.select_agent("code_understand") == "code_understanding_agent"
        assert ao.select_agent("creative_write") == "creative_writing_agent"

    def test_classify_routes_specialized_intents(self):
        """Regex sub-classification routes specialized-agent intents."""
        ao = AgentOrchestrator()
        assert ao.classify_intent("幫我寫一首詩") == "creative_write"
        assert ao.classify_intent("解釋 Python 語法") == "code_understand"
        assert ao.classify_intent("查詢知識圖譜") == "knowledge_query"
        assert ao.select_agent("knowledge_query") == "knowledge_graph_agent"
        assert ao.classify_intent("搜尋 python 歷史") == "web_search"

    def test_classify_code_vs_analysis(self):
        """Bare code mentions are analysis; execution needs an explicit verb."""
        ao = AgentOrchestrator()
        assert ao.classify_intent("分析這段程式碼") == "code_understand"
        assert ao.classify_intent("解釋這段代碼") == "code_understand"
        assert ao.classify_intent("執行這段程式碼") == "code_execute"
        assert ao.classify_intent("分析這張圖片") == "vision"
        assert ao.classify_intent("分析這份數據") == "data_analysis"

    def test_decompose_multi_step_task(self):
        ao = AgentOrchestrator()
        subtasks = ao.decompose_task("讀取文件然後寫入文件")
        assert len(subtasks) >= 2

    def test_decompose_single_step_task(self):
        ao = AgentOrchestrator()
        subtasks = ao.decompose_task("讀取文件")
        assert len(subtasks) == 1


class TestPlanningEngineIntegration:
    """Integration tests for PlanningEngine"""

    def test_create_plan_returns_structure(self):
        pe = PlanningEngine()
        plan = pe.create_plan("Build a web app with login")
        assert plan is not None

    def test_plan_has_steps(self):
        pe = PlanningEngine()
        plan = pe.create_plan("Build a web app")
        assert hasattr(plan, "steps") or hasattr(plan, "goal")


class TestReasoningEnginesIntegration:
    """Integration tests for ReasoningEngines"""

    def test_chain_of_thought_produces_steps(self):
        cot = ChainOfThoughtReasoner()
        result = cot.reason("If it rains, the ground gets wet. It is raining.")
        assert result is not None
        assert "steps" in result
        assert len(result["steps"]) >= 3

    def test_chain_of_thought_has_confidence(self):
        cot = ChainOfThoughtReasoner()
        result = cot.reason("A implies B. A is true.")
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_analogical_finds_similarities(self):
        ar = AnalogicalReasoner()
        result = ar.find_analogy("brain is to thinking", "computer is to processing")
        assert result is not None
        assert "similarities" in result
        assert "strength" in result

    def test_abductive_generates_hypotheses(self):
        ab = AbductiveReasoner()
        result = ab.explain("The ground is wet")
        assert result is not None
        assert "hypotheses" in result
        assert len(result["hypotheses"]) > 0

    def test_abductive_has_best_hypothesis(self):
        ab = AbductiveReasoner()
        result = ab.explain("The ground is wet")
        assert "best_hypothesis" in result


class TestEndToEndOrchestration:
    """End-to-end orchestration test"""

    def test_full_pipeline(self):
        # Step 1: Classify intent
        ao = AgentOrchestrator()
        intent = ao.classify_intent("讀取文件 report.txt")
        assert intent == "file_read"

        # Step 2: Select agent
        agent = ao.select_agent(intent)
        assert agent is not None

        # Step 3: Create plan
        pe = PlanningEngine()
        plan = pe.create_plan("讀取文件 report.txt")
        assert plan is not None

        # Step 4: Reason about the plan
        cot = ChainOfThoughtReasoner()
        result = cot.reason(f"Execute plan: {plan}")
        assert result is not None
        assert "steps" in result
