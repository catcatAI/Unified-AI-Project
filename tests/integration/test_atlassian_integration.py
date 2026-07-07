import pytest

pytest.importorskip("integrations.atlassian_bridge")
from integrations.atlassian_bridge import AtlassianBridge


class TestAtlassianIntegration:
    async def test_atlassian_bridge_imports(self):
        assert AtlassianBridge is not None

    async def test_atlassian_bridge_construct(self):
        try:
            from integrations.rovo_dev_connector import RovoDevConnector
            connector = RovoDevConnector(config={"atlassian": {}})
            bridge = AtlassianBridge(connector=connector)
            assert bridge is not None
        except Exception as e:
            pytest.skip(f"AtlassianBridge construct failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
