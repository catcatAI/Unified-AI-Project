# =============================================================================
# ANGELA-MATRIX: [L2] [γ] [C] [L4]
# =============================================================================
"""Tests for the deterministic knowledge base (native factual recall)."""

import pytest

from ai.knowledge_base import known_subjects, route_knowledge


class TestKnowledgeBase:
    """route_knowledge must answer simple factual questions deterministically."""

    def test_color_of_sky(self):
        assert route_knowledge("What color is the sky?") == "blue"

    def test_opposite_of_hot(self):
        assert route_knowledge("What is the opposite of hot?") == "cold"

    def test_animal_says_meow(self):
        assert route_knowledge("What animal says meow?") == "cat"

    def test_days_in_week(self):
        assert route_knowledge("How many days are in a week?") == "7"

    def test_red_planet(self):
        assert route_knowledge("What planet is known as the Red Planet?") == "Mars"

    def test_antonym_reverse(self):
        assert route_knowledge("opposite of cold") == "hot"

    def test_unknown_returns_none(self):
        assert route_knowledge("Tell me a joke about quantum physics") is None

    def test_empty_returns_none(self):
        assert route_knowledge("") is None
        assert route_knowledge(None) is None

    def test_known_subjects_nonempty(self):
        subjects = known_subjects()
        assert isinstance(subjects, list)
        assert "sky" in subjects
        assert "cat" in subjects

    def test_engine_returns_answer_for_knowledge_question(self):
        # Smoke: the engine path must surface the KB answer (not fall through).
        from ai.garden.garden_engine import GARDENEngine

        eng = GARDENEngine()
        result = eng.process("What color is the sky?")
        assert "blue" in result
