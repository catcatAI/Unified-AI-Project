# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [A] [L4]
# =============================================================================
"""
Phase 13 (REFACTOR_PLAN §13): adaptive main-line dispatch tests.

Verifies the ingest-time, content-driven routing decision: a mod that submits
only text + time is judged by content (GENERATE / LEARN / TRAIN) rather than
forced down a single "produce a response" path, and training is queued with
priority (sorted execution).
"""

from ai.core.training_coordinator import TrainingCoordinator
from services.mainline_dispatcher import (
    ActionType,
    DispatchIntent,
    build_envelope,
    classify_dispatch,
    dispatch,
    plan_actions,
)


def test_build_envelope_binds_time():
    env = build_envelope({"text": "寫一段故事", "time": "08/12,18:30"})
    assert env.text == "寫一段故事"
    assert env.time == "08/12,18:30"


def test_build_envelope_accepts_message_and_timestamp():
    env = build_envelope({"message": "hi", "timestamp": "x"})
    assert env.text == "hi"
    assert env.time == "x"


def test_classify_creative_is_generate():
    # The user's motivating example: a creative prompt must route to GENERATE
    # (FORWARD) and never be silently dropped to fallback.
    dec = classify_dispatch("你作為例中的用戶來編寫，寫一段故事")
    assert dec.intent is DispatchIntent.GENERATE


def test_classify_learn_hint():
    dec = classify_dispatch("請記住這個事實：地球是圓的")
    assert dec.intent is DispatchIntent.LEARN


def test_classify_train_hint():
    dec = classify_dispatch("訓練這個對話模式")
    assert dec.intent is DispatchIntent.TRAIN


def test_plan_actions_generate_only_forward():
    env = build_envelope({"text": "寫一段故事", "time": "08/12,18:30"})
    actions = plan_actions(env)
    assert actions[0].action is ActionType.FORWARD
    assert all(a.action is ActionType.FORWARD for a in actions)


def test_plan_actions_train_is_multi_action():
    env = build_envelope({"text": "訓練這個模式", "time": "08/12,18:30"})
    actions = plan_actions(env, response_text="好，我會記住這個模式。")
    types = {a.action for a in actions}
    assert ActionType.FORWARD in types
    assert ActionType.LEARN in types
    assert ActionType.TRAIN in types


def test_plan_actions_omits_train_without_a_response():
    """A training sample needs the assistant's reply to be learnable.

    The old contract emitted TRAIN with {"input": …, "time": …} only, so the
    queue filled with rows no trainer could act on. See
    tests/ai/core/test_training_processors.py for the full contract.
    """
    env = build_envelope({"text": "訓練這個模式", "time": "08/12,18:30"})
    types = {a.action for a in plan_actions(env)}
    assert ActionType.TRAIN not in types


def test_dispatch_attaches_intent():
    dec = dispatch({"text": "寫一段故事", "time": "08/12,18:30"})
    assert dec.intent is DispatchIntent.GENERATE


def test_training_priority_queue_orders_execution():
    tc = TrainingCoordinator()
    tc.enqueue("general", {"input": "low"}, priority=0.1)
    tc.enqueue("general", {"input": "high"}, priority=0.9)
    tc.enqueue("general", {"input": "mid"}, priority=0.5)
    drained = tc.drain_priority_queue()
    assert [d["sample"]["input"] for d in drained] == ["high", "mid", "low"]
    assert tc.pending_training_count() == 0


def test_dispatch_leaves_training_work_for_coordinator_owner():
    tc = TrainingCoordinator()

    decision = dispatch(
        {"text": "訓練這個模式"},
        training_coordinator=tc,
        response_text="好，我會記住這個模式。",
    )

    assert decision.intent is DispatchIntent.TRAIN
    assert tc.pending_training_count() == 1


def test_dispatch_skips_untrainable_sample():
    tc = TrainingCoordinator()

    decision = dispatch({"text": "訓練這個模式"}, training_coordinator=tc)

    assert decision.intent is DispatchIntent.TRAIN
    assert tc.pending_training_count() == 0, "input-only samples must not be queued"
