# src/shared/types/common_types.py
"""
This module defines common Python `TypedDict` structures used for data exchange
between various internal modules of the Unified-AI-Project. These types help ensure
clarity, maintainability, and enable static type checking.

For guidelines on creating and using these types, refer to:
`docs/INTERNAL_DATA_STANDARDS.md`
"""

from typing import TypedDict, List, Optional, Any, Dict, Literal, Union # Re-add Union if it was there
from typing_extensions import Required # Added for new types

# --- User and Session Related Types ---
class UserProfileSnippet(TypedDict):
    """A brief summary of a user's profile."""
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


# --- Memory System Types ---
class CritiqueResult(TypedDict):
    """Represents the result of an AI's self-critique or external critique."""
    score: float  # e.g., 0.0 (bad) to 1.0 (good)
    reason: Optional[str]
    suggested_alternative: Optional[str]

class DialogueMemoryEntryMetadata(TypedDict):
    """
    Metadata associated with a dialogue entry stored in memory (e.g., HAM).
    This is the consolidated and extended version.
    """
    speaker: str # Who spoke (e.g., "user", "ai_agent_name")
    timestamp: str # ISO format datetime string of when the entry was recorded
    user_input_ref: Optional[str] # If an AI response, refers to the mem_id of the user input it's responding to
    sha256_checksum: Optional[str] # Checksum of the raw data associated with this entry
    # Fields from Learning and Feedback
    critique: Optional[CritiqueResult] # Results of self-critique or external critique
    user_feedback_explicit: Optional[str] # Explicit feedback from user (e.g., "thumbs_up", "correction: new text")
    learning_weight: Optional[float] # Weight assigned for learning purposes, derived from critique/feedback

class MemoryRecord(TypedDict):
    """
    Generic structure for a record stored in the Hierarchical Associative Memory (HAM).
    """
    memory_id: str # Unique identifier for this memory record within HAM
    timestamp: str # ISO format datetime string of when the memory was recorded/created
    data_type: str # Describes the nature of the data (e.g., "dialogue_text", "learned_fact", "sensor_reading")
    content_gist: Any # An abstracted or summarized version of the raw data. Format depends on data_type.
    raw_data_reference: Optional[str] # Optional pointer or key to retrieve the full raw data if stored separately
    metadata: DialogueMemoryEntryMetadata # Using the consolidated metadata type, or a more generic Dict[str, Any] if varied

class DialogueMemoryEntry(TypedDict):
    """
    Represents a single entry in a dialogue history, typically stored in HAM.
    This structure is often what's serialized/deserialized from files like dialogue_context_memory.json.
    """
    timestamp: str # ISO format datetime of the dialogue turn or event
    data_type: str # e.g., "user_dialogue_text", "ai_dialogue_text"
    encrypted_package_b64: str # Base64 encoded string of the encrypted and compressed dialogue content
    metadata: DialogueMemoryEntryMetadata # Metadata about this dialogue entry

class DialogueContextMemory(TypedDict):
    """Structure for the entire dialogue context memory store, typically mapping to a JSON file."""
    next_memory_id: int # Counter for the next available memory ID
    store: Dict[str, DialogueMemoryEntry] # Key is memory_id (e.g., "mem_000001")


# --- Tooling Related Types ---
class ToolCallRequest(TypedDict):
    """Represents a request to call a tool."""
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
    """Defines integration points with Fragmenta-like processing chains."""
    persona_chain_default: List[str]
    persona_chain_options: Dict[str, Dict[str, Any]] # Inner dict can be empty or have varied content
    default_tone_vector_profile: str

class CustomizationOptions(TypedDict):
    """Options for how the AI's personality can be customized or learn."""
    allow_user_trait_adjustment: bool
    learn_from_interaction: bool

class PersonalityProfile(TypedDict):
    """
    Defines the complete profile for an AI personality, influencing its behavior,
    communication style, and operational parameters. Based on miko_base.json.
    """
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


# --- System Configuration Types (derived from configs/system_config.yaml) ---
class SystemSubConfig(TypedDict):
    """General system settings like logging."""
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
    """Configuration for enabling/disabling specific Fragmenta modules."""
    # Field names are camelCase matching the typical JS/JSON config source.
    echoShell: bool
    sillScan: bool
    toneFragment: bool
    tailStitch: bool

