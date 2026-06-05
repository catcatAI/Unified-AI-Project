"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Card Import Pipeline — resolver subpackage.
"""

try:
    from core.card.resolver.llm_fallback import LLMFallback
except ImportError:
    LLMFallback = None

try:
    from core.card.resolver.pipeline_orchestrator import CardImportPipeline, PipelineResult
except ImportError:
    CardImportPipeline = PipelineResult = None

try:
    from core.card.resolver.text_gravity import TextGravityField
except ImportError:
    TextGravityField = None

from core.card.resolver.token_extractor import TokenExtractor

__all__ = [
    "CardImportPipeline",
    "LLMFallback",
    "PipelineResult",
    "TextGravityField",
    "TokenExtractor",
]
