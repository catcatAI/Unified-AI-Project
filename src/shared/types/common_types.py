# Placeholder for Common Python Type Definitions
# Used across different modules in the Unified-AI-Project.

from typing import TypedDict, List, Optional, Any, Dict, Literal

# Example TypedDict for a user profile snippet
class UserProfileSnippet(TypedDict):
    user_id: str
    display_name: Optional[str]
    preferences: Dict[str, Any]

# Example for a structured AI response
class AIResponse(TypedDict):
    text_content: str
    speech_audio_b64: Optional[str] # base64 encoded audio
    visual_elements: Optional[List[Dict[str, Any]]] # e.g., cards, images
    suggested_actions: Optional[List[str]]
    emotion_cue: Optional[str] # e.g., "happy", "neutral"
    metadata: Dict[str, Any]

# Example for a memory node or experience
class MemoryRecord(TypedDict):
    memory_id: str
    timestamp: str # ISO format
    data_type: str # e.g., "dialogue_text", "sensor_reading", "user_preference"
    content_gist: Any # Could be a summary string, a dict of keywords, etc.
    raw_data_reference: Optional[str] # Pointer to more complete raw data if needed
    metadata: Dict[str, Any] # Source, user_id, session_id, tags, etc.

# Example for a tool call structure
class ToolCallRequest(TypedDict):
    tool_name: str
    parameters: Dict[str, Any]

class ToolCallResponse(TypedDict):
    tool_name: str
    status: str # e.g., "success", "error"
    result: Optional[Any]
    error_message: Optional[str]


# Personality Profile Types based on miko_base.json
class CommunicationStyle(TypedDict):
    default_style: str
    tone_presets: Dict[str, str]
    response_length_preference: str

class FragmentaIntegrations(TypedDict):
    persona_chain_default: List[str]
    persona_chain_options: Dict[str, Dict[str, Any]] # Inner dict can be empty or have varied content
    default_tone_vector_profile: str

class CustomizationOptions(TypedDict):
    allow_user_trait_adjustment: bool
    learn_from_interaction: bool

class PersonalityProfile(TypedDict):
    profile_name: str
    display_name: str
    description: str
    core_values: List[str]
    communication_style: CommunicationStyle
    initial_prompt: str
    personality_traits_base: Dict[str, float]
    behavioral_guidelines: List[str]
    fragmenta_integrations: FragmentaIntegrations
    customization_options: CustomizationOptions
    version: str


# Specific Tool Parameter Types
class LogicToolParams(TypedDict):
    expression_string: str
    method: Optional[str]

class MathToolParams(TypedDict):
    input_string: str

class TranslationToolParams(TypedDict):
    text: str
    target_language: str
    source_language: Optional[str]


# Formula Config Types (from configs/formula_configs/default_formulas.json)
# Convention for tool dispatch:
# If action == "dispatch_tool", parameters is expected to contain:
#   "tool_name": str  (Name of the tool to dispatch to)
#   "tool_query": str (The query/input for the tool. Can be a template.)
#   Optionally, other parameters specific to the tool if the dispatcher/tool supports them.
class FormulaConfigEntry(TypedDict):
    name: str
    conditions: List[str]
    action: str  # Special value "dispatch_tool" triggers tool dispatch
    description: str
    parameters: Dict[str, Any] # Holds tool_name, tool_query, etc. for dispatch_tool
    priority: int
    enabled: bool
    version: str
    response_template: Optional[str] # Used if action is not "dispatch_tool" or as fallback

# System Config Types (from configs/system_config.yaml)
class SystemSubConfig(TypedDict):
    log_path: str
    log_level: str

class MemoryManagerConfig(TypedDict):
    short_term_memory_limit: int

class ToolDispatcherConfig(TypedDict):
    default_location: str

class LocalStorageConfig(TypedDict):
    path: str

class OllamaConfig(TypedDict):
    base_url: str
    model_name: str

class CoreSystemsConfig(TypedDict):
    local_storage: LocalStorageConfig
    ollama: Optional[OllamaConfig] # Making ollama config optional as it's an example

class FragmentaModulesConfig(TypedDict):
    echoShell: bool
    sillScan: bool
    toneFragment: bool
    tailStitch: bool

