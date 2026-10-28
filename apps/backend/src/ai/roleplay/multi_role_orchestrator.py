# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""MultiRoleOrchestrator — the registry that turns roles into a conversation.

P2-1 of ``MULTI_ROLE_PLAY_AGENT_PLAN.md``, minus the router coupling (that is
P2-2). Turns run sequentially on purpose: the primary role's reply lands in the
shared base, and a later role should be able to read it in the same group turn.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai.roleplay.context import DEFAULT_TOKEN_BUDGET
from ai.roleplay.role import ContextScope, Role
from ai.roleplay.role_play_agent import LLMCall, MemoryWriter, RolePlayAgent

logger = logging.getLogger(__name__)


class MultiRoleOrchestrator:
    """Owns the role registry and routes turns to the right ``RolePlayAgent``."""

    def __init__(
        self,
        llm_service: Optional[LLMCall] = None,
        memory_writer: Optional[MemoryWriter] = None,
        default_backend: Optional[str] = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
    ) -> None:
        self.llm_service = llm_service
        self.memory_writer = memory_writer
        self.default_backend = default_backend
        self.token_budget = token_budget
        self._agents: Dict[str, RolePlayAgent] = {}

    # ------------------------------------------------------------------
    # registry
    # ------------------------------------------------------------------
    def register(
        self,
        role: Role,
        llm_service: Optional[LLMCall] = None,
        memory_writer: Optional[MemoryWriter] = None,
    ) -> RolePlayAgent:
        """Add a role; per-role services fall back to the orchestrator's."""
        if role.role_id in self._agents:
            raise ValueError(f"role already registered: {role.role_id}")
        if role.context_scope is ContextScope.SHARED and self.primary_role_id is not None:
            raise ValueError(f"only one SHARED role is allowed (already: {self.primary_role_id})")

        agent = RolePlayAgent(
            role,
            llm_service=llm_service or self.llm_service,
            memory_writer=memory_writer or self.memory_writer,
            token_budget=self.token_budget,
        )
        self._agents[role.role_id] = agent
        logger.info("[%s] registered role %s", agent.agent_id, role.role_id)
        return agent

    def unregister(self, role_id: str) -> bool:
        return self._agents.pop(role_id, None) is not None

    def get(self, role_id: str) -> Optional[RolePlayAgent]:
        return self._agents.get(role_id)

    @property
    def roles(self) -> List[str]:
        return list(self._agents)

    @property
    def primary_role_id(self) -> Optional[str]:
        for agent in self._agents.values():
            if agent.role.context_scope is ContextScope.SHARED:
                return agent.role.role_id
        return None

    # ------------------------------------------------------------------
    # turns
    # ------------------------------------------------------------------
    async def turn(self, role_id: str, message: str, **kwargs: Any) -> Dict[str, Any]:
        agent = self._agents.get(role_id)
        if agent is None:
            raise KeyError(f"unknown role: {role_id}")
        kwargs.setdefault("active_backend", self.default_backend)
        return await agent.respond(message, **kwargs)

    async def group_turn(
        self, message: str, role_ids: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Dict[str, Any]]:
        """Ask every role in registration order and key the replies by role id."""
        targets = list(role_ids) if role_ids is not None else self.roles
        results: Dict[str, Dict[str, Any]] = {}
        for role_id in targets:
            results[role_id] = await self.turn(role_id, message, **kwargs)
        return results
