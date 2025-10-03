"""
Tests for Context7 MCP Connector
Context7 MCP連接器測試

This module tests the Context7 MCP integration functionality
including context management, model collaboration, and protocol validation.
"""

import pytest
import asyncio
    Context7MCPConnector,
    Context7Config,
    UnifiedAIMCPIntegration
)
from apps.backend.src.mcp.types import MCPMessage, MCPResponse, MCPCapability


class TestContext7Config:
    """Test Context7 configuration."""

    @pytest.mark.timeout(5)
    def test_config_creation(self) -> None:
    """Test basic config creation."""
    config = Context7Config(
            endpoint="https://api.context7.com/mcp",
            api_key="test-key",
            timeout=30
    )

    assert config.endpoint == "https://api.context7.com/mcp"
    assert config.api_key == "test-key"
    assert config.timeout == 30
    assert config.enable_context_caching is True

    @pytest.mark.timeout(5)
    def test_config_defaults(self) -> None:
    """Test default configuration values."""
    config = Context7Config(endpoint="https://test.com")

    assert config.api_key is None
    assert config.timeout == 30
    assert config.max_retries == 3
    assert config.enable_context_caching is True
    assert config.context_window_size == 8192


@pytest.mark.asyncio
@pytest.mark.context7
class TestContext7MCPConnector:
    """Test Context7 MCP Connector functionality."""

    @pytest.fixture
    def config(self)
    """Create test configuration."""
    return Context7Config(
            endpoint="https://test-mcp.context7.com",
            api_key="test-api-key",
            timeout = 40.0
    )

    @pytest.fixture
    def connector(self, config)
    """Create test connector."""
    return Context7MCPConnector(config)

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    async def test_connector_initialization(self, connector) -> None:
    """Test connector initialization."""
    assert connector.config.endpoint == "https://test-mcp.context7.com"
    assert connector.session_id is None
    assert not connector._connected
    assert len(connector.capabilities) == 0

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_connect_success(self, connector) -> None:
    """Test successful connection."""
    result = await connector.connect()

    assert result is True
    assert connector._connected is True
    assert connector.session_id is not None
    assert connector.session_id.startswith("unified-ai-")
    assert len(connector.capabilities) > 0

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_disconnect(self, connector) -> None:
    """Test disconnection."""
    _ = await connector.connect()
    assert connector._connected is True

    _ = await connector.disconnect()
    assert connector._connected is False
    assert connector.session_id is None
    assert len(connector.context_cache) == 0

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_send_context(self, connector) -> None:
    """Test sending context data."""
    _ = await connector.connect()

    context_data = {
            "user_message": "Hello, how are you?",
            "conversation_history": ["Previous message"],
            "current_topic": "greeting"
    }

    response = await connector.send_context(
            context_data=context_data,
            context_type="dialogue",
            priority=1
    )

    assert response["success"] is True
    assert "context_id" in response["data"]

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_request_context(self, connector) -> None:
    """Test requesting context."""
    _ = await connector.connect()

    context_items = await connector.request_context(
            context_query="greeting conversation",
            max_results=5
    )

    assert isinstance(context_items, list)
    assert len(context_items) > 0

        for item in context_items:


    assert "id" in item
            assert "content" in item
            assert "relevance" in item

    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_collaborate_with_model(self, connector) -> None:
    """Test model collaboration."""
    _ = await connector.connect()

    shared_context = {
            "task_type": "text_generation",
            "user_input": "Write a story about AI",
            "style_preferences": "creative, engaging"
    }

    response = await connector.collaborate_with_model(
            model_id="gpt-4",
            task_description="Creative writing assistance",
            shared_context=shared_context
    )

    assert response["success"] is True
    assert response["data"]["status"] == "processed"

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_compress_context(self, connector) -> None:
    """Test context compression."""
    _ = await connector.connect()

    large_context = {
            "conversation": ["Message " + str(i) for i in range(1000)],
            "metadata": {"key" + str(i) "value" + str(i) for i in range(100)}
    }

    compressed = await connector.compress_context(large_context)

        # Should return compressed data for large contexts
    assert isinstance(compressed, dict)

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_connection_required_error(self, connector) -> None:
    """Test operations requiring connection."""
    # Should raise error when not connected
    with pytest.raises(RuntimeError, match="Not connected to Context7 MCP")
    _ = await connector.send_context({"test": "data"})

    with pytest.raises(RuntimeError, match="Not connected to Context7 MCP")
    _ = await connector.request_context("test query")

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_capabilities_discovery(self, connector) -> None:
    """Test capability discovery."""
    _ = await connector.connect()

    capabilities = connector.get_capabilities()
    assert len(capabilities) > 0

        # Check for expected capabilities
    capability_names = [cap["name"] for cap in capabilities]:
    assert "context_management" in capability_names
    assert "model_collaboration" in capability_names

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_unhandled_message_type(self, connector) -> None:
    """Test handling of unhandled message types."""
    _ = await connector.connect()

    unhandled_message = MCPMessage(
            type="unhandled_test_type",
            session_id=connector.session_id,
            payload={"data": "test"}
    )

    response = await connector._send_message(unhandled_message)

    assert response["success"] is False
    assert "Unknown or unhandled message type" in response["error"]