class FragmentaToneVectorConfig(TypedDict):
    """Defines parameters for a Fragmenta tone vector."""
    # Field names are V1,V2,V3 matching typical config source.
    V1: float
    V2: float
    V3: float

class FragmentaSettingsConfig(TypedDict):
    """Overall settings for Fragmenta integration."""
    modules: FragmentaModulesConfig
    tone_vector: FragmentaToneVectorConfig

class SystemConfig(TypedDict):
    """Root structure for the system_config.yaml file."""
    system: SystemSubConfig
    ai_name: str
    memory_manager: MemoryManagerConfig
    tool_dispatcher: ToolDispatcherConfig
    core_systems: CoreSystemsConfig
    fragmenta_settings: FragmentaSettingsConfig

# Chat History Types (from data/chat_histories/ollama_chat_histories.json)
class OllamaChatHistoryEntry(TypedDict, total=False): # total=False due to varying fields
    # Field names like userId, userPrompt, catResponse are often from external data sources (e.g., Ollama logs)
    # and are kept as is for easier mapping, though internal project convention is snake_case.
    # A comment highlighting this discrepancy is useful.
    # TODO: Consider a transformation step if strict snake_case is required internally for these.
    userId: str # Note: camelCase from source
    userPrompt: str # Note: camelCase from source; sometimes 'prompt' in source
    prompt: Optional[str] # Alias for userPrompt in some entries
    catResponse: str # Note: camelCase from source; sometimes 'response', can be JSON string
    response: Optional[str] # Alias for catResponse, can be JSON string
    referenceResponse: Optional[str]
    ollamaReferenceResponse: Optional[str]
    similarity: Optional[str] # Can be "N/A" or float string, consider parsing to float if used numerically
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
# The DialogueMemoryEntryMetadata, DialogueMemoryEntry, and DialogueContextMemory types
# were consolidated and moved to the "Memory System Types" section earlier.


# Ollama Formula Log Types (from data/raw_datasets/ollama_cat_formulas_log.json)
class OllamaFormulaLogEntry(TypedDict):
    """Represents an entry from logs related to formula execution with Ollama."""
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


# --- Learning and Feedback Related Types ---
# CritiqueResult was moved to "Memory System Types" as it's part of DialogueMemoryEntryMetadata.
# The extended DialogueMemoryEntryMetadata is now the canonical one in "Memory System Types".

class LearnedFactRecord(TypedDict):
    """
    Represents a structured fact learned by the AI, typically stored in HAM.
    """
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
    """Thresholds related to learning and knowledge acquisition."""
    min_fact_confidence_to_store: float # 0.0 - 1.0, for facts from user input
    min_critique_score_to_store: float   # 0.0 - 1.0, for storing critique results
    min_hsp_fact_confidence_to_store: Optional[float] # For facts from HSP, can differ from user facts
    hsp_fact_conflict_confidence_delta: Optional[float] # Delta for comparing confidence in conflict resolution

class OperationalConfig(TypedDict, total=False): # Make sections optional
    """
    Configuration for operational aspects like timeouts and learning thresholds.
    Typically loaded from system_config.yaml.
    """
    timeouts: Optional[TimeoutConfig]
    learning_thresholds: Optional[LearningThresholdConfig]
    default_hsp_fact_topic: Optional[str] # Default topic for publishing facts via HSP
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
    """Represents an entity in the knowledge graph."""
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
    """Represents the overall structure of the knowledge graph data."""
    entities: Dict[str, KGEntity]  # Mapping entity ID to KGEntity object
    relationships: List[KGRelationship]  # List of all relationships
    metadata: Dict[str, Any]  # Metadata about the graph (e.g., source, creation date)


# --- Tool Dispatcher Structured Response ---
class ToolDispatcherResponse(TypedDict):
    """Standardized response format from the ToolDispatcher."""
    status: Literal["success", "failure_tool_error", "unhandled_by_local_tool", "error_dispatcher_issue"]
    payload: Optional[Any] # Actual result from tool if success
    tool_name_attempted: Optional[str]
    original_query_for_tool: Optional[str] # The query that was passed to the tool
    error_message: Optional[str] # Error message if status is failure or error
    # Add new status: "failed_needs_hsp_retry" - for tools that specifically suggest HSP
    # status: Literal["success", "failure_tool_error", "unhandled_by_local_tool", "error_dispatcher_issue", "failed_suggest_hsp"]


