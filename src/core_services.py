# src/core_services.py

from typing import Optional, Dict, Any
import uuid

# Core AI Modules
from core_ai.agent_manager import AgentManager
from core_ai.dialogue.dialogue_manager import DialogueManager
from core_ai.learning.learning_manager import LearningManager
from core_ai.learning.fact_extractor_module import FactExtractorModule
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from core_ai.trust_manager.trust_manager_module import TrustManager
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from core_ai.personality.personality_manager import PersonalityManager
from core_ai.emotion_system import EmotionSystem
from core_ai.crisis_system import CrisisSystem
from core_ai.time_system import TimeSystem
from core_ai.formula_engine import FormulaEngine
from tools.tool_dispatcher import ToolDispatcher

# Services
from services.llm_interface import LLMInterface, LLMInterfaceConfig
from hsp.connector import HSPConnector
from mcp.connector import MCPConnector

# --- Constants ---
CAP_ADVERTISEMENT_TOPIC = "hsp/capabilities/advertisements/general"
FACT_TOPIC_GENERAL = "hsp/knowledge/facts/general"

# --- Global Singleton Instances ---
# These will be initialized by `initialize_services`

# Foundational Services
llm_interface_instance: Optional[LLMInterface] = None
ham_manager_instance: Optional[HAMMemoryManager] = None
personality_manager_instance: Optional[PersonalityManager] = None
trust_manager_instance: Optional[TrustManager] = None
agent_manager_instance: Optional[AgentManager] = None

# HSP Related Services
hsp_connector_instance: Optional[HSPConnector] = None
mcp_connector_instance: Optional[MCPConnector] = None
service_discovery_module_instance: Optional[ServiceDiscoveryModule] = None

# Core AI Logic Modules that depend on foundational services
fact_extractor_instance: Optional[FactExtractorModule] = None
content_analyzer_instance: Optional[ContentAnalyzerModule] = None
learning_manager_instance: Optional[LearningManager] = None
emotion_system_instance: Optional[EmotionSystem] = None
crisis_system_instance: Optional[CrisisSystem] = None
time_system_instance: Optional[TimeSystem] = None
formula_engine_instance: Optional[FormulaEngine] = None
tool_dispatcher_instance: Optional[ToolDispatcher] = None
dialogue_manager_instance: Optional[DialogueManager] = None


# Configuration (can be loaded from file or passed)
# For PoC, CLI and API might use slightly different default configs or AI IDs.
DEFAULT_AI_ID = f"did:hsp:unified_ai_core_{uuid.uuid4().hex[:6]}"
DEFAULT_MQTT_BROKER = "localhost"
DEFAULT_MQTT_PORT = 1883

# Default operational configs, can be overridden
DEFAULT_OPERATIONAL_CONFIGS: Dict[str, Any] = {
    "learning_thresholds": {
        "min_fact_confidence_to_store": 0.6,
        "min_fact_confidence_to_share_via_hsp": 0.75,
        "min_hsp_fact_confidence_to_store": 0.5,
        "hsp_fact_conflict_confidence_delta": 0.1
    },
    "default_hsp_fact_topic": "hsp/knowledge/facts/unified_ai_general"
    # Add other operational configs like timeouts if needed by modules here
}

DEFAULT_LLM_CONFIG: LLMInterfaceConfig = { #type: ignore
    "default_provider": "mock",
    "default_model": "core_services_mock_v1",
    "providers": {},
    "default_generation_params": {},
    "operational_configs": DEFAULT_OPERATIONAL_CONFIGS # Pass operational configs to LLM if it needs them
}


