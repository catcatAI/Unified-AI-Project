# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3]
# =============================================================================
"""
Execution-gate ownership for every chat entry point.

The gate decides whether a side-effecting action may run. Previously the whole
flow lived in ``api.routes.chat_routes._handle_execution_gate``, which meant the
REPL / ``ChatService.generate_response`` path executed handlers and agents with
**no gate at all** (the local model then answered "Done!" for actions that never
happened). This module is the single owner:

* :class:`GateExecutionOwner` runs pending-confirm/cancel resolution, the shared
  ContextScheduler plan, the ExecutionGate decision, the IntentRegistry
  cross-check and the actual handler execution.
* Callers only translate the returned :class:`GateOutcome` into their own
  response shape (HTTP route dict vs LLMResponse for the REPL).
"""

import inspect
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CONFIRM_WORDS = {
    "好",
    "是",
    "确认",
    "ok",
    "yes",
    "sure",
    "確定",
    "对",
}

CANCEL_WORDS = {
    "不要",
    "取消",
    "算了",
    "no",
    "cancel",
    "skip",
    "不用",
}

# Outcome actions shared by every entry point.
OUTCOME_NONE = "none"
OUTCOME_CONFIRM = "confirm"
OUTCOME_CANCEL = "cancel"
OUTCOME_EXECUTED = "executed"
OUTCOME_FAILED = "failed"
OUTCOME_REJECT = "reject"
OUTCOME_AGENT_CONFIRM = "agent_confirm"
OUTCOME_AGENT_EXECUTED = "agent_executed"
OUTCOME_AGENT_FAILED = "agent_failed"

# Handler → IntentRegistry name, used as the second opinion before auto-execute.
_HANDLER_TO_INTENT = {
    "file_ops": "file_op",
    "web_search": "web_search",
    "code_exec": "code",
    "task_mgr": "task",
    "vision": "vision",
}

# Intents whose *only* implementation is a ModelBus handler and therefore have
# no entry in ExecutionGate.HANDLER_MAP (that map is keyed by QueryType). They
# are resolved through IntentRegistry, which carries the executable handler id in
# `metadata["handler_id"]` — data, not a regex in the service layer.
_REGISTRY_DISPATCH_INTENTS = ("learning", "image_generation", "app_mount")
# IntentRegistry confidence is keyword-density (matched chars / total chars), so
# a short imperative lands around 0.2-0.3. The same 0.1 floor the gate already
# uses for IntentRegistry confirmation is too weak here; 0.2 plus the pattern's
# own require_keywords list keeps 「設定檔在哪」 out of the memory store.
_REGISTRY_MIN_CONFIDENCE = 0.2