# --- Dialogue Manager Specific Internal Types ---
class DialogueTurn(TypedDict):
    """Represents a single turn in a dialogue session history."""
    speaker: str  # Typically "user" or the AI's name/role
    text: str     # The text content of the turn

class PendingHSPTaskInfo(TypedDict):
    """Information stored by DialogueManager about a pending HSP task request."""
    user_id: Optional[str]
    session_id: Optional[str]
    original_query_text: str
    request_timestamp: str  # ISO datetime string
    capability_id: str
    target_ai_id: str
    expected_callback_topic: str
    request_type: str  # e.g., "generic_task", "proactive_fact_query"

class ToolParameterDetail(TypedDict, total=False):
    """Details of a parameter for a tool, typically parsed by an LLM for tool drafting."""
    name: Required[str]
    type: Required[str]  # Python type hint as a string
    default: Any        # Default value, if any
    description: Required[str]

class ParsedToolIODetails(TypedDict, total=False):
    """Structured Input/Output details for a tool, parsed by an LLM for tool drafting."""
    suggested_method_name: Required[str]
    class_docstring_hint: Required[str]
    method_docstring_hint: Required[str]
    parameters: Required[List[ToolParameterDetail]]
    return_type: Required[str] # Python type hint as a string
    return_description: Required[str]
# --- End Dialogue Manager Specific Internal Types ---

# --- HAMMemoryManager Specific Internal Types ---
class HAMDataPackageInternal(TypedDict):
    """Internal structure for how data is held in HAM's core_memory_store (before file serialization)."""
    timestamp: str
    data_type: str
    encrypted_package: bytes # Encrypted and compressed data
    metadata: Dict[str, Any] # Should ideally conform to DialogueMemoryEntryMetadata or a more generic version

class HAMRecallResult(TypedDict):
    """Standardized structure for results from HAMMemoryManager.recall_gist and query_core_memory."""
    id: str # The memory_id (mem_XXXXXX)
    timestamp: str # ISO format datetime string of when the memory was recorded
    data_type: str # The data_type of the stored experience
    rehydrated_gist: Any # The processed/rehydrated content. For text, it's a string summary. For other data, it might be the decoded string of the content.
    metadata: Dict[str, Any] # The metadata associated with the memory record. Should conform to DialogueMemoryEntryMetadata where applicable.
# --- End HAMMemoryManager Specific Internal Types ---

# --- Fact Extractor Module Specific Types ---
class ExtractedFactContentPreference(TypedDict, total=False):
    """Content structure for a 'user_preference' fact."""
    category: Required[str]
    preference: Required[str]
    liked: Optional[bool] # True for like, False for dislike, None if not specified

class ExtractedFactContentStatement(TypedDict, total=False):
    """Content structure for a 'user_statement' fact (e.g., about self)."""
    attribute: Required[str]
    value: Required[Any] # Value can be string, number, boolean etc.

# Union for the 'content' field of an ExtractedFact
ExtractedFactContent = Union[ExtractedFactContentPreference, ExtractedFactContentStatement, Dict[str, Any]]

class ExtractedFact(TypedDict):
    """
    Represents a single fact extracted by the FactExtractorModule from user text.
    This is the structure LearningManager receives.
    """
    fact_type: Required[str]  # e.g., "user_preference", "user_statement"
    content: Required[ExtractedFactContent] # The structured content of the fact
    confidence: Required[float] # LLM's confidence in this extraction (0.0-1.0)
# --- End Fact Extractor Module Specific Types ---

# --- LLM Interface Specific Types ---
class LLMModelInfo(TypedDict, total=False):
    """Information about an available LLM model."""
    id: Required[str] # Model ID or name (e.g., "nous-hermes2:latest", "gpt-3.5-turbo")
    provider: Required[str]  # e.g., "ollama", "openai", "mock"
    name: Optional[str] # Often same as id, but can be more descriptive
    family: Optional[str] # e.g., "llama", "gpt"
    size_bytes: Optional[int]
    modified_at: Optional[str] # ISO datetime string
