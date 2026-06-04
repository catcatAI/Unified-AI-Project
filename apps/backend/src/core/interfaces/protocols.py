"""
Angela AI Layer Protocols (L1-L4)
Defines formal communication contracts and shared types for the system.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


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

