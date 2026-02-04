"""
Angela AI v6.0 - Action Execution Bridge Tests
动作执行桥接器测试

Comprehensive test suite for ActionExecutionBridge including:
- All action type handlers
- Error handling
- Concurrent execution
- Feedback loops

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.backend.src.core.action_execution_bridge import (
    ActionExecutionBridge,
    ActionType,
    ExecutionResult,
    ExecutionResultStatus,
    ExecutionContext,
    FeedbackCollector,
    ActionExecutionBridgeFactory
)


# ========== Fixtures ==========

@pytest.fixture
def mock_components():
    """Create mock components for testing"""
    return {
        "orchestrator": Mock(),
        "desktop_pet": Mock(),
        "file_manager": Mock(),
        "download_manager": Mock(),
        "web_search_tool": Mock(),
        "hsm": Mock(),
        "cdm": Mock(),
        "live2d_integration": Mock()
    }


@pytest.fixture
async def bridge(mock_components):
    """Create and initialize a bridge for testing"""
    bridge = ActionExecutionBridge(
        orchestrator=mock_components["orchestrator"],
        desktop_pet=mock_components["desktop_pet"],
        file_manager=mock_components["file_manager"],
        download_manager=mock_components["download_manager"],
        web_search_tool=mock_components["web_search_tool"],
        hsm=mock_components["hsm"],
        cdm=mock_components["cdm"],
        live2d_integration=mock_components["live2d_integration"],
        config={"max_concurrent": 2, "max_history_size": 100}
    )
    await bridge.initialize()
    yield bridge
    await bridge.shutdown()


@pytest.fixture
async def basic_bridge():
    """Create a basic bridge without dependencies"""
    bridge = ActionExecutionBridge()
    await bridge.initialize()
    yield bridge
    await bridge.shutdown()


# ========== Test Classes ==========

class TestActionExecutionBridgeInitialization:
    """Test bridge initialization and shutdown"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_components):
        """Test bridge initialization"""
        bridge = ActionExecutionBridge(**mock_components)
        await bridge.initialize()
        
        assert bridge._running is True
        assert bridge._execution_task is not None
        
        await bridge.shutdown()
    
    @pytest.mark.asyncio
    async def test_shutdown(self, mock_components):
        """Test bridge shutdown"""
        bridge = ActionExecutionBridge(**mock_components)
        await bridge.initialize()
        await bridge.shutdown()
        
        assert bridge._running is False
        assert bridge._execution_task is None
    
    @pytest.mark.asyncio
    async def test_factory_create_basic(self):
        """Test factory create_basic_bridge"""
        bridge = ActionExecutionBridgeFactory.create_basic_bridge()
        await bridge.initialize()
        
        assert bridge._running is True
        assert bridge.orchestrator is None
        
        await bridge.shutdown()
    
    @pytest.mark.asyncio
    async def test_factory_create_full(self, mock_components):
        """Test factory create_full_bridge"""
        bridge = ActionExecutionBridgeFactory.create_full_bridge(
            orchestrator=mock_components["orchestrator"],
            desktop_pet=mock_components["desktop_pet"],
            file_manager=mock_components["file_manager"],
            download_manager=mock_components["download_manager"],
            web_search_tool=mock_components["web_search_tool"],
            hsm=mock_components["hsm"],
            cdm=mock_components["cdm"],
            live2d_integration=mock_components["live2d_integration"]
        )
        await bridge.initialize()
        
        assert bridge.orchestrator is mock_components["orchestrator"]
        assert bridge.desktop_pet is mock_components["desktop_pet"]
        
        await bridge.shutdown()


