# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend provider implementations

All imports are lazy to avoid slow/torch-dependent module loading at import time.
Import directly from submodules: from services.llm.providers.anthropic import AnthropicAPIBackend
"""

import importlib
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

_LAZY_PROVIDERS = {
    "AnthropicAPIBackend": (".anthropic", "AnthropicAPIBackend"),
    "BaseLLMBackend": (".base", "BaseLLMBackend"),
    "ED3NBackend": (".ed3n", "ED3NBackend"),
    "GARDENBackend": (".garden", "GARDENBackend"),
    "GoogleAPIBackend": (".google", "GoogleAPIBackend"),
    "LlamaCppBackend": (".llamacpp", "LlamaCppBackend"),
    "OllamaBackend": (".ollama", "OllamaBackend"),
    "OpenAIAPIBackend": (".openai", "OpenAIAPIBackend"),
    "LLMBackend": (".registry", "LLMBackend"),
}

_lazy_cache: dict = {}
_warned: set = set()


class _MissingSentinel:
    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return True

    def __repr__(self):
        return "<missing>"


_MISSING = _MissingSentinel()


def __getattr__(name: str) -> Any:
    if name in _LAZY_PROVIDERS:
        if name in _lazy_cache:
            return _lazy_cache[name]
        module_path, attr = _LAZY_PROVIDERS[name]
        try:
            module = importlib.import_module(module_path, package=__package__)
            result = getattr(module, attr)
            _lazy_cache[name] = result
            return result
        except Exception as e:
            if name not in _warned:
                logger.warning("Failed to lazy-import %s: %s", name, e)
                _warned.add(name)
            _lazy_cache[name] = _MISSING
            return _MISSING
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "BaseLLMBackend",
    "LLMBackend",
    "LlamaCppBackend",
    "OllamaBackend",
    "OpenAIAPIBackend",
    "AnthropicAPIBackend",
    "GoogleAPIBackend",
    "ED3NBackend",
    "GARDENBackend",
]
