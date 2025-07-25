"""
Tests for Context7 MCP Connector
Context7 MCP連接器測試

This module tests the Context7 MCP integration functionality
including context management, model collaboration, and protocol validation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.mcp.context7_connector import (
    Context7MCPConnector,
    Context7Config,
    UnifiedAIMCPIntegration
)
from src.mcp.types import MCPMessage, MCPResponse, MCPCapability


class TestContext7Config:
    """Test Context7 configuration."""
    
    @pytest.mark.timeout(5)
    def test_config_creation(self):
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
    def test_config_defaults(self):
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
    def config(self):
        """Create test configuration."""
        return Context7Config(
            endpoint="https://test-mcp.context7.com",
            api_key="test-api-key",
            timeout=10
        )
    
    @pytest.fixture
    def connector(self, config):
        """Create test connector."""
        return Context7MCPConnector(config)
    
    @pytest.mark.timeout(5)
    async def test_connector_initialization(self, connector):
        """Test connector initialization."""
        assert connector.config.endpoint == "https://test-mcp.context7.com"
        assert connector.session_id is None
        assert not connector._connected
        assert len(connector.capabilities) == 0
    
    @pytest.mark.timeout(5)
    async def test_connect_success(self, connector):
        """Test successful connection."""
        result = await connector.connect()
        
        assert result is True
        assert connector._connected is True
        assert connector.session_id is not None
        assert connector.session_id.startswith("unified-ai-")
        assert len(connector.capabilities) > 0
    
    @pytest.mark.timeout(5)
    async def test_disconnect(self, connector):
        """Test disconnection."""
        await connector.connect()
        assert connector._connected is True
        
        await connector.disconnect()
        assert connector._connected is False
        assert connector.session_id is None
        assert len(connector.context_cache) == 0
    
    @pytest.mark.timeout(5)
    async def test_send_context(self, connector):
        """Test sending context data."""
        await connector.connect()
        
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
    async def test_request_context(self, connector):
        """Test requesting context."""
        await connector.connect()
        
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
    async def test_collaborate_with_model(self, connector):
        """Test model collaboration."""
        await connector.connect()
        
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
    async def test_compress_context(self, connector):
        """Test context compression."""
        await connector.connect()
        
        large_context = {
            "conversation": ["Message " + str(i) for i in range(1000)],
            "metadata": {"key" + str(i): "value" + str(i) for i in range(100)}
        }
        
        compressed = await connector.compress_context(large_context)
        
        # Should return compressed data for large contexts
        assert isinstance(compressed, dict)
    
    @pytest.mark.timeout(5)
    async def test_connection_required_error(self, connector):
        """Test operations requiring connection."""
        # Should raise error when not connected
        with pytest.raises(RuntimeError, match="Not connected to Context7 MCP"):
            await connector.send_context({"test": "data"})
        
        with pytest.raises(RuntimeError, match="Not connected to Context7 MCP"):
            await connector.request_context("test query")
    
    @pytest.mark.timeout(5)
    async def test_capabilities_discovery(self, connector):
        """Test capability discovery."""
        await connector.connect()
        
        capabilities = connector.get_capabilities()
        assert len(capabilities) > 0
        
        # Check for expected capabilities
        capability_names = [cap["name"] for cap in capabilities]
        assert "context_management" in capability_names
        assert "model_collaboration" in capability_names


@pytest.mark.asyncio
@pytest.mark.context7
class TestUnifiedAIMCPIntegration:
    """Test Unified AI MCP Integration."""
    
    @pytest.fixture
    async def mcp_connector(self):
        """Create and connect MCP connector."""
        config = Context7Config(endpoint="https://test.com")
        connector = Context7MCPConnector(config)
        await connector.connect()
        return connector
    
    @pytest.fixture
    def integration(self, mcp_connector):
        """Create MCP integration instance."""
        return UnifiedAIMCPIntegration(mcp_connector)
    
    @pytest.mark.timeout(5)
    async def test_dialogue_manager_integration(self, integration):
        """Test integration with DialogueManager."""
        dialogue_context = {
            "user_message": "What's the weather like?",
            "conversation_id": "conv_123",
            "current_topic": "weather_inquiry",
            "user_preferences": {"location": "Tokyo"}
        }
        
        enhanced_context = await integration.integrate_with_dialogue_manager(
            dialogue_context
        )
        
        assert enhanced_context["mcp_enhanced"] is True
        assert "mcp_historical_context" in enhanced_context
        assert enhanced_context["user_message"] == "What's the weather like?"
    

    @pytest.mark.timeout(5)
    async def test_ham_memory_integration(self, integration):
        """Test integration with HAM Memory."""
        memory_data = {
            "memory_type": "episodic",
            "content": "User asked about weather in Tokyo",
            "timestamp": datetime.now().isoformat(),
            "importance_score": 0.7,
            "related_memories": ["mem_456", "mem_789"]
        }
        
        enhanced_memory = await integration.integrate_with_ham_memory(
            memory_data
        )
        
        assert isinstance(enhanced_memory, dict)
        assert "memory_type" in enhanced_memory
        assert "content" in enhanced_memory
    
    @pytest.mark.timeout(5)
    async def test_context_mapping(self, integration):
        """Test context mapping functionality."""
        # Test that context mappings are maintained
        assert isinstance(integration.context_mappings, dict)
        
        # Add a mapping
        integration.context_mappings["test_context"] = "mcp_context_123"
        assert integration.context_mappings["test_context"] == "mcp_context_123"


@pytest.mark.mcp
class TestMCPTypeValidation:
    """Test MCP type validation."""
    

    @pytest.mark.timeout(5)
    def test_mcp_message_structure(self):
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
    def test_mcp_response_structure(self):
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
    def test_mcp_capability_structure(self):
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
    async def connector(self):
        """Create performance test connector."""
        config = Context7Config(
            endpoint="https://test.com",
            timeout=5,  # Shorter timeout for performance tests
            compression_threshold=1024
        )
        connector = Context7MCPConnector(config)
        await connector.connect()
        return connector
    
    @pytest.mark.timeout(5)
    async def test_concurrent_context_requests(self, connector):
        """Test concurrent context operations."""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = connector.send_context(
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
    async def test_large_context_handling(self, connector):
        """Test handling of large context data."""
        # Create large context data
        large_context = {
            "large_data": "x" * 10000,  # 10KB of data
            "metadata": {"size": "large", "test": True}
        }
        
        # Should handle large context without issues
        response = await connector.send_context(
            context_data=large_context,
            context_type="large_test"
        )
        
        assert response["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])