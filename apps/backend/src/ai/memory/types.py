# TODO: Fix import - module 'typing' not found
# TODO: Fix import - module 'enum' not found

class MemoryType(Enum):
    """Enumeration of different memory types."""
    CORE = "core"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"

class HAMDataPackageInternal(TypedDict):
    timestamp: str  # ISO 8601 UTC string
    data_type: str
    encrypted_package: bytes # The actual encrypted data
    metadata: Dict[str, Any]
    relevance: float  # Relevance score
    protected: bool   # Protection flag

class HAMRecallResult(TypedDict):
    id: str # Memory ID
    timestamp: str # ISO 8601 UTC string of original storage
    data_type: str
    rehydrated_gist: Any # Could be str for text, or other types:
    metadata: Dict[str, Any]