import os
import pytest
import os
import asyncio
import pytest
from cryptography.fernet import Fernet

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

@pytest.fixture
def mock_core_services():
    from unittest.mock import MagicMock, AsyncMock
    from src.core_ai.dialogue.dialogue_manager import DialogueManager
    from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
    from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
    from src.core_ai.trust_manager.trust_manager_module import TrustManager
    from src.core_ai.personality.personality_manager import PersonalityManager
    from src.services.multi_llm_service import MultiLLMService
    from src.core_ai.emotion_system import EmotionSystem
    from src.core_ai.crisis_system import CrisisSystem
    from src.core_ai.time_system import TimeSystem
    from src.core_ai.formula_engine import FormulaEngine
    from src.tools.tool_dispatcher import ToolDispatcher
    from src.core_ai.learning.learning_manager import LearningManager
    from src.hsp.connector import HSPConnector
    from src.core_ai.agent_manager import AgentManager
    from src.core_ai.dialogue.project_coordinator import ProjectCoordinator

    # Mock individual services
    mock_ham_manager = MagicMock(spec=HAMMemoryManager)
    mock_llm_interface = MagicMock(spec=MultiLLMService)
    mock_service_discovery = MagicMock(spec=ServiceDiscoveryModule)
    mock_trust_manager = MagicMock(spec=TrustManager)
    mock_personality_manager = MagicMock(spec=PersonalityManager)
    mock_emotion_system = MagicMock(spec=EmotionSystem)
    mock_crisis_system = MagicMock(spec=CrisisSystem)
    mock_time_system = MagicMock(spec=TimeSystem)
    mock_formula_engine = MagicMock(spec=FormulaEngine)
    mock_tool_dispatcher = MagicMock(spec=ToolDispatcher)
    mock_learning_manager = MagicMock(spec=LearningManager)
    mock_hsp_connector = MagicMock(spec=HSPConnector)
    mock_hsp_connector.ai_id = "mock_ai_id"
    mock_agent_manager = MagicMock(spec=AgentManager)
    mock_project_coordinator = MagicMock(spec=ProjectCoordinator)

    # Configure mocks as needed for common scenarios
    mock_llm_interface.generate_response = AsyncMock(return_value="Mocked LLM response.")
    mock_ham_manager.store_experience = AsyncMock()
    mock_service_discovery.find_capabilities = AsyncMock(return_value=[])
    mock_hsp_connector.advertise_capability = AsyncMock()
    mock_hsp_connector.send_task_result = AsyncMock()
    mock_hsp_connector.send_task_request = AsyncMock(return_value="mock_correlation_id")
    mock_project_coordinator.handle_project = AsyncMock(return_value="Mocked project response.")
    mock_project_coordinator.handle_task_result = AsyncMock()

    # Create a mock DialogueManager instance that uses these mocks
    mock_dialogue_manager = DialogueManager(
        ai_id="test_ai_id",
        personality_manager=mock_personality_manager,
        memory_manager=mock_ham_manager,
        llm_interface=mock_llm_interface,
        emotion_system=mock_emotion_system,
        crisis_system=mock_crisis_system,
        time_system=mock_time_system,
        formula_engine=mock_formula_engine,
        tool_dispatcher=mock_tool_dispatcher,
        learning_manager=mock_learning_manager,
        service_discovery_module=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,
        project_coordinator=mock_project_coordinator
    )

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
