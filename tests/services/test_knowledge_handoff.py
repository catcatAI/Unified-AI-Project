"""A lookup is not an explanation: causal questions defer to the generator.

The curated store answers attributes ("為什麼天空是藍的？" → "blue"). That is
an answer to *what colour*, not to *why*, so with a backend that can generate
the lookup must not pre-empt the model — a confident non-answer in the
knowledge layer's voice is the same "surface replaces the core" shape this
project keeps paying for. The native path keeps the curated value: it has
nothing better offline (the offline-speak contract pins that behaviour).
"""

import asyncio

from services.llm.providers.registry import LLMBackend
from services.llm.router import AngelaLLMService


def _service(backends):
    service = object.__new__(AngelaLLMService)
    service.backends = backends
    service.stats = {"total_requests": 1, "total_response_time": 0.0, "memory_hits": 0}
    return service


def _knowledge(service, question):
    return asyncio.run(service._try_knowledge(question, {}, 0.0))


def test_a_causal_question_defers_to_the_generator():
    result = _knowledge(_service({LLMBackend.OPENAI: object()}), "為什麼天空是藍的？")
    assert result is None, "an attribute value is not an explanation"


def test_the_native_path_keeps_the_offline_answer():
    result = _knowledge(_service({LLMBackend.UNIFIED: object()}), "為什麼天空是藍的？")
    assert result is not None
    assert "藍" in result.text


def test_a_plain_fact_still_uses_the_lookup_with_a_generator():
    """The guard is about explanation shapes, not knowledge in general."""
    result = _knowledge(_service({LLMBackend.OPENAI: object()}), "水的沸點是多少？")
    assert result is not None
    assert "100" in result.text
