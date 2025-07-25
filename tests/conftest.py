import pytest
from unittest.mock import MagicMock, AsyncMock
import socket
import os

# Import the necessary classes from your project
from src.core_ai.agent_manager import AgentManager
if os.environ.get("TEST_LEVEL") != "simple":
    from src.core_ai.dialogue.dialogue_manager import DialogueManager
    from src.core_ai.learning.learning_manager import LearningManager
    from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.core_ai.personality.personality_manager import PersonalityManager
from src.core_ai.emotion_system import EmotionSystem
from src.core_ai.crisis_system import CrisisSystem
from src.core_ai.time_system import TimeSystem
from src.core_ai.formula_engine import FormulaEngine
if os.environ.get("TEST_LEVEL") != "simple":
    from src.tools.tool_dispatcher import ToolDispatcher
    from src.hsp.connector import HSPConnector
    from src.core_ai.dialogue.project_coordinator import ProjectCoordinator
from src.services.llm_interface import LLMInterface
from src.mcp.connector import MCPConnector
from src.shared.types.common_types import OperationalConfig

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
    if os.environ.get("TEST_LEVEL") != "simple":
        mock_hsp_connector = MagicMock(spec=HSPConnector)
        mock_hsp_connector.ai_id = "test_ai_id"
    else:
        mock_hsp_connector = MagicMock()
    mock_mcp_connector = MagicMock(spec=MCPConnector)
    mock_service_discovery = MagicMock(spec=ServiceDiscoveryModule)

    # --- Mock Core AI Logic Modules ---
    mock_fact_extractor = MagicMock(spec=FactExtractorModule)
    if os.environ.get("TEST_LEVEL") != "simple":
        mock_content_analyzer = MagicMock(spec=ContentAnalyzerModule)
        mock_learning_manager = AsyncMock(spec=LearningManager)
    else:
        mock_content_analyzer = MagicMock()
        mock_learning_manager = AsyncMock()
    mock_emotion_system = MagicMock(spec=EmotionSystem)
    mock_crisis_system = MagicMock(spec=CrisisSystem)
    mock_time_system = MagicMock(spec=TimeSystem)
    mock_formula_engine = MagicMock(spec=FormulaEngine)
    if os.environ.get("TEST_LEVEL") != "simple":
        mock_tool_dispatcher = MagicMock(spec=ToolDispatcher)
    else:
        mock_tool_dispatcher = MagicMock()

    # --- Default Behaviors & Return Values ---
    # Example: Personality Manager should return a default name
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"
    # Example: Formula Engine finds no match by default
    mock_formula_engine.match_input.return_value = None
    # Example: Crisis system reports no crisis by default
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
    if os.environ.get("TEST_LEVEL") != "simple":
        # Instantiate ProjectCoordinator with its mocked dependencies
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
    else:
        mock_project_coordinator = MagicMock()

    # --- Instantiate DialogueManager with Mocks ---
    # The DialogueManager often sits at the center, so we instantiate it
    # with all the other mocks to ensure it's wired correctly.
    if os.environ.get("TEST_LEVEL") != "simple":
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
        # --- Override Internal Components with Mocks if necessary ---
        # The DM constructor already assigns these, but this makes it explicit
        # that the ProjectCoordinator inside the DM is also a mock.
        mock_dialogue_manager.project_coordinator = mock_project_coordinator
    else:
        mock_dialogue_manager = MagicMock()


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

# You can add markers or other pytest configurations here if needed