# --- End LLM Interface Specific Types ---


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


# --- LIS (Linguistic Immune System) Specific Types ---

# Represents the specific type of anomaly detected by LIS components.
LIS_AnomalyType = Literal[
    "RHYTHM_BREAK",                 # Anomaly in semantic/linguistic rhythm.
    "UNEXPECTED_TONE_SHIFT",        # Sudden or contextually inappropriate tone shift.
    "NARRATIVE_DIVERGENCE",         # Output deviates from established goals or logical narrative.
    "INTERNAL_STATE_MISMATCH",      # Linguistic expression contradicts AI's internal state.
    "SELF_REPETITION",              # Excessive self-repetition in output.
    "EXTERNAL_ECHO_DOMINANCE",      # Undue influence from specific HSP echoes leading to repetition.
    "LOW_DIVERSITY",                # General low linguistic diversity in output.
    "ANTI_PATTERN_DETECTED",        # Use of known problematic grammatical structures.
    "COHERENCE_FAILURE",            # Local semantic incoherence (e.g., "word salad").
    "COMPLEXITY_ANOMALY",           # Sudden, unexplained change in syntactic complexity.
    "CASCADE_ERROR_SUSPECTED",      # Minor fix leading to a cascade of new errors.
    "FACTUAL_INCONSISTENCY_INTERNAL", # AI's statement contradicts its own knowledge base (HAM).
    "FACTUAL_INCONSISTENCY_EXTERNAL"  # AI's statement contradicts verified external fact (advanced).
]

# Type alias for LIS severity scores, typically a float between 0.0 (minor) and 1.0 (critical).
LIS_SeverityScore = float

# Represents the outcome of an LIS intervention.
LIS_InterventionOutcome = Literal[
    "SUCCESS",                      # Intervention successfully resolved/mitigated the anomaly.
    "PARTIAL_SUCCESS",              # Intervention partially addressed the anomaly.
    "FAILURE",                      # Intervention did not resolve the anomaly.
    "NEEDS_REVIEW",                 # Anomaly or intervention requires human review.
    "NO_ACTION_TAKEN",              # Anomaly detected, but no intervention was performed.
    "ESCALATED"                     # Anomaly escalated to another system or human.
]

class LIS_SemanticAnomalyDetectedEvent(TypedDict, total=False):
    """
    Represents a structured event payload generated when an LIS component
    (e.g., ERR-INTROSPECTOR) detects a semantic or linguistic anomaly.
    """
    anomaly_id: Required[str]  # Unique identifier for this specific anomaly event (e.g., UUID).
    timestamp: Required[str]   # ISO 8601 UTC timestamp of detection.
    anomaly_type: Required[LIS_AnomalyType] # The type of anomaly detected.
    severity_score: Required[LIS_SeverityScore] # Score from 0.0 (minor) to 1.0 (critical).
    problematic_output_segment: Required[str] # The specific segment of AI output or processed text that is anomalous.
    current_context_snapshot: Dict[str, Any] # Snapshot of relevant context (e.g., dialogue history, task state, AI emotion state).
    expected_pattern_description: Optional[str] # Description of what was expected if the anomaly is a deviation.
    triggering_data: Optional[Dict[str, Any]] # Optional data that triggered the anomaly (e.g., specific HSP pulse, user input segment).
    detector_component: Optional[str] # Name of the LIS component or sub-module that detected this anomaly.

class LIS_InterventionReport(TypedDict, total=False):
    """
    Represents a structured report detailing an intervention attempt by an LIS
    component (e.g., TONAL_REPAIR_ENGINE) in response to a detected anomaly.
    """
    report_id: Required[str]  # Unique identifier for this intervention report (e.g., UUID).
    incident_id_ref: Required[str] # Reference to the anomaly_id from LIS_SemanticAnomalyDetectedEvent.
    timestamp: Required[str]    # ISO 8601 UTC timestamp of when the intervention was performed/logged.
    action_taken: Required[str] # Description of the intervention action (e.g., "Rephrased segment", "Adjusted tone", "Applied Antibody_XYZ", "No action - logged only").
    parameters_used: Optional[Dict[str, Any]] # Parameters used for the intervention (e.g., specific antibody ID, LLM prompt used for rephrasing).
    outcome: Required[LIS_InterventionOutcome] # The outcome of the intervention.
    reasoning: Optional[str]    # Brief reasoning for the chosen action or outcome, if applicable.
    repaired_output_segment: Optional[str] # The new segment of AI output if a repair was made.

