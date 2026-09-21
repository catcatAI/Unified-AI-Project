# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MSBAPipeline — the main 7-layer MSBA pipeline.

All inputs enter MSBA. Simple inputs (social/reflex) use lightweight
block selection (fewer blocks) but do NOT skip the block system.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .ab_testing import ABTesting
from .block_coordinator import BlockCoordinator
from .block_selector import BlockSelector
from .checkpointer import MSBACheckpointer
from .cold_start import ColdStartManager
from .intra_block_hit import IntraBlockHitEngine
from .metrics_collector import MetricsCollector
from .multi_dir_decoder import MultiDirectionalDecoder
from .relevance_convergence import RelevanceConvergence
from .semantic_block import SemanticBlock
from .types import BlockHitResult, SeedResult

logger = logging.getLogger(__name__)

# Query types that use lightweight block selection
LIGHTWEIGHT_TYPES = {"reflex", "greeting", "unknown"}


class MSBAPipeline:
    """
    Multi-Dimensional Semantic Block Architecture pipeline.

    7-layer processing:
      Layer 0: Deterministic Seed
      Layer 1: Semantic Block Library
      Layer 2: Block Selector (4-signal fusion)
      Layer 3: Intra-Block Hit (parallel)
      Layer 4: Relevance Convergence
      Layer 5: Multi-Directional Decode
      Layer 6: Output + Learning
    """

    LATENCY_BUDGET_MS = 100.0

    def __init__(
        self,
        blocks: Optional[Dict[str, SemanticBlock]] = None,
        query_classifier: Any = None,
        llm_service: Any = None,
        dictionary: Any = None,
        enable_ab_testing: bool = False,
        enable_metrics: bool = False,
        auto_save_interval: float = 300.0,
    ):
        self.blocks = blocks or {}
        self.query_classifier = query_classifier
        self.llm_service = llm_service
        self.dictionary = dictionary

        # Layer 2: Block Selector
        self.block_selector = BlockSelector(self.blocks)

        # Layer 3: Intra-Block Hit
        self.hit_engine = IntraBlockHitEngine(self.blocks)

        # Layer 4: Relevance Convergence
        self.convergence = RelevanceConvergence(self.blocks)

        # Layer 5: Multi-Directional Decoder
        self.decoder = MultiDirectionalDecoder(
            dictionary=self.dictionary,
            blocks=self.blocks,
            llm_service=self.llm_service,
        )

        # Cold start manager
        self.cold_start = ColdStartManager(self.blocks)

        # Checkpointer with auto-save
        self.checkpointer = MSBACheckpointer(
            auto_save_interval=auto_save_interval,
        )

        # A/B testing
        self.ab_testing = ABTesting() if enable_ab_testing else None

        # Metrics collector
        self.metrics = MetricsCollector() if enable_metrics else None

        # Process counter for auto-save
        self._process_count = 0

    async def process(self, input_text: str, state_ctx: Any = None) -> str:
        """
        Process input through the full MSBA pipeline.

        ALL inputs enter MSBA. Lightweight inputs (social/reflex)
        simply select fewer blocks.
        """
        start = time.monotonic()

        # Auto-save check
        self._process_count += 1
        if self.checkpointer.check_auto_save():
            self.save_checkpoint()
            self.checkpointer.mark_saved()

        # Layer 0: Deterministic Seed
        seed = self._deterministic_seed(input_text, state_ctx)

        # Classify for lightweight flag
        lightweight = self._is_lightweight(input_text)

        # Layer 2: Block Selector
        selection = self.block_selector.select(input_text, seed, lightweight=lightweight)

        # Latency budget: limit blocks
        elapsed_ms = (time.monotonic() - start) * 1000
        remaining = self.LATENCY_BUDGET_MS - elapsed_ms
        max_blocks = self._compute_max_blocks(seed, remaining, lightweight)
        selection.selected = selection.selected[:max_blocks]

        # Layer 3: Intra-Block Hit (parallel)
        try:
            block_hits = await asyncio.wait_for(
                self.hit_engine.hit_all(input_text, seed, selection.selected, state_ctx),
                timeout=max(remaining / 1000, 0.01),
            )
        except asyncio.TimeoutError:
            block_hits = self.hit_engine.get_partial_results()
            logger.debug("Hit engine timed out, using partial results")

        # Layer 4: Relevance Convergence
        fused = self.convergence.converge(block_hits, seed, state_ctx)

        # LLM fallback
        if fused.confidence < 0.5 and self.llm_service:
            llm_result = await self._llm_fallback(fused, input_text)
            if llm_result:
                return llm_result

        # Layer 5: Multi-Directional Decode
        result = self.decoder.decode(fused, seed)

        # Layer 6: Learning
        self._post_process(result, fused, seed, state_ctx)

        # Metrics
        if self.metrics:
            elapsed = (time.monotonic() - start) * 1000
            self.metrics.record_request(
                latency_ms=elapsed,
                cache_hit=False,
                success=True,
            )

        return result

    def process_sync(self, input_text: str, state_ctx: Any = None) -> str:
        """Synchronous wrapper for process()."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.process(input_text, state_ctx),
                    )
                    return future.result(timeout=2.0)
            else:
                return loop.run_until_complete(self.process(input_text, state_ctx))
        except Exception:
            return asyncio.run(self.process(input_text, state_ctx))

    def _deterministic_seed(self, input_text: str, state_ctx: Any) -> SeedResult:
        """Layer 0: Generate deterministic seed."""
        # Try math
        try:
            from ai.ed3n.deterministic_router import (
                DeterministicRouter,
            )

            router = DeterministicRouter()
            result = router.evaluate(input_text)
            if result and result.get("answer"):
                return SeedResult(
                    answer=str(result["answer"]),
                    confidence=float(result.get("confidence", 0.8)),
                    source="math",
                    reasoning_chain=result.get("steps", []),
                )
        except Exception:
            pass

        # Try knowledge base
        try:
            from ai.ed3n.knowledge_base import knowledge_base

            kb_result = knowledge_base.query(input_text)
            if kb_result and kb_result.get("answer"):
                return SeedResult(
                    answer=str(kb_result["answer"]),
                    confidence=float(kb_result.get("confidence", 0.7)),
                    source="knowledge",
                )
        except Exception:
            pass

        return SeedResult()

    def _is_lightweight(self, input_text: str) -> bool:
        """Determine if input should use lightweight selection."""
        if self.query_classifier is None:
            return len(input_text) <= 3
        try:
            qt = self.query_classifier.classify(input_text)
            qt_name = qt.primary_type.value if hasattr(qt, "primary_type") else str(qt).lower()
            return qt_name in LIGHTWEIGHT_TYPES
        except Exception:
            return len(input_text) <= 3

    def _compute_max_blocks(
        self,
        seed: SeedResult,
        remaining_ms: float,
        lightweight: bool,
    ) -> int:
        """Compute max blocks based on latency budget."""
        if lightweight:
            return 2
        if seed.confidence > 0.95:
            return 3
        if seed.confidence > 0.7:
            return 5
        return 7

    async def _llm_fallback(self, fused, input_text: str) -> Optional[str]:
        """LLM fallback when blocks can't reach consensus."""
        if self.llm_service is None:
            return None
        try:
            context = f"Semantic dimensions: {fused.dimensions}"
            prompt = f"Input: {input_text}\n" f"{context}\n" f"Provide a concise answer:"
            if hasattr(self.llm_service, "generate"):
                return await self.llm_service.generate(prompt)
        except Exception as e:
            logger.debug("LLM fallback failed: %s", e)
        return None

    def _post_process(
        self,
        output: str,
        fused,
        seed: SeedResult,
        state_ctx: Any,
    ) -> None:
        """Layer 6: Post-process and learn."""
        # Reconstruct block hits from fused primary
        block_hits: Dict[str, BlockHitResult] = {}
        for (bid, sid, act), weight in fused.primary.items():
            if bid not in block_hits:
                block_hits[bid] = BlockHitResult(
                    block_id=bid,
                    seed_verdict=fused.seed_verdicts.get(bid, "neutral"),
                )
            block_hits[bid].hit_sources[sid] = weight

        # Update convergence cross-attention
        if block_hits:
            self.convergence.update_from_cooccurrence(block_hits)

        # Record seed verdicts in block selector
        for bid, verdict in fused.seed_verdicts.items():
            self.block_selector.record_verdict(bid, verdict)

    def save_checkpoint(self) -> None:
        """Save MSBA state."""
        cross_attention = self.convergence.cross_attention
        history = {bid: hist.to_dict() for bid, hist in self.block_selector.block_history.items()}
        training_state = self.convergence.get_training_stats()
        ab_state = self.ab_testing.get_stats() if self.ab_testing else None
        metrics_snapshot = self.metrics.get_metrics() if self.metrics else None

        self.checkpointer.save(
            self.blocks,
            cross_attention,
            history,
            training_state=training_state,
            ab_state=ab_state,
            metrics_snapshot=metrics_snapshot,
        )

    def load_checkpoint(self, version: Optional[int] = None) -> None:
        """Load MSBA state."""
        result = self.checkpointer.load(self.blocks, version=version)
        if not result:
            return

        ca = result.get("cross_attention")
        if ca is not None:
            self.convergence.cross_attention = ca

        # Restore training state
        train = result.get("training_state")
        if train:
            self.convergence._step_count = train.get("step_count", 0)
            self.convergence._learning_rate = train.get(
                "learning_rate", self.convergence.BASE_LEARNING_RATE
            )
