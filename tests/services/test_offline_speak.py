# ANGELA-MATRIX: [L3] [βγ] [B] [L0-L11]
"""Offline-speak acceptance gate (2026-10-19).

不接外部 LLM 時，專案自帶棧（UNIFIED 引擎 + 確定性數學 + 知識庫 + 模板 +
honest refusal）必須「說點啥」：有意義的回答或誠實棄權。本組測試鎖定六類
離線病灶的修復，任一回歸即 fail：

  F1 OOD 統計票垃圾（"<q>=e"）   F2 假的系統操作確認   F8 身分 reflex
  F3 知識覆蓋（光合作用/沸點/哺乳動物…）               F4 應用題（單步）
  F5 情緒模板反向 + F10 雨天誤配   F6 翻譯吃到愛情模板   F7 笑話/薦書 salad
  F9 知識裸片段包句
"""

import asyncio
import re

import pytest

# ---------------------------------------------------------------------------
# 1. UNIFIED 引擎層：reflex / 確定性 / OOD 防垃圾
# ---------------------------------------------------------------------------


def _engine():
    from ai.unified_engine.unified_engine import UnifiedEngine

    return UnifiedEngine()


def test_offline_identity_and_micro_content():
    """F7/F8: 身分與微型內容由 reflex 單一源供應（免 checkpoint）。"""
    eng = _engine()
    assert "Angela" in eng.process("你是誰？")
    assert eng._last_route == "reflex"
    assert "Angela" in eng.process("Who are you?")
    assert "Oct 31" in eng.process("講個笑話")
    assert "小王子" in eng.process("推薦一本書")
    assert "Little Prince" in eng.process("recommend a book")


def test_offline_math_and_boolean_still_speak():
    """F1 不得誤傷確定性數學與布林層（布林走統計核心，參照
    test_unified_backend 的小樣本即訓即測）。"""
    eng = _engine()
    out = eng.process("15 * 27 + 8 = ?")
    assert "413" in out
    assert eng._last_route == "deterministic-math"
    eng.learn_batch(["1 and 0=true"] * 5)
    out = eng.process("1 and 0=?")
    assert "true" in out
    assert eng._last_route == "statistical-core"


def test_offline_ood_question_never_byte_garbage():
    """F1 回歸鎖：無限域問句走 echo（後端拒答 → 誠實鏈），
    絕不產出單字節 vote 垃圾（"光合作用是什麼？=e"）。"""
    eng = _engine()
    for q in ("光合作用是什麼？", "水的沸點是多少度？", "所有哺乳動物都會飛嗎？"):
        out = eng.process(q)
        assert out == q, f"expected honest echo for {q!r}, got {out!r}"
        assert eng._last_route == "none"


# ---------------------------------------------------------------------------
# 2. 知識層：策展事實 + 裸片段包句
# ---------------------------------------------------------------------------


def test_offline_knowledge_curated_facts():
    """F3: 五個 probe 空洞（光合作用/沸點/哺乳動物/地球繞星/單位換算）全有答。"""
    from ai.knowledge_base import route_knowledge

    assert "綠色植物" in (route_knowledge("光合作用是什麼？") or "")
    assert route_knowledge("水的沸點是多少度？") == "100"
    assert "蝙蝠" in (route_knowledge("所有哺乳動物都會飛嗎？") or "")
    assert "太陽" in (route_knowledge("地球繞著什麼星轉？") or "")
    assert route_knowledge("為什麼天空是藍的？") == "blue"
    assert "220" in (route_knowledge("100公斤等於幾磅？") or "")
    assert route_knowledge("Do all mammals fly?") is not None
    # 既有邊界不得回歸
    assert route_knowledge("WHAT COLOR IS THE SKY?") == "blue"
    assert route_knowledge("how many m in a km") is not None
    assert route_knowledge("Explain quantum entanglement") is None


