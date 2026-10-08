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
    """單 voter 拋錯不殺整輪（resolve 內建 fail-open，此處釘選）。"""

    def _boom(_context: dict):
        raise RuntimeError("voter boom")

    negotiator = _negotiator()
    negotiator.register_voter("broken", _boom)
    result = negotiator.resolve(_context(FIXED_TEXT, 0.9, "exploratory", 0.9))
    assert result["routing_mode"] == "exploratory"


def test_router_voter_weights_default_unchanged() -> None:
    """E1 後續：權重可配置化，但預設值與歷史常數一致（行為不變）。"""
    from services.llm.router import _negotiator as router_negotiator

    expected = {
        "lifecycle": 0.8,
        "emotional": 0.7,
        "intent": 0.6,
        "angela_emotion": 0.9,
        "causal": 0.5,
        "meta_calibration": 0.4,
        "heartbeat": 0.3,
        "dli_state": 0.4,
    }
    for name, weight in expected.items():
        assert router_negotiator._weight_fns[name]({}) == weight


class TestRoutingConsistencyPairs:
    """E2 路由層配對實驗（H2 的路由層類比）：多輪一致性由狀態決定。

    同一追問意圖、每輪 incidental 文字都不同：狀態保持組應全輪同模，
    狀態擾動組應翻轉。一致性 = 與首輪同模的輪次佔比。
    """

    TEXTS = ["你今天好嗎", "今天天氣如何", "幫我查個資料", "說個笑話", "最近如何"]

    def _run_turns(self, healths: list) -> list:
        negotiator = _negotiator()
        modes = []
        for i, health in enumerate(healths):
            context = _context(self.TEXTS[i % len(self.TEXTS)], health, "exploratory", 0.9)
            modes.append(negotiator.resolve(context)["routing_mode"])
        return modes

    @staticmethod
    def _consistency(modes: list) -> float:
        first = modes[0]
        return sum(1 for m in modes if m == first) / len(modes)

    def test_texts_actually_vary(self) -> None:
        """配對非空轉：各輪 incidental 文字確實不同。"""
        assert len(set(self.TEXTS)) > 1

    def test_hold_state_holds_mode(self) -> None:
        modes = self._run_turns([0.9] * 6)
        assert self._consistency(modes) == 1.0
        assert set(modes) == {"exploratory"}

    def test_perturbed_state_breaks_mode(self) -> None:
        modes = self._run_turns([0.9, 0.1] * 3)
        assert self._consistency(modes) < 1.0
        assert "conservative" in modes

    def test_hold_beats_perturbed_adjudicated(self) -> None:
        """H3 聯合判定的一半：保持組一致性嚴格高於擾動組（解讀器裁決）。"""
        from core.facts import Fact, adjudicate

        hold = self._consistency(self._run_turns([0.9] * 6))
        perturbed = self._consistency(self._run_turns([0.9, 0.1] * 3))
        report = adjudicate(
            [
                Fact("e2.hold_consistency", hold, 1.0, "ge", "ratio", "E2-pairs", ""),
                Fact(
                    "e2.hold_minus_perturbed",
                    hold - perturbed,
                    0.0,
                    "ge",
                    "ratio",
                    "E2-pairs",
                    f"hold={hold} perturbed={perturbed}",
                ),
            ]
        )
        assert report.ok is True, report.summary()


class TestPromptRewriteControl:
    """提示詞改寫對照組：同狀態下換五種說法，路由不應翻轉。

    路由層 voter 不讀原文——此處釘選該性質：文字變異效應為零，
    狀態變異效應為全翻轉（H3：狀態效應 > 文本效應，在路由層成立）。
    """

    def test_rewritten_prompts_do_not_flip_mode(self) -> None:
        negotiator = _negotiator()
        modes = {
            negotiator.resolve(_context(text, 0.9, "exploratory", 0.9))["routing_mode"]
            for text in TestRoutingConsistencyPairs.TEXTS
        }
        assert modes == {"exploratory"}

    def test_h3_joint_verdict(self) -> None:
        """H3 聯合裁決：狀態翻轉成立 + 文本對照成立 + E2 配對成立，三合一。"""
        from core.facts import Fact, adjudicate, merge_reports

        negotiator = _negotiator()
        flip = negotiator.resolve(_context(FIXED_TEXT, 0.1, "exploratory", 0.9))
        flip_ok = flip["routing_mode"] == "conservative"
        pairs = TestRoutingConsistencyPairs()
        hold = pairs._consistency(pairs._run_turns([0.9] * 6))
        control_modes = {
            negotiator.resolve(_context(t, 0.9, "exploratory", 0.9))["routing_mode"]
            for t in pairs.TEXTS
        }
        report = merge_reports(
            adjudicate([Fact("h1.state_flips_mode", float(flip_ok), 1.0, "ge", "bool", "E1", "")]),
            adjudicate([Fact("h2.hold_consistent", hold, 1.0, "ge", "ratio", "E2", "")]),
            adjudicate(
                [
                    Fact(
                        "h3.text_control_stable",
                        float(len(control_modes)),
                        1.0,
                        "le",
                        "modes",
                        "control",
                        f"modes={sorted(control_modes)}",
                    )
                ]
            ),
        )
        assert report.ok is True, report.summary()
        assert len(report.verdicts) == 3
