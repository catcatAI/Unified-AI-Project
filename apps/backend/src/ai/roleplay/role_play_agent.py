# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""RolePlayAgent — one role, one persona, one forced backend slot.

Phase 1 (P1-1/P1-2) of ``MULTI_ROLE_PLAY_AGENT_PLAN.md``. The class is
deliberately thin about *how* the LLM is reached and where memory goes: both
are injected seams, so P1-3 (HAM/vector namespace) can wire the real
implementations without editing this file.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from ai.agents.base.base_agent import BaseAgent
from ai.persona.persona_engine import PersonaEngine, get_persona_engine
from ai.roleplay.context import DEFAULT_TOKEN_BUDGET, RoleContext
from ai.roleplay.role import ContextScope, Role

logger = logging.getLogger(__name__)

#: ``llm_service(messages=..., prompt=..., backend_slot=..., temperature=..., max_tokens=...)``
LLMCall = Callable[..., Awaitable[Any]]
#: ``memory_writer(namespace=..., role_id=..., content=...)``
MemoryWriter = Callable[..., Awaitable[Any]]


class RolePlayAgent(BaseAgent):
    """A playable role bound to its own persona, context and memory namespace."""

    def __init__(
        self,
        role: Role,
        llm_service: Optional[LLMCall] = None,
        memory_writer: Optional[MemoryWriter] = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        **base_kwargs: Any,
    ) -> None:
        base_kwargs.setdefault("agent_id", f"roleplay-{role.role_id}")
        base_kwargs.setdefault("agent_name", f"RolePlayAgent[{role.role_id}]")
        base_kwargs.setdefault(
            "capabilities",
            [
                {
                    "name": "role_play_respond",
                    "capability_id": "role_play_respond",
                    "description": f"以 {role.display_name} 的角色回覆",
                    "version": "1.0.0",
                }
            ],
        )
        super().__init__(**base_kwargs)

        self.role = role
        # 角色專屬 persona：role_id 一給就是自己的實例，不是 Angela 的單例
        self.persona_engine: PersonaEngine = get_persona_engine(role.role_id)
        self.context = RoleContext(role_id=role.role_id, token_budget=token_budget)
        self.llm_service = llm_service
        self.memory_writer = memory_writer

    # ------------------------------------------------------------------
    # main entry
    # ------------------------------------------------------------------
    async def respond(
        self,
        user_message: str,
        *,
        al_state: Optional[Dict[str, float]] = None,
        active_backend: Optional[str] = None,
        viewer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer as this role.

        ``active_backend`` is only a fallback: when the role declares a
        ``backend_slot`` it always wins, which is what keeps role B on its own
        model even if the caller passed the global default.
        """
        text = (user_message or "").strip()
        if not text:
            raise ValueError("user_message must be a non-empty string")

        state = al_state or {}
        persona_prompt = self.persona_engine.get_persona_prompt_injection(
            float(state.get("fatigue", 0.2)),
            float(state.get("stress", 0.1)),
            float(state.get("valence", 0.5)),
        )
        system_prompt = f"{persona_prompt}\n[Role: {self.role.display_name}]"

        self._write_turn({"role": "user", "content": text})
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.context.merged_messages(viewer=viewer))

        backend_slot = self.role.resolved_backend(active_backend)
        base_result = {
            "role_id": self.role.role_id,
            "backend_slot": backend_slot,
            "memory_namespace": self.role.memory_namespace,
        }

        if self.llm_service is None:
            logger.warning("[%s] llm_service not configured; role play degraded", self.agent_id)
            return {**base_result, "status": "unavailable", "reply": None}

        try:
            raw = await self.llm_service(
                messages=messages,
                prompt=system_prompt,
                backend_slot=backend_slot,
                temperature=self.role.temperature_override,
                max_tokens=self.role.max_tokens_override,
            )
        except Exception as exc:  # noqa: BLE001 - 角色回覆失敗不該拖垮整條對話
            logger.warning("[%s] LLM call failed: %s", self.agent_id, exc, exc_info=True)
            return {**base_result, "status": "error", "reply": None, "error": str(exc)}

        reply = self._extract_text(raw)
        self._write_turn({"role": "assistant", "content": reply})
        await self._remember(reply)

        return {
            **base_result,
            "status": "success",
            "reply": reply,
            "messages_sent": len(messages),
            "over_budget": self.context.is_over_budget(),
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _write_turn(self, message: Dict[str, Any]) -> str:
        """Primary role writes into the shared base; everyone else into overlay."""
        if self.role.context_scope is ContextScope.SHARED:
            self.context.add_shared(message)
            return "shared"
        self.context.add_private(message)
        return "private"

    async def _remember(self, reply: str) -> None:
        if self.memory_writer is None:
            return
        try:
            await self.memory_writer(
                namespace=self.role.memory_namespace,
                role_id=self.role.role_id,
                content=reply,
            )
        except Exception as exc:  # noqa: BLE001 - 記憶寫入是 best-effort
            logger.warning("[%s] memory write failed: %s", self.agent_id, exc)

    @staticmethod
    def _extract_text(raw: Any) -> str:
        if isinstance(raw, str):
            return raw
        content = getattr(raw, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(raw, dict):
            for key in ("content", "text", "reply"):
                value = raw.get(key)
                if isinstance(value, str):
                    return value
        return str(raw)