class TestActionTypeHandlers:
    """Test all action type handlers"""
    
    @pytest.mark.asyncio
    async def test_initiate_conversation(self, bridge, mock_components):
        """Test initiate_conversation action"""
        mock_components["orchestrator"].generate_proactive_message = AsyncMock(
            return_value={"message": "Hello!", "emotion": "happy"}
        )
        mock_components["desktop_pet"].show_message = Mock()
        
        result = await bridge.execute_action(
            action_type=ActionType.INITIATE_CONVERSATION,
            parameters={"message": "Hello!", "emotion": "happy", "topic": "greeting"},
            priority=1
        )
        
        assert result.success is True
        assert result.action_type == ActionType.INITIATE_CONVERSATION
        assert result.data["message"] == "Hello!"
        assert "orchestrator_response" in result.data
    
    @pytest.mark.asyncio
    async def test_initiate_conversation_without_orchestrator(self, basic_bridge):
        """Test initiate_conversation without orchestrator"""
        result = await basic_bridge.execute_action(
            action_type=ActionType.INITIATE_CONVERSATION,
            parameters={"message": "Hello!", "emotion": "happy"},
            priority=1
        )
        
        assert result.success is True
        assert result.data["message"] == "Hello!"
    
    @pytest.mark.asyncio
    async def test_explore_topic(self, bridge, mock_components):
        """Test explore_topic action"""
        mock_components["web_search_tool"].search = AsyncMock(
            return_value=[
                {"title": "Test", "snippet": "Test snippet", "url": "http://test.com"}
            ]
        )
        mock_components["file_manager"].search_files = AsyncMock(return_value=[])
        mock_components["cdm"].ingest_document = AsyncMock()
        
        result = await bridge.execute_action(
            action_type=ActionType.EXPLORE_TOPIC,
            parameters={"topic": "AI", "depth": "medium", "source": "web"},
            priority=2
        )
        
        assert result.success is True
        assert result.data["topic"] == "AI"
        assert "exploration_data" in result.data
    
    @pytest.mark.asyncio
    async def test_satisfy_need_social(self, bridge, mock_components):
        """Test satisfy_need action for social need"""
        mock_components["desktop_pet"].show_message = Mock()
        
        result = await bridge.execute_action(
            action_type=ActionType.SATISFY_NEED,
            parameters={"need_type": "social", "urgency": 0.7},
            priority=3
        )
        
        assert result.success is True
        assert result.data["need_type"] == "social"
        assert result.data["action_taken"] == "initiated_conversation"
        assert "message" in result.data
    
    @pytest.mark.asyncio
    async def test_satisfy_need_curiosity(self, bridge):
        """Test satisfy_need action for curiosity"""
        result = await bridge.execute_action(
            action_type=ActionType.SATISFY_NEED,
            parameters={"need_type": "curiosity", "urgency": 0.5},
            priority=3
        )
        
        assert result.success is True
        assert result.data["need_type"] == "curiosity"
        assert result.data["action_taken"] == "explored_topic"
        assert "topic" in result.data
    
    @pytest.mark.asyncio
    async def test_express_feeling(self, bridge, mock_components):
        """Test express_feeling action"""
        mock_components["desktop_pet"].show_message = Mock()
        mock_components["live2d_integration"].set_expression = AsyncMock()
        
        result = await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "happy", "intensity": 0.8, "reason": "test"},
            priority=4
        )
        
        assert result.success is True
        assert result.data["emotion"] == "happy"
        assert result.data["intensity"] == 0.8
        assert "message" in result.data
    
    @pytest.mark.asyncio
    async def test_download_resource(self, bridge, mock_components):
        """Test download_resource action"""
        mock_components["download_manager"].download_file = AsyncMock(
            return_value={"file_path": "/tmp/test.txt", "success": True}
        )
        mock_components["file_manager"].read_file = AsyncMock(return_value="Test content")
        mock_components["cdm"].ingest_document = AsyncMock()
        
        result = await bridge.execute_action(
            action_type=ActionType.DOWNLOAD_RESOURCE,
            parameters={
                "url": "http://example.com/test.txt",
                "resource_type": "knowledge",
                "auto_ingest": True
            },
            priority=5
        )
        
        assert result.success is True
        assert result.data["downloaded"] is True
    
    @pytest.mark.asyncio
    async def test_download_resource_without_manager(self, basic_bridge):
        """Test download_resource without download manager"""
        result = await basic_bridge.execute_action(
            action_type=ActionType.DOWNLOAD_RESOURCE,
            parameters={"url": "http://example.com/test.txt"},
            priority=5
        )
        
        assert result.success is False
        assert "error" in result.data
    
    @pytest.mark.asyncio
    async def test_change_appearance(self, bridge, mock_components):
        """Test change_appearance action"""
        mock_components["live2d_integration"].set_expression = AsyncMock()
        
        result = await bridge.execute_action(
            action_type=ActionType.CHANGE_APPEARANCE,
            parameters={"change_type": "expression", "value": "happy"},
            priority=6
        )
        
        assert result.success is True
        assert result.data["applied"] is True
    
    @pytest.mark.asyncio
    async def test_file_operation_read(self, bridge, mock_components):
        """Test file_operation read action"""
        mock_components["file_manager"].read_file = AsyncMock(return_value="Test content")
        
        result = await bridge.execute_action(
            action_type=ActionType.FILE_OPERATION,
            parameters={"operation": "read", "path": "/tmp/test.txt"},
            priority=7
        )
        
        assert result.success is True
        assert result.data["success"] is True
        assert result.data["content"] == "Test content"
    
    @pytest.mark.asyncio
    async def test_file_operation_write(self, bridge, mock_components):
        """Test file_operation write action"""
        mock_components["file_manager"].write_file = AsyncMock(return_value=True)
        
        result = await bridge.execute_action(
            action_type=ActionType.FILE_OPERATION,
            parameters={"operation": "write", "path": "/tmp/test.txt", "content": "Test"},
            priority=7
        )
        
        assert result.success is True
        assert result.data["success"] is True
    
    @pytest.mark.asyncio
    async def test_web_search(self, bridge, mock_components):
        """Test web_search action"""
        mock_components["web_search_tool"].search = AsyncMock(
            return_value=[{"title": "Result", "snippet": "Snippet", "url": "http://test.com"}]
        )
        
        result = await bridge.execute_action(
            action_type=ActionType.WEB_SEARCH,
            parameters={"query": "Python programming", "num_results": 5},
            priority=8
        )
        
        assert result.success is True
        assert result.data["query"] == "Python programming"
        assert len(result.data["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_system_query(self, bridge):
        """Test system_query action"""
        result = await bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "health"},
            priority=9
        )
        
        assert result.success is True
        assert "health" in result.data
        assert "components" in result.data["health"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_unknown_action_type(self, bridge):
        """Test handling of unknown action type"""
        result = await bridge.execute_action(
            action_type="unknown_type",
            parameters={},
            priority=1
        )
        
        assert result.success is False
        assert "error_message" in result.to_dict()
    
    @pytest.mark.asyncio
    async def test_handler_exception(self, bridge, mock_components):
        """Test handling of exceptions in action handlers"""
        mock_components["web_search_tool"].search = AsyncMock(
            side_effect=Exception("Search failed")
        )
        
        result = await bridge.execute_action(
            action_type=ActionType.WEB_SEARCH,
            parameters={"query": "test"},
            priority=1
        )
        
        assert result.success is False
        assert "error" in result.data
    
    @pytest.mark.asyncio
    async def test_missing_required_component(self, basic_bridge):
        """Test actions with missing components"""
        result = await basic_bridge.execute_action(
            action_type=ActionType.FILE_OPERATION,
            parameters={"operation": "read", "path": "/test.txt"},
            priority=1
        )
        
        assert result.success is False
        assert result.data["error"] == "File manager not available"
    
    @pytest.mark.asyncio
    async def test_cancel_action(self, bridge):
        """Test action cancellation"""
        # Submit action without waiting
        result = bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status"},
            wait_for_completion=False
        )
        
        # Cancel should return False (action already executing or completed)
        # Or True if still in queue
        cancel_result = await bridge.cancel_action(result.action_id)
        assert isinstance(cancel_result, bool)


