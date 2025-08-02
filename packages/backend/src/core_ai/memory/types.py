from typing import TypedDict, Dict, Any

class HAMDataPackageInternal(TypedDict):
    timestamp: str  # ISO 8601 UTC string
    data_type: str
    encrypted_package: bytes # The actual encrypted data
    metadata: Dict[str, Any]

class HAMRecallResult(TypedDict):
    id: str # Memory ID
    timestamp: str # ISO 8601 UTC string of original storage
    data_type: str
    rehydrated_gist: Any # Could be str for text, or other types
    metadata: Dict[str, Any]
