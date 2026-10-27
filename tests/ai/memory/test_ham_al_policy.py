"""Phase 2 item ④ — §10：retention/decay policy 在記憶層的執行與結果回報。

契約 §10 的完整往返：AL 輸出策略 → 記憶層執行 → ``submit_event`` 回報。
本檔釘住五件事：

1. **policy 真的執行進 metadata**：state 觀測 → ``al_retain_days`` /
   ``al_weight`` 戳記；``CONSOLIDATION`` → ``protected``。未觀測的量一個
   戳都不留（D11）；AL 缺席時照常存東西、不回報事件（記憶層不能因為
   AL 不在就存不下東西）。
2. **兩層分離**：caller 的 ``importance`` 原值不被改寫（panel 契約釘住
   0.42），AL 權重是獨立戳記，在保留決策點（``_entry_importance``）才
   乘進有效重要性 —— 內容評分與生命調制各自可取證。
3. **prune 接活**：``prune()``（30/90 天分層）在 2026-10-27 前生產零
   呼叫、只有測試在跑 —— 現在每次 ``store_experience`` 順帶執行，過期
   真的會掉，``mem_id`` 在 prune 前取（寫入位置，避免編號回撞）。
4. **執行優先序**：``protected`` 與 keep-floor（有效重要性 ≥ 0.7）先於
   policy TTL；壞戳記退預設 30/90 分層（一個壞值不該誤殺記憶）。
5. **結果事件是統計不是內容**：payload 只有 ``mem_id`` / ``applied`` /
   ``pruned``（§8 原始內容不進 AL）。
"""

import asyncio
import dataclasses
from datetime import datetime, timedelta, timezone

import pytest
from ai.memory.ham_memory.ham_manager import HAMMemoryManager
from core.life import al_state
from core.life.al_state import EventType

_BUCKET = "conversations"


@pytest.fixture(autouse=True)
def _clean_event_buffer():
    """事件緩衝是模組級共享狀態 — 清了才量得到本檔自己寫的事件。"""
    al_state.clear_events()
    yield
    al_state.clear_events()


@pytest.fixture
def ham(tmp_path):
    return HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)


def _patch_al(monkeypatch, **overrides):
    """把 ham 內部的 ``get_al_state()`` 指到受控快照。

    ham 在函式內 ``from ... import``，呼叫時解析 → patch 模組屬性有效。
    預設三個觀測欄全 ``None`` ＝ policy 全退基準（一個戳都不留）。
    """
    fields = dict(drift=None, intensity=None, life_phase=None)
    fields.update(overrides)
    snap = dataclasses.replace(al_state.get_al_state(), **fields)
    monkeypatch.setattr(al_state, "get_al_state", lambda: snap)


def _old_entry(days_old, importance, **meta_extra):
    """直接造一條帶年齡的記憶（種子用；模擬「以前存下的」）。"""
    stamp = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    meta = {"timestamp": stamp, "importance": importance, **meta_extra}
    return {"content": f"seed {days_old}d", "data_type": "conversation", "metadata": meta}


