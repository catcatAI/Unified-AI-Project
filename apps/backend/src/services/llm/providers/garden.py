# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""GARDEN-1G LLM backend provider for Angela's AngelaLLMService router."""

import logging
import os
import time
from typing import Any, Optional

from core.interfaces.protocols import LLMResponse
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class GARDENBackend(BaseLLMBackend):
    """
    GARDEN-1G 後端 — PyTorch 向量字典 + TensorSNN 輕量推理。
    掛載到 AngelaLLMService 的 LLMBackend 路由系統。
    """

    def __init__(
        self,
        model: str = "garden-1g",
        checkpoint: str = "",
        timeout: float = 30.0,
    ):
        self.model = model
        # When no explicit checkpoint is configured, fall back to the trained
        # checkpoint produced by scripts/train_pipeline.py so inference uses what
        # was actually trained (previously the engine loaded presets only,
        # orphaning the trained garden_checkpoint on disk).
        if not checkpoint:
            checkpoint = self._resolve_default_checkpoint()
        self.checkpoint = checkpoint
        self.timeout = timeout
        self._engine: Optional[Any] = None

    @staticmethod
    def _resolve_default_checkpoint() -> str:
        """Locate the trained ``data/checkpoints/garden_checkpoint`` dir.

        Resolution order:
          1. ``ANGELA_PROJECT_ROOT`` env override (explicit, unambiguous).
          2. Walk up from this module's dir to the dir containing
             ``apps/backend/src`` (bounded — this file lives at
             apps/backend/src/services/llm/providers/, 6 levels below root).
        """
        env_root = os.environ.get("ANGELA_PROJECT_ROOT", "").strip()
        if env_root:
            candidate = os.path.join(env_root, "data", "checkpoints", "garden_checkpoint")
            if os.path.isdir(candidate):
                return candidate
        here = os.path.abspath(os.path.dirname(__file__))
        root = here
        # Bounded walk: this module is exactly 6 levels below the project root
        # (providers/llm/services/src/backend/apps). 8 covers symlink layouts.
        for _ in range(8):
            if os.path.isdir(os.path.join(root, "apps", "backend", "src")):
                break
            parent = os.path.dirname(root)
            if parent == root:
                break
            root = parent
        candidate = os.path.join(root, "data", "checkpoints", "garden_checkpoint")
        if os.path.isdir(candidate):
            return candidate
        return ""

    def _get_engine(self):
        if self._engine is None:
            from ai.garden.garden_engine import GARDENEngine

            engine = GARDENEngine(compatibility_mode=True)
            if self.checkpoint and os.path.isdir(self.checkpoint):
                engine.load(self.checkpoint)
                logger.info("GARDEN backend: loaded checkpoint from %s", self.checkpoint)
            else:
                engine.load_presets()
                logger.info("GARDEN backend: loaded presets")
            self._engine = engine
        return self._engine

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.time()
        try:
            engine = self._get_engine()
            context = kwargs.get("context")

            # NeuralBridge: when the switch is ON, state matrix axis values
            # are injected directly into the SNN as input activations (via the
            # designed-but-unused context slot), and SNN output activations are
            # written back to the state matrix — a minimal-translation direct
            # numeric link that bypasses the LLM text-based transfer.
            neural_context = None
            writeback_result = {}
            try:
                from ai.bridge.neural_bridge import (
                    apply_state_updates,
                    build_neural_context,
                    neural_bridge_enabled,
                )

                if neural_bridge_enabled():
                    state_matrix = None
                    try:
                        from api.lifespan import get_digital_life

                        dli = get_digital_life()
                        if dli is not None and hasattr(dli, "state_matrix"):
                            state_matrix = dli.state_matrix
                    except Exception:
                        state_matrix = None
                    if state_matrix is not None:
                        neural_context = build_neural_context(context, state_matrix)
                        # The injected slot is ``neural_state`` (consumed by the
                        # SNN forward); bridge activity is surfaced to callers via
                        # the ``metadata["bridge"]`` flag below.
            except Exception as e:
                logger.warning(f"NeuralBridge context build failed: {e}", exc_info=True)

            if neural_context is not None:
                text = engine.process(prompt, context=neural_context)
            else:
                text = engine.process(prompt, context=context)

            # Writeback: SNN activations → state matrix axis values.
            try:
                from ai.bridge.neural_bridge import apply_state_updates, neural_outputs_to_state_updates

                if neural_bridge_enabled():
                    state_matrix = None
                    try:
                        from api.lifespan import get_digital_life

                        dli = get_digital_life()
                        if dli is not None and hasattr(dli, "state_matrix"):
                            state_matrix = dli.state_matrix
                    except Exception:
                        state_matrix = None
                    if state_matrix is not None:
                        updates = neural_outputs_to_state_updates(
                            engine.get_last_network_output()
                        )
                        writeback_result = {"updates": updates}
                        applied = apply_state_updates(state_matrix, updates)
                        if applied:
                            logger.debug(
                                "NeuralBridge writeback: %d state keys updated from SNN output",
                                applied,
                            )
            except Exception as e:
                logger.warning(f"NeuralBridge writeback failed: {e}", exc_info=True)

            if not text:
                text = "抱歉，我暂时无法理解你的意思。"
            elapsed_ms = (time.time() - start) * 1000
            metadata = {"bridge": True} if neural_context is not None else {}
            if writeback_result:
                metadata.update(writeback_result)
            return LLMResponse(
                text=text,
                backend="garden",
                model=self.model,
                tokens_used=0,
                response_time_ms=elapsed_ms,
                confidence=0.80,
                metadata=metadata,
            )
        except Exception as e:
            logger.error("GARDEN backend error: %s", e, exc_info=True)
            return LLMResponse(text="", backend="garden", model=self.model, error=safe_error(e))

    async def check_health(self) -> bool:
        try:
            engine = self._get_engine()
            return engine is not None
        except Exception as e:
            logger.warning("GARDEN health check failed: %s", e, exc_info=True)
            return False
