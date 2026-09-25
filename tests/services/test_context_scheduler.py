"""長程一致性上下文排程器測試：分配計畫＋消化＋帳本一致性＋整合守門。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from services.llm.context_scheduler import (
    ContextLedger,
    ContextScheduler,
    get_context_scheduler,
)
from services.llm.prompt_builder import estimate_tokens


def _sys(content: str) -> Dict[str, str]:
    return {"role": "system", "content": content}


def _msg(role: str, content: str) -> Dict[str, str]:
    return {"role": role, "content": content}


# ---------- 分配計畫 ----------


class TestQueryPreprocessingPlan:
    def test_identity_is_planned_llm_first(self):
        from ai.core.query_classifier import ROUTE_LLM_FIRST

        plan = ContextScheduler().plan_query("自我介紹一下")
        assert plan.route_hint == ROUTE_LLM_FIRST
        assert plan.allow_context_enrichment is False
        assert plan.allow_knowledge_pipeline is False
        assert plan.allow_specialized_agents is False

    def test_capability_is_planned_for_runtime_catalog(self):
        from ai.core.query_classifier import ROUTE_CAPABILITY_CATALOG

        plan = ContextScheduler().plan_query("你有啥能力？")
        assert plan.route_hint == ROUTE_CAPABILITY_CATALOG
        assert plan.allow_knowledge_pipeline is False

    def test_deterministic_request_keeps_local_knowledge_enabled(self):
        plan = ContextScheduler().plan_query("1+1等于多少")
        assert plan.route_hint == "balanced"
        assert plan.allow_context_enrichment is True
        assert plan.allow_knowledge_pipeline is True
        assert plan.allow_specialized_agents is True

    def test_explicit_definition_keeps_knowledge_pipeline_enabled(self):
        plan = ContextScheduler().plan_query("高興的意思")
        assert plan.route_hint == "balanced"
        assert plan.allow_knowledge_pipeline is True

    def test_ambiguous_short_text_does_not_enable_dictionary_shortcut(self):
        plan = ContextScheduler().plan_query("嗯嗯")
        assert plan.route_hint == "balanced"
        assert plan.allow_knowledge_pipeline is False

    def test_plan_is_written_to_shared_context(self):
        context: Dict[str, Any] = {}
        plan = ContextScheduler().plan_query("自我介紹一下", context)
        assert context["_preprocessing_plan"] == plan.to_dict()


class TestAllocationPlan:
    def test_protects_system_and_final_user(self):
        scheduler = ContextScheduler()
        messages = [
            _sys("核心提示"),
            _msg("user", "區塊A " + "x" * 100),
            _msg("assistant", "區塊B " + "y" * 100),
            _msg("user", "最終問題"),
        ]
        plan = scheduler.build_plan(messages, budget_tokens=500)
        assert plan.protected_indices == [0, 3]
        assert plan.digested_indices == [1, 2]
        assert plan.chunks, "中段應被分塊"

    def test_chunks_respect_worker_window(self):
        scheduler = ContextScheduler()
        messages = [_sys("S")]
        for i in range(10):
            messages.append(_msg("user", f"訊息{i} " + "x" * 600))  # 各約 150+ tokens
        messages.append(_msg("user", "final"))
        plan = scheduler.build_plan(messages, budget_tokens=10000)
        assert len(plan.chunks) >= 2
        for chunk in plan.chunks:
            assert chunk.tokens <= 1000  # 單塊不超過工作者視窗（800）＋單則餘裕

    def test_no_middle_messages_no_chunks(self):
        scheduler = ContextScheduler()
        messages = [_sys("S"), _msg("user", "直接問題")]
        plan = scheduler.build_plan(messages, budget_tokens=100)
        assert plan.chunks == []
        assert plan.digested_indices == []


# ---------- 同步消化 ----------


class TestSyncDigest:
    def _oversized(self) -> List[Dict]:
        messages = [_sys("核心提示" * 5)]
        for i in range(6):
            messages.append(_msg("user", f"[Block {i}] 標題行\n" + "內容描述" * 80))
        messages.append(_msg("user", "<user_message>請回答</user_message>"))
        return messages

    def test_digest_replaces_middle_with_bounded_block(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        messages = self._oversized()
        before_middle = len(messages) - 2
        result = scheduler.digest_overflow_sync(messages, 3000, "conv1")
        assert result["digested"] == before_middle
        assert result["freed_chars"] > 0
        # 中段變成單一消化訊息
        middle = messages[1:-1]
        assert len(middle) == 1
        assert "[Digested Context]" in middle[0]["content"]
        assert estimate_tokens(middle[0]["content"]) <= 350

    def test_not_worth_digesting_when_already_small(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        messages = [_sys("S"), _msg("user", "短短的中段"), _msg("user", "final")]
        result = scheduler.digest_overflow_sync(messages, 3000, "conv1")
        assert result["digested"] == 0
        assert len(messages) == 3  # 原樣不動

    def test_ledger_cache_makes_repeat_digest_consistent(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        messages1 = self._oversized()
        scheduler.digest_overflow_sync(messages1, 3000, "conv1")
        digest1 = messages1[1]["content"]

        messages2 = self._oversized()  # 同內容重來
        scheduler.digest_overflow_sync(messages2, 3000, "conv1")
        digest2 = messages2[1]["content"]
        # 同內容 → 帳本快取命中 → 摘要一致（長程一致性核心保證）
        assert digest1 == digest2
        assert scheduler.stats()["cache_hits"] >= 1

    def test_different_conversations_independent_turns(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        t1 = scheduler.ledger.next_turn("convA")
        t2 = scheduler.ledger.next_turn("convB")
        t1_again = scheduler.ledger.next_turn("convA")
        assert t1 == 1 and t2 == 1 and t1_again == 2


# ---------- 帳本持久化（跨重啟一致性） ----------


class TestLedgerPersistence:
    def test_survives_restart(self, tmp_path: Path):
        ledger_dir = tmp_path / "ledger"
        ledger1 = ContextLedger(ledger_dir)
        ledger1.next_turn("conv1")
        ledger1.cache_put("conv1", "hash123", "摘要內容")
        ledger1.save()

        ledger2 = ContextLedger(ledger_dir)  # 模擬重啟
        assert ledger2.next_turn("conv1") == 2
        assert ledger2.cache_get("conv1", "hash123") == "摘要內容"

    def test_corrupt_ledger_degrades_gracefully(self, tmp_path: Path):
        ledger_dir = tmp_path / "ledger"
        ledger_dir.mkdir(parents=True)
        (ledger_dir / "ledger.json").write_text("not json{", encoding="utf-8")
        ledger = ContextLedger(ledger_dir)
        assert ledger.next_turn("conv1") == 1  # 全新開始，不炸

    def test_digest_block_is_system_role_and_survives(self, tmp_path: Path):
        """消化後的摘要訊息為 system 角色——不會被後續裁剪階段驅逐。"""
        from services.llm.prompt_builder import _enforce_prompt_budget

        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            return_value=scheduler,
        ):
            with patch(
                "services.llm.prompt_builder._get_llm_config", return_value=None
            ):
                messages = [_sys("核心提示" * 5)]
                for i in range(6):
                    # CJK 密度高：每塊 ~800 tokens × 6 ≈ 4800 > 預算 2000
                    messages.append(
                        _msg("user", f"[Block {i}]\n" + "內容描述" * 200)
                    )
                messages.append(_msg("user", "<user_message>請回答</user_message>"))
                _enforce_prompt_budget(messages, {"_prompt_token_budget": 2000})
        digest_msgs = [m for m in messages if "[Digested Context]" in m["content"]]
        assert digest_msgs, "消化區塊應在場"
        assert digest_msgs[0]["role"] == "system"  # 受保護角色


# ---------- 非同步升級（小模型工作者） ----------


class TestLlmDigest:
    @pytest.mark.asyncio
    async def test_uses_chat_completion_and_caches(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")

        class FakeResponse:
            text = "小模型摘要：三條要點"

        class FakeLLM:
            async def chat_completion(self, messages, **kwargs):
                return FakeResponse()

        scheduler._llm_service = FakeLLM()
        text = "一段上下文內容"
        digest = await scheduler.digest_with_llm(text, "conv1")
        assert digest == "小模型摘要：三條要點"
        assert scheduler.stats()["llm_digests"] == 1
        # 快取已寫入：同內容直接命中（重啟後一致性）
        import hashlib

        text_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        assert scheduler.ledger.cache_get("conv1", text_hash) == "小模型摘要：三條要點"

    @pytest.mark.asyncio
    async def test_lazy_service_factory_is_awaited(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")

        class FakeResponse:
            text = "由共享服務產生的摘要"

        class FakeLLM:
            async def chat_completion(self, messages, **kwargs):
                return FakeResponse()

        async def get_service():
            return FakeLLM()

        with patch("services.llm.router.get_llm_service", new=get_service):
            digest = await scheduler.digest_with_llm("跨輪上下文", "conv1")

        assert digest == "由共享服務產生的摘要"
        assert scheduler.stats()["llm_digests"] == 1

    @pytest.mark.asyncio
    async def test_no_llm_returns_none_extractive_remains(self, tmp_path: Path):
        scheduler = ContextScheduler(llm_service=None, ledger_dir=tmp_path / "ledger")

        def _boom():  # 純函式替代——避免 AsyncMock 遺留未 await 協程
            raise ImportError("no llm service")

        with patch("services.llm.router.get_llm_service", new=_boom):
            digest = await scheduler.digest_with_llm("內容", "conv1")
        assert digest is None  # 優雅降級，萃取摘要仍在

    @pytest.mark.asyncio
    async def test_llm_exception_degrades_gracefully(self, tmp_path: Path):
        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")

        class BrokenLLM:
            async def chat_completion(self, messages, **kwargs):
                raise RuntimeError("backend down")

        scheduler._llm_service = BrokenLLM()
        digest = await scheduler.digest_with_llm("內容", "conv1")
        assert digest is None


# ---------- 整合：守門的階段 0 ----------


class TestGateIntegration:
    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_digest_runs_before_trimming(self, mock_cfg, tmp_path: Path):
        from services.llm.prompt_builder import _enforce_prompt_budget

        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            return_value=scheduler,
        ):
            messages = [_sys("核心提示" * 5)]
            for i in range(6):
                # CJK 密度高：每塊 ~800 tokens × 6 = ~4800 > 預算 2500
                messages.append(_msg("user", f"[Block {i}] 標題\n" + "內容描述" * 200))
            messages.append(_msg("user", "<user_message>請回答</user_message>"))
            stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 2500})
        # 消化優先：中段全部被消化（無驅逐）
        assert stats["digested_messages"] == 6
        assert stats["dropped_messages"] == 0
        assert stats["truncated_messages"] == 0
        # 消化區塊在場
        assert any("[Digested Context]" in m["content"] for m in messages)

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_scheduler_absent_falls_back_to_trimming(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        def _boom():
            raise ImportError("scheduler missing")

        with patch(
            "services.llm.context_scheduler.get_context_scheduler", side_effect=_boom
        ):
            messages = [_sys("核心提示" * 5)]
            for i in range(4):
                messages.append(_msg("user", "x" * 4000))
            messages.append(_msg("user", "final"))
            stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 1500})
        assert stats["dropped_messages"] > 0  # 舊路徑仍在

    def test_telemetry_counts_digested(self, tmp_path: Path):
        from services.llm.prompt_builder import (
            _enforce_prompt_budget,
            get_prompt_budget_stats,
        )

        scheduler = ContextScheduler(ledger_dir=tmp_path / "ledger")
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            return_value=scheduler,
        ):
            with patch(
                "services.llm.prompt_builder._get_llm_config", return_value=None
            ):
                before = get_prompt_budget_stats()["events"]
                messages = [_sys("核心提示" * 5)]
                for i in range(5):
                    # CJK 密度高：每塊 ~600 tokens × 5 = ~3000 > 預算 2200
                    messages.append(_msg("user", f"[Block {i}]\n" + "內容" * 300))
                messages.append(_msg("user", "final"))
                _enforce_prompt_budget(messages, {"_prompt_token_budget": 2200})
        assert get_prompt_budget_stats()["events"] == before + 1
        assert get_prompt_budget_stats()["digested_messages"] >= 1


# ---------- 單例 ----------


def test_singleton_is_stable():
    assert get_context_scheduler() is get_context_scheduler()