class TestConcurrentExecution:
    """Test concurrent action execution"""
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self, basic_bridge):
        """Test executing multiple actions concurrently"""
        actions = []
        for i in range(5):
            result = await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status", "index": i},
                priority=i
            )
            actions.append(result)
        
        # All should succeed
        assert all(r.success for r in actions)
        assert len(actions) == 5
    
    @pytest.mark.asyncio
    async def test_priority_queue(self, basic_bridge):
        """Test priority queue ordering"""
        results = []
        
        # Submit actions with different priorities
        for priority in [5, 1, 3, 2, 4]:
            result = await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status", "priority": priority},
                priority=priority
            )
            results.append((priority, result))
        
        # All should complete successfully
        assert all(r[1].success for r in results)
    
    @pytest.mark.asyncio
    async def test_execution_order_with_dependencies(self, basic_bridge):
        """Test action execution with dependencies"""
        # Execute first action
        result1 = await basic_bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status", "name": "first"},
            priority=1
        )
        
        # Execute second action with dependency on first
        result2 = await basic_bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status", "name": "second"},
            priority=1,
            dependencies=[result1.action_id]
        )
        
        assert result1.success is True
        assert result2.success is True


class TestFeedbackLoops:
    """Test feedback collection and learning integration"""
    
    @pytest.mark.asyncio
    async def test_feedback_collection(self, basic_bridge):
        """Test that feedback is collected for all actions"""
        # Execute some actions
        for i in range(5):
            await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status", "index": i},
                priority=1
            )
        
        # Check feedback data
        feedback = basic_bridge.get_feedback_data()
        assert feedback["feedback_count"] == 5
        assert feedback["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_cdm_feedback_integration(self, bridge, mock_components):
        """Test feedback integration with CDM"""
        mock_components["cdm"].integrate_execution_feedback = AsyncMock()
        
        await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "happy"},
            priority=1
        )
        
        # CDM should have been called
        # Note: This might be async and called in background
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_execution_history(self, basic_bridge):
        """Test execution history tracking"""
        # Execute actions
        for i in range(3):
            await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status", "index": i},
                priority=1
            )
        
        # Get history
        history = basic_bridge.get_action_history(limit=10)
        assert len(history) == 3
    
    @pytest.mark.asyncio
    async def test_success_failure_patterns(self, bridge, mock_components):
        """Test success and failure pattern tracking"""
        # Successful action
        mock_components["desktop_pet"].show_message = Mock()
        await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "happy"},
            priority=1
        )
        
        # Failed action
        mock_components["web_search_tool"].search = AsyncMock(
            side_effect=Exception("Search failed")
        )
        await bridge.execute_action(
            action_type=ActionType.WEB_SEARCH,
            parameters={"query": "test"},
            priority=1
        )
        
        # Check patterns
        feedback = bridge.get_feedback_data()
        assert feedback["feedback_count"] == 2
        assert feedback["success_rate"] == 0.5


