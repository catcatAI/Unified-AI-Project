import pytest

pytest.importorskip("core.hsp.connector")
from core.hsp.connector import HSPConnector


class TestHSPDebug:
    async def test_hsp_connector_imports(self):
        assert HSPConnector is not None

    async def test_hsp_connector_construct_with_mock(self):
        connector = HSPConnector(ai_id="test_debug", mock_mode=True)
        assert connector.ai_id == "test_debug"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
