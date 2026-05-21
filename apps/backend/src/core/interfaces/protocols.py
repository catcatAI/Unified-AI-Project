"""
Angela AI Layer Protocols (L1-L4)
Defines formal communication contracts for the system.
"""

from typing import Protocol, Dict, Any, List, runtime_checkable
from abc import abstractmethod

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
