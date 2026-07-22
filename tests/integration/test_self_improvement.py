import pytest

pytest.importorskip("core.life.evolution_engine")
from core.life.evolution_engine import EvolutionEngine


class TestSelfImprovement:
    @pytest.mark.asyncio
    async def test_evolution_engine_instantiation(self):
        engine = EvolutionEngine()
        assert engine is not None
        assert len(engine._traits) == 5

    @pytest.mark.asyncio
    async def test_evolution_engine_get_trait_default(self):
        engine = EvolutionEngine()
        trait = engine.get_trait("openness")
        assert trait == 0.5
        trait = engine.get_trait("nonexistent")
        assert trait == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
