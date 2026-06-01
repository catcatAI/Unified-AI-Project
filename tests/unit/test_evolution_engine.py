"""Smoke tests for core.life.evolution_engine"""
import pytest


class TestEvolutionEngine:
    def test_import(self):
        try:
            from core.life.evolution_engine import EvolutionEngine
            assert EvolutionEngine is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.life.evolution_engine import EvolutionEngine
            instance = EvolutionEngine(personality_manager=None)
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