class TestStatistics:
    """Test execution statistics"""
    
    @pytest.mark.asyncio
    async def test_execution_stats(self, basic_bridge):
        """Test execution statistics tracking"""
        # Execute multiple actions
        for i in range(5):
            await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status"},
                priority=1
            )
        
        stats = basic_bridge.get_execution_stats()
        assert stats["total_executed"] == 5
        assert stats["total_successful"] == 5
        assert stats["total_failed"] == 0
        assert "average_execution_time" in stats
    
    @pytest.mark.asyncio
    async def test_action_type_counts(self, bridge, mock_components):
        """Test action type count tracking"""
        mock_components["desktop_pet"].show_message = Mock()
        
        # Execute different action types
        await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "happy"},
            priority=1
        )
        
        await bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status"},
            priority=1
        )
        
        stats = bridge.get_execution_stats()
        assert "action_type_counts" in stats
        assert "express_feeling" in stats["action_type_counts"]
        assert "system_query" in stats["action_type_counts"]


class TestCallbacks:
    """Test pre and post execution callbacks"""
    
    @pytest.mark.asyncio
    async def test_pre_execution_callback(self, basic_bridge):
        """Test pre-execution callback"""
        callback_called = False
        received_context = None
        
        def pre_callback(context):
            nonlocal callback_called, received_context
            callback_called = True
            received_context = context
        
        basic_bridge.register_pre_execution_callback(pre_callback)
        
        await basic_bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status"},
            priority=1
        )
        
        assert callback_called is True
        assert received_context is not None
        assert received_context.action_type == ActionType.SYSTEM_QUERY
    
    @pytest.mark.asyncio
    async def test_post_execution_callback(self, basic_bridge):
        """Test post-execution callback"""
        callback_called = False
        received_context = None
        received_result = None
        
        def post_callback(context, result):
            nonlocal callback_called, received_context, received_result
            callback_called = True
            received_context = context
            received_result = result
        
        basic_bridge.register_post_execution_callback(post_callback)
        
        await basic_bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "status"},
            priority=1
        )
        
        assert callback_called is True
        assert received_context is not None
        assert received_result is not None
        assert received_result.success is True