@pytest.mark.asyncio
@pytest.mark.context7
class TestUnifiedAIMCPIntegration:
    """Test Unified AI MCP Integration."""

    @pytest.fixture
    async def mcp_connector(self)
    """Create and connect MCP connector."""
    config = Context7Config(endpoint="https://test.com")
    connector = Context7MCPConnector(config)
    _ = await connector.connect()
    return connector

    @pytest.fixture
    async def integration(self, mcp_connector)
    """Create MCP integration instance."""
    return UnifiedAIMCPIntegration(await mcp_connector)

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_dialogue_manager_integration(self, integration) -> None:
    """Test integration with DialogueManager.""":
    integration_instance = await integration
    dialogue_context = {
            "user_message": "What's the weather like?",
            "conversation_id": "conv_123",
            "current_topic": "weather_inquiry",
            "user_preferences": {"location": "Tokyo"}
    }

    enhanced_context = await integration_instance.integrate_with_dialogue_manager(
            dialogue_context
    )

    assert enhanced_context["mcp_enhanced"] is True
    assert "mcp_historical_context" in enhanced_context
    assert enhanced_context["user_message"] == "What's the weather like?"


    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_ham_memory_integration(self, integration) -> None:
    """Test integration with HAM Memory.""":
    integration_instance = await integration
    memory_data = {
            "memory_type": "episodic",
            "content": "User asked about weather in Tokyo",
            "timestamp": datetime.now().isoformat(),
            "importance_score": 0.7,
            "related_memories": ["mem_456", "mem_789"]
    }

    enhanced_memory = await integration_instance.integrate_with_ham_memory(
            memory_data
    )

    @pytest.mark.timeout(5)
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_context_mapping(self, integration) -> None:
    """Test context mapping functionality."""
    integration_instance = await integration
    # Test that context mappings are maintained
    assert isinstance(integration_instance.context_mappings, dict)

    # Add a mapping
    integration_instance.context_mappings["test_context"] = "mcp_context_123"
    assert integration_instance.context_mappings["test_context"] == "mcp_context_123"


@pytest.mark.mcp
class TestMCPTypeValidation:
    """Test MCP type validation."""


    @pytest.mark.timeout(5)
    def test_mcp_message_structure(self) -> None:
    """Test MCPMessage type structure."""
    message: MCPMessage = {
            "type": "context_update",
            "session_id": "session_123",
            "payload": {"data": "test"},
            "timestamp": datetime.now().isoformat(),
            "priority": 1
    }

    assert message["type"] == "context_update"
    assert message["session_id"] == "session_123"
    assert isinstance(message["payload"], dict)


    @pytest.mark.timeout(5)
    def test_mcp_response_structure(self) -> None:
    """Test MCPResponse type structure."""
    response: MCPResponse = {
            "success": True,
            "message_id": "msg_123",
            "data": {"result": "processed"},
            "error": None,
            "timestamp": datetime.now().isoformat()
    }

    assert response["success"] is True
    assert response["message_id"] == "msg_123"
    assert isinstance(response["data"], dict)


    @pytest.mark.timeout(5)
    def test_mcp_capability_structure(self) -> None:
    """Test MCPCapability type structure."""
    capability: MCPCapability = {
            "name": "context_management",
            "version": "1.0",
            "description": "Context management capability",
            "parameters": {"max_context_size": 8192}
    }

    assert capability["name"] == "context_management"
    assert capability["version"] == "1.0"
    assert isinstance(capability["parameters"], dict)


@pytest.mark.slow
@pytest.mark.context7
class TestContext7Performance:
    """Test Context7 MCP performance characteristics."""

    @pytest.fixture
    def connector(self)
    """Create performance test connector."""
    config = Context7Config(
            endpoint="https://test.com",
            timeout = 40.0,  # Shorter timeout for performance tests
    compression_threshold=1024
    )
    return Context7MCPConnector(config)

    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_concurrent_context_requests(self, connector) -> None:
    """Test concurrent context operations."""
    connector_instance = connector
    _ = await connector_instance.connect()
    # Create multiple concurrent requests
    tasks = []
        for i in range(10)

    task = connector_instance.send_context(
                context_data={"test_id": i, "data": f"test_data_{i}"},
                context_type="test",
                priority=1
            )
            tasks.append(task)

    # Execute concurrently
    responses = await asyncio.gather(*tasks)

    # Verify all succeeded
    assert len(responses) == 10
        for response in responses:

    assert response["success"] is True

    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_large_context_handling(self, connector) -> None:
    """Test handling of large context data."""
    connector_instance = connector
    _ = await connector_instance.connect()
    # Create large context data
    large_context = {
            "large_data": "x" * 10000,  # 10KB of data
            "metadata": {"size": "large", "test": True}
    }

    # Should handle large context without issues
    response = await connector_instance.send_context(
            context_data=large_context,
            context_type="large_test"
    )

    assert response["success"] is True


if __name__ == "__main__":



    pytest.main([__file__, "-v", "--tb=short"])