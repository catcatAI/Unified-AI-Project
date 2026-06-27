"""
Angela LLM Service - Backward Compat Shim
===========================================
A3 refactor: all core logic moved to services/llm/router.py.
This file re-exports everything from services/llm/* for backward compatibility.
"""

# Protocol re-exports (needed by ai/memory/precompute_service.py via relative import)
from core.interfaces.protocols import ChatMessage, LLMResponse, ModelProvider  # noqa: F401

# Prompt builder functions
from services.llm.prompt_builder import (  # noqa: F401
    construct_angela_prompt,
    get_biological_state,
    get_formula_summaries,
)

# Provider backends
from services.llm.providers import (  # noqa: F401
    AnthropicAPIBackend,
    BaseLLMBackend,
    GoogleAPIBackend,
    LlamaCppBackend,
    LLMBackend,
    OllamaBackend,
    OpenAIAPIBackend,
)

# Core logic moved to services/llm/router.py
from services.llm.router import (  # noqa: F401
    MEMORY_ENHANCED,
    AngelaLLMService,
    _get_llm_config,
    _llm_service,
    _load_memory_modules,
    angela_llm_response,
    get_llm_service,
    is_memory_enhanced,
    logger,
)
