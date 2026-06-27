"""
Angela AI Layer Protocols (L1-L4)
Defines formal communication contracts and shared types for the system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Backward compatibility aliases (2026-06-07)
# These allow old imports to work while implementations use new names
try:
    from services.llm.providers.registry import LLMBackend as ModelProvider
except ImportError:
    ModelProvider = None
    logger.warning("ModelProvider alias: LLMBackend not available")


@dataclass
class ChatMessage:
    """A single message in a conversation"""
    role: str = "user"
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM call"""
    text: str = ""
    backend: str = "unknown"
    model: str = "unknown"
    error: str = ""
    confidence: float = 0.0
    tokens_used: Optional[int] = None
    response_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def content(self) -> str:
        """Alias for text — used by ensemble and other consumers"""
        return self.text

    @content.setter
    def content(self, value: str) -> None:
        self.text = value


@dataclass
class ChatResponse(LLMResponse):
    """Chat pipeline response — extends LLMResponse with hit scoring and routing."""
    hit_score: float = 0.0
    hit_source: str = "none"
    route: str = "llm"
    emotion: str = "neutral"
    emotion_confidence: float = 0.5
    emotion_intensity: float = 0.5
    bio_state: Dict[str, Any] = field(default_factory=dict)
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class L1Biological:
    """L1 - Biological / Sensory inputs"""
    sensory_input: Dict[str, Any] = field(default_factory=dict)
    reaction_time_ms: float = 0.0
    signal_strength: float = 1.0

    def process(self) -> Dict[str, Any]:
        return {"status": "processed", "input": self.sensory_input}


@dataclass
class L2Cognitive:
    """L2 - Cognitive / Pattern recognition"""
    cognitive_load: float = 0.0
    attention_focus: str = ""
    working_memory: Dict[str, Any] = field(default_factory=dict)

    def analyze(self) -> Dict[str, Any]:
        return {"status": "analyzed", "load": self.cognitive_load}


@dataclass
class L3Identity:
    """L3 - Identity / Self-awareness"""
    identity_id: str = ""
    core_values: Dict[str, float] = field(default_factory=dict)
    self_model: Dict[str, Any] = field(default_factory=dict)

    def reflect(self) -> Dict[str, Any]:
        return {"status": "reflected", "identity": self.identity_id}


@dataclass
class L4Creative:
    """L4 - Creative / Generative synthesis"""
    creative_context: Dict[str, Any] = field(default_factory=dict)
    generation_params: Dict[str, Any] = field(default_factory=dict)

    def generate(self) -> Dict[str, Any]:
        return {"status": "generated", "output": {}}