class TTLSessionManager:
    """Bounded, TTL-expiring session store (single shared instance)."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        ttl_seconds = 3600
        max_sessions = 1000
        try:
            from core.config_loader import get_angela_config

            session_cfg = (
                get_angela_config().get_authority("angela_core", {}).get("session_manager", {})
            )
            ttl_seconds = int(session_cfg.get("ttl_seconds", ttl_seconds))
            max_sessions = int(session_cfg.get("max_sessions", max_sessions))
        except Exception as exc:  # pragma: no cover - config is optional
            logger.debug("Session manager config unavailable, using defaults: %s", exc)
        self._ttl = ttl_seconds
        self._max_sessions = max_sessions
        self._last_purge = time.time()

    def _try_purge(self) -> None:
        """Lazy purge — runs O(n) scan at most once per 60s."""
        now = time.time()
        if now - self._last_purge < 60.0:
            return
        self._last_purge = now
        cutoff = datetime.now() - timedelta(seconds=self._ttl)
        expired = [
            sid
            for sid, s in self._sessions.items()
            if s.get("created_at") and datetime.fromisoformat(s["created_at"]) < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
        if len(self._sessions) > self._max_sessions:
            sorted_sessions = sorted(
                self._sessions.items(), key=lambda x: x[1].get("created_at", "")
            )
            for sid, _ in sorted_sessions[: len(sorted_sessions) - self._max_sessions]:
                del self._sessions[sid]

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._try_purge()
            return self._sessions.get(session_id)

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._try_purge()
            if len(self._sessions) >= self._max_sessions:
                oldest = min(
                    self._sessions.keys(), key=lambda k: self._sessions[k].get("created_at", "")
                )
                del self._sessions[oldest]
            self._sessions[session_id] = data

    def __contains__(self, session_id: str) -> bool:
        with self._lock:
            self._try_purge()
            return session_id in self._sessions

    def items(self) -> List[Tuple[str, Dict[str, Any]]]:
        with self._lock:
            self._try_purge()
            return list(self._sessions.items())


sessions = TTLSessionManager()


@dataclass
class GateOutcome:
    """What the gate decided, in transport-neutral form."""

    action: str = OUTCOME_NONE
    message: str = ""
    handler: Optional[str] = None
    query_type: str = ""
    confidence: float = 0.0
    result: Any = None
    error: str = ""
    plan: Any = None
    decision: Any = None

    @property
    def is_terminal(self) -> bool:
        """True when the caller must answer with this outcome, not generate."""
        return self.action != OUTCOME_NONE


class GateExecutionOwner:
    """Owns: pending confirmations, the gate decision, and the execution."""

    def __init__(self, session_store: Optional[TTLSessionManager] = None) -> None:
        self._sessions = session_store or sessions

    # ------------------------------------------------------------------
    # Pending confirmations
    # ------------------------------------------------------------------
    def store_pending(
        self, session_id: str, context: Dict[str, Any], pending: Dict[str, Any]
    ) -> None:
        context["pending_action"] = pending
        session_data = self._sessions.get(session_id) or {}
        session_data["pending_action"] = pending
        self._sessions.set(session_id, session_data)

    def take_pending(
        self, user_message: str, context: Dict[str, Any], session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Pop a pending action from context/session (single use)."""
        pending = context.pop("pending_action", None)
        if pending is None:
            session_data = self._sessions.get(session_id) or {}
            pending = session_data.pop("pending_action", None)
            self._sessions.set(session_id, session_data)
        if not isinstance(pending, dict):
            return None
        return pending

    # ------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------
    def plan_and_decide(
        self,
        user_message: str,
        context: Dict[str, Any],
        model_bus: Any = None,
    ) -> Tuple[Any, Any]:
        """Shared plan (ContextScheduler) + gate decision (ExecutionGate)."""
        from ai.core.execution_gate import ExecutionGate
        from services.llm.context_scheduler import get_context_scheduler

        plan = get_context_scheduler().plan_query(user_message, context)
        context["_classify_result_type"] = plan.query_type
        context["_classify_result_confidence"] = plan.confidence
        context["_classify_result_action"] = plan.action_type
        gate = ExecutionGate(model_bus=model_bus)
        decision = gate.decide(
            query_type=plan.query_type,
            action_type=plan.action_type,
            user_message=user_message,
            confidence=plan.confidence,
            context=context,
        )
        return plan, decision

    @staticmethod
    def _is_code_write_request(plan: Any, user_message: str) -> bool:
        """True for code-WRITE requests (no executable code in the message).

        Kept for unit compat; the live gate keys on the resolved handler
        (see process()) since EXECUTE-planned write requests need it too.
        """
        qt = getattr(plan, "query_type", "")
        qts = getattr(qt, "value", str(qt or "")).lower()
        if qts != "code":
            return False
        return GateExecutionOwner._has_no_executable_code(user_message)

    @staticmethod
    def _has_no_executable_code(user_message: str) -> bool:
        """True when the message carries no fenced/inline/multiline code."""
        text = (user_message or "").strip()
        if not text or "\n" in text:
            return False
        if "```" in text or "`" in text:
            return False
        return True

    @staticmethod
    def _llm_generation_available() -> bool:
        """True when the router has a live non-unified backend (no init side effects)."""
        try:
            import services.llm.router as _router_mod

            svc = getattr(_router_mod, "_llm_service", None)
            if svc is None:
                return False
            backends = getattr(svc, "backends", None) or {}
            for btype in backends:
                if getattr(btype, "value", str(btype)) != "unified":
                    return True
            return False
        except Exception:
            return False

    def _intent_registry_confirms(self, user_message: str, handler: Optional[str]) -> bool:
        """Second opinion before auto-execute; failures never block execution."""
        if not handler:
            return False
        try:
            from core.intent_registry import IntentRegistry

            ir_name, ir_conf = IntentRegistry().detect(user_message)
        except Exception as exc:
            logger.warning("IntentRegistry gate failed: %s", exc, exc_info=True)
            return True
        if not ir_name or ir_conf < 0.1:
            return True
        expected = _HANDLER_TO_INTENT.get(handler)
        if expected and ir_name != expected:
            logger.info(
                "IntentRegistry vetoed %s (detected=%s expected=%s)",
                handler,
                ir_name,
                expected,
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    async def execute_handler(
        self,
        handler_id: str,
        original_query: str,
        context: Dict[str, Any],
        model_bus: Any,
    ) -> GateOutcome:
        """Run a user-approved handler and report the real outcome."""
        from ai.core.execution_gate import ExecutionGate

        if not model_bus:
            return GateOutcome(
                action=OUTCOME_FAILED,
                handler=handler_id,
                error="no execution backend available",
            )
        executed = False
        error = ""
        result: Any = None
        try:
            outcome = model_bus.execute_handler(handler_id, original_query, context)
            result = await outcome if inspect.isawaitable(outcome) else outcome
            executed = not (isinstance(result, dict) and result.get("success") is False)
        except Exception as exc:
            error = str(exc)
            logger.warning("Execution gate handler failed: %s", exc, exc_info=True)
        context["last_action_result"] = result if executed else None
        context["continuation_count"] = 0
        try:
            ExecutionGate().record_result(handler_id, executed)
        except Exception:  # pragma: no cover - feedback is best-effort
            logger.warning("Failed to record execution gate feedback", exc_info=True)
        return GateOutcome(
            action=OUTCOME_EXECUTED if executed else OUTCOME_FAILED,
            handler=handler_id,
            result=result,
            error=error,
        )

    def _registry_handler_for(
        self, user_message: str, categories: Tuple[str, ...]
    ) -> Optional[Tuple[str, str]]:
        """Resolve (intent_name, handler_id) from IntentRegistry.

        ``IntentPattern.handler`` is a class name that nothing can dispatch, so
        the executable id lives in ``metadata["handler_id"]``. Returns None when
        the intent is unknown, too weak, or declares no handler id — the caller
        then falls through to normal generation rather than guessing.
        """
        try:
            from core.intent_registry import IntentRegistry

            registry = IntentRegistry()
        except Exception as exc:  # pragma: no cover - registry is optional
            logger.debug("IntentRegistry unavailable: %s", exc)
            return None
        for category in categories:
            name, confidence = registry.detect(user_message, category=category)
            if not name:
                continue
            pattern = registry.get_pattern(name)
            if not pattern:
                continue
            handler_id = (pattern.metadata or {}).get("handler_id")
            if not handler_id:
                continue
            required = (pattern.metadata or {}).get("require_keywords") or []
            has_verb = any(kw in user_message for kw in required) if required else False
            if required and not has_verb:
                continue
            # Density confidence is query-length-normalized, so a longer fact
            # dilutes a single explicit verb below the floor ("記住，水的沸點是
            # 一百度" scored 0.18 < 0.2 while the shorter fox/dog teaches scored
            # exactly 0.2). An explicit require-verb IS the authorization — it
            # bypasses the density floor; without it the floor still applies.
            if confidence < _REGISTRY_MIN_CONFIDENCE and not has_verb:
                continue
            return str(name), str(handler_id)
        return None

    async def _registry_dispatch(
        self, user_message: str, context: Dict[str, Any], model_bus: Any
    ) -> Optional[GateOutcome]:
        """Execute a handler that only IntentRegistry can name (e.g. learning).

        The gate still authorizes the action (``decide_agent_execution``), so a
        rejected/confirm-worthy action never runs, and the real outcome is
        reported instead of letting the model claim success.
        """
        if not model_bus:
            return None
        resolved = self._registry_handler_for(user_message, _REGISTRY_DISPATCH_INTENTS)
        if not resolved:
            return None
        intent_name, handler_id = resolved
        from ai.core.execution_gate import ExecutionGate

        gate = ExecutionGate(model_bus=model_bus)
        decision = gate.decide_agent_execution(
            intent=intent_name,
            agent_name=handler_id,
            user_message=user_message,
        )
        if decision.action == "confirm_then_execute":
            self.store_pending(
                str(context.get("session_id") or "repl::default"),
                context,
                {
                    "kind": "registry_handler",
                    "handler": handler_id,
                    "intent": "learning",
                    "original_query": user_message,
                },
            )
            return GateOutcome(
                action=OUTCOME_CONFIRM,
                message=decision.confirm_message,
                handler=handler_id,
                confidence=1.0,
                decision=decision,
            )
        if decision.action != "auto_execute":
            return None
        return await self.execute_handler(handler_id, user_message, context, model_bus)

    # ------------------------------------------------------------------
    # Full request pass
    # ------------------------------------------------------------------
    async def process(
        self,
        user_message: str,
        context: Dict[str, Any],
        session_id: str,
        model_bus: Any,
    ) -> GateOutcome:
        """Run the whole gate pass. Returns ``OUTCOME_NONE`` when the request may
        proceed to generation."""
        try:
            pending = self.take_pending(user_message, context, session_id)
            if pending:
                outcome = await self._resolve_pending(
                    user_message, context, session_id, model_bus, pending
                )
                if outcome is not None:
                    return outcome

            # Intents that exist only as a registered handler (user-taught
            # facts) must be dispatched here: QueryClassifier files them under
            # command/greeting, which decide() treats as non-actionable, so the
            # handler used to be unreachable and the model only pretended.
            registry_outcome = await self._registry_dispatch(user_message, context, model_bus)
            if registry_outcome is not None:
                return registry_outcome

            plan, decision = self.plan_and_decide(user_message, context, model_bus)

            # Code-WRITE requests carry no code (no fences/backticks, single
            # line): there is nothing to execute, and gating them only yields
            # a confirm prompt followed by "specify code". When an LLM backend
            # is available, fall through so the model WRITES the code instead
            # (live 2026-10-10: gemma writes correct fibonacci, gate blocked).
            # Fenced/inline/multiline code keeps the execute path. Keyed on
            # the resolved HANDLER (code_exec), not the plan type: a Unity
            # build script ("建車身…存檔") plans as EXECUTE but still needs
            # code written first (live 2026-10-10). System handlers
            # (system_cmd: 關機 etc.) never bypass.
            if decision.action in ("auto_execute", "confirm_then_execute"):
                if (
                    getattr(decision, "handler", "") == "code_exec"
                    and self._has_no_executable_code(user_message)
                    and self._llm_generation_available()
                ):
                    context["last_action_result"] = None
                    return GateOutcome(action=OUTCOME_NONE, plan=plan, decision=decision)

            if decision.action == "auto_execute":
                if self._intent_registry_confirms(user_message, decision.handler):
                    if decision.handler and model_bus:
                        return await self.execute_handler(
                            decision.handler, user_message, context, model_bus
                        )
                context["last_action_result"] = None
                context["_gate_ir_mismatch"] = True
                return GateOutcome(action=OUTCOME_NONE, plan=plan, decision=decision)

            if decision.action == "confirm_then_execute":
                self.store_pending(
                    session_id,
                    context,
                    {
                        "handler": decision.handler,
                        "action_type": decision.action_type,
                        "original_query": decision.original_query,
                    },
                )
                return GateOutcome(
                    action=OUTCOME_CONFIRM,
                    message=decision.confirm_message,
                    handler=decision.handler,
                    query_type=plan.query_type,
                    confidence=plan.confidence,
                    plan=plan,
                    decision=decision,
                )

            # reject: clear action result, continue to generation
            context["last_action_result"] = None
            return GateOutcome(action=OUTCOME_NONE, plan=plan, decision=decision)
        except Exception as exc:
            logger.warning("Execution gate unavailable: %s", exc, exc_info=True)
            return GateOutcome(action=OUTCOME_NONE)

    async def _resolve_pending(
        self,
        user_message: str,
        context: Dict[str, Any],
        session_id: str,
        model_bus: Any,
        pending: Dict[str, Any],
    ) -> Optional[GateOutcome]:
        """Confirm / cancel a previously requested action. None → keep going."""
        msg_lower = user_message.strip().lower()
        if msg_lower in CANCEL_WORDS:
            return GateOutcome(
                action=OUTCOME_CANCEL, message="好的，不執行。還有什麼需要幫忙的嗎？"
            )
        if msg_lower not in CONFIRM_WORDS:
            return None

        handler_id = pending.get("handler")
        if handler_id:
            return await self.execute_handler(
                handler_id, pending.get("original_query", user_message), context, model_bus
            )

        if pending.get("kind") == "agent":
            return await self._execute_confirmed_agent(pending, context)
        return None

    async def _execute_confirmed_agent(
        self, pending: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[GateOutcome]:
        """Re-enter the AgentOrchestrator with explicit user consent."""
        agent_name = pending.get("agent")
        intent = pending.get("intent")
        original_query = pending.get("original_query", "")
        if not agent_name or not intent:
            return None
        try:
            from ai.agents.agent_orchestrator import AgentOrchestrator

            manager = None
            try:
                from api.lifespan import get_agent_manager

                manager = get_agent_manager()
            except Exception:  # pragma: no cover - lifespan not initialized
                manager = None
            orchestrator = AgentOrchestrator(agent_manager=manager)
            context["_gate_confirmed_agent"] = agent_name
            context["_gate_confirmed_intent"] = intent
            route_result = await orchestrator.route_task(original_query, context)
            primary = (route_result.get("results") or [{}])[0]
            agent_result = primary.get("result") or {}
            inner = agent_result.get("result") if isinstance(agent_result, dict) else None
            if isinstance(inner, dict) and inner.get("message"):
                context["last_action_result"] = agent_result
                context["continuation_count"] = 0
                return GateOutcome(
                    action=OUTCOME_AGENT_EXECUTED,
                    handler=agent_name,
                    message=str(inner["message"]),
                    result=agent_result,
                )
            return GateOutcome(
                action=OUTCOME_AGENT_FAILED,
                handler=agent_name,
                error=str(primary.get("gate_reason") or "agent produced no result"),
            )
        except Exception as exc:
            logger.warning(
                "Confirmed agent execution failed for %s: %s", agent_name, exc, exc_info=True
            )
            return GateOutcome(action=OUTCOME_AGENT_FAILED, handler=agent_name, error=str(exc))


_owner: Optional[GateExecutionOwner] = None


def get_gate_execution_owner() -> GateExecutionOwner:
    """Shared gate owner singleton (same instance for every entry point)."""
    global _owner
    if _owner is None:
        _owner = GateExecutionOwner()
    return _owner
