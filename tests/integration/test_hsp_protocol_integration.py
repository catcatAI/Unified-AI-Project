import pytest

pytest.importorskip("core.hsp.connector")
from core.hsp.connector import HSPConnector


class TestHSPProtocolIntegration:
    @pytest.mark.asyncio
    async def test_hsp_module_import(self):
        assert HSPConnector is not None

    @pytest.mark.asyncio
    async def test_hsp_construct_with_mock(self):
        connector = HSPConnector(ai_id="test_proto", mock_mode=True)
        assert connector is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
