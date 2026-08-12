# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [A] [L4]
# =============================================================================
"""
Main-line adaptive dispatcher (REFACTOR_PLAN §13).

Problem: the chat pipeline funnels every input straight into "produce a
response", discarding the `time` metadata and never deciding whether an input
is a *learning signal* or *training data* vs a *generation request*. A mod that
submits only ``text`` + ``time`` therefore has no defined path and risks
falling back to "sorry I didn't understand".

This module adds an **ingest-time, content-driven dispatch decision**:
    build InputEnvelope(text, time, ...) -> classify_dispatch(text)
        -> DispatchDecision(intent, confidence, sub_type)
        -> plan_actions(...)  -> {FORWARD, LEARN, TRAIN(queue)}

FORWARD routes to the existing generative pipeline (§11), LEARN writes to
memory, TRAIN enqueues into TrainingCoordinator with priority (sorted
execution, non-blocking). It is intentionally defensive: a failure in dispatch
never breaks the main response path.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DispatchIntent(Enum):
    """High-level intent decided at ingest time."""

    GENERATE = "generate"  # produce a response (FORWARD to pipeline)
    LEARN = "learn"        # ingest as a learning signal
    TRAIN = "train"        # enqueue for (sorted) training execution


class ActionType(Enum):
    FORWARD = "forward"  # continue the generative pipeline
    LEARN = "learn"      # record into memory / continuous learning
    TRAIN = "train"      # enqueue into TrainingCoordinator


@dataclass
class InputEnvelope:
    """Normalized ingest input. Aligns /chat/unified + /session/{id}/send."""

    text: str
    time: Optional[str] = None
    origin: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None


@dataclass
class DispatchDecision:
    intent: DispatchIntent
    confidence: float
    sub_type: str  # QueryType value (e.g. "creative") or "unknown"
    reason: str = ""


@dataclass
class Action:
    action: ActionType
    payload: Dict[str, Any] = field(default_factory=dict)


# Keywords that mark an input as a learning/training request rather than a
# plain generation request.
_LEARN_HINTS = {"學習", "請記住", "記住", "學", "learn", "remember", "memorize"}
_TRAIN_HINTS = {"訓練", "訓練我", "train", "fine-tune", "finetune"}


def build_envelope(request: Dict[str, Any]) -> InputEnvelope:
    """Build a normalized InputEnvelope from a chat/mod request dict.

    Reads the same field names the existing endpoints already accept
    (``message``/``text`` and ``time``/``timestamp``) so mod inputs that pass
    only ``text`` + ``time`` are captured with the time metadata bound.
    """
    text = request.get("message", request.get("text", ""))
    if not isinstance(text, str):
        text = str(text)
    time_val = request.get("time")
    if time_val is None:
        time_val = request.get("timestamp")
    meta = {
        k: v
        for k, v in request.items()
        if k not in ("message", "text", "time", "timestamp", "origin")
    }
    return InputEnvelope(
        text=text,
        time=time_val if isinstance(time_val, str) else None,
        origin=request.get("origin", request.get("client_id", "unknown")),
        metadata=meta,
        raw=request,
    )


def classify_dispatch(text: str) -> DispatchDecision:
    """Decide the high-level intent from content.

    Reuses QueryClassifier for the fine-grained sub-type, but adds the
    learn/train-vs-generate decision that the classifier alone does not make.
    Defaults to GENERATE so creative/unknown inputs still get a normal response
    (never silently dropped to fallback).
    """
    sub_type = "unknown"
    confidence = 0.0
    try:
        from ai.core.query_classifier import QueryClassifier

        result = QueryClassifier().classify(text)
        sub_type = result.primary_type.value
        confidence = result.confidence
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("QueryClassifier unavailable for dispatch: %s", exc)

    lowered = text.lower()
    if any(h in lowered for h in _TRAIN_HINTS):
        intent = DispatchIntent.TRAIN
        reason = "explicit training hint"
    elif any(h in lowered for h in _LEARN_HINTS):
        intent = DispatchIntent.LEARN
        reason = "explicit learning hint"
    else:
        intent = DispatchIntent.GENERATE
        reason = f"sub_type={sub_type}; default generate"

    return DispatchDecision(
        intent=intent, confidence=confidence, sub_type=sub_type, reason=reason
    )


def _priority_for(envelope: InputEnvelope, decision: DispatchDecision) -> float:
    """Higher = executed earlier in the training queue.

    Combines recency (a present ``time`` beats none) and classification
    confidence so more certain / more recent inputs train first.
    """
    prio = decision.confidence
    if envelope.time:
        prio += 0.25
    return round(prio, 4)


def plan_actions(
    envelope: InputEnvelope,
    decision: Optional[DispatchDecision] = None,
) -> List[Action]:
    """Map a dispatch decision to concrete actions.

    GENERATE -> FORWARD only. LEARN/TRAIN additionally append their action so a
    single input can both generate AND be learned/trained (multi-action set).
    """
    if decision is None:
        decision = classify_dispatch(envelope.text)
    actions: List[Action] = [Action(ActionType.FORWARD, {"text": envelope.text})]
    if decision.intent in (DispatchIntent.LEARN, DispatchIntent.TRAIN):
        actions.append(
            Action(
                ActionType.LEARN,
                {"text": envelope.text, "time": envelope.time},
            )
        )
    if decision.intent == DispatchIntent.TRAIN:
        actions.append(
            Action(
                ActionType.TRAIN,
                {
                    "domain": decision.sub_type or "general",
                    "sample": {"input": envelope.text, "time": envelope.time},
                    "priority": _priority_for(envelope, decision),
                },
            )
        )
    return actions


def dispatch(
    request: Dict[str, Any],
    training_coordinator: Optional[Any] = None,
    learn_fn: Optional[Any] = None,
) -> DispatchDecision:
    """Best-effort ingest dispatch.

    Builds the envelope, classifies, and performs the non-generative actions
    (enqueue training / call learn_fn) without ever raising into the caller's
    response path. Returns the decision for observability.
    """
    envelope = build_envelope(request)
    decision = classify_dispatch(envelope.text)
    try:
        actions = plan_actions(envelope, decision)
        for action in actions:
            if action.action is ActionType.TRAIN and training_coordinator is not None:
                training_coordinator.enqueue(
                    domain=action.payload.get("domain", "general"),
                    sample=action.payload.get("sample", {}),
                    priority=action.payload.get("priority", 0.0),
                )
            elif action.action is ActionType.LEARN and learn_fn is not None:
                learn_fn(action.payload)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Dispatch side-action failed (ignored): %s", exc, exc_info=True)
    return decision
