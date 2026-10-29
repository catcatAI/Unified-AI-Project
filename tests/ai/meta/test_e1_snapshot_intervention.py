# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E1 干預測試（嚴格版）：固定同一段文本、**只動快照欄位**。

Phase 2「驗」段的 E1 原文：「固定同一段文本、只動 snapshot 欄位，看
``resolved_by`` 是否指名到對應 voter、行為是否可重複翻轉」。Phase 3 item
3 之前 9 個 voter 全讀散落的 context 鍵（``heartbeat_health`` /
``dli_state``），只動快照欄位**必紅** —— 本檔是該項交付後的證據位：

- 干預面只有 ``context["al_state"]`` 的欄位；``user_text`` 逐字固定。
- 每個干預場景都斷言 ``resolved_by`` 指名到**對應**那個 voter。
- 三跑一致，否則 H1（狀態 → 行為）不成立。
- 文字對照組：換文本不動快照 → 模式不變（翻轉只能來自狀態，
  不是提示詞裝飾）。
"""

from __future__ import annotations

from ai.meta.priority_negotiator import (
    PriorityNegotiator,
    dli_state_voter,
    heartbeat_voter,
    lifecycle_voter,
)

# 干預全程固定的文本（voter 不讀它 —— 對照組釘住這一點）。
FIXED_TEXT = "你今天好嗎"

# 固定不動的第三票（lifecycle）：兩個干預場景下它必須保持同一票，
# 才能證明翻轉只來自被動的那個快照欄位。
BASELINE_LC = {
    "routing_mode": "exploratory",
    "response_style": "neutral",
    "confidence": 0.5,
}


def _negotiator() -> PriorityNegotiator:
    negotiator = PriorityNegotiator()
    negotiator.register_voter("heartbeat", heartbeat_voter)
    negotiator.register_voter("dli_state", dli_state_voter)
    negotiator.register_voter("lifecycle", lifecycle_voter)
    return negotiator


def _context(health: float | None, life_cycle_state: str | None = None) -> dict:
    """文本逐字固定；唯一干預面是 ``al_state`` 的欄位。"""
    al_state: dict = {"health": health}
    if life_cycle_state is not None:
        al_state["life_cycle_state"] = life_cycle_state
    return {
        "user_text": FIXED_TEXT,
        "al_state": al_state,
        "lifecycle_behavior": dict(BASELINE_LC),
    }


def _resolve_x3(context: dict) -> list[dict]:
    """同一 context 跑三輪 —— H1 要求翻轉可重複。"""
    negotiator = _negotiator()
    return [negotiator.resolve(dict(context)) for _ in range(3)]


class TestHealthFieldIntervention:
    """只動 ``al_state["health"]``：對應 voter = heartbeat。"""

    def test_low_health_flips_to_conservative(self) -> None:
        calm = _negotiator().resolve(_context(0.9))
        crisis = _negotiator().resolve(_context(0.1))
        assert calm["routing_mode"] == "exploratory"  # 只有 baseline 投 mode
        assert crisis["routing_mode"] == "conservative"
        # resolved_by 指名到動那個欄位對應的 voter
        assert calm["resolved_by"] == "heartbeat"
        assert crisis["resolved_by"] == "heartbeat"

    def test_flip_is_repeatable(self) -> None:
        low = {r["routing_mode"] for r in _resolve_x3(_context(0.1))}
        high = {r["routing_mode"] for r in _resolve_x3(_context(0.9))}
        assert low == {"conservative"}
        assert high == {"exploratory"}

    def test_unobserved_health_abstains(self) -> None:
        """D11：``health=None``（未觀測）→ heartbeat 弃權，不拿預設投票。"""
        result = _negotiator().resolve(_context(None))
        assert "heartbeat" not in result["voter_contributions"]


class TestLifeCycleStateFieldIntervention:
    """只動 ``al_state["life_cycle_state"]``：對應 voter = dli_state。"""

    def test_dormant_vs_mature_flips_mode(self) -> None:
        # health 固定 0.5（heartbeat 中立、不投 mode）→ 動的只有 DLI 欄位
        dormant = _negotiator().resolve(_context(0.5, "DORMANT"))
        mature = _negotiator().resolve(_context(0.5, "MATURE"))
        assert dormant["routing_mode"] == "conservative"
        assert mature["routing_mode"] == "exploratory"
        assert dormant["resolved_by"] == "dli_state"
        assert mature["resolved_by"] == "dli_state"

    def test_flip_is_repeatable(self) -> None:
        dormant = {r["routing_mode"] for r in _resolve_x3(_context(0.5, "DORMANT"))}
        mature = {r["routing_mode"] for r in _resolve_x3(_context(0.5, "MATURE"))}
        assert dormant == {"conservative"}
        assert mature == {"exploratory"}


class TestTextControl:
    """文字對照組：同一快照、換五種說法 → 模式不翻（狀態效應 > 文本效應）。"""

    TEXTS = ["你今天好嗎", "今天天氣如何", "幫我查個資料", "說個笑話", "最近如何"]

    def test_rewritten_texts_do_not_flip_mode(self) -> None:
        negotiator = _negotiator()
        modes = set()
        for text in self.TEXTS:
            context = _context(0.1)
            context["user_text"] = text
            modes.add(negotiator.resolve(context)["routing_mode"])
        assert modes == {"conservative"}


class TestProductionInjection:
    """生產路徑：router 注入的就是那一份快照，散落鍵已除名。"""

    @staticmethod
    def _bare_router():
        from services.llm.router import AngelaLLMService

        router = object.__new__(AngelaLLMService)
        router.meta_controller = None
        return router

    def test_negotiator_signals_inject_al_state_only(self) -> None:
        from core.life.al_state import AL_STATE_VERSION

        context: dict = {}
        self._bare_router()._inject_negotiator_signals(context)
        assert "al_state" in context
        assert context["al_state"]["version"] == AL_STATE_VERSION
        # Phase 3 item 3 除名的散落鍵 —— AL 狀態只經快照交換
        assert "heartbeat_health" not in context
        assert "dli_state" not in context

    def test_production_negotiator_flips_on_snapshot_field(self) -> None:
        """用 router 真註冊的 9 voter + 真權重跑同一組干預。"""
        from services.llm.router import _negotiator as router_negotiator

        def context(health: float) -> dict:
            return {
                "user_text": FIXED_TEXT,
                "al_state": {"health": health, "life_cycle_state": "MATURE"},
            }

        calm = router_negotiator.resolve(context(0.9))
        crisis = router_negotiator.resolve(context(0.1))
        assert calm["routing_mode"] == "exploratory"  # 只有 dli 投 mode
        assert crisis["routing_mode"] == "conservative"
        assert calm["resolved_by"] == "heartbeat"
        assert crisis["resolved_by"] == "heartbeat"
