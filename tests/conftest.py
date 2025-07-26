from __future__ import annotations
import pytest
from unittest.mock import MagicMock, AsyncMock
import socket
from typing import TYPE_CHECKING

# Import the necessary classes from your project
from src.core_ai.agent_manager import AgentManager
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.core_ai.learning.learning_manager import LearningManager
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.core_ai.personality.personality_manager import PersonalityManager
from src.core_ai.emotion_system import EmotionSystem
from src.core_ai.crisis_system import CrisisSystem
from src.core_ai.time_system import TimeSystem
from src.core_ai.formula_engine import FormulaEngine
from src.tools.tool_dispatcher import ToolDispatcher
from src.services.llm_interface import LLMInterface
from src.mcp.connector import MCPConnector
from src.core_ai.dialogue.project_coordinator import ProjectCoordinator
from src.shared.types.common_types import OperationalConfig

if TYPE_CHECKING:
    from src.hsp.connector import HSPConnector

@pytest.fixture(scope="function")
def trust_manager_fixture():
    return TrustManager()

@pytest.fixture(scope="function")
def service_discovery_module_fixture(trust_manager_fixture):
    sdm = ServiceDiscoveryModule(trust_manager=trust_manager_fixture)
    sdm.start_cleanup_task(cleanup_interval_seconds=1) # Shorter interval for tests
    yield sdm
    sdm.stop_cleanup_task()

@pytest.fixture(scope="function")
async def hsp_connector_fixture():
    from src.hsp.connector import HSPConnector
    # Check if MQTT broker is available before attempting to connect
    if not is_mqtt_broker_available():
        pytest.skip("MQTT broker not available")

    connector = HSPConnector(
        ai_id="test_ai_id",
        broker_address="127.0.0.1",
        broker_port=1883,
        client_id_suffix="test_hsp_connector"
    )
    await connector.connect()
    yield connector
    await connector.disconnect()

def is_mqtt_broker_available():
    """
    Checks if the MQTT broker is available by attempting to create a socket connection.
    """
    try:
        # Use a non-blocking socket with a short timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(("127.0.0.1", 1883))
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception:
        return False

@pytest.fixture(scope="function")
def mock_core_services():
    """
    Provides a dictionary of mocked core services for use in tests.
    This fixture initializes all major components with MagicMock or AsyncMock
    and wires them together as they would be in `core_services.py`.
    """
    # --- Mock Foundational Services ---
    mock_llm_interface = AsyncMock(spec=LLMInterface)
    mock_ham_manager = AsyncMock(spec=HAMMemoryManager)
    mock_personality_manager = MagicMock(spec=PersonalityManager)
    mock_trust_manager = MagicMock(spec=TrustManager)
    mock_agent_manager = MagicMock(spec=AgentManager)
    mock_hsp_connector = MagicMock(spec=HSPConnector)
    mock_hsp_connector.ai_id = "test_ai_id"
    mock_mcp_connector = MagicMock(spec=MCPConnector)
    mock_service_discovery = MagicMock(spec=ServiceDiscoveryModule)

    # --- Mock Core AI Logic Modules ---
    mock_fact_extractor = MagicMock(spec=FactExtractorModule)
    mock_content_analyzer = MagicMock(spec=ContentAnalyzerModule)
    mock_learning_manager = AsyncMock(spec=LearningManager)
    mock_emotion_system = MagicMock(spec=EmotionSystem)
    mock_crisis_system = MagicMock(spec=CrisisSystem)
    mock_time_system = MagicMock(spec=TimeSystem)
    mock_formula_engine = MagicMock(spec=FormulaEngine)
    mock_tool_dispatcher = MagicMock(spec=ToolDispatcher)

    # --- Default Behaviors & Return Values ---
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"
    mock_formula_engine.match_input.return_value = None
    mock_crisis_system.assess_input_for_crisis.return_value = 0

    # --- Minimal Configuration ---
    test_config: OperationalConfig = { # type: ignore
        "max_dialogue_history": 6,
        "operational_configs": {
            "timeouts": {"dialogue_manager_turn": 120},
            "learning_thresholds": {"min_critique_score_to_store": 0.0}
        },
        "command_triggers": {
            "complex_project": "project:",
            "manual_delegation": "!delegate_to",
            "context_analysis": "!analyze:"
        },
        "crisis_response_text": "Crisis response."
    }

    # --- Mock Coordinator ---
    mock_project_coordinator = ProjectCoordinator(
        llm_interface=mock_llm_interface,
        service_discovery=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,
        memory_manager=mock_ham_manager,
        learning_manager=mock_learning_manager,
        personality_manager=mock_personality_manager,
        dialogue_manager_config=test_config
    )

    # --- Instantiate DialogueManager with Mocks ---
    mock_dialogue_manager = DialogueManager(
        ai_id="test_ai_01",
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
        config=test_config
    )

    mock_dialogue_manager.project_coordinator = mock_project_coordinator

    services = {
        "llm_interface": mock_llm_interface,
        "ham_manager": mock_ham_manager,
        "personality_manager": mock_personality_manager,
        "trust_manager": mock_trust_manager,
        "agent_manager": mock_agent_manager,
        "hsp_connector": mock_hsp_connector,
        "mcp_connector": mock_mcp_connector,
        "service_discovery": mock_service_discovery,
        "fact_extractor": mock_fact_extractor,
        "content_analyzer": mock_content_analyzer,
        "learning_manager": mock_learning_manager,
        "emotion_system": mock_emotion_system,
        "crisis_system": mock_crisis_system,
        "time_system": mock_time_system,
        "formula_engine": mock_formula_engine,
        "tool_dispatcher": mock_tool_dispatcher,
        "dialogue_manager": mock_dialogue_manager,
        "project_coordinator": mock_project_coordinator,
        "config": test_config
    }

    return services