class FragmentaToneVectorConfig(TypedDict):
    V1: float
    V2: float
    V3: float

class FragmentaSettingsConfig(TypedDict):
    modules: FragmentaModulesConfig
    tone_vector: FragmentaToneVectorConfig

class SystemConfig(TypedDict):
    system: SystemSubConfig
    ai_name: str
    memory_manager: MemoryManagerConfig
    tool_dispatcher: ToolDispatcherConfig
    core_systems: CoreSystemsConfig
    fragmenta_settings: FragmentaSettingsConfig

# Chat History Types (from data/chat_histories/ollama_chat_histories.json)
class OllamaChatHistoryEntry(TypedDict, total=False): # total=False due to varying fields
    userId: str
    userPrompt: str # sometimes 'prompt'
    prompt: str # alias for userPrompt in some entries
    catResponse: str # sometimes 'response', can be JSON string
    response: str # alias for catResponse, can be JSON string
    referenceResponse: Optional[str]
    ollamaReferenceResponse: Optional[str]
    similarity: Optional[str] # Can be "N/A" or float string
    learningAction: Optional[str]
    timestamp: str
    model: Optional[str]

# Emotion Map Types (from data/knowledge_bases/LingCat_emotion_map.yaml)
class EmotionEffects(TypedDict):
    blink: bool
    tail: str
    ears: str
    voice: str
    text_ending: str

# Dialogue Context Memory Types (from data/processed_data/dialogue_context_memory.json)
class DialogueMemoryEntryMetadata(TypedDict):
    speaker: str
    timestamp: str # ISO format
    user_input_ref: Optional[str] # Optional, only for AI responses
    sha256_checksum: Optional[str] # Optional

class DialogueMemoryEntry(TypedDict):
    timestamp: str # ISO format
    data_type: str
    encrypted_package_b64: str
    metadata: DialogueMemoryEntryMetadata

class DialogueContextMemory(TypedDict):
    next_memory_id: int
    store: Dict[str, DialogueMemoryEntry] # Keys are "mem_XXXXXX"

# Ollama Formula Log Types (from data/raw_datasets/ollama_cat_formulas_log.json)
class OllamaFormulaLogEntry(TypedDict):
    prompt: str
    response: str # Can be simple string or multi-line JSON string
    reference: Optional[str]
    timestamp: str


# LLM Configuration Types
class LLMProviderOllamaConfig(TypedDict):
    base_url: str
    # Potentially other ollama specific like keep_alive, etc.

class LLMProviderOpenAIConfig(TypedDict):
    api_key: str
    # Potentially organization_id, default_model for this provider, etc.

class LLMProviderAnthropicConfig(TypedDict):
    api_key: str
    # Potentially default_model for this provider, etc.

class LLMProvidersConfigGroup(TypedDict, total=False): # Each provider is optional
    ollama: LLMProviderOllamaConfig
    openai: LLMProviderOpenAIConfig
    anthropic: LLMProviderAnthropicConfig
    # mock provider doesn't need specific config here, handled by name 'mock'

class LLMInterfaceConfig(TypedDict):
    default_provider: str # e.g., "ollama", "openai", "mock"
    default_model: Optional[str] # A specific model ID like "llama2", "gpt-3.5-turbo"
    providers: LLMProvidersConfigGroup
    # Optional: default parameters for generation like temperature, max_tokens
    default_generation_params: Optional[Dict[str, Any]]


# Learning and Feedback Types
class CritiqueResult(TypedDict):
    score: float  # e.g., 0.0 (bad) to 1.0 (good)
    reason: Optional[str]
    suggested_alternative: Optional[str]

class DialogueMemoryEntryMetadata(TypedDict): # Original definition, now extended
    speaker: str
    timestamp: str # ISO format
    user_input_ref: Optional[str]
    sha256_checksum: Optional[str]
    critique: Optional[CritiqueResult] # Added for AI's self-critique
    user_feedback_explicit: Optional[str] # e.g., "positive", "negative", "correction: new text"
    learning_weight: Optional[float] # Derived from critique/feedback

class LearnedFactRecord(TypedDict):
    record_id: str # UUID
    timestamp: str # ISO format datetime
    user_id: Optional[str]
    session_id: Optional[str]
    source_interaction_ref: Optional[str] # mem_id of user's DialogueMemoryEntry
    fact_type: str # e.g., "user_preference", "user_statement", "user_correction"
    content: Dict[str, Any] # Structured fact, e.g., {"type": "favorite_color", "value": "blue"}
    confidence: float # LLM's confidence in this extracted fact (0.0-1.0)
    source_text: str # Original user text from which fact was extracted


# Operational Configuration Types (for foolproofing, performance)
class TimeoutConfig(TypedDict):
    llm_general_request: int # seconds
    llm_critique_request: int
    llm_fact_extraction_request: int
    dialogue_manager_turn: int # Overall time for a single get_simple_response turn

class LearningThresholdConfig(TypedDict):
    min_fact_confidence_to_store: float # 0.0 - 1.0
    min_critique_score_to_store: float   # 0.0 - 1.0

class OperationalConfig(TypedDict, total=False): # Make sections optional
    timeouts: TimeoutConfig
    learning_thresholds: LearningThresholdConfig
    # Future: resource_limits (e.g., max_cpu_for_task), concurrency_limits (e.g., max_background_threads)


# You can add more complex types, Enums, Pydantic models, etc. here as needed.
# For example:
# from enum import Enum
# class UserRole(Enum):
#     GUEST = "guest"
#     REGISTERED = "registered"
#     ADMIN = "admin"

# --- Knowledge Graph Data Structures ---
class KGEntity(TypedDict):
    id: str  # Unique identifier for the entity
    label: str  # Textual representation of the entity
    type: str  # Entity type (e.g., "PERSON", "FOOD", "CONCEPT")
    attributes: Dict[str, Any]  # Additional properties of the entity

class KGRelationship(TypedDict):
    source_id: str  # ID of the source KGEntity
    target_id: str  # ID of the target KGEntity
    type: str  # Relationship type (e.g., "is_a", "has_ingredient", "works_for")
    weight: Optional[float]  # Confidence or importance of the relationship
    attributes: Dict[str, Any]  # Additional properties of the relationship

class KnowledgeGraph(TypedDict):
    entities: Dict[str, KGEntity]  # Mapping entity ID to KGEntity object
    relationships: List[KGRelationship]  # List of all relationships
    metadata: Dict[str, Any]  # Metadata about the graph (e.g., source, creation date)
# --- End Knowledge Graph Data Structures ---

# --- Tool Dispatcher Structured Response ---
class ToolDispatcherResponse(TypedDict):
    status: Literal["success", "failure_tool_error", "unhandled_by_local_tool", "error_dispatcher_issue"]
    payload: Optional[Any] # Actual result from tool if success
    tool_name_attempted: Optional[str]
    original_query_for_tool: Optional[str] # The query that was passed to the tool
    error_message: Optional[str] # Error message if status is failure or error
    # Add new status: "failed_needs_hsp_retry" - for tools that specifically suggest HSP
    # status: Literal["success", "failure_tool_error", "unhandled_by_local_tool", "error_dispatcher_issue", "failed_suggest_hsp"]


print("common_types.py placeholder loaded.")

