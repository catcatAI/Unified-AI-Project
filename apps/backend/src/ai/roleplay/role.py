# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Role model for multi-role play (Phase 0 of the multi-role plan).

Data-only on purpose: no LLM calls, no I/O, no global state. Phase 1
(`RolePlayAgent`) consumes these objects; keeping them inert is what makes the
scope rules unit-testable without a backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from ai.persona.persona_engine import PersonaState


class ContextScope(str, Enum):
    """How a role relates to the main AI's conversation."""

    SHARED = "shared"  # 角色 A = main，完全共享主 AI 上下文
    PRIVATE = "private"  # 角色 B/C，完全隔離
    HYBRID = "hybrid"  # 讀共享基底 + 自己的 private overlay


@dataclass
class Role:
    """One playable identity.

    ``persona_state`` is per-role by construction (``default_factory``), so two
    roles never share a mutable default — that was the bug the singleton
    persona engine had.
    """

    role_id: str
    display_name: str
    persona_card_id: Optional[str] = None
    persona_state: PersonaState = field(default_factory=PersonaState)
    backend_slot: Optional[str] = None  # None → 用 active backend
    context_scope: ContextScope = ContextScope.PRIVATE
    memory_namespace: Optional[str] = None  # None → role_id
    shared_memory_read: bool = True
    shared_memory_write: bool = False  # 只有主 AI 該是 True
    conversation_id: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None

    def __post_init__(self) -> None:
        self.role_id = (self.role_id or "").strip()
        if not self.role_id:
            raise ValueError("role_id must be a non-empty string")

        self.display_name = (self.display_name or "").strip() or self.role_id
        self.memory_namespace = (self.memory_namespace or "").strip() or self.role_id

        if isinstance(self.context_scope, str):
            self.context_scope = ContextScope(self.context_scope)

        if self.shared_memory_write and not self.shared_memory_read:
            raise ValueError("shared_memory_write requires shared_memory_read")

        if self.temperature_override is not None and not 0.0 < self.temperature_override <= 2.0:
            raise ValueError("temperature_override must be in (0.0, 2.0]")
        if self.max_tokens_override is not None and self.max_tokens_override <= 0:
            raise ValueError("max_tokens_override must be positive")

    @property
    def is_primary(self) -> bool:
        """Whether this role owns the shared base (i.e. is the main AI)."""
        return self.context_scope is ContextScope.SHARED

    def resolved_backend(self, active_backend: Optional[str]) -> Optional[str]:
        """Force the role's slot when set, otherwise fall back to the active one."""
        return self.backend_slot or active_backend

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "display_name": self.display_name,
            "persona_card_id": self.persona_card_id,
            "persona_state": self.persona_state,
            "backend_slot": self.backend_slot,
            "context_scope": self.context_scope.value,
            "memory_namespace": self.memory_namespace,
            "shared_memory_read": self.shared_memory_read,
            "shared_memory_write": self.shared_memory_write,
            "conversation_id": self.conversation_id,
            "temperature_override": self.temperature_override,
            "max_tokens_override": self.max_tokens_override,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        known = {f for f in cls.__dataclass_fields__ if f != "persona_state"}
        kwargs = {k: v for k, v in data.items() if k in known}
        state = data.get("persona_state")
        if isinstance(state, PersonaState):
            kwargs["persona_state"] = state
        elif isinstance(state, dict):
            kwargs["persona_state"] = PersonaState(**state)
        return cls(**kwargs)
