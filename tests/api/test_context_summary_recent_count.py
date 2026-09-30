"""context_summary 死路徑 #19 回歸測試。

歷史缺陷：/context/summary 的 memory 區塊在 async 端點內以
``loop.is_running()`` 判定——async 端點執行時循環必然在跑，判定
永遠為真，導致 ``recent_count`` 永不填充（查詢死路徑）。
修復：移除死分支，直接 ``await memory_manager.query_core_memory()``。
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import api.lifespan as api_lifespan  # noqa: E402
import api.routes.context_routes as context_routes  # noqa: E402
import core.config_loader as config_loader  # noqa: E402
import services.angela_llm_service as llm_service_module  # noqa: E402

_STATE_AXES = ("alpha", "beta", "gamma", "delta", "epsilon", "theta")


def _make_fake_service() -> MagicMock:
    svc = MagicMock()
    for axis in _STATE_AXES:
        getattr(svc.state_matrix, axis).values = {"x": 0.5}
    svc.eta_state = SimpleNamespace(execution_count=2, success_rate=0.9, structural_drift=0.05)
    svc.memory_manager = MagicMock()
    svc.memory_manager.query_core_memory = AsyncMock(return_value=[object() for _ in range(3)])
    return svc


@pytest.mark.asyncio
async def test_summary_recent_count_is_filled(monkeypatch):
    """recent_count 必須等於記憶查詢實際回傳筆數（死路徑 #19 契約）."""
    fake = _make_fake_service()
    monkeypatch.setattr(api_lifespan, "_get_chat_service", AsyncMock(return_value=fake))
    monkeypatch.setattr(
        config_loader,
        "get_angela_config",
        lambda: SimpleNamespace(get_intents=lambda: {"intent_a": {}}),
    )
    monkeypatch.setattr(
        llm_service_module,
        "get_llm_service",
        AsyncMock(
            return_value=SimpleNamespace(
                is_available=True, active_backend_type=None, llm_mode="mock"
            )
        ),
    )

    result = await context_routes.context_summary()

    assert result["memory"]["initialized"] is True
    assert result["memory"]["recent_count"] == 3
    fake.memory_manager.query_core_memory.assert_awaited_once()


@pytest.mark.asyncio
async def test_summary_memory_query_error_keeps_none(monkeypatch):
    """查詢拋例外時 recent_count 回 None，不讓整個端點炸掉."""
    fake = _make_fake_service()
    fake.memory_manager.query_core_memory = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(api_lifespan, "_get_chat_service", AsyncMock(return_value=fake))
    monkeypatch.setattr(
        config_loader,
        "get_angela_config",
        lambda: SimpleNamespace(get_intents=lambda: {}),
    )
    monkeypatch.setattr(
        llm_service_module,
        "get_llm_service",
        AsyncMock(
            return_value=SimpleNamespace(
                is_available=False, active_backend_type=None, llm_mode="mock"
            )
        ),
    )

    result = await context_routes.context_summary()

    assert result["memory"]["initialized"] is True
    assert result["memory"]["recent_count"] is None
