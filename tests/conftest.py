import os
import pytest
import asyncio
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet

# 添加 src 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from core_ai.test_utils.deadlock_detector import (
        deadlock_detection, 
        timeout_with_detection,
        ResourceLeakDetector,
        AsyncLoopDetector
    )
    DEADLOCK_DETECTION_AVAILABLE = True
except ImportError:
    DEADLOCK_DETECTION_AVAILABLE = False


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

    # Mock individual services
    mock_ham_manager = MagicMock(spec='src.core_ai.memory.ham_memory_manager.HAMMemoryManager')
    mock_llm_interface = MagicMock(spec='src.services.multi_llm_service.MultiLLMService')
    mock_service_discovery = MagicMock(spec='src.core_ai.service_discovery.service_discovery_module.ServiceDiscoveryModule')
    mock_service_discovery.get_all_capabilities = MagicMock()
    mock_trust_manager = MagicMock(spec='src.core_ai.trust_manager.trust_manager_module.TrustManager')
    mock_personality_manager = MagicMock(spec='src.core_ai.personality.personality_manager.PersonalityManager')
    mock_personality_manager.get_initial_prompt = MagicMock()
    mock_emotion_system = MagicMock(spec='src.core_ai.emotion_system.EmotionSystem')
    mock_crisis_system = MagicMock(spec='src.core_ai.crisis_system.CrisisSystem')
    mock_time_system = MagicMock(spec='src.core_ai.time_system.TimeSystem')
    mock_time_system.get_time_of_day_segment = MagicMock()
    mock_formula_engine = MagicMock(spec='src.core_ai.formula_engine.FormulaEngine')
    mock_tool_dispatcher = MagicMock(spec='src.tools.tool_dispatcher.ToolDispatcher')
    mock_tool_dispatcher.dispatch = AsyncMock()
    mock_learning_manager = MagicMock(spec='src.core_ai.learning.learning_manager.LearningManager')
    mock_learning_manager.analyze_for_personality_adjustment = AsyncMock(return_value=None)
    mock_hsp_connector = MagicMock(spec='src.hsp.connector.HSPConnector')
    mock_hsp_connector.ai_id = "mock_ai_id"
    mock_agent_manager = MagicMock(spec='src.core_ai.agent_manager.AgentManager')
    from src.core_ai.dialogue.project_coordinator import ProjectCoordinator

    mock_project_coordinator = ProjectCoordinator(
        llm_interface=mock_llm_interface,
        service_discovery=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,
        memory_manager=mock_ham_manager,
        learning_manager=mock_learning_manager,
        personality_manager=mock_personality_manager,
        dialogue_manager_config={} # Pass an empty dict or a mock config
    )

    # Configure mocks as needed for common scenarios
    mock_llm_interface.generate_response = AsyncMock(return_value='[{"capability_needed": "test_capability_v1", "task_parameters": {"param": "value"}, "task_description": "Test task"}]')
    mock_ham_manager.store_experience = AsyncMock()
    mock_service_discovery.find_capabilities = AsyncMock(return_value=[])
    mock_hsp_connector.advertise_capability = AsyncMock()
    mock_hsp_connector.send_task_result = AsyncMock()
    mock_hsp_connector.send_task_request = AsyncMock(return_value="mock_correlation_id")
    mock_project_coordinator.handle_project = AsyncMock(return_value="Mocked project response.")
    mock_project_coordinator.handle_task_result = AsyncMock()

    # Directly mock DialogueManager
    mock_dialogue_manager = MagicMock(spec='src.core_ai.dialogue.dialogue_manager.DialogueManager')
    mock_dialogue_manager.get_simple_response = AsyncMock(return_value="Mocked simple response.")
    mock_dialogue_manager.start_session = AsyncMock(return_value="Mocked session greeting.")
    mock_dialogue_manager._handle_incoming_hsp_task_result = AsyncMock()
    mock_dialogue_manager.project_coordinator = mock_project_coordinator # Ensure project_coordinator is accessible
    mock_dialogue_manager.memory_manager = mock_ham_manager # Ensure memory_manager is accessible
    mock_dialogue_manager.tool_dispatcher = mock_tool_dispatcher # Ensure tool_dispatcher is accessible
    mock_dialogue_manager.personality_manager = mock_personality_manager # Ensure personality_manager is accessible
    mock_dialogue_manager.learning_manager = mock_learning_manager # Ensure learning_manager is accessible
    mock_dialogue_manager.triggers = {"complex_project": "project:", "manual_delegation": "!delegate_to", "context_analysis": "!analyze:"} # Ensure triggers are set

    # Directly mock DialogueManager
    mock_dialogue_manager = MagicMock(spec='src.core_ai.dialogue.dialogue_manager.DialogueManager')

    async def mock_get_simple_response(user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        if user_input.lower().startswith("project:"):
            project_query = user_input[len("project:"):].strip()
            return await mock_project_coordinator.handle_project(project_query, session_id, user_id)
        else:
            # Simulate tool dispatch
            tool_response = await mock_tool_dispatcher.dispatch(user_input, session_id=session_id, user_id=user_id)
            if tool_response['status'] == "success":
                response_text = tool_response['payload']
            else:
                response_text = f"TestAI: You said '{user_input}'. This is a simple response."

            # Simulate memory storage
            await mock_ham_manager.store_experience(user_input, "user_dialogue_text", {"speaker": "user", "session_id": session_id})
            await mock_ham_manager.store_experience(response_text, "ai_dialogue_text", {"speaker": "ai", "session_id": session_id})

            # Simulate personality adjustment
            adjustment = await mock_learning_manager.analyze_for_personality_adjustment(user_input)
            if adjustment:
                mock_personality_manager.apply_personality_adjustment(adjustment)

            return response_text

    async def mock_start_session(user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        time_segment = mock_time_system.get_time_of_day_segment()
        initial_prompt = mock_personality_manager.get_initial_prompt()
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {initial_prompt}".strip()

    async def mock_handle_incoming_hsp_task_result(result_payload: Dict[str, Any], sender_ai_id: str, envelope: Dict[str, Any]) -> None:
        await mock_project_coordinator.handle_task_result(result_payload, sender_ai_id, envelope)

    mock_dialogue_manager.get_simple_response = AsyncMock(side_effect=mock_get_simple_response)
    mock_dialogue_manager.start_session = AsyncMock(side_effect=mock_start_session)
    mock_dialogue_manager._handle_incoming_hsp_task_result = AsyncMock(side_effect=mock_handle_incoming_hsp_task_result)
    mock_dialogue_manager.triggers = {"complex_project": "project:", "manual_delegation": "!delegate_to", "context_analysis": "!analyze:"}
    mock_dialogue_manager.ai_id = "test_ai_id" # Set ai_id for the mock

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