class TestPolicyExecutesIntoMetadata:
    def test_state_observation_stamps_retention_and_weight(self, ham, monkeypatch):
        _patch_al(monkeypatch, drift={"zeta": 0.5}, intensity=0.5)
        asyncio.run(ham.store_experience("note", "conversation"))
        meta = ham._data[_BUCKET][-1]["metadata"]
        assert meta["al_retain_days"] == pytest.approx(15.0)
        assert meta["al_weight"] == pytest.approx(1.0)
        assert "protected" not in meta

    def test_unobserved_policy_stamps_nothing(self, ham, monkeypatch):
        _patch_al(monkeypatch)  # 全未觀測
        asyncio.run(ham.store_experience("note", "conversation"))
        meta = ham._data[_BUCKET][-1]["metadata"]
        assert "al_retain_days" not in meta
        assert "al_weight" not in meta
        assert "protected" not in meta

    def test_caller_importance_survives_al_weight(self, ham, monkeypatch):
        # panel 契約（test_memory_recent_panel:69）：caller 的 0.42 原值保留
        _patch_al(monkeypatch, intensity=1.0)
        asyncio.run(ham.store_experience("note", "conversation", metadata={"importance": 0.42}))
        meta = ham._data[_BUCKET][-1]["metadata"]
        assert meta["importance"] == pytest.approx(0.42)
        assert meta["al_weight"] == pytest.approx(1.5)

    def test_consolidation_phase_protects_the_entry(self, ham, monkeypatch):
        _patch_al(monkeypatch, life_phase="CONSOLIDATION", drift={"zeta": 1.0})
        asyncio.run(ham.store_experience("keepsake", "conversation"))
        meta = ham._data[_BUCKET][-1]["metadata"]
        assert meta["protected"] is True
        assert meta["al_retain_days"] == pytest.approx(3.0)  # drift 拉滿 → 10% 地板

    def test_al_absent_stores_plain_and_reports_nothing(self, ham, monkeypatch):
        def boom():
            raise RuntimeError("AL snapshot offline")

        monkeypatch.setattr(al_state, "get_al_state", boom)
        mid = asyncio.run(ham.store_experience("note", "conversation"))
        assert mid, "AL 不在也必須存得下"
        meta = ham._data[_BUCKET][-1]["metadata"]
        assert "al_retain_days" not in meta
        assert "al_weight" not in meta
        assert "protected" not in meta
        assert al_state.recent_events() == [], "沒套用 policy 就沒結果可回報"