def test_knowledge_fragments_wrapped_into_sentences():
    """F9: 短裸片段（blue/100）包成句子；長的策展答案原樣透過。"""
    from ai.knowledge_base import format_knowledge_answer

    assert format_knowledge_answer("blue", "為什麼天空是藍的？") == "顏色是藍色。"
    assert format_knowledge_answer("100", "水的沸點是多少度？") == "答案是 100。"
    assert format_knowledge_answer("blue", "what color is the sky?") == "The color is blue."
    assert format_knowledge_answer("7", "how many days?") == "The answer is 7."
    long = "綠色植物在陽光下把二氧化碳和水轉成養分並放出氧氣 / plants use sunlight, CO2"
    assert format_knowledge_answer(long, "光合作用是什麼？") == long


# ---------------------------------------------------------------------------
# 3. 應用題：單步可解 → 數字；歧義 → 誠實 None
# ---------------------------------------------------------------------------


def test_offline_word_problems_solve_or_decline():
    """F4: 單步應用題有答；打折/找零/多步一律拒答（錯算比不答糟）。"""
    from services.math_verifier import solve_word_problem

    assert solve_word_problem("一個西瓜35元，買4個要多少錢？") == 140.0
    assert solve_word_problem("西瓜35元買4個要多少錢？") == 140.0
    assert solve_word_problem("一箱蘋果有24顆，7箱共有幾顆？") == 168.0
    assert solve_word_problem("每箱24個，7箱共幾顆？") == 168.0
    assert solve_word_problem("若一件外套原價800元打七五折，售價是多少元？") is None
    assert solve_word_problem("瑪麗買了5支筆每支12元，付了100元，應找多少元？") is None
    assert solve_word_problem("今天天氣如何") is None
    assert solve_word_problem("15 * 27 + 8 = ?") is None  # 純算式交給 compute_arithmetic


# ---------------------------------------------------------------------------
# 4. 情緒/天氣模板方向
# ---------------------------------------------------------------------------


def test_offline_emotion_direction():
    """F5/F10: 負向心情 → 安慰模板（非喜悅）；雨天不拿到「出去走走」晴天文案。"""
    import services.llm.router as router_mod
    from ai.memory.template_library import get_template_library

    templates = get_template_library().get_all_templates()
    sad = router_mod._pick_relevant_template(templates, "我今天心情好差…")
    assert sad is not None and sad.id == "comfort_sad"
    joy = router_mod._pick_relevant_template(templates, "我好開心")
    assert joy is not None and joy.id == "comfort_joy"
    wx = router_mod._pick_relevant_template(templates, "你覺得雨天怎麼樣？")
    assert wx is not None
    assert "天氣確實不錯" not in wx.content
    assert "出去走走" not in wx.content


# ---------------------------------------------------------------------------
# 5. 執行閘：無可執行碼不問「要執行嗎」；真執行意圖保留確認
# ---------------------------------------------------------------------------


def test_offline_gate_never_confirms_nothing():
    """F2: 寫碼請求/定義問題 fall-through（離線接誠實拒答）；
    真執行意圖（執行 script.py）保留 confirm。"""
    from services.execution.gate_execution import GateExecutionOwner

    owner = GateExecutionOwner()
    out = asyncio.run(owner.process("幫我寫一支排序的程式碼", {}, "off-gate-1", None))
    assert out.action == "none"
    out = asyncio.run(owner.process("Python 是什麼語言？", {}, "off-gate-2", None))
    assert out.action == "none"
    out = asyncio.run(owner.process("執行 script.py", {}, "off-gate-3", None))
    assert out.action == "confirm"


# ---------------------------------------------------------------------------
# 6. 翻譯：模板層跳過 + 誠實 cannot-do（帶棄權信封）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_offline_translation_never_answers_love_template():
    """F6: 「翻譯：我愛你成英文」不得吃到 intimacy 模板「我也愛你！」。"""
    from core.interfaces.protocols import LLMResponse  # noqa: F401
    from services.llm.router import AngelaLLMService

    service = object.__new__(AngelaLLMService)
    assert service._template_layers_enabled("翻譯：我愛你成英文") is False
    assert service._template_layers_enabled("我愛你英文怎麼說？") is False

    resp = await service._fb_honest_refusal("翻譯：我愛你成英文", {}, False)
    assert resp is not None
    assert resp.model == "honest-cannot-do"
    assert resp.metadata["abstain"]["reason"] == "cannot_do"

    en = await service._fb_honest_refusal("What is quantum entanglement?", {}, True)
    assert en is not None
    assert en.model == "honest-no-answer"
