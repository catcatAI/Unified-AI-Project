# =============================================================================
# ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
# =============================================================================
"""One definition of "a backend that can generate the reply is registered".

Three places used to answer this question on their own, and they disagreed:

- ``memory_integration._has_generative_backend`` kept an allowlist that said
  ``llama_cpp`` while the provider enum says ``llamacpp`` (and the Qwen/Gemma
  slots say ``llamacpp-qwen`` / ``llamacpp-gemma``). A llama.cpp backend was
  therefore invisible to the memory layer, so the canned teaching frame
  pre-empted a real model — the exact "surface replaces core" regression the
  check was written to prevent.
- ``router._llm_backend_available`` called every non-unified backend
  generative (including the project's own ED3N/GARDEN), so a template was
  handed to an engine that cannot follow a prompt.
- ``gate_execution._llm_generation_available`` duplicated the router check.

The enum values below are the authoritative names (``LLMBackend`` in
``services/llm/providers/registry.py``). The unified engine is deliberately
NOT here: it is the project's offline statistical core, not a model that can
be given a prompt and asked to rephrase it — with it alone the honest surface
layer is the only thing that can answer.
"""

# LAYER: surface

from __future__ import annotations

from typing import Any, Iterable

# The providers that accept a prompt and generate a reply. Keep the names in
# step with ``LLMBackend`` values (not class names, not config ids).
GENERATIVE_BACKENDS = frozenset(
    {
        "openai",
        "deepseek",
        "anthropic",
        "google",
        "ollama",
        "llamacpp",
        "llamacpp-qwen",
        "llamacpp-gemma",
    }
)


def backend_name(backend: Any) -> str:
    """The wire name of a backend (enum member, string, or config id)."""
    value = getattr(backend, "value", backend)
    return str(value or "").strip().lower()


def has_generative_backend(backends: Any) -> bool:
    """True when any registered backend can generate a reply.

    Accepts a ``{backend: instance}`` mapping, an iterable of names, or the
    service itself (its ``.backends`` mapping is used).
    """
    if backends is None:
        return False
    if hasattr(backends, "backends"):
        backends = getattr(backends, "backends")
    if backends is None:
        return False
    if isinstance(backends, dict):
        names: Iterable[Any] = backends.keys()
    else:
        try:
            names = list(backends)
        except TypeError:
            return False
    return any(backend_name(name) in GENERATIVE_BACKENDS for name in names)


def generation_available(service: Any = None) -> bool:
    """True when a generative backend is available on ``service`` (or globally).

    When no service is given the module-level LLM service is read *without*
    initializing it (the same no-side-effect contract as the execution gate):
    callers must be able to ask before the first request without paying for a
    service start-up.
    """
    if service is not None:
        return has_generative_backend(getattr(service, "backends", service))
    try:
        from services.llm import router as router_module

        service = getattr(router_module, "_llm_service", None)
        if service is None:
            # The module global is only set once get_llm_service() ran. A
            # caller that asks before that (chat_routes Step 1c runs before it
            # fetches the chat service) must still see a registered model, or
            # the memory layer speaks on the first turn of a server that has
            # an LLM configured. The registry entry is written by the same
            # get_llm_service() call, after initialize().
            from core.interfaces.service_registry import get_registry

            service = get_registry().get("angela_llm_service")
        return has_generative_backend(getattr(service, "backends", service))
    except Exception:  # pragma: no cover - import cycle safety
        return False


__all__ = [
    "GENERATIVE_BACKENDS",
    "backend_name",
    "generation_available",
    "has_generative_backend",
]
