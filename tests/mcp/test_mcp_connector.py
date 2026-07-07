import pytest

pytest.importorskip("paho.mqtt")
pytest.importorskip("mcp.connector")
from mcp.connector import MCPConnector


class TestMCPConnector:
    async def test_mcp_connector_instantiation(self):
        connector = MCPConnector(ai_id="test_mcp")
        assert connector is not None
        assert connector.ai_id == "test_mcp"

    async def test_mcp_connector_health(self):
        connector = MCPConnector(ai_id="test_mcp")
        assert not connector.is_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