class LIS_IncidentRecord(TypedDict, total=False):
    """
    Represents a comprehensive record of a linguistic/semantic incident handled
    or logged by the LIS. This is the primary data structure for the
    IMMUNO-NARRATIVE CACHE.
    """
    incident_id: Required[str] # Unique identifier for this incident record (can be same as anomaly_id if 1:1).
    timestamp_logged: Required[str] # ISO 8601 UTC timestamp when this record was created/logged in the cache.
    anomaly_event: Required[LIS_SemanticAnomalyDetectedEvent] # The detected anomaly event.
    intervention_reports: Optional[List[LIS_InterventionReport]] # Optional: A list of intervention attempts and their reports. Could be multiple if retried.
    error_bloom_ref: Optional[str] # Optional reference to an ErrorBloom event ID if related.
    learned_antibody_ref: Optional[str] # Optional reference to a NarrativeAntibody ID if one was applied or learned from this.
    status: Optional[Literal["OPEN", "CLOSED_RESOLVED", "CLOSED_UNRESOLVED", "MONITORING", "ESCALATED_MANUAL"]] # Current status of this incident.
    tags: Optional[List[str]] # Tags for categorization or querying.
    notes: Optional[str] # Any additional notes or human annotations.

# Defines the type/category of corrective action an antibody represents.
LIS_AntibodyStrategyType = Literal[
    "REPHRASE_LLM",             # Use an LLM to rephrase or generate alternative text.
    "APPLY_TEMPLATE",           # Apply a predefined response template.
    "SUGGEST_CLARIFICATION",    # Formulate a question to the user for clarification.
    "MODIFY_CONTEXT_FLAG",      # Adjust an internal context flag or state.
    "LOG_ONLY_ENHANCED",        # Perform enhanced logging, no direct output modification.
    "ALERT_HUMAN_REVIEW",       # Flag the incident for human review.
    "CUSTOM_INTERNAL_ACTION"    # Trigger a custom, specific internal function or process.
]

class NarrativeAntibodyObject(TypedDict, total=False):
    """
    Represents a "narrative antibody" - a learned or defined pattern or strategy
    for responding to specific types of semantic anomalies. These are stored and
    retrieved by the LISCacheInterface.
    """
    antibody_id: Required[str]  # Unique identifier for this antibody (e.g., UUID).
    description: Optional[str]  # Human-readable description of the antibody.
    target_anomaly_types: Required[List[LIS_AnomalyType]] # LIS_AnomalyType(s) this antibody addresses.

    # Structured representation of conditions that trigger this antibody.
    # Flexible to allow for various pattern matching techniques (keywords, semantic features, etc.)
    # Example: {"keywords_in_segment": ["repeat", "stuck"], "context_has_flag": "user_confused"}
    trigger_conditions: Required[Dict[str, Any]]

    response_strategy_type: Required[LIS_AntibodyStrategyType] # Category of corrective action.

    # Details specific to the response_strategy_type.
    # Example for REPHRASE_LLM: {"llm_prompt_template": "Rephrase: {segment}", "model_params": {"temp": 0.6}}
    # Example for APPLY_TEMPLATE: {"template_id": "empathy_tpl_001", "vars": ["username"]}
    response_strategy_details: Required[Dict[str, Any]]

    effectiveness_score: Optional[float]    # Historical effectiveness (0.0-1.0), updated over time.
    usage_count: Optional[int]              # Number of times successfully applied.
    confidence_in_applicability: Optional[float] # Dynamic score (0.0-1.0) for current situation match.

    timestamp_created: Required[str]        # ISO 8601 UTC when defined/learned.
    timestamp_last_updated: Optional[str]   # ISO 8601 UTC when last modified or effectiveness updated.
    version: Optional[int]                  # Version number for the antibody definition.

    source_incident_ids: Optional[List[str]] # LIS_IncidentRecord.incident_id(s) that led to this antibody.
    metadata: Optional[Dict[str, Any]]       # Other relevant metadata (e.g., creator, model versions).

# --- End LIS Specific Types ---


