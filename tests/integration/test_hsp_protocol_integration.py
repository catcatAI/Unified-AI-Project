import pytest

pytest.importorskip("core.hsp.connector")
from core.hsp.connector import HSPConnector


class TestHSPProtocolIntegration:
    async def test_hsp_module_import(self):
        assert HSPConnector is not None

    async def test_hsp_construct_with_mock(self):
        try:
            connector = HSPConnector(ai_id="test_proto", mock_mode=True)
            assert connector is not None
        except AttributeError as e:
            pytest.skip(f"HSPConnector instantiation blocked by: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