def initialize_services(
    ai_id: str = DEFAULT_AI_ID,
    hsp_broker_address: str = DEFAULT_MQTT_BROKER,
    hsp_broker_port: int = DEFAULT_MQTT_PORT,
    llm_config: Optional[LLMInterfaceConfig] = None,
    operational_configs: Optional[Dict[str, Any]] = None,
    use_mock_ham: bool = False # Flag to use MockHAM for CLI/testing ease
):
    """
    Initializes and holds singleton instances of all core services and modules.
    This function should be called once at application startup.
    """
    global llm_interface_instance, ham_manager_instance, personality_manager_instance
    global trust_manager_instance, hsp_connector_instance, mcp_connector_instance, service_discovery_module_instance
    global fact_extractor_instance, content_analyzer_instance, learning_manager_instance
    global emotion_system_instance, crisis_system_instance, time_system_instance
    global formula_engine_instance, tool_dispatcher_instance, dialogue_manager_instance, agent_manager_instance

    print(f"Core Services: Initializing for AI ID: {ai_id}")

    # --- 0. Configurations ---
    effective_llm_config = llm_config if llm_config else DEFAULT_LLM_CONFIG
    effective_op_configs = operational_configs if operational_configs else DEFAULT_OPERATIONAL_CONFIGS

    # Ensure operational_configs are part of the main config dict for modules that expect it at top level
    main_config_dict = {
        "operational_configs": effective_op_configs,
        # Add other top-level config keys if needed by modules from self.config
    }

    # --- 1. Foundational Services ---
    if not llm_interface_instance:
        llm_interface_instance = LLMInterface(config=effective_llm_config)

    if not ham_manager_instance:
        if use_mock_ham:
            # This is a simplified MockHAM, the one in CLI is more elaborate.
            # For true shared mock, it should be defined centrally or passed.
            # For now, this illustrates the concept.
            class TempMockHAM(HAMMemoryManager): # type: ignore
                def __init__(self, *args, **kwargs): self.memory_store = {}; self.next_id = 1; print("CoreServices: Using TempMockHAM.")
                def store_experience(self, raw_data, data_type, metadata=None): mid = f"temp_mock_ham_{self.next_id}"; self.next_id+=1; self.memory_store[mid]={}; return mid
                def query_core_memory(self, **kwargs): return []
                def recall_gist(self, mem_id): return None
            ham_manager_instance = TempMockHAM(encryption_key="mock_key", db_path=None) # type: ignore
        else:
            # Ensure MIKO_HAM_KEY is set for real HAM
            ham_manager_instance = HAMMemoryManager(core_storage_filename=f"ham_core_{ai_id.replace(':','_')}.json")

    if not personality_manager_instance:
        personality_manager_instance = PersonalityManager() # Uses default profile initially

    if not trust_manager_instance:
        trust_manager_instance = TrustManager()

    if not mcp_connector_instance:
        mcp_connector_instance = MCPConnector(
            ai_id=ai_id,
            mqtt_broker_address=hsp_broker_address,
            mqtt_broker_port=hsp_broker_port
        )
        mcp_connector_instance.connect()

    # --- 2. HSP Related Services ---
    if not hsp_connector_instance:
        hsp_connector_instance = HSPConnector(
            ai_id=ai_id,
            broker_address=hsp_broker_address,
            broker_port=hsp_broker_port
        )
        if not hsp_connector_instance.connect(): # Attempt to connect
            print(f"Core Services: WARNING - HSPConnector for {ai_id} failed to connect to {hsp_broker_address}:{hsp_broker_port}")
            # Decide if this is a fatal error for the app context
        else:
            print(f"Core Services: HSPConnector for {ai_id} connected.")
            # Basic subscriptions needed by multiple modules
            hsp_connector_instance.subscribe(f"{CAP_ADVERTISEMENT_TOPIC}/#")
            hsp_connector_instance.subscribe(f"hsp/results/{ai_id}/#") # For DM task results
            hsp_connector_instance.subscribe(f"{FACT_TOPIC_GENERAL}/#") # For general facts

    if not service_discovery_module_instance:
        service_discovery_module_instance = ServiceDiscoveryModule(trust_manager=trust_manager_instance)
    
    # Always attempt to register callbacks if the instances exist, in case of re-initialization or partial setups.
    if hsp_connector_instance and service_discovery_module_instance:
        hsp_connector_instance.register_on_capability_advertisement_callback(
            service_discovery_module_instance.process_capability_advertisement
        )

    # --- 3. Core AI Logic Modules ---
    if not fact_extractor_instance:
        fact_extractor_instance = FactExtractorModule(llm_interface=llm_interface_instance)

    if not content_analyzer_instance:
        try:
            content_analyzer_instance = ContentAnalyzerModule()
        except Exception as e: # Catch potential spaCy model loading issues
            print(f"Core Services: WARNING - ContentAnalyzerModule failed to initialize: {e}. Some KG features may be unavailable.")
            content_analyzer_instance = None # Ensure it's None if failed

    if not learning_manager_instance:
        learning_manager_instance = LearningManager(
            ai_id=ai_id,
            ham_memory_manager=ham_manager_instance,
            fact_extractor=fact_extractor_instance,
            personality_manager=personality_manager_instance,
            content_analyzer=content_analyzer_instance,
            hsp_connector=hsp_connector_instance,
            trust_manager=trust_manager_instance,
            operational_config=effective_op_configs # Pass just the op_configs part
        )
        if hsp_connector_instance: # Register LM's fact callback
            hsp_connector_instance.register_on_fact_callback(learning_manager_instance.process_and_store_hsp_fact)

    if not emotion_system_instance:
        emotion_system_instance = EmotionSystem(personality_profile=personality_manager_instance.current_personality)

    if not crisis_system_instance:
        crisis_system_instance = CrisisSystem(config=main_config_dict)

    if not time_system_instance:
        time_system_instance = TimeSystem(config=main_config_dict)

    if not formula_engine_instance:
        formula_engine_instance = FormulaEngine() # Uses default formulas path

    if not tool_dispatcher_instance:
        tool_dispatcher_instance = ToolDispatcher(llm_interface=llm_interface_instance)

    if not agent_manager_instance:
        # AgentManager needs the python executable path. We assume it's the same one running this script.
        import sys
        agent_manager_instance = AgentManager(python_executable=sys.executable)

    if not dialogue_manager_instance:
        dialogue_manager_instance = DialogueManager(
            ai_id=ai_id,
            personality_manager=personality_manager_instance,
            memory_manager=ham_manager_instance,
            llm_interface=llm_interface_instance,
            emotion_system=emotion_system_instance,
            crisis_system=crisis_system_instance,
            time_system=time_system_instance,
            formula_engine=formula_engine_instance,
            tool_dispatcher=tool_dispatcher_instance,
            self_critique_module=None, # SelfCritiqueModule needs LLM, can be added if LM doesn't own it
            learning_manager=learning_manager_instance,
            content_analyzer=content_analyzer_instance,
            service_discovery_module=service_discovery_module_instance,
            hsp_connector=hsp_connector_instance,
            agent_manager=agent_manager_instance, # Add AgentManager
            config=main_config_dict # Pass the main config dict
        )
        # DM's __init__ now registers its own task result callback with hsp_connector_instance

    print("Core Services: All services initialized (or attempted).")


