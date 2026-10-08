# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E1 干預測試：固定文本、只動連續狀態，看路由跟不跟著走。

這是 H1 的證據位：同一段文本逐字相同，狀態鍵變化導致路由翻轉且可重複，
翻轉只能來自狀態（voter 根本不讀原文），不是提示詞裝飾。
"""

from __future__ import annotations

from ai.meta.priority_negotiator import (
    PriorityNegotiator,
    heartbeat_voter,
    lifecycle_voter,
)

# 干預全程固定的文本（voter 不讀它——這正是要證明的點）。
FIXED_TEXT = "你今天好嗎"


def _negotiator() -> PriorityNegotiator:
    negotiator = PriorityNegotiator()
    negotiator.register_voter("heartbeat", heartbeat_voter)
    negotiator.register_voter("lifecycle", lifecycle_voter)
    return negotiator


def _context(user_text: str, health: float, mode: str | None, confidence: float) -> dict:
    context: dict = {"user_text": user_text}
    context["heartbeat_health"] = {"system_health": health}
    if mode is not None:
        context["lifecycle_behavior"] = {
            "routing_mode": mode,
            "response_style": "neutral",
            "confidence": confidence,
        }
    return context


def test_state_flip_with_text_fixed() -> None:
    """calm→exploratory、crisis→conservative，文本逐字相同。"""
    negotiator = _negotiator()
    calm = negotiator.resolve(_context(FIXED_TEXT, 0.9, "exploratory", 0.9))
    crisis = negotiator.resolve(_context(FIXED_TEXT, 0.1, "exploratory", 0.9))
    assert calm["routing_mode"] == "exploratory"
    assert crisis["routing_mode"] == "conservative"
    assert calm["routing_mode"] != crisis["routing_mode"]
    assert crisis["resolved_by"] == "heartbeat"


def test_flip_is_repeatable() -> None:
    """翻轉可重複（三跑一致），否則 H1 不成立。"""
    negotiator = _negotiator()
    modes = {
        negotiator.resolve(_context(FIXED_TEXT, 0.1, "exploratory", 0.9))["routing_mode"]
        for _ in range(3)
    }
    assert modes == {"conservative"}


def test_single_voter_failure_does_not_kill_resolution() -> None:
    """單 voter 抛錯不殺整輪（resolve 內建 fail-open，此處釘選）。"""

    def _boom(_context: dict):
        raise RuntimeError("voter boom")

    negotiator = _negotiator()
    negotiator.register_voter("broken", _boom)
    result = negotiator.resolve(_context(FIXED_TEXT, 0.9, "exploratory", 0.9))
    assert result["routing_mode"] == "exploratory"
