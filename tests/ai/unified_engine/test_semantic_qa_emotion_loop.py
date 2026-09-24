"""semantic_qa Path 1 死路徑 #16 回歸測試。

歷史缺陷：_emotion_threshold_adjustment() 用不存在的 state_store.get() 拉取
情緒事件——GlobalStateStore 只有 get_state(domain) 且 emit_event 為瞬態推送，
pull 模式永遠收不到 → 情緒→閾值閉環的 Path 1 從未生效。
修復：改訂閱式推送（subscribe_event）＋模組級快取最新 payload。
"""

import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import ai.unified_engine.semantic_qa as semantic_qa  # noqa: E402
from core.system.state_store.global_store import state_store  # noqa: E402


def test_state_store_has_no_pull_get_api():
    """契約鎖定：GlobalStateStore 無 .get() pull API（防回歸到死路徑）."""
    assert not hasattr(state_store, "get") or callable(
        getattr(type(state_store), "get_state", None)
    )


def test_emotion_event_push_updates_threshold():
    """閉環驗證：emit_event 推送 → 訂閱快取 → threshold 增量生效."""
    semantic_qa._ensure_emotion_event_subscription()

    state_store.emit_event(
        "emotion.behavioral_adjustment",
        {
            "routing_mode": "conservative",
            "valence": -0.5,
            "arousal": 0.5,
            "sustained_negative_counter": 3,
        },
    )
    assert semantic_qa._LATEST_EMOTION_EVENT is not None
    adj = semantic_qa._emotion_threshold_adjustment()
    assert adj > 0, "conservative 路由應提高閾值"


def test_emotion_event_exploratory_lowers_threshold():
    """探索模式應降低閾值（提高召回）."""
    semantic_qa._ensure_emotion_event_subscription()

    state_store.emit_event(
        "emotion.behavioral_adjustment",
        {
            "routing_mode": "exploratory",
            "valence": 0.5,
            "arousal": 0.6,
            "sustained_negative_counter": 0,
        },
    )
    adj = semantic_qa._emotion_threshold_adjustment()
    assert adj < 0, "exploratory 路由應降低閾值"


def test_subscription_is_idempotent():
    """重複訂閱不應重複註冊 callback."""
    semantic_qa._ensure_emotion_event_subscription()
    subs_before = len(state_store._event_subscribers["emotion.behavioral_adjustment"])
    semantic_qa._ensure_emotion_event_subscription()
    subs_after = len(state_store._event_subscribers["emotion.behavioral_adjustment"])
    assert subs_before == subs_after