def get_services() -> Dict[str, Any]:
    """Returns a dictionary of the initialized service instances."""
    return {
        "llm_interface": llm_interface_instance,
        "ham_manager": ham_manager_instance,
        "personality_manager": personality_manager_instance,
        "trust_manager": trust_manager_instance,
        "hsp_connector": hsp_connector_instance,
        "service_discovery": service_discovery_module_instance,
        "fact_extractor": fact_extractor_instance,
        "content_analyzer": content_analyzer_instance,
        "learning_manager": learning_manager_instance,
        "emotion_system": emotion_system_instance,
        "crisis_system": crisis_system_instance,
        "time_system": time_system_instance,
        "formula_engine": formula_engine_instance,
        "tool_dispatcher": tool_dispatcher_instance,
        "dialogue_manager": dialogue_manager_instance,
        "agent_manager": agent_manager_instance,
    }

def shutdown_services():
    """Gracefully shuts down services, e.g., AgentManager and HSPConnector."""
    global hsp_connector_instance, agent_manager_instance

    if agent_manager_instance:
        print("Core Services: Shutting down all active agents...")
        agent_manager_instance.shutdown_all_agents()

    if hsp_connector_instance and hsp_connector_instance.is_connected:
        print("Core Services: Shutting down HSPConnector...")
        hsp_connector_instance.disconnect()

    print("Core Services: Shutdown process complete.")

if __name__ == '__main__':
    print("--- Core Services Initialization Test ---")
    initialize_services(ai_id="did:hsp:coreservice_test_ai_001", use_mock_ham=True)

    services = get_services()
    for name, service_instance in services.items():
        print(f"Service '{name}': {'Initialized' if service_instance else 'NOT Initialized'}")

    assert services["dialogue_manager"] is not None
    assert services["hsp_connector"] is not None
    # Add more assertions here if needed

    print("\n--- Verifying service references ---")
    dm = services["dialogue_manager"]
    lm = services["learning_manager"]
    sdm = services["service_discovery"]

    if dm and lm: assert dm.learning_manager == lm, "DM not using shared LM"
    if dm and sdm : assert dm.service_discovery_module == sdm, "DM not using shared SDM"
    if lm and services["trust_manager"]: assert lm.trust_manager == services["trust_manager"], "LM not using shared TrustManager"
    if sdm and services["trust_manager"]: assert sdm.trust_manager == services["trust_manager"], "SDM not using shared TrustManager"

    print("Service reference checks seem okay.")

    shutdown_services()
    print("--- Core Services Initialization Test Finished ---")