if __name__ == '__main__':
    # Example usage (not for runtime, just for type checking or understanding)
    user_snippet: UserProfileSnippet = {
        "user_id": "user123",
        "display_name": "Test User",
        "preferences": {"theme": "dark", "notifications": True}
    }
    print(f"Example UserProfileSnippet: {user_snippet}")

    ai_resp: AIResponse = {
        "text_content": "Hello there!",
        "emotion_cue": "friendly",
        "metadata": {"engine": "main_dialogue"}
    }
    print(f"Example AIResponse: {ai_resp}")

    # Example usage for PersonalityProfile
    example_miko_profile: PersonalityProfile = {
        "profile_name": "miko_base_example",
        "display_name": "Miko Example",
        "description": "An example AI assistant.",
        "core_values": ["learning", "empathy"],
        "communication_style": {
            "default_style": "friendly",
            "tone_presets": {"default": "warm", "formal": "precise"},
            "response_length_preference": "medium"
        },
        "initial_prompt": "Hello, I am Miko Example.",
        "personality_traits_base": {"friendly": 0.9, "curious": 0.8},
        "behavioral_guidelines": ["Be helpful.", "Ask clarifying questions."],
        "fragmenta_integrations": {
            "persona_chain_default": ["neutral"],
            "persona_chain_options": {"neutral": {}, "reflective": {"param1": "value1"}},
            "default_tone_vector_profile": "standard_miko_example"
        },
        "customization_options": {
            "allow_user_trait_adjustment": True,
            "learn_from_interaction": True
        },
        "version": "1.0.0-example"
    }
    print(f"Example PersonalityProfile: {example_miko_profile}")

    example_formula: FormulaConfigEntry = {
        "name": "example_formula",
        "conditions": ["example trigger", "another example"],
        "action": "do_example_action",
        "description": "This is an example formula.",
        "parameters": {"param1": "value1", "param2": 123},
        "priority": 100,
        "enabled": True,
        "version": "0.9-example",
        "response_template": "You triggered the example formula with param1: {param1}!"
    }
    print(f"Example FormulaConfigEntry: {example_formula}")

    example_system_config: SystemConfig = {
        "system": {"log_path": "logs/example.log", "log_level": "DEBUG"},
        "ai_name": "ExampleAI",
        "memory_manager": {"short_term_memory_limit": 20},
        "tool_dispatcher": {"default_location": "London"},
        "core_systems": {
            "local_storage": {"path": "data/example_storage"},
            "ollama": {"base_url": "http://localhost:11434", "model_name": "example_model"}
        },
        "fragmenta_settings": {
            "modules": {"echoShell": False, "sillScan": True, "toneFragment": False, "tailStitch": True},
            "tone_vector": {"V1": 0.1, "V2": 0.2, "V3": 0.7}
        }
    }
    print(f"Example SystemConfig: {example_system_config}")

    example_chat_history_entry: OllamaChatHistoryEntry = {
        "userId": "user_example_456",
        "userPrompt": "Tell me a joke",
        "catResponse": "Why don't scientists trust atoms? Because they make up everything!",
        "timestamp": "2023-10-27T10:00:00Z",
        "model": "example_chat_model"
    }
    print(f"Example OllamaChatHistoryEntry: {example_chat_history_entry}")

    example_emotion_effects_map: Dict[str, EmotionEffects] = {
        "happy_example": {
            "blink": True, "tail": "wag_fast", "ears": "perked",
            "voice": "cheerful", "text_ending": "! :D"
        }
    }
    print(f"Example EmotionEffects Map: {example_emotion_effects_map}")

    example_dialogue_memory: DialogueContextMemory = {
        "next_memory_id": 3,
        "store": {
            "mem_000001_example": {
                "timestamp": "2023-10-27T10:01:00Z",
                "data_type": "user_dialogue_text_example",
                "encrypted_package_b64": "example_base64_string_user",
                "metadata": {
                    "speaker": "user_example",
                    "timestamp": "2023-10-27T10:01:00Z",
                    "sha256_checksum": "example_checksum_user"
                }
            },
            "mem_000002_example": {
                "timestamp": "2023-10-27T10:01:05Z",
                "data_type": "ai_dialogue_text_example",
                "encrypted_package_b64": "example_base64_string_ai",
                "metadata": {
                    "speaker": "ai_example",
                    "timestamp": "2023-10-27T10:01:05Z",
                    "user_input_ref": "mem_000001_example",
                    "sha256_checksum": "example_checksum_ai"
                }
            }
        }
    }
    print(f"Example DialogueContextMemory: {example_dialogue_memory}")

    example_formula_log_entry: OllamaFormulaLogEntry = {
        "prompt": "Is it sunny?",
        "response": "{\"weather\": \"sunny\", \"temp\": \"25C\"}",
        "reference": "Actual weather: partly cloudy",
        "timestamp": "2023-10-27T10:02:00Z"
    }
    print(f"Example OllamaFormulaLogEntry: {example_formula_log_entry}")

    example_llm_interface_config: LLMInterfaceConfig = {
        "default_provider": "ollama",
        "default_model": "llama3:8b",
        "providers": {
            "ollama": {
                "base_url": "http://localhost:11434"
            },
            "openai": {
                "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        },
        "default_generation_params": {
            "temperature": 0.8,
            "max_tokens": 512
        }
    }
    print(f"Example LLMInterfaceConfig: {example_llm_interface_config}")