class TestPruneRunsOnStore:
    """prune() 斷線多年的修復：生產呼叫點接上 store 路徑（item ④）。"""

    def test_store_prunes_stale_entries_and_reports_stats(self, ham, monkeypatch):
        _patch_al(monkeypatch)  # policy 不摻入 → 純預設規則
        ham._data[_BUCKET] = [_old_entry(200, 0.1) for _ in range(10)]
        ham._data[_BUCKET] += [_old_entry(1, 0.5) for _ in range(50)]
        # 61 筆 → prune 清 10 筆過期 → 51；mem_id 在 prune 前取（寫入位置）
        mid = asyncio.run(ham.store_experience("newest", "conversation"))
        assert mid == "exp_61"
        assert len(ham._data[_BUCKET]) == 51
        assert ham._data[_BUCKET][-1]["content"] == "newest"

        events = al_state.recent_events()
        assert len(events) == 1
        payload = events[-1]["payload"]
        assert payload["mem_id"] == "exp_61"
        assert payload["pruned"] == {"templates": 0, "conversations": 10}

    def test_policy_ttl_replaces_default_tiers(self, ham, monkeypatch):
        # 戳記 al_retain_days=1 → 5 天舊記憶就該掉（預設 90 天層不會）
        _patch_al(monkeypatch)
        ham._data[_BUCKET] = [_old_entry(5, 0.5, al_retain_days=1.0) for _ in range(10)]
        ham._data[_BUCKET] += [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        assert len(ham._data[_BUCKET]) == 51
        assert not any(
            e["metadata"].get("al_retain_days") == 1.0 for e in ham._data[_BUCKET]
        ), "TTL 到期的戳記記憶必須被清掉"

    def test_default_tiers_still_apply_without_stamp(self, ham, monkeypatch):
        # 對照組：同一種 5 天舊記憶、沒戳記 → 90 天層 → 保留（D11）
        _patch_al(monkeypatch)
        ham._data[_BUCKET] = [_old_entry(5, 0.5) for _ in range(10)]
        ham._data[_BUCKET] += [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        assert len(ham._data[_BUCKET]) == 61

    def test_keep_floor_beats_policy_ttl(self, ham, monkeypatch):
        # 有效重要性 ≥ 0.7 → TTL 再短也保留（keep-floor 先判）
        _patch_al(monkeypatch)
        keepers = [_old_entry(400, 0.9, al_retain_days=1.0) for _ in range(10)]
        ham._data[_BUCKET] = keepers + [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        assert len(ham._data[_BUCKET]) == 61

    def test_protected_beats_policy_ttl(self, ham, monkeypatch):
        # 固化（protected）不論年齡與 TTL 都保留
        _patch_al(monkeypatch)
        seeds = [_old_entry(400, 0.1, protected=True, al_retain_days=1.0) for _ in range(3)]
        ham._data[_BUCKET] = seeds + [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        assert len(ham._data[_BUCKET]) == 54

    def test_broken_ttl_stamp_falls_back_to_default_tiers(self, ham, monkeypatch):
        # 壞戳記 → 退 30/90 分層：imp 0.5（90 層）、5 天 → 活
        _patch_al(monkeypatch)
        broken = [_old_entry(5, 0.5, al_retain_days="garbage") for _ in range(10)]
        ham._data[_BUCKET] = broken + [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        assert len(ham._data[_BUCKET]) == 61


class TestEffectiveImportance:
    """``al_weight`` 只在保留決策點生效，不改寫 caller 原評分。"""

    def test_weight_scales_the_effective_score(self):
        entry = {"metadata": {"importance": 0.6, "al_weight": 0.4}}
        assert HAMMemoryManager._entry_importance(entry) == pytest.approx(0.24)

    def test_without_weight_it_is_the_plain_score(self):
        entry = {"metadata": {"importance": 0.6}}
        assert HAMMemoryManager._entry_importance(entry) == pytest.approx(0.6)

    def test_effective_score_is_clamped_to_unit(self):
        entry = {"metadata": {"importance": 1.2, "al_weight": 1.5}}
        assert HAMMemoryManager._entry_importance(entry) == pytest.approx(1.0)

    def test_bad_weight_falls_back_to_plain_score(self):
        entry = {"metadata": {"importance": 0.6, "al_weight": "nonsense"}}
        assert HAMMemoryManager._entry_importance(entry) == pytest.approx(0.6)

    def test_weight_switches_the_retention_tier(self, ham, monkeypatch):
        # 有效 0.6 → 90 天層（60 天還活著）；×0.4 → 0.24 < 0.3 → 30 天層（掉）
        _patch_al(monkeypatch)
        ham._data[_BUCKET] = [_old_entry(60, 0.6, al_weight=0.4) for _ in range(10)]
        ham._data[_BUCKET] += [_old_entry(60, 0.6) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        weighted_left = sum(1 for e in ham._data[_BUCKET] if "al_weight" in e["metadata"])
        assert weighted_left == 0, "低權重記憶掉進 30 天層 → 60 天就該死"
        assert len(ham._data[_BUCKET]) == 51


class TestResultEvent:
    def test_reports_statistics_not_content(self, ham, monkeypatch):
        _patch_al(monkeypatch, drift={"zeta": 0.5}, intensity=0.7)
        asyncio.run(ham.store_experience("TOP SECRET diary line", "conversation"))
        events = al_state.recent_events()
        assert len(events) == 1
        record = events[0]
        assert record["type"] == EventType.MEMORY_RESULT.value
        assert isinstance(record["at"], float)

        payload = record["payload"]
        assert set(payload) == {"mem_id", "applied", "pruned"}
        assert payload["applied"]["policy"]["source"] == {
            "retention": "state",
            "weight": "state",
            "consolidate": "default",
        }
        assert payload["applied"]["stamped"]["al_retain_days"] == pytest.approx(15.0)
        assert "TOP SECRET" not in str(payload), "§8：原始內容不進 AL"

    def test_no_event_when_policy_unavailable(self, ham, monkeypatch):
        def boom():
            raise RuntimeError("offline")

        monkeypatch.setattr(al_state, "get_al_state", boom)
        asyncio.run(ham.store_experience("note", "conversation"))
        assert al_state.recent_events() == []

    def test_stores_without_stamping_still_reports_prune_only(self, ham, monkeypatch):
        # 全未觀測 → applied.policy 存在但 stamped 空；事件仍回報 prune 統計
        _patch_al(monkeypatch)
        ham._data[_BUCKET] = [_old_entry(200, 0.1) for _ in range(10)]
        ham._data[_BUCKET] += [_old_entry(1, 0.5) for _ in range(50)]
        asyncio.run(ham.store_experience("newest", "conversation"))
        payload = al_state.recent_events()[-1]["payload"]
        assert payload["applied"]["stamped"] == {}
        assert payload["applied"]["policy"]["source"]["retention"] == "default"
        assert payload["pruned"] == {"templates": 0, "conversations": 10}
