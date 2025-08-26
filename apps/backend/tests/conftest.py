import os
import pytest
import asyncio
import sys
import threading
import time
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from cryptography.fernet import Fernet
from src.shared.types.common_types import DialogueTurn, DialogueMemoryEntryMetadata
from datetime import datetime, timezone
import uuid

# 定义占位符类
class PlaceholderResourceLeakDetector:
    def __init__(self):
        pass
    def start_monitoring(self):
        pass
    def check_leaks(self) -> List:
        return []

class PlaceholderAsyncLoopDetector:
    def __init__(self):
        pass
    def start_monitoring(self):
        pass
    def check_async_leaks(self) -> List:
        return []

class PlaceholderDeadlockDetector:
    pass

# 定义占位符上下文管理器
from contextlib import contextmanager
@contextmanager
def placeholder_deadlock_detection(timeout: float = 30.0, check_interval: float = 1.0):
    try:
        yield PlaceholderDeadlockDetector()
    finally:
        pass

# 尝试导入实际的类和函数
try:
    from src.core_ai.test_utils.deadlock_detector import (
        deadlock_detection,
        timeout_with_detection,
        ResourceLeakDetector,
        AsyncLoopDetector
    )
    DEADLOCK_DETECTION_AVAILABLE = True
except ImportError:
    DEADLOCK_DETECTION_AVAILABLE = False
    # 使用占位符
    ResourceLeakDetector = PlaceholderResourceLeakDetector
    AsyncLoopDetector = PlaceholderAsyncLoopDetector
    deadlock_detection = placeholder_deadlock_detection

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設置測試環境變量"""
    # 設置測試用的 MIKO_HAM_KEY
    if not os.environ.get('MIKO_HAM_KEY'):
        # 生成一個測試用的密鑰
        test_key = Fernet.generate_key().decode()
        os.environ['MIKO_HAM_KEY'] = test_key

    # 設置其他測試環境變量
    os.environ['TESTING'] = 'true'
    os.environ['OPENAI_API_KEY'] = 'dummy_key' # Re-add dummy key for module-level imports

    yield

    # 清理（如果需要）
    pass

@pytest.fixture(scope="session")
def mqtt_broker_available():
    # Placeholder for actual MQTT broker availability check
    # In a real scenario, this would attempt to connect to the broker
    # or check a configuration flag.
    return True

@pytest.fixture(scope="function")
def clean_test_files():
    """清理測試文件"""
    import glob

    # 在測試前清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

    yield

    # 在測試後清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

@pytest.fixture(scope="function")
def deadlock_detector():
    """死鎖檢測 fixture"""
    if not DEADLOCK_DETECTION_AVAILABLE:
        pytest.skip("Deadlock detection not available")

    resource_detector = ResourceLeakDetector()
    async_detector = AsyncLoopDetector()

    # 開始監控
    resource_detector.start_monitoring()
    async_detector.start_monitoring()

    yield {
        'resource_detector': resource_detector,
        'async_detector': async_detector
    }

    # 檢查洩漏
    leaks = resource_detector.check_leaks()
    async_leaks = async_detector.check_async_leaks()

    for leak in leaks + async_leaks:
        if leak.detected:
            pytest.fail(f"Resource leak detected: {leak.details}")

@pytest.fixture(scope="function")
def timeout_protection():
    """超時保護 fixture"""
    start_time = time.time()
    initial_thread_count = threading.active_count()

    yield

    # 檢查測試是否運行過長時間
    execution_time = time.time() - start_time
    if execution_time > 60:  # 60秒警告閾值
        pytest.fail(f"Test took too long: {execution_time:.2f}s")

    # 檢查線程洩漏
    final_thread_count = threading.active_count()
    if final_thread_count > initial_thread_count + 2:  # 允許一些容差
        pytest.fail(f"Thread leak detected: {final_thread_count} vs {initial_thread_count}")

@pytest.fixture(scope="function", autouse=True)
def test_timeout_and_monitoring(request):
    """自動應用的測試超時和監控"""
    # 檢查測試是否標記為需要特殊處理
    timeout_marker = request.node.get_closest_marker("timeout")
    deadlock_marker = request.node.get_closest_marker("deadlock_detection")

    # 設置默認超時
    timeout = 30.0
    if timeout_marker:
        timeout = timeout_marker.args[0] if timeout_marker.args else 30.0

    # 如果需要死鎖檢測
    if deadlock_marker and DEADLOCK_DETECTION_AVAILABLE:
        with deadlock_detection(timeout=timeout):
            yield
    else:
        yield

@pytest.fixture
def mock_core_services():
    from unittest.mock import MagicMock, AsyncMock
    import logging
    from src.core_ai.dialogue.dialogue_manager import DialogueManager
    from src.core_ai.dialogue.project_coordinator import ProjectCoordinator # Import ProjectCoordinator
    from src.core_ai.personality.personality_manager import PersonalityManager # Import PersonalityManager

    # Create mock service discovery that matches MockSDM behavior and provides Mock tracking
    from unittest.mock import AsyncMock

    # Create the actual mock behavior instance
    class MockSDMBehavior:
        def __init__(self):
            self._mock_sdm_capabilities_store = {}

        async def process_capability_advertisement(self, payload, sender_ai_id, envelope):
            try:
                from src.hsp.types import HSPCapabilityAdvertisementPayload
                from datetime import datetime, timezone

                if isinstance(payload, dict):
                    if 'availability_status' not in payload:
                        raise ValueError(f"Missing required field: availability_status")
                    processed_payload = HSPCapabilityAdvertisementPayload(**payload)
                elif hasattr(payload, '__getitem__'):  # TypedDict-like
                    processed_payload = payload
                else:
                    logging.error(f"Invalid payload type: {type(payload)}")
                    return
                # 使用 get 方法安全访问 capability_id，提供默认值以防键不存在
                capability_id = processed_payload.get('capability_id')
                if capability_id is None:
                    logging.error("Missing required field: capability_id")
                    return
                self._mock_sdm_capabilities_store[capability_id] = (processed_payload, datetime.now(timezone.utc))
            except Exception as e:
                logging.error(f"Failed to process capability advertisement: {e}")

        async def find_capabilities(self, capability_id_filter=None, capability_name_filter=None, tags_filter=None, min_trust_score=None, sort_by_trust=False):
            results = []
            for cap_id, (payload, last_seen) in self._mock_sdm_capabilities_store.items():
                if capability_id_filter and cap_id != capability_id_filter:
                    continue
                payload_name = payload.get('name')
                if capability_name_filter and payload_name != capability_name_filter:
                    continue
                payload_tags = payload.get('tags', [])
                if tags_filter and not all(tag in payload_tags for tag in tags_filter):
                    continue
                results.append(payload)
            return results

        def get_all_capabilities(self):
            """同步版本的get_all_capabilities"""
            results = []
            for cap_id, (payload, _) in self._mock_sdm_capabilities_store.items():
                results.append(payload)
            return results

        async def get_all_capabilities_async(self):
            """异步版本的get_all_capabilities"""
            return self.get_all_capabilities()

    # Create the behavior instance
    mock_behavior = MockSDMBehavior()

    # Create an AsyncMock that delegates to the behavior instance
    mock_service_discovery = AsyncMock()

    # Provide a sync wrapper for process_capability_advertisement so tests that don't await it still work
    from unittest.mock import MagicMock
    def _process_capability_advertisement_sync(payload, sender_ai_id, envelope):
        try:
            from src.hsp.types import HSPCapabilityAdvertisementPayload
            from datetime import datetime, timezone

            if isinstance(payload, dict):
                if 'availability_status' not in payload:
                    raise ValueError(f"Missing required field: availability_status")
                processed_payload = HSPCapabilityAdvertisementPayload(**payload)
            elif hasattr(payload, '__getitem__'):  # TypedDict-like or dict-like
                processed_payload = payload
            else:
                logging.error(f"Invalid payload type: {type(payload)}")
                return
            # 使用 get 方法安全访问 capability_id，提供默认值以防键不存在
            capability_id = processed_payload.get('capability_id')
            if capability_id is None:
                logging.error("Missing required field: capability_id")
                return
            mock_behavior._mock_sdm_capabilities_store[capability_id] = (processed_payload, datetime.now(timezone.utc))
        except Exception as e:
            logging.error(f"Failed to process capability advertisement (sync): {e}")

    # Assign mocks
    mock_service_discovery.process_capability_advertisement = MagicMock(side_effect=_process_capability_advertisement_sync)
    mock_service_discovery.find_capabilities = mock_behavior.find_capabilities
    mock_service_discovery.get_all_capabilities = mock_behavior.get_all_capabilities
    mock_service_discovery.get_all_capabilities_async = mock_behavior.get_all_capabilities_async

    # Store a reference to the behavior for access if needed
    mock_service_discovery._mock_behavior = mock_behavior

    # Create mock HAM manager that matches MockHAMMemoryManager behavior
    class MockHAMManager:
        def __init__(self):
            self.memory_store = {}
            self._next_id = 1
            self.store_experience = MagicMock(side_effect=self._store_experience_impl)

        def _store_experience_impl(self, raw_data: str, data_type: str, metadata):
            from datetime import datetime, timezone
            mem_id = f"mem_{self._next_id:06d}"
            self._next_id += 1
            record_pkg = {
                "raw_data": raw_data,
                "data_type": data_type,
                "metadata": metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mem_id": mem_id
            }
            self.memory_store[mem_id] = record_pkg
            # 确保始终返回memory_id而不是None
            return mem_id

        def query_memory(self, query_params):
            results = []
            for mem_id, record_pkg in self.memory_store.items():
                match = True
                for key, value in query_params.items():
                    if key == "hsp_correlation_id":
                        if record_pkg.get("metadata", {}).get("hsp_correlation_id") != value:
                            match = False
                            break
                if match:
                    results.append(record_pkg)
            return results

        def recall_gist(self, memory_id: str):
            """Mock implementation of recall_gist"""
            if memory_id in self.memory_store:
                record = self.memory_store[memory_id]
                # Ensure metadata is properly returned with required fields
                metadata = record["metadata"].copy() if record["metadata"] else {}
                # Ensure speaker field is present in metadata
                if 'speaker' not in metadata:
                    metadata['speaker'] = 'unknown'
                return {
                    "id": memory_id,
                    "timestamp": record["timestamp"],
                    "data_type": record["data_type"],
                    "rehydrated_gist": str(record["raw_data"]),
                    "metadata": metadata
                }
            return None

        def query_core_memory(self, **kwargs):
            """Mock implementation of query_core_memory"""
            # Simplified implementation for testing
            results = []
            for mem_id, record in self.memory_store.items():
                # Ensure metadata is properly returned
                metadata = record["metadata"].copy() if record["metadata"] else {}
                results.append({
                    "id": mem_id,
                    "timestamp": record["timestamp"],
                    "data_type": record["data_type"],
                    "rehydrated_gist": str(record["raw_data"]),
                    "metadata": metadata
                })
            return results

    # Remove stray reassignment that overrides our AsyncMock and causes NameError
    # mock_service_discovery = MockServiceDiscovery()
    mock_ham_manager = MockHAMManager()

    # Mock individual services
    mock_llm_interface = MagicMock(spec='src.services.multi_llm_service.MultiLLMService')
    mock_trust_manager = MagicMock(spec='src.core_ai.trust_manager.trust_manager_module.TrustManager')

    # Explicitly mock PersonalityManager methods
    mock_personality_manager = MagicMock(spec=PersonalityManager)
    mock_personality_manager.get_initial_prompt = MagicMock(return_value="Welcome!")
    mock_personality_manager.get_current_personality_trait = MagicMock(return_value="TestAI") # Explicitly mock and set return_value
    mock_personality_manager.apply_personality_adjustment = MagicMock() # Mock this method as well if it's called

    mock_emotion_system = MagicMock(spec='src.core_ai.emotion_system.EmotionSystem')
    mock_crisis_system = MagicMock(spec='src.core_ai.crisis.CrisisSystem')
    mock_time_system = MagicMock(spec='src.core_ai.time_system.TimeSystem')
    mock_time_system.get_time_of_day_segment = MagicMock(return_value="morning")
    mock_formula_engine = MagicMock(spec='src.core_ai.formula_engine.FormulaEngine')
    mock_tool_dispatcher = MagicMock(spec='src.tools.tool_dispatcher.ToolDispatcher')
    mock_tool_dispatcher.dispatch = AsyncMock()
    mock_learning_manager = MagicMock(spec='src.core_ai.learning.learning_manager.LearningManager')
    mock_learning_manager.analyze_for_personality_adjustment = AsyncMock(return_value=None)
    mock_hsp_connector = MagicMock(spec='src.hsp.connector.HSPConnector')
    mock_hsp_connector.ai_id = "mock_ai_id"
    mock_agent_manager = MagicMock(spec='src.core_ai.agent_manager.AgentManager')

    # Mock the ProjectCoordinator instance
    mock_project_coordinator = MagicMock(spec=ProjectCoordinator)
    mock_project_coordinator.llm_interface = mock_llm_interface
    mock_project_coordinator.service_discovery = mock_service_discovery
    mock_project_coordinator.hsp_connector = mock_hsp_connector
    mock_project_coordinator.agent_manager = mock_agent_manager
    mock_project_coordinator.memory_manager = mock_ham_manager
    mock_project_coordinator.learning_manager = mock_learning_manager
    mock_project_coordinator.personality_manager = mock_personality_manager
    mock_project_coordinator.dialogue_manager_config = {} # Pass an empty dict or a mock config

    # Configure mocks as needed for common scenarios
    mock_llm_interface.generate_response = AsyncMock(return_value='[{"capability_needed": "test_capability_v1", "task_parameters": {"param": "value"}, "task_description": "Test task"}]')
    # Keep store_experience as sync if defined on mock_ham_manager
    # (Do not override with AsyncMock)
    # mock_ham_manager.store_experience = AsyncMock() if not hasattr(mock_ham_manager, 'store_experience') else mock_ham_manager.store_experience
    mock_hsp_connector.advertise_capability = AsyncMock()
    mock_hsp_connector.send_task_result = AsyncMock()
    mock_hsp_connector.send_task_request = AsyncMock(return_value="mock_correlation_id")
    mock_project_coordinator.handle_project = AsyncMock(return_value="Mocked project response.")
    mock_project_coordinator.handle_task_result = AsyncMock()
    mock_project_coordinator._execute_task_graph = AsyncMock() # Added mock for _execute_task_graph
    mock_project_coordinator._decompose_user_intent_into_subtasks = AsyncMock(return_value=[]) # Added mock for _decompose_user_intent_into_subtasks

    # Mock the DialogueManager instance
    mock_dialogue_manager = MagicMock(spec=DialogueManager)
    mock_dialogue_manager.ai_id = "test_ai_id"
    mock_dialogue_manager.personality_manager = mock_personality_manager
    mock_dialogue_manager.memory_manager = mock_ham_manager
    mock_dialogue_manager.llm_interface = mock_llm_interface
    mock_dialogue_manager.emotion_system = mock_emotion_system
    mock_dialogue_manager.crisis_system = mock_crisis_system
    mock_dialogue_manager.time_system = mock_time_system
    mock_dialogue_manager.formula_engine = mock_formula_engine
    mock_dialogue_manager.tool_dispatcher = mock_tool_dispatcher
    mock_dialogue_manager.learning_manager = mock_learning_manager
    mock_dialogue_manager.service_discovery_module = mock_service_discovery
    mock_dialogue_manager.hsp_connector = mock_hsp_connector
    mock_dialogue_manager.agent_manager = mock_agent_manager
    mock_dialogue_manager.config = {}
    mock_dialogue_manager.triggers = {"complex_project": "project:", "manual_delegation": "!delegate_to", "context_analysis": "!analyze:"}
    mock_dialogue_manager.active_sessions = {} # Initialize active_sessions

    # Define mock side effect functions
    async def mock_get_simple_response_side_effect(dialogue_manager, project_coordinator, tool_dispatcher, ham_manager, learning_manager, personality_manager, user_input, session_id=None, user_id=None):
        # Mock implementation for get_simple_response
        # Check if this is a project trigger
        if project_coordinator and user_input.lower().startswith("project:"):
            project_query = user_input[8:].strip()  # Remove "project:" prefix
            # 直接调用project_coordinator.handle_project而不是返回mock响应
            return await project_coordinator.handle_project(project_query, session_id, user_id)
        # For standard flow, generate expected response format
        ai_name = personality_manager.get_current_personality_trait("display_name", "TestAI")
        return f"{ai_name}: You said '{user_input}'. This is a simple response."

    async def mock_start_session_side_effect(dialogue_manager, time_system, personality_manager, user_id=None, session_id=None):
        # Mock implementation for start_session
        time_segment = time_system.get_time_of_day_segment()
        base_prompt = personality_manager.get_initial_prompt()
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {base_prompt}".strip()

    async def mock_handle_incoming_hsp_task_result_side_effect(project_coordinator, result_payload, sender_ai_id, envelope):
        # Mock implementation for _handle_incoming_hsp_task_result
        await project_coordinator.handle_task_result(result_payload, sender_ai_id, envelope)

    # Define nested async functions for side_effects
    async def _get_simple_response_side_effect_wrapper(user_input, session_id=None, user_id=None):
        return await mock_get_simple_response_side_effect(mock_dialogue_manager, mock_project_coordinator, mock_tool_dispatcher, mock_ham_manager, mock_learning_manager, mock_personality_manager, user_input, session_id, user_id)

    async def _start_session_side_effect_wrapper(user_id=None, session_id=None):
        return await mock_start_session_side_effect(mock_dialogue_manager, mock_time_system, mock_personality_manager, user_id, session_id)

    async def _handle_incoming_hsp_task_result_side_effect_wrapper(result_payload, sender_ai_id, envelope):
        return await mock_handle_incoming_hsp_task_result_side_effect(mock_project_coordinator, result_payload, sender_ai_id, envelope)

    mock_dialogue_manager.get_simple_response = AsyncMock(side_effect=_get_simple_response_side_effect_wrapper)
    mock_dialogue_manager.start_session = AsyncMock(side_effect=_start_session_side_effect_wrapper)
    mock_dialogue_manager._handle_incoming_hsp_task_result = AsyncMock(side_effect=_handle_incoming_hsp_task_result_side_effect_wrapper)

    # Return a dictionary mimicking the structure of get_services()
    return {
        "ham_manager": mock_ham_manager,
        "llm_interface": mock_llm_interface,
        "service_discovery": mock_service_discovery,
        "trust_manager": mock_trust_manager,
        "personality_manager": mock_personality_manager,
        "emotion_system": mock_emotion_system,
        "crisis_system": mock_crisis_system,
        "time_system": mock_time_system,
        "formula_engine": mock_formula_engine,
        "tool_dispatcher": mock_tool_dispatcher,
        "learning_manager": mock_learning_manager,
        "hsp_connector": mock_hsp_connector,
        "agent_manager": mock_agent_manager,
        "project_coordinator": mock_project_coordinator,
        "dialogue_manager": mock_dialogue_manager,
    }

@pytest.fixture(scope="function")
def client_with_overrides(mock_core_services):
    """
    Provides a FastAPI TestClient with core services mocked out.
    This allows for isolated testing of API endpoints.
    """
    from fastapi.testclient import TestClient
    from src.services.main_api_server import app
    from src.core_services import get_services

    # Backup original dependencies and overrides
    original_get_services = app.dependency_overrides.get(get_services)

    # Apply the mock overrides
    app.dependency_overrides[get_services] = lambda: mock_core_services

    client = TestClient(app)
    try:
        yield (
            client,
            mock_core_services["service_discovery"],
            mock_core_services["dialogue_manager"],
            mock_core_services["ham_manager"],
            mock_core_services["hsp_connector"],
        )
    finally:
        # Ensure the client is explicitly closed after the test completes
        try:
            client.close()
        except Exception: 
            pass

    # Restore original dependencies
    if original_get_services:
        app.dependency_overrides[get_services] = original_get_services
    else:
        # If there was no override before, clear it
        if get_services in app.dependency_overrides:
            del app.dependency_overrides[get_services]