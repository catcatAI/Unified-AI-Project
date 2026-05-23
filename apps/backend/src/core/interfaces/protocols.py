"""
Angela AI Layer Protocols (L1-L4)
Defines formal communication contracts and shared types for the system.
"""

from typing import Protocol, Dict, Any, List, Optional, runtime_checkable
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

@runtime_checkable
class L1Biological(Protocol):
    """Protocol for Biological/Physiological modules."""
    @abstractmethod
    async def advance_time(self, dt: float) -> None:
        """Advance the biological state by dt seconds (Continuous Domain)."""
        ...

    @abstractmethod
    def get_metabolic_cost(self) -> float:
        """Returns the current energy consumption rate."""
        ...

@runtime_checkable
class L2Cognitive(Protocol):
    """Protocol for Cognitive/Logical modules."""
    @abstractmethod
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a discrete event (Discrete Domain)."""
        ...

@runtime_checkable
class L3Identity(Protocol):
    """Protocol for Identity/Ego modules."""
    @abstractmethod
    def verify_alignment(self, intent: Any) -> bool:
        """Verify if an intent aligns with the core identity."""
        ...

@runtime_checkable
class L4Creative(Protocol):
    """Protocol for Creative/Evolutionary modules."""
    @abstractmethod
    def evaluate_novelty(self, input_data: Any) -> float:
        """Evaluates the novelty of the input (0.0 - 1.0)."""
        ...


# =============================================================================
# Shared Types (moved from services.angela_llm_service for layer isolation)
# =============================================================================

class ModelProvider(Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"


@dataclass
class LLMResponse:
    """LLM response structure."""
    text: str
    backend: str
    model: str
    tokens_used: int = 0
    response_time_ms: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def content(self) -> str:
        return self.text


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str
    content: str
    name: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
        )
