"""
Angela LLM Service - Backward Compat Shim
===========================================
A3 refactor: all core logic moved to services/llm/router.py.
This file re-exports everything from services/llm/* for backward compatibility.
"""

# Core logic moved to services/llm/router.py
from services.llm.router import (  # noqa: F401
    AngelaLLMService,
    _load_memory_modules,
    is_memory_enhanced,
    MEMORY_ENHANCED,
    _get_llm_config,
    _llm_service,
    get_llm_service,
    angela_llm_response,
    logger,
)

# Provider backends
from services.llm.providers import (  # noqa: F401
    BaseLLMBackend,
    LLMBackend,
    LlamaCppBackend,
    OllamaBackend,
    OpenAIAPIBackend,
    AnthropicAPIBackend,
    GoogleAPIBackend,
)

# Protocol re-exports (needed by ai/memory/precompute_service.py via relative import)
from core.interfaces.protocols import ChatMessage, LLMResponse, ModelProvider  # noqa: F401

# Prompt builder functions
from services.llm.prompt_builder import (  # noqa: F401
    get_biological_state,
    get_formula_summaries,
    construct_angela_prompt,
)
