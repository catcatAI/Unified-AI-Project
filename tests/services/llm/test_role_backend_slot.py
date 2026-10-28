# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P2-2/P2-3: a role's forced backend slot beats normal selection.

The router is not constructed here — ``object.__new__`` + the few attributes the
two methods touch keeps these tests free of config/backend bootstrapping.
"""

import pytest
from core.interfaces.protocols import LLMResponse
from services.llm.providers.registry import LLMBackend
from services.llm.router import AngelaLLMService


class FakeBackend:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"FakeBackend({self.name})"


class SelectionStub:
    """Stands in for _select_light_backend and records whether it ran."""

    def __init__(self, result=(None, None)):
        self.result = result
        self.calls = 0

    async def __call__(self, user_message, context):
        self.calls += 1
        return self.result


def make_router(backends=None, selection=None):
    router = object.__new__(AngelaLLMService)
    router.backends = backends if backends is not None else {}
    router._select_light_backend = selection or SelectionStub()
    return router


def backends_with_qwen_and_base():
    return {
        LLMBackend.LLAMA_CPP: FakeBackend("cpp"),
        LLMBackend.LLAMA_CPP_QWEN: FakeBackend("qwen"),
    }


# --------------------------------------------------------------------------
# slot resolution
# --------------------------------------------------------------------------
def test_resolves_exact_slot():
    router = make_router(backends_with_qwen_and_base())
    backend, backend_type = router._resolve_forced_backend("llamacpp-qwen")
    assert backend.name == "qwen"
    assert backend_type is LLMBackend.LLAMA_CPP_QWEN


def test_slot_resolution_is_separator_insensitive():
    router = make_router(backends_with_qwen_and_base())
    backend, _ = router._resolve_forced_backend("LLAMA_CPP_QWEN")
    assert backend.name == "qwen"


def test_qwen_slot_does_not_fall_onto_base_model():
    router = make_router(backends_with_qwen_and_base())
    backend, backend_type = router._resolve_forced_backend("llamacpp")
    assert backend.name == "cpp"
    assert backend_type is LLMBackend.LLAMA_CPP


def test_unknown_slot_returns_none():
    router = make_router(backends_with_qwen_and_base())
    assert router._resolve_forced_backend("gemma-9b") == (None, None)


@pytest.mark.parametrize("slot", [None, ""])
def test_missing_slot_returns_none(slot):
    assert make_router()._resolve_forced_backend(slot) == (None, None)


# --------------------------------------------------------------------------
# backend choice
# --------------------------------------------------------------------------
async def test_forced_slot_skips_light_selection():
    selection = SelectionStub(result=(FakeBackend("light"), LLMBackend.OLLAMA))
    router = make_router(backends_with_qwen_and_base(), selection)
    backend, backend_type = await router._choose_backend(
        "hi", {"_force_backend_slot": "llamacpp-qwen"}
    )
    assert backend.name == "qwen"
    assert backend_type is LLMBackend.LLAMA_CPP_QWEN
    assert selection.calls == 0


async def test_no_slot_uses_light_selection():
    selection = SelectionStub(result=(FakeBackend("light"), LLMBackend.OLLAMA))
    router = make_router(backends_with_qwen_and_base(), selection)
    backend, backend_type = await router._choose_backend("hi", {})
    assert backend.name == "light"
    assert backend_type is LLMBackend.OLLAMA
    assert selection.calls == 1


async def test_unknown_slot_falls_back_to_light_selection():
    selection = SelectionStub(result=(None, None))
    router = make_router(backends_with_qwen_and_base(), selection)
    assert await router._choose_backend("hi", {"_force_backend_slot": "gone"}) == (None, None)
    assert selection.calls == 1


async def test_unknown_slot_with_empty_registry_is_harmless():
    router = make_router({}, SelectionStub(result=(None, None)))
    assert await router._choose_backend("hi", {"_force_backend_slot": "gone"}) == (None, None)


# --------------------------------------------------------------------------
# response metadata (P2-3)
# --------------------------------------------------------------------------
def test_role_id_is_stamped_into_metadata():
    response = LLMResponse(text="hi")
    AngelaLLMService._stamp_role_metadata(response, {"_role_id": "role_b"})
    assert response.metadata["role_id"] == "role_b"


def test_metadata_untouched_without_role():
    response = LLMResponse(text="hi", metadata={"cached": True})
    AngelaLLMService._stamp_role_metadata(response, {})
    assert response.metadata == {"cached": True}


def test_stamp_does_not_overwrite_existing_role_key():
    response = LLMResponse(text="hi", metadata={"role_id": "main"})
    AngelaLLMService._stamp_role_metadata(response, {"_role_id": "role_b"})
    assert response.metadata["role_id"] == "main"


def test_stamp_survives_missing_metadata_attribute():
    class Bare:
        pass

    AngelaLLMService._stamp_role_metadata(Bare(), {"_role_id": "role_b"})  # must not raise


# --------------------------------------------------------------------------
# new slots: gemma (local) and deepseek (cloud)
# --------------------------------------------------------------------------
def test_gemma_and_deepseek_slots_resolve():
    backends = {
        LLMBackend.LLAMA_CPP_GEMMA: FakeBackend("gemma"),
        LLMBackend.DEEPSEEK: FakeBackend("deepseek"),
    }
    router = make_router(backends)
    assert router._resolve_forced_backend("llamacpp-gemma")[0].name == "gemma"
    assert router._resolve_forced_backend("deepseek")[0].name == "deepseek"
    assert router._resolve_forced_backend("deepseek")[1] is LLMBackend.DEEPSEEK


def test_factory_table_knows_the_new_providers():
    from services.llm.router import _BACKEND_FACTORIES

    assert _BACKEND_FACTORIES["llama_cpp_gemma"] == "_init_llamacpp_gemma"
    assert _BACKEND_FACTORIES["deepseek"] == "_init_deepseek"


def test_deepseek_is_a_cloud_provider():
    from services.llm.router import AngelaLLMService

    assert "deepseek" in AngelaLLMService._CLOUD_PROVIDERS
