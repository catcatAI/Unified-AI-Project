"""Tests for BiogenicReflexManager."""
import pytest
from core.life.bio_reflex_manager import BiogenicReflexManager


class TestBiogenicReflexManager:
    def test_init_default(self):
        mgr = BiogenicReflexManager()
        assert mgr.bio_integrator is None

    def test_init_with_bio(self):
        class FakeBio:
            def on_trauma(self, body_part, damage):
                pass
        mgr = BiogenicReflexManager(bio_integrator=FakeBio())
        assert mgr.bio_integrator is not None

    @pytest.mark.asyncio
    async def test_trigger_trauma_no_bio(self):
        mgr = BiogenicReflexManager()
        result = await mgr.trigger_physical_trauma("arm", 0.5)
        assert result is None

    @pytest.mark.asyncio
    async def test_trigger_trauma_with_bio(self):
        class FakeBio:
            def __init__(self):
                self.called = False
            def on_trauma(self, body_part, damage):
                self.called = True
        fake = FakeBio()
        mgr = BiogenicReflexManager(bio_integrator=fake)
        await mgr.trigger_physical_trauma("leg", 0.8)
        assert fake.called is True

    @pytest.mark.asyncio
    async def test_trigger_trauma_no_on_trauma_method(self):
        class FakeBioWithoutMethod:
            pass
        mgr = BiogenicReflexManager(bio_integrator=FakeBioWithoutMethod())
        result = await mgr.trigger_physical_trauma("head", 0.2)
        assert result is None

    @pytest.mark.asyncio
    async def test_trigger_trauma_multiple_parts(self):
        class FakeBio:
            def __init__(self):
                self.calls = []
            def on_trauma(self, body_part, damage):
                self.calls.append((body_part, damage))
        fake = FakeBio()
        mgr = BiogenicReflexManager(bio_integrator=fake)
        await mgr.trigger_physical_trauma("arm", 0.3)
        await mgr.trigger_physical_trauma("leg", 0.7)
        assert len(fake.calls) == 2
        assert fake.calls[0] == ("arm", 0.3)
        assert fake.calls[1] == ("leg", 0.7)
