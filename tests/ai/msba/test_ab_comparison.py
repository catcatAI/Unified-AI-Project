"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
The MSBA A/B comparison must actually run.

The status matrix recorded "A/B 對照未啟用": the MSBA pipeline had an A/B
framework and a ``enable_ab_testing`` flag, but nothing ever produced the
"legacy" counterpart, so the comparison could not happen.

The counterpart is the same pipeline without the semantic blocks — the
pre-block architecture — so both variants run in the same process, on the
same input, through the same decoder.
"""

import pytest
from ai.msba.block_factory import create_all_blocks
from ai.msba.pipeline import MSBAPipeline


@pytest.mark.asyncio
class TestMSBAAbComparison:
    async def test_the_legacy_variant_has_no_blocks(self):
        pipeline = MSBAPipeline(blocks=create_all_blocks())
        legacy = pipeline.legacy_pipeline()
        assert legacy.blocks == {}
        assert pipeline.blocks  # the MSBA variant keeps its blocks

    async def test_compare_reports_both_variants(self):
        pipeline = MSBAPipeline(blocks=create_all_blocks())
        comparison = await pipeline.compare("今天天氣如何？")
        assert comparison["input"] == "今天天氣如何？"
        assert "msba_output" in comparison
        assert "legacy_output" in comparison
        assert comparison["msba_latency_ms"] >= 0.0
        assert comparison["legacy_latency_ms"] >= 0.0
        assert isinstance(comparison["agree"], bool)

    async def test_compare_is_readable_by_the_chat_pipeline(self):
        """The chat route stores the comparison in the routing state."""
        from core.system.state_store import state_store

        pipeline = MSBAPipeline(blocks=create_all_blocks())
        comparison = await pipeline.compare("你好")
        state_store.update_state("routing", {"msba": {"ab_comparison": comparison}}, notify=False)
        stored = state_store.get_state("routing")
        assert stored["msba"]["ab_comparison"]["input"] == "你好"
