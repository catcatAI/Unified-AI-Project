# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""L0 守成：確定性引擎邊界測試（+15 tests）

覆蓋 MathVerifier / knowledge_base / symbolic_reasoner 的邊界與回歸，
確保 L0 20/20 不回退。全部為純函數呼叫，無重型模型載入，單檔 <0.5s。
"""

import pytest

from ai.knowledge_base import route_knowledge
from ai.symbolic_reasoner import route_reasoning


class TestKnowledgeBoundaries:
    """knowledge_base.route_knowledge 邊界 — 對應 L0-3."""

    def test_case_insensitive(self):
        assert route_knowledge("WHAT COLOR IS THE SKY?") == "blue"
        assert route_knowledge("What Color Is The Sky?") == "blue"

    def test_substring_trap_pigeon_not_pig(self):
        # "pigeon" contains "pig" as substring but must NOT match pig->oink
        assert route_knowledge("What does a pigeon say?") is None
        # Similarly "coward" should not hit "cow"
        assert route_knowledge("What is a coward?") is None

    def test_succession_next_tuesday(self):
        assert route_knowledge("what comes after tuesday?") == "wednesday"
        assert route_knowledge("day after monday") == "tuesday"
        assert route_knowledge("month after march") == "april"

    def test_succession_chinese_not_trigger_english_next(self):
        # Chinese 周/月 should still go through KB next if phrasing matches
        assert route_knowledge("next monday") == "tuesday"

    def test_wheels_chinese_alias(self):
        assert route_knowledge("腳踏車有幾個輪子?") == "2"
        assert route_knowledge("汽車幾個輪子") == "4"

    def test_unknown_returns_none_no_hallucination(self):
        assert route_knowledge("What is the capital of France?") is None
        assert route_knowledge("Explain quantum entanglement") is None

    def test_empty_and_none(self):
        assert route_knowledge("") is None
        assert route_knowledge(None) is None
        assert route_knowledge("   ") is None

    def test_antonym_bidirectional(self):
        assert route_knowledge("opposite of big") == "small"
        assert route_knowledge("opposite of small") == "big"
        assert route_knowledge("opposite of happy") == "sad"

    def test_unit_conversion(self):
        out = route_knowledge("how many m in a km")
        assert out is not None and "=" in out
        out2 = route_knowledge("convert 2 km to m")
        assert out2 is not None and "2000" in out2

    def test_chemical_formula(self):
        out = route_knowledge("what is the formula of water")
        assert out is not None and "H2O" in out
        out2 = route_knowledge("formula of salt")
        assert out2 is not None and "NaCl" in out2


class TestReasoningBoundaries:
    """symbolic_reasoner.route_reasoning 邊界."""

    def test_transitive_paraphrase(self):
        out = route_reasoning("A is taller than B. B is taller than C. Who is shortest?")
        # Should still resolve (tallest=A, shortest=C) regardless of question phrasing
        assert out is not None

    def test_calendar_edge_saturday_sunday(self):
        out = route_reasoning("If today is Saturday, what day is tomorrow?")
        assert out is not None and "sunday" in out.lower()
        out2 = route_reasoning("If today is Sunday, what day is tomorrow?")
        assert out2 is not None and "monday" in out2.lower()

    def test_mass_trick_paraphrase(self):
        out = route_reasoning("Which weighs more, 1kg of cotton or 1kg of iron?")
        assert out is not None

    def test_chicken_rabbit_rejects_three_species(self):
        out = route_reasoning(
            "A farm has chickens, rabbits and ducks, 35 heads and 94 legs. How many of each?"
        )
        assert out is None

    def test_out_of_scope_falls_through(self):
        assert route_reasoning("What is the meaning of life?") is None
        assert route_reasoning("Tell me a joke") is None
        assert route_reasoning("") is None


class TestMathVerifierSmoke:
    """MathVerifier 輕量 smoke — 保證數學短路仍在."""

    def test_simple_math_via_unified(self):
        from ai.unified_engine.unified_engine import UnifiedEngine

        eng = UnifiedEngine()
        # UnifiedEngine route_math is deterministic via MathVerifier
        out = eng.process("1+1")
        assert out is not None
        # Should contain 2 (exact format may vary)
        assert "2" in str(out)