# --- AI Virtual Input System Types ---

VirtualMouseEventType = Literal[
    "move_relative_to_element", # Move mouse to a relative x,y within a target_element_id
    "move_relative_to_window",  # Move mouse by delta_x_ratio, delta_y_ratio of current window
    "click",                    # Perform a click (left, right, double)
    "scroll",                   # Scroll (up, down, left, right)
    "drag_start",               # Start a drag operation (implicitly at current mouse pos or on an element)
    "drag_end",                 # End a drag operation (potentially to a new position or element)
    "hover"                     # Hover over an element or position
]

VirtualKeyboardActionType = Literal[
    "type_string",              # Types a sequence of characters.
    "press_keys",               # Simulates pressing one or more keys, including modifiers (e.g., ['ctrl', 'alt', 't'], ['enter']).
    "special_key"               # Press a special key like 'enter', 'tab', 'esc', 'delete', 'backspace', arrow keys.
    # 'hold_key', 'release_key' could be added for more fine-grained control if needed.
]

VirtualInputPermissionLevel = Literal[
    "simulation_only",          # Commands are logged/simulated, no real OS events. (Default)
    "allow_actual_input_restricted", # Actual input allowed, but perhaps restricted to specific app/window (Future).
    "allow_actual_input_full"        # Full actual input allowed (Requires extreme caution and explicit grant).
]

class VirtualInputElementDescription(TypedDict, total=False):
    """
    Describes a UI element as perceived by the AI's virtual environment.
    This structure can be recursive for nested elements.
    """
    element_id: Required[str]  # Unique identifier for this element within the current context/screen.
    element_type: Required[str] # Type of the element (e.g., "button", "text_field", "checkbox", "label", "window", "file_icon", "list_item").
    label_text: Optional[str]   # Visible text label or content of the element.
    value: Optional[Any]        # Current value (e.g., text in a field, checked state of a box).
    is_enabled: Optional[bool]  # Whether the element is interactive.
    is_focused: Optional[bool]  # Whether the element currently has virtual focus.
    is_visible: Optional[bool]  # Whether the element is currently considered visible.
    # Relative bounds [x_ratio, y_ratio, width_ratio, height_ratio] within its parent or the screen/window.
    # Ratios are 0.0 to 1.0. (e.g., x_ratio=0.5 means horizontal center).
    bounds_relative: Optional[List[float]] # Typically List[float] of 4 elements. Using List for TypedDict compatibility.
    children: Optional[List['VirtualInputElementDescription']] # Recursive definition for child elements.
    attributes: Optional[Dict[str, Any]] # Other specific attributes (e.g., 'is_scrollable', 'options' for a dropdown).

class VirtualMouseCommand(TypedDict, total=False):
    """Command for the virtual mouse."""
    action_type: Required[VirtualMouseEventType]
    target_element_id: Optional[str] # ID of the element to interact with.
    # Relative coordinates (0.0-1.0).
    # For 'move_relative_to_element', relative to target_element_id's bounds.
    # For 'move_relative_to_window', these are deltas from current position or absolute if specified.
    relative_x: Optional[float]
    relative_y: Optional[float]

    # Specific to click
    click_type: Optional[Literal['left', 'right', 'double']] # Defaults to 'left' if 'click' action.

    # Specific to scroll
    scroll_direction: Optional[Literal['up', 'down', 'left', 'right']]
    scroll_amount_ratio: Optional[float] # Ratio of scrollable area, e.g., 0.1 for 10%.
    scroll_pages: Optional[int]          # Number of "pages" to scroll.

    # Specific to drag_end
    drag_to_element_id: Optional[str]
    drag_to_relative_x: Optional[float]
    drag_to_relative_y: Optional[float]


class VirtualKeyboardCommand(TypedDict, total=False):
    """Command for the virtual keyboard."""
    action_type: Required[VirtualKeyboardActionType]
    target_element_id: Optional[str] # Element to focus before typing, if applicable.
    text_to_type: Optional[str]      # For 'type_string'.
    keys: Optional[List[str]]        # For 'press_keys' (e.g., ["ctrl", "c"], ["shift", "a"], ["enter"]).
                                     # For 'special_key', a single key string like "enter", "tab".

# --- End AI Virtual Input System Types ---
