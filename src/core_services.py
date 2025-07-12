# src/core_services.py

import yaml
import os
from typing import Optional, Dict, Any
import uuid

# Helper function to load YAML files
def _load_yaml_config(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        print(f"Warning: Config file not found at {filepath}. Returning empty dict.")
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {filepath}: {e}. Returning empty dict.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred loading config from {filepath}: {e}. Returning empty dict.")
        return {}

# Helper function to recursively resolve environment variables in a dictionary
def _resolve_env_vars(config_data: Any) -> Any:
    if isinstance(config_data, dict):
        return {k: _resolve_env_vars(v) for k, v in config_data.items()}
    elif isinstance(config_data, list):
        return [_resolve_env_vars(elem) for elem in config_data]
    elif isinstance(config_data, str):
        # Handle _PLACEHOLDER pattern (e.g., "GEMINI_API_KEY_PLACEHOLDER")
        if config_data.endswith('_PLACEHOLDER'):
            env_var_name = config_data.replace('_PLACEHOLDER', '')
            return os.getenv(env_var_name, config_data) # Return original if env var not set
        # Handle ${ENV_VAR} pattern
        elif config_data.startswith('${') and config_data.endswith('}'):
            env_var_name = config_data[2:-1]
            return os.getenv(env_var_name, config_data) # Return original if env var not set
        return config_data
    else:
        return config_data



# Core AI Modules
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
from src.fragmenta.fragmenta_orchestrator import FragmentaOrchestrator # Added import

# Services
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig
from src.hsp.connector import HSPConnector
from src.hsp.constants import CAP_ADVERTISEMENT_TOPIC, FACT_TOPIC_GENERAL

# --- Global Singleton Instances ---
# These will be initialized by `initialize_services`

# Foundational Services
llm_interface_instance: Optional[LLMInterface] = None
ham_manager_instance: Optional[HAMMemoryManager] = None # Using MockHAM in CLI for now
personality_manager_instance: Optional[PersonalityManager] = None
trust_manager_instance: Optional[TrustManager] = None

# HSP Related Services
hsp_connector_instance: Optional[HSPConnector] = None
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
fragmenta_orchestrator_instance: Optional[FragmentaOrchestrator] = None # Added instance


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
    hsp_broker_address: str = os.getenv("MQTT_BROKER_ADDRESS", DEFAULT_MQTT_BROKER),
    hsp_broker_port: int = int(os.getenv("MQTT_BROKER_PORT", DEFAULT_MQTT_PORT)),
    llm_config: Optional[LLMInterfaceConfig] = None,
    operational_configs: Optional[Dict[str, Any]] = None,
    use_mock_ham: bool = False # Flag to use MockHAM for CLI/testing ease
):
    """
    Initializes and holds singleton instances of all core services and modules.
    This function should be called once at application startup.
    """
    global llm_interface_instance, ham_manager_instance, personality_manager_instance
    global trust_manager_instance, hsp_connector_instance, service_discovery_module_instance
    global fact_extractor_instance, content_analyzer_instance, learning_manager_instance
    global emotion_system_instance, crisis_system_instance, time_system_instance
    global formula_engine_instance, tool_dispatcher_instance, dialogue_manager_instance, fragmenta_orchestrator_instance # Added to global

    print(f"Core Services: Initializing for AI ID: {ai_id}")

    # --- 0. Configurations ---
    # Determine project root for config file paths
    project_root = os.path.dirname(os.path.abspath(__file__)) # src/
    project_root = os.path.abspath(os.path.join(project_root, '..')) # Unified-AI-Project/

    # Load system_config.yaml
    system_config_path = os.path.join(project_root, 'configs', 'system_config.yaml')
    loaded_system_config = _load_yaml_config(system_config_path)

    # Load api_keys.yaml and resolve environment variables
    api_keys_config_path = os.path.join(project_root, 'configs', 'api_keys.yaml')
    loaded_api_keys_raw = _load_yaml_config(api_keys_config_path)
    resolved_api_keys = _resolve_env_vars(loaded_api_keys_raw)

    # Merge provided operational_configs with loaded system_config
    # Provided operational_configs take precedence
    effective_op_configs = loaded_system_config.get('operational_configs', {})
    if operational_configs:
        # Deep merge operational_configs if necessary, for now, simple update
        effective_op_configs.update(operational_configs)

    # Construct the main config dictionary to be passed around
    main_config_dict = {
        **loaded_system_config, # Start with all system config
        "operational_configs": effective_op_configs, # Ensure operational_configs are updated
        "api_keys": resolved_api_keys, # Add resolved API keys
        # Any other top-level configs from system_config.yaml will be included here
    }

    # Update effective_llm_config based on loaded configs
    # Start with default LLM config, then override with system_config and api_keys
    effective_llm_config = DEFAULT_LLM_CONFIG.copy() # Start with a copy to avoid modifying global default

    # Override default_provider and default_model from system_config if present
    if 'llm_settings' in loaded_system_config:
        llm_sys_settings = loaded_system_config['llm_settings']
        if 'default_provider' in llm_sys_settings:
            effective_llm_config['default_provider'] = llm_sys_settings['default_provider']
        if 'default_model' in llm_sys_settings:
            effective_llm_config['default_model'] = llm_sys_settings['default_model']

    # Merge providers from system_config and api_keys
    # Providers from system_config (e.g., ollama base_url)
    if 'llm_settings' in loaded_system_config and 'providers' in loaded_system_config['llm_settings']:
        for provider_name, provider_config in loaded_system_config['llm_settings']['providers'].items():
            if provider_name not in effective_llm_config['providers']:
                effective_llm_config['providers'][provider_name] = {}
            effective_llm_config['providers'][provider_name].update(provider_config)

    # Providers from resolved_api_keys (e.g., gemini api_key)
    if 'api_keys' in main_config_dict:
        for provider_name, api_key_config in main_config_dict['api_keys'].items():
            if provider_name not in effective_llm_config['providers']:
                effective_llm_config['providers'][provider_name] = {}
            effective_llm_config['providers'][provider_name].update(api_key_config)

    # If an llm_config was explicitly passed to initialize_services, it takes highest precedence
    if llm_config:
        # Deep merge the passed llm_config into the effective_llm_config
        # This is a simplified merge, for production, a more robust deep_merge might be needed
        for key, value in llm_config.items():
            if isinstance(value, dict) and key in effective_llm_config and isinstance(effective_llm_config[key], dict):
                effective_llm_config[key].update(value)
            else:
                effective_llm_config[key] = value

    # Ensure operational_configs are passed to LLMInterface if it expects them
    effective_llm_config['operational_configs'] = effective_op_configs

    # --- 1. Foundational Services ---
    if not llm_interface_instance:
        llm_interface_instance = LLMInterface(config=effective_llm_config)

    if not ham_manager_instance:
        ham_encryption_key = main_config_dict.get('system', {}).get('ham_encryption_key')
        if use_mock_ham:
            # This is a simplified MockHAM, the one in CLI is more elaborate.
            # For true shared mock, it should be defined centrally or passed.
            # For now, this illustrates the concept.
            class TempMockHAM(HAMMemoryManager): # type: ignore
                def __init__(self, *args, **kwargs): self.memory_store = {}; self.next_id = 1; print("CoreServices: Using TempMockHAM.")
                def store_experience(self, raw_data, data_type, metadata=None): mid = f"temp_mock_ham_{self.next_id}"; self.next_id+=1; self.memory_store[mid]={}; return mid
                def query_core_memory(self, **kwargs): return []
                def recall_gist(self, mem_id): return None
            ham_manager_instance = TempMockHAM(encryption_key=ham_encryption_key, db_path=None) # type: ignore
        else:
            ham_manager_instance = HAMMemoryManager(
                core_storage_filename=f"ham_core_{ai_id.replace(':','_')}.json",
                encryption_key=ham_encryption_key # Pass the key here
            )

    if not personality_manager_instance:
        personality_manager_instance = PersonalityManager() # Uses default profile initially

    if not trust_manager_instance:
        trust_manager_instance = TrustManager()

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
            hsp_connector_instance.subscribe(f"{CAP_ADVERTISEMENT_TOPIC}/#") # Uses imported constant
            hsp_connector_instance.subscribe(f"hsp/results/{ai_id}/#") # For DM task results
            hsp_connector_instance.subscribe(f"{FACT_TOPIC_GENERAL}/#") # Uses imported constant

    if not service_discovery_module_instance:
        service_discovery_module_instance = ServiceDiscoveryModule(trust_manager=trust_manager_instance)
        if hsp_connector_instance: # Register callback if connector is up
            hsp_connector_instance.subscribe(f"{CAP_ADVERTISEMENT_TOPIC}/#") # Uses imported constant
            hsp_connector_instance.register_on_capability_advertisement_callback(
                service_discovery_module_instance.process_capability_advertisement
            )
            service_discovery_module_instance.set_hsp_connector(hsp_connector_instance) # Pass the connector

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
            content_analyzer=content_analyzer_instance,
            hsp_connector=hsp_connector_instance,
            trust_manager=trust_manager_instance,
            operational_config=effective_op_configs # Pass just the op_configs part
        )
        if hsp_connector_instance: # Register LM's fact callback
            hsp_connector_instance.register_on_fact_callback(learning_manager_instance.process_and_store_hsp_fact)

    # Initialize Emotion, Crisis, Time systems as they might be dependencies for Fragmenta or DM
    if not emotion_system_instance:
        emotion_system_instance = EmotionSystem(personality_profile=personality_manager_instance.current_personality, config=main_config_dict)

    if not crisis_system_instance:
        crisis_system_instance = CrisisSystem(config=main_config_dict)

    if not time_system_instance:
        time_system_instance = TimeSystem(config=main_config_dict)

    if not formula_engine_instance: # Initialize before tool_dispatcher if it's a dependency (not currently)
        formula_engine_instance = FormulaEngine() # Uses default formulas path

    if not tool_dispatcher_instance: # Initialize before Fragmenta and DialogueManager
        tool_dispatcher_instance = ToolDispatcher(llm_interface=llm_interface_instance)

    # --- 4. Fragmenta Orchestrator (after its own dependencies are up) ---
    if not fragmenta_orchestrator_instance:
        fragmenta_orchestrator_instance = FragmentaOrchestrator(
            ham_manager=ham_manager_instance,
            tool_dispatcher=tool_dispatcher_instance,
            llm_interface=llm_interface_instance,
            service_discovery=service_discovery_module_instance,
            hsp_connector=hsp_connector_instance,
            personality_manager=personality_manager_instance,
            emotion_system=emotion_system_instance,
            crisis_system=crisis_system_instance,
            config=main_config_dict
        )
        if hsp_connector_instance and fragmenta_orchestrator_instance:
            # Register Fragmenta's handler for HSP task results
            # (This is now addressed by HSPConnector supporting multiple task result callbacks)
            hsp_connector_instance.register_on_task_result_callback(
                fragmenta_orchestrator_instance._handle_hsp_sub_task_result
            )
            print("Core Services: FragmentaOrchestrator initialized and HSP task result callback registered.")
        else:
            print("Core Services: FragmentaOrchestrator initialized but HSP task result callback NOT registered (HSPConnector or Fragmenta instance missing).")

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
            # trust_manager=trust_manager_instance, # Removed, not an expected arg for DialogueManager
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
        "fragmenta_orchestrator": fragmenta_orchestrator_instance, # Added Fragmenta
    }

def shutdown_services():
    """Gracefully shuts down services, e.g., HSPConnector."""
    global hsp_connector_instance
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
