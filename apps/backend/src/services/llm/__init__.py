# ANGELA-MATRIX: L3 [γ] [A] [L0-L11]
"""Angela LLM services — router, prompt builder, and backend providers

All submodule imports are lazy to avoid slow/torch-dependent module loading.
Import directly: from services.llm.router import router
"""

import importlib
import logging
from types import ModuleType
from typing import Any, List

logger = logging.getLogger(__name__)

_LAZY_SUBMODULES = {
    "emotion_analyzer": ".emotion_analyzer",
    "memory_integration": ".memory_integration",
    "prompt_builder": ".prompt_builder",
    "providers": ".providers",
    "router": ".router",
}

_lazy_cache: dict = {}


def __getattr__(name: str) -> Any:
    if name in _LAZY_SUBMODULES:
        if name in _lazy_cache:
            return _lazy_cache[name]
        try:
            module = importlib.import_module(_LAZY_SUBMODULES[name], package=__package__)
            _lazy_cache[name] = module
            return module
        except Exception as e:
            raise AttributeError(f"cannot import {name!r}: {e}") from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "prompt_builder",
    "providers",
    "router",
    "emotion_analyzer",
    "memory_integration",
]
