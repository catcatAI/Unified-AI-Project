"""
StatePersistence protocol conformance tests.

Verifies structural subtyping conformance via isinstance checks against
the @runtime_checkable protocol, and basic round-trip persistence.

（MetacognitiveCapabilitiesEngine 段已刪：該類別全庫不存在，幽靈模組
core/metacognition/ 24L docstring-only 樓已隨本輪清除；原本的 skipif
reason 還誤寫 sklearn。）
"""

import pytest

# ── Structural subtyping conformance ──────────────────────────────────────


class FakePersistence:
    """Minimal structural subtype of StatePersistence."""

    async def save_state(self, key: str, data: dict) -> bool:
        return True

    async def load_state(self, key: str) -> dict | None:
        return None

    async def delete_state(self, key: str) -> bool:
        return True

    async def list_keys(self, prefix: str = "") -> list:
        return []


def test_fake_conforms_to_protocol():
    """Structural subtyping: a class with the right shape is a StatePersistence."""
    from core.interfaces.persistence import StatePersistence

    assert isinstance(FakePersistence(), StatePersistence)


# ── StateMatrixAdapter ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def sm_adapter():
    from core.engine.state_matrix_adapter import StateMatrixAdapter

    return StateMatrixAdapter()


def test_state_matrix_adapter_conforms(sm_adapter):
    """StateMatrixAdapter must implement StatePersistence."""
    from core.interfaces.persistence import StatePersistence

    assert isinstance(sm_adapter, StatePersistence)


async def test_state_matrix_adapter_save_load(sm_adapter):
    """Basic save + load via protocol interface (JSON-file backend)."""
    key = "test_sma_rt"
    data = {"msg": "hello"}
    ok = await sm_adapter.save_state(key, data)
    assert ok is True
    loaded = await sm_adapter.load_state(key)
    assert loaded == data
    await sm_adapter.delete_state(key)
    assert await sm_adapter.load_state(key) is None


def test_state_matrix_adapter_list_keys(sm_adapter):
    async def _run():
        for k in ("sma_a", "sma_b", "other"):
            await sm_adapter.save_state(k, {"d": True})
        all_keys = await sm_adapter.list_keys()
        assert "sma_a" in all_keys
        a_keys = await sm_adapter.list_keys(prefix="sma_")
        assert len(a_keys) == 2
        assert "other" not in a_keys
        for k in ("sma_a", "sma_b", "other"):
            await sm_adapter.delete_state(k)

    import asyncio

    asyncio.run(_run())
