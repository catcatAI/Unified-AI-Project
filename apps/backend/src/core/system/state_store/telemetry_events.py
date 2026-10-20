# =============================================================================
# ANGELA-MATRIX: [L2] [β] [A] [L0]
# =============================================================================
"""
Telemetry-only CNS events — the documented orphan list.

WHY this file exists
--------------------
The CNS event bus (``core.system.state_store.global_store``) is a *public*
signal surface: a subsystem emits an event and anyone (the heartbeat, the
DLI, an external tool, a test) may subscribe. 26 events are emitted; only 5
have an in-process subscriber today, so 21 looked like "orphans" — events
nobody listens to.

They are not accidents:

* every one of them describes state that is *already* available through the
  state store's domains (routing, execution, lifecycle, meta, …), so a
  subscriber would be a second copy of the same fact; and
* they are the extension points the surrounding code documents as
  "reserved for external observers" (the WebSocket bridge, the CLI, tests).

Recording them here turns an opaque count into a reviewed list:

* ``check_fact_gates.py`` subtracts this list from the orphan scan, so the
  gate reports *unexplained* orphans (currently 0) instead of a raw number;
* the gate also asserts that every entry here is really emitted — a stale
  entry (an event that was removed) fails the gate, so the list cannot rot;
* adding a *new* event to this list is a visible act (it changes the
  reviewed count) rather than a silent one.

The list is the "decision preserved" record from
``docs/06-project-management/fixes/DEFINITIONS_AUDIT_2026-10-14.md`` (§已評估、
決策保留): the events stay, and the reason is written down.
"""

from __future__ import annotations

# event name -> why it has no in-process subscriber
TELEMETRY_ONLY_EVENTS: dict[str, str] = {
    "causal.learned": "因果學習結果：同樣的推論已在 causal_reasoning 的狀態裡，事件供外部觀察者使用",
    "causal.prediction": "因果預測：結果由預測引擎自身持有，事件供外部觀察者使用",
    "dli.feedback_processed": "DLI 回饋處理結果：已寫入生命狀態，事件供外部觀察者使用",
    "dli.state_changed": "DLI 狀態變化：生命週期 JSON 已同步，事件供外部觀察者使用",
    "essence.generational_bloom": "世代累積里程碑：已記在 LifeEssence，事件供外部觀察者使用",
    "essence.trace_recorded": "情緒軌跡：已寫入 LifeEssence，事件供外部觀察者使用",
    "execution.gate_decided": "閘門決策：已寫入 execution 狀態域，事件供外部觀察者使用",
    "execution.result_recorded": "執行結果：已寫入 execution 狀態域，事件供外部觀察者使用",
    "heartbeat.integration": "心跳整合資料：心跳自身持有，事件供外部觀察者使用",
    "heartbeat.pulse": "心跳脈衝：心跳自身持有，事件供外部觀察者使用",
    "intent.adjustment_computed": "意圖調整量：已寫入 intent 狀態域，事件供外部觀察者使用",
    "intent.homeostatic_generated": "意圖恆態建議：意圖模型自身持有，事件供外部觀察者使用",
    "intent.outcome_recorded": "意圖結果回饋：意圖模型自身持有，事件供外部觀察者使用",
    "lifecycle.behavioral_adjustment": "行為調整量：已寫入 lifecycle 狀態域，事件供外部觀察者使用",
    "lifecycle.interaction_recorded": "互動紀錄：已寫入 lifecycle 狀態域，事件供外部觀察者使用",
    "meta.closed_loop_adjusted": "閉環調整量：已寫入 meta 狀態域，事件供外部觀察者使用",
    "meta.confidence_recorded": "信心紀錄：已寫入 meta 狀態域，事件供外部觀察者使用",
    "meta.weighted_adjustment": "加權調整量：已寫入 meta 狀態域，事件供外部觀察者使用",
    "modality.gate_updated": "模態閘門狀態：已寫入 modality 狀態域，事件供外部觀察者使用",
    "routing.context_prepared": "路由上下文準備：已寫入 routing 狀態域，事件供外部觀察者使用",
    "routing.telemetry": "路由遙測：同一份資料已寫入 routing 狀態域的 steps 統計，事件供外部觀察者使用",
}

# The reviewed count (2026-10-14 的決策保留基線；只減不增，且每一筆都要有理由).
REVIEWED_TELEMETRY_EVENT_COUNT = len(TELEMETRY_ONLY_EVENTS)


def telemetry_event_names() -> frozenset[str]:
    """The event names that are intentionally without an in-process consumer."""
    return frozenset(TELEMETRY_ONLY_EVENTS)


__all__ = [
    "REVIEWED_TELEMETRY_EVENT_COUNT",
    "TELEMETRY_ONLY_EVENTS",
    "telemetry_event_names",
]
