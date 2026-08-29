# ANGELA-MATRIX: L3 [βγ] [B] [L2]
"""Unified Engine LLM backend provider — the single text-inference core.

Routes queries through the UnifiedEngine: deterministic math/logic (real
capabilities) first, then the fixed-size statistical core (real learned
generalisation). Replaces ED3N/GARDEN as the *text* inference entry point;
their multimodal branches (image/audio encoders) are untouched.
"""

import logging
import os
import re
import time
from typing import Any, Optional

from core.interfaces.protocols import LLMResponse
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class UnifiedBackend(BaseLLMBackend):
    """Unified Engine 後端 — fixed-size statistical core + deterministic layers."""

    def __init__(
        self,
        model: str = "unified-1g",
        checkpoint: str = "",
        timeout: float = 30.0,
    ):
        self.model = model
        self.checkpoint = checkpoint or self._resolve_default_checkpoint()
        self.timeout = timeout
        self._engine: Optional[Any] = None

    @staticmethod
    def _resolve_default_checkpoint() -> str:
        """Locate the best trained checkpoint.

        Preference order: 128k-slot npz (best quality) > legacy unified.json.
        Searches data_config root then repo-local fallback.
        """
        candidates = []

        # 1. env override
        env_root = os.environ.get("ANGELA_PROJECT_ROOT", "").strip()
        search_roots = []
        if env_root:
            search_roots.append(os.path.join(env_root, "data", "checkpoints", "unified"))
        # 2. walk up from module dir
        here = os.path.abspath(os.path.dirname(__file__))
        root = here
        for _ in range(8):
            cp = os.path.join(root, "data", "checkpoints", "unified")
            if os.path.isdir(cp):
                search_roots.append(cp)
                break
            root = os.path.dirname(root)
        # 3. data_config
        try:
            from core.data_config import get_checkpoints_dir

            search_roots.append(os.path.join(str(get_checkpoints_dir()), "unified"))
        except Exception:  # noqa: BLE001
            pass

        for d in search_roots:
            # Prefer 128k npz (best quality, delta-fusion ready)
            for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                if f.endswith("_128k.npz"):
                    candidates.append(os.path.join(d, f))
            if not candidates:
                for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                    if f.endswith(".npz") and "full_train" in f:
                        candidates.append(os.path.join(d, f))
            legacy = os.path.join(d, "unified.json")
            if os.path.isfile(legacy):
                candidates.append(legacy)
            if candidates:
                break

        resolved = candidates[0] if candidates else ""
        logger.info("[UnifiedBackend] checkpoint resolved to %s", resolved or "(none)")
        return resolved

    def _get_engine(self) -> Any:
        """Lazy-init UnifiedEngine from resolved checkpoint."""
        if self._engine is not None:
            return self._engine
        try:
            from ai.unified_engine.unified_engine import UnifiedEngine

            engine = UnifiedEngine()
            if self.checkpoint and os.path.isfile(self.checkpoint):
                if self.checkpoint.endswith(".npz"):
                    import numpy as np

                    z = np.load(self.checkpoint)
                    core = engine.core
                    for attr in ("pos", "trans", "gram", "gram3", "gram5", "uni"):
                        if attr in z:
                            setattr(core, f"_{attr}", z[attr])
                else:
                    engine.load(self.checkpoint)
            # Load QA knowledge
            qa_dir = os.path.dirname(self.checkpoint) if self.checkpoint else ""
            qa_path = os.path.join(qa_dir, "qa_knowledge.json") if qa_dir else ""
            if not qa_path or not os.path.isfile(qa_path):
                try:
                    from core.data_config import get_checkpoints_dir

                    qa_path = os.path.join(
                        str(get_checkpoints_dir()), "unified", "qa_knowledge.json"
                    )
                except Exception:  # noqa: BLE001
                    qa_path = ""
            if qa_path and os.path.isfile(qa_path):
                try:
                    import json as _json

                    from ai.unified_engine.semantic_qa import SemanticQA

                    engine.semantic_qa = SemanticQA()
                    with open(qa_path, encoding="utf-8") as _f:
                        engine.semantic_qa.load_dict(_json.load(_f))
                except Exception:  # noqa: BLE001
                    pass
            self._engine = engine
            return engine
        except Exception as exc:
            logger.error("Failed to init unified engine: %s", exc, exc_info=True)
            from ai.unified_engine.unified_engine import UnifiedEngine

            self._engine = UnifiedEngine()
            return self._engine

    @staticmethod
    def _strip_wrapper(prompt: str) -> str:
        m = re.search(r"<user_message>(.*?)</user_message>", prompt, re.DOTALL)
        return m.group(1) if m else prompt

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start = time.time()
        try:
            engine = self._get_engine()
            user_text = self._strip_wrapper(prompt)
            text = await self._run_in_thread(engine, user_text)
            if not text or text == user_text:
                return LLMResponse(
                    text="",
                    backend="unified",
                    model=self.model,
                    response_time_ms=(time.time() - start) * 1000,
                )
            elapsed_ms = (time.time() - start) * 1000
            return LLMResponse(
                text=text,
                backend="unified",
                model=self.model,
                tokens_used=0,
                response_time_ms=elapsed_ms,
                confidence=float(getattr(engine, "_last_confidence", 0.0) or 0.5),
                metadata={"route": engine._last_route},
            )
        except Exception as e:
            logger.error("unified backend error: %s", e, exc_info=True)
            return LLMResponse(text="", backend="unified", model=self.model, error=safe_error(e))

    async def _run_in_thread(self, engine: Any, user_text: str) -> str:
        import asyncio

        return await asyncio.to_thread(engine.process, user_text)

    async def check_health(self) -> bool:
        try:
            engine = self._get_engine()
            return engine is not None
        except Exception as e:
            logger.warning("unified health check failed: %s", e, exc_info=True)
            return False