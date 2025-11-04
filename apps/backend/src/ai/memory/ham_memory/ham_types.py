from typing import Dict, Any, TypedDict
from datetime import datetime

class HAMDataPackageInternal(TypedDict):
    timestamp: str
    data_type: str
    encrypted_package: bytes
    metadata: Dict[str, Any]
    relevance: float
    protected: bool

class HAMMemory(TypedDict):
    memory_id: str
    content: str
    metadata: Dict[str, Any]
    relevance: float

class HAMRecallResult(TypedDict):
    memory_id: str
    content: str
    score: float
    timestamp: datetime
    metadata: Dict[str, Any]

class HAMMemoryError(Exception):
    """Custom exception for HAM memory operations."""
    pass
