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
from typing import Any, Callable, Dict, List, Optional

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

# Deterministic seed dependencies are imported at module level so their
# import cost (dictionary_layer alone is ~200ms) lands at backend startup,
# not inside the first request's event loop. None keeps graceful degradation
# if the optional engines are unavailable.
try:
    from services.math_verifier import compute_arithmetic as _compute_arithmetic
except Exception:  # pragma: no cover - optional engine
    _compute_arithmetic = None  # type: ignore[assignment]
try:
    from ai.ed3n.dictionary_layer import get_dictionary as _get_dictionary
except Exception:  # pragma: no cover - optional engine
    _get_dictionary = None  # type: ignore[assignment]


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
        legacy_pipeline: Any = None,
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

        # A/B testing (requires a legacy pipeline to compare against)
        if enable_ab_testing and legacy_pipeline is not None:
            self.ab_testing: Optional[ABTesting] = ABTesting(
                self,
                legacy_pipeline,
            )
        else:
            self.ab_testing = None

        # Metrics collector
        self.metrics: Optional[MetricsCollector] = MetricsCollector() if enable_metrics else None

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
            self.metrics.record_request()
            self.metrics.record_latency("pipeline", elapsed)

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
        """Layer 0: Generate deterministic seed.

        Reuses the project's real deterministic engines (single
        implementation, no parallel re-implementation):
        - Math: services.math_verifier (compute_arithmetic)
        - Knowledge: ai.ed3n.dictionary_layer (DictionaryLayer singleton)
        """
        # Math via the project's math verifier (deterministic, safe eval)
        try:
            if _compute_arithmetic is not None:
                value = _compute_arithmetic(input_text)
            else:
                value = None
            if value is not None:
                return SeedResult(
                    answer=str(value),
                    confidence=0.95,
                    source="math",
                    reasoning_chain=[f"compute_arithmetic({input_text!r}) = {value}"],
                )
        except Exception:
            pass

        # Knowledge via the shared ED3N dictionary layer singleton
        try:
            if _get_dictionary is None:
                return SeedResult()
            dictionary = _get_dictionary()
            keys = dictionary.encode(input_text, max_keys=3)
            if keys:
                entries = dictionary.lookup(keys)
                hits = [e for e in entries.values() if e is not None]
                if hits:
                    best = max(hits, key=lambda e: getattr(e, "confidence", 0.0))
                    return SeedResult(
                        answer=str(getattr(best, "key", "")),
                        confidence=min(0.9, float(getattr(best, "confidence", 0.5))),
                        source="knowledge",
                        reasoning_chain=[f"dictionary hits: {[e.key for e in hits]}"],
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
                result: Any = await self.llm_service.generate(prompt)
                return str(result) if result is not None else None
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
        ab_state = self.ab_testing.get_metrics() if self.ab_testing else None
        metrics_snapshot = self.metrics.get_summary() if self.metrics else None

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