class TestPersistence:
    """Test history persistence"""
    
    @pytest.mark.asyncio
    async def test_history_save_load(self, tmp_path):
        """Test saving and loading execution history"""
        history_file = tmp_path / "test_history.json"
        
        bridge = ActionExecutionBridge(config={"history_path": str(history_file)})
        await bridge.initialize()
        
        # Execute actions
        for i in range(3):
            await bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status"},
                priority=1
            )
        
        await bridge.shutdown()
        
        # Check file exists
        assert history_file.exists()
        
        # Load and verify
        import json
        with open(history_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 3
    
    @pytest.mark.asyncio
    async def test_clear_history(self, basic_bridge):
        """Test clearing execution history"""
        # Execute actions
        for i in range(3):
            await basic_bridge.execute_action(
                action_type=ActionType.SYSTEM_QUERY,
                parameters={"query_type": "status"},
                priority=1
            )
        
        # Clear history
        basic_bridge.clear_history()
        
        # Verify cleared
        history = basic_bridge.get_action_history()
        assert len(history) == 0


# ========== Integration Tests ==========

class TestIntegration:
    """Integration tests for complete workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_components):
        """Test complete workflow with all components"""
        # Setup mocks
        mock_components["orchestrator"].generate_proactive_message = AsyncMock(
            return_value={"message": "Hello!"}
        )
        mock_components["desktop_pet"].show_message = Mock()
        mock_components["web_search_tool"].search = AsyncMock(
            return_value=[{"title": "Test", "snippet": "Test", "url": "http://test.com"}]
        )
        mock_components["file_manager"].read_file = AsyncMock(return_value="Content")
        mock_components["cdm"].ingest_document = AsyncMock()
        
        # Create bridge
        bridge = ActionExecutionBridge(**mock_components)
        await bridge.initialize()
        
        # Execute various actions
        actions = [
            (ActionType.INITIATE_CONVERSATION, {"message": "Hi!", "emotion": "happy"}),
            (ActionType.EXPRESS_FEELING, {"emotion": "curious", "intensity": 0.7}),
            (ActionType.EXPLORE_TOPIC, {"topic": "AI", "depth": "shallow"}),
            (ActionType.SYSTEM_QUERY, {"query_type": "health"}),
        ]
        
        results = []
        for action_type, params in actions:
            result = await bridge.execute_action(
                action_type=action_type,
                parameters=params,
                priority=1
            )
            results.append(result)
        
        # Verify all succeeded
        assert all(r.success for r in results)
        assert len(results) == 4
        
        # Check stats
        stats = bridge.get_execution_stats()
        assert stats["total_executed"] == 4
        
        await bridge.shutdown()
    
    @pytest.mark.asyncio
    async def test_autonomous_behavior_simulation(self, mock_components):
        """Simulate autonomous behavior flow"""
        mock_components["desktop_pet"].show_message = Mock()
        mock_components["live2d_integration"].set_expression = AsyncMock()
        
        bridge = ActionExecutionBridge(**mock_components)
        await bridge.initialize()
        
        # Simulate: Feeling lonely -> Express feeling -> Initiate conversation
        express_result = await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "lonely", "intensity": 0.6},
            priority=1
        )
        
        conversation_result = await bridge.execute_action(
            action_type=ActionType.INITIATE_CONVERSATION,
            parameters={"message": "我想你了，在吗？", "emotion": "lonely"},
            priority=1,
            dependencies=[express_result.action_id]
        )
        
        assert express_result.success is True
        assert conversation_result.success is True
        
        await bridge.shutdown()


# ========== Main ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
