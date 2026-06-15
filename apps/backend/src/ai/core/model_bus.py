# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.system.config.magic_numbers import confidence_value, latency_value, timeout_value

logger = logging.getLogger(__name__)


@dataclass
class ModelCapability:
    tier: str
    domain: str
    latency_ms: float
    min_confidence: float


@dataclass
class ModelRouteResult:
    model_id: str
    text: str
    confidence: float
    latency_ms: float
    domain: str
    error: Optional[str] = None


@dataclass
class RouteDecision:
    query: str
    query_type: str
    selected_model: str
    results: Dict[str, ModelRouteResult]
    total_latency_ms: float
    confidence: float
    reason: str


class ModelBus:
    """Central registry + router for all AI models in the system.

    Instead of sequential fallback (try ED3N, then GARDEN, then Cloud),
    the bus can:
    - Route by query type (reflex -> ED3N, math -> ED3N, knowledge -> GARDEN, creative -> LLM)
    - Fan-out to multiple models in parallel when domain overlaps
    - Track which domains each model owns (for training deconfliction)
    - Sync knowledge between models (high-signal patterns)
    - Route to handlers for FILE/SEARCH/CODE/EXECUTE/TASK intents
    """

    def __init__(self, default_timeout: float = 30.0) -> None:
        self._registry: Dict[str, Tuple[Any, ModelCapability]] = {}
        self._handlers: Dict[str, Any] = {}
        self._handler_map: Dict[str, str] = {}
        self._query_classifier: Any = None
        self.default_timeout = timeout_value("ai.model_bus.default_timeout", default_timeout)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, model_id: str, engine: Any, capability: ModelCapability) -> None:
        """Register a model with its capability descriptor."""
        self._registry[model_id] = (engine, capability)
        logger.info(
            "Registered model '%s'  tier=%s  domain=%s  latency=%.2fms  min_conf=%.2f",
            model_id,
            capability.tier,
            capability.domain,
            capability.latency_ms,
            capability.min_confidence,
        )

    def register_ed3n(self, engine: Any) -> None:
        """Convenience: register ED3N reflex engine (fastest tier)."""
        cap = ModelCapability(
            tier="reflex",
            domain="reflex",
            latency_ms=latency_value("ai.model_bus.ed3n.latency_ms", 0.1),
            min_confidence=confidence_value("ai.model_bus.ed3n.min_confidence", 0.95),
        )
        self.register("ed3n", engine, cap)

    def register_garden(self, engine: Any) -> None:
        """Convenience: register GARDEN lightweight reasoning engine."""
        cap = ModelCapability(
            tier="lightweight",
            domain="knowledge",
            latency_ms=latency_value("ai.model_bus.garden.latency_ms", 10.0),
            min_confidence=confidence_value("ai.model_bus.garden.min_confidence", 0.70),
        )
        self.register("garden", engine, cap)

    def register_cloud(self, backend: Any) -> None:
        """Convenience: register cloud LLM backend.

        Wraps backends that expose ``generate()`` instead of ``process()``
        so the internal ``_try_model`` dispatch can call ``process()`` uniformly.
        """
        if not hasattr(backend, 'process'):
            original = backend

            class _CloudAdapter:
                def __init__(self, b):
                    self._backend = b

                async def process(self, query: str, context=None) -> str:
                    from core.interfaces.protocols import LLMResponse
                    kwargs = {"context": context} if context else {}
                    result: LLMResponse = await self._backend.generate(query, **kwargs)
                    return result.text if result else ""

            backend = _CloudAdapter(original)
        cap = ModelCapability(
            tier="cloud",
            domain="creative",
            latency_ms=latency_value("ai.model_bus.cloud.latency_ms", 500.0),
            min_confidence=confidence_value("ai.model_bus.cloud.min_confidence", 0.60),
        )
        self.register("cloud", backend, cap)

    def register_handler(self, handler_id: str, handler: Any, intent_types: List[str]) -> None:
        """Register a handler for specific intent types.

        The handler must expose an async ``process(query, context)`` method,
        or an async ``handle(text, intent)`` method (auto-adapted).

        Args:
            handler_id: Unique identifier (e.g. "file_ops", "web_search").
            handler: The handler instance.
            intent_types: QueryType values this handler handles
                         (e.g. ["file", "search"]).
        """
        adapted = self._adapt_handler(handler)
        self._handlers[handler_id] = adapted
        for intent in intent_types:
            self._handler_map[intent] = handler_id
        logger.info(
            "Registered handler '%s' for intents: %s",
            handler_id,
            ", ".join(intent_types),
        )

    def _adapt_handler(self, handler: Any) -> Any:
        """Wrap a handler to expose process(query, context) interface."""
        if hasattr(handler, 'process'):
            return handler

        class _HandlerAdapter:
            def __init__(self, h):
                self._handler = h

            async def process(self, query: str, context=None) -> str:
                intent = (context or {}).get("query_type", "unknown")
                if hasattr(self._handler, 'handle'):
                    import inspect
                    sig = inspect.signature(self._handler.handle)
                    params = list(sig.parameters.keys())
                    if len(params) >= 2:
                        result = await self._handler.handle(query, intent)
                    else:
                        result = await self._handler.handle(query)
                else:
                    result = ""
                return result if isinstance(result, str) else str(result)

        return _HandlerAdapter(handler)

    async def execute_handler(self, handler_id: str, query: str, context: dict) -> dict:
        """执行 handler 并返回结构化结果"""
        handler = self._handlers.get(handler_id)
        if not handler:
            return {"type": "unknown", "success": False, "result": None,
                    "error": f"handler {handler_id} not found"}

        try:
            if asyncio.iscoroutinefunction(handler.process):
                result = await asyncio.wait_for(
                    handler.process(query, context),
                    timeout=30.0,
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(handler.process, query, context),
                    timeout=30.0,
                )
            return {
                "type": handler_id,
                "success": True,
                "result": str(result),
                "error": None,
            }
        except asyncio.TimeoutError:
            return {"type": handler_id, "success": False, "result": None, "error": "timeout"}
        except Exception as e:
            return {"type": handler_id, "success": False, "result": None, "error": str(e)}

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    async def route(
        self,
        query: str,
        query_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RouteDecision:
        """Route query through best model(s) for the given type.

        If *query_type* is ``"auto"`` the internal ``QueryClassifier`` is
        loaded lazily and used to determine the type before routing.
        """
        if query_type == "auto":
            classifier = self._get_classifier()
            classify_result = classifier.classify(query)
            query_type = classify_result.primary_type.value

        candidates = self._resolve_candidates(query_type)
        results: Dict[str, ModelRouteResult] = {}
        start = time.perf_counter()

        if query_type in ("reflex", "greeting"):
            # ED3N only — fastest path
            r = await self._try_model("ed3n", query, context, "reflex")
            results[r.model_id] = r

        elif query_type == "math":
            # ED3N first (trained 77.7%), GARDEN fallback
            r1 = await self._try_model("ed3n", query, context, "math")
            results[r1.model_id] = r1
            if r1.confidence < confidence_value("ai.model_bus.route.math_threshold", 0.70) and "garden" in self._registry:
                r2 = await self._try_model("garden", query, context, "math")
                results[r2.model_id] = r2

        elif query_type == "knowledge":
            # GARDEN first, cloud fallback
            r1 = await self._try_model("garden", query, context, "knowledge")
            results[r1.model_id] = r1
            if r1.confidence < confidence_value("ai.model_bus.route.knowledge_threshold", 0.60) and "cloud" in self._registry:
                r2 = await self._try_model("cloud", query, context, "knowledge")
                results[r2.model_id] = r2

        elif query_type == "creative":
            # Cloud LLM only
            r = await self._try_model("cloud", query, context, "creative")
            results[r.model_id] = r

        elif query_type in ("file", "search", "code", "execute", "task", "system", "vision"):
            # Handler-based routing — check registered handlers first
            handler_id = self._handler_map.get(query_type)
            if handler_id and handler_id in self._handlers:
                handler = self._handlers[handler_id]
                try:
                    t0 = time.perf_counter()
                    if asyncio.iscoroutinefunction(handler.process):
                        raw = await asyncio.wait_for(
                            handler.process(query, context or {"query_type": query_type}),
                            timeout=self.default_timeout,
                        )
                    else:
                        raw = await asyncio.wait_for(
                            asyncio.to_thread(handler.process, query, context or {"query_type": query_type}),
                            timeout=self.default_timeout,
                        )
                    elapsed = (time.perf_counter() - t0) * 1000
                    if raw and isinstance(raw, str) and len(raw) > 0:
                        results[handler_id] = ModelRouteResult(
                            model_id=handler_id,
                            text=raw,
                            confidence=0.9,
                            latency_ms=round(elapsed, 3),
                            domain=query_type,
                        )
                except Exception as e:
                    logger.warning("Handler '%s' failed: %s", handler_id, e)
            # Fallback to model candidates if no handler result
            if not results:
                tasks = [
                    self._try_model(mid, query, context, query_type)
                    for mid in candidates
                ]
                for coro in asyncio.as_completed(tasks):
                    r = await coro
                    results[r.model_id] = r

        elif query_type in ("vision", "audio"):
            # Perception — try all eligible candidates
            tasks = [
                self._try_model(mid, query, context, query_type)
                for mid in candidates
            ]
            for coro in asyncio.as_completed(tasks):
                r = await coro
                results[r.model_id] = r

        else:
            # general / unknown / opinion / command — try all eligible, pick best
            tasks = [
                self._try_model(mid, query, context, query_type)
                for mid in candidates
            ]
            for coro in asyncio.as_completed(tasks):
                r = await coro
                results[r.model_id] = r

        elapsed = (time.perf_counter() - start) * 1000
        best = self._pick_best(results)
        selected_model = best["model_id"]
        confidence = best["confidence"]
        
        # ========== Hybrid Routing (Draft for Refinement) ==========
        # If a local model (ED3N/GARDEN) has decent but not perfect confidence,
        # and cloud LLM is available, we mark it for refinement.
        if selected_model in ("ed3n", "garden") and 0.4 <= confidence < 0.8:
            if "cloud" in self._registry:
                logger.info(f"ModelBus: {selected_model} confidence ({confidence:.2f}) in refinement zone. Routing to cloud for polish.")
                # We keep the local model as selected, but the service layer will see the confidence
                # and decide whether to use it as a draft for the cloud model.
        
        return RouteDecision(
            query=query,
            query_type=query_type,
            selected_model=selected_model,
            results=results,
            total_latency_ms=round(elapsed, 2),
            confidence=confidence,
            reason=best["reason"],
        )

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------

    def get_models_for_domain(self, domain: str) -> List[str]:
        """Return all model IDs that handle the given domain."""
        return [
            mid
            for mid, (_, cap) in self._registry.items()
            if cap.domain == domain
        ]

    def get_training_assignment(self, domain: str) -> Optional[str]:
        """Return which model should train on this domain (deconfliction).

        The first model registered with a matching domain wins.
        """
        for mid, (_, cap) in self._registry.items():
            if cap.domain == domain:
                return mid
        return None

    # ------------------------------------------------------------------
    # Knowledge sync
    # ------------------------------------------------------------------

    def sync_knowledge(
        self,
        source_model: str,
        target_model: str,
        patterns: List[Tuple[str, str]],
    ) -> int:
        """Copy high-signal reflex patterns between models.

        Each pattern is a ``(trigger, response)`` tuple.  Returns the
        number of patterns successfully transferred.
        """
        source_engine, _ = self._registry.get(source_model, (None, None))
        target_engine, _ = self._registry.get(target_model, (None, None))
        if source_engine is None or target_engine is None:
            logger.warning("sync_knowledge: unknown model %s or %s", source_model, target_model)
            return 0

        count = 0
        for trigger, response in patterns:
            if self._inject_pattern(target_engine, trigger, response):
                count += 1

        logger.info(
            "sync_knowledge: %d / %d patterns synced %s -> %s",
            count,
            len(patterns),
            source_model,
            target_model,
        )
        return count

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic information about the bus and all registered models."""
        return {
            "registered_models": list(self._registry.keys()),
            "registered_handlers": list(self._handlers.keys()),
            "handler_map": dict(self._handler_map),
            "capabilities": {
                mid: {
                    "tier": cap.tier,
                    "domain": cap.domain,
                    "latency_ms": cap.latency_ms,
                    "min_confidence": cap.min_confidence,
                }
                for mid, (_, cap) in self._registry.items()
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_classifier(self) -> Any:
        """Lazy-import and cache the query classifier."""
        if self._query_classifier is None:
            from ai.core.query_classifier import QueryClassifier

            self._query_classifier = QueryClassifier()
        return self._query_classifier

    def _resolve_candidates(self, query_type: str) -> List[str]:
        """Map a query type to an ordered list of candidate model IDs."""
        mapping: Dict[str, List[str]] = {
            "reflex": ["ed3n"],
            "greeting": ["ed3n"],
            "math": ["ed3n", "garden"],
            "logic": ["ed3n", "garden"],
            "knowledge": ["garden", "cloud"],
            "creative": ["cloud"],
            "opinion": ["cloud"],
            "command": ["ed3n", "garden"],
            "file": ["ed3n", "garden", "cloud"],
            "search": ["ed3n", "garden", "cloud"],
            "code": ["ed3n", "garden", "cloud"],
            "execute": ["ed3n", "garden", "cloud"],
            "task": ["ed3n", "garden", "cloud"],
            "vision": ["ed3n", "garden", "cloud"],
            "audio": ["ed3n", "garden", "cloud"],
        }
        candidates = mapping.get(query_type, list(self._registry.keys()))
        return [mid for mid in candidates if mid in self._registry]

    async def _try_model(
        self,
        model_id: str,
        query: str,
        context: Optional[Dict[str, Any]],
        domain: str,
    ) -> ModelRouteResult:
        """Try to process a query with a single model, measuring latency."""
        entry = self._registry.get(model_id)
        if entry is None:
            return ModelRouteResult(
                model_id=model_id,
                text="",
                confidence=0.0,
                latency_ms=0.0,
                domain=domain,
                error=f"Model '{model_id}' not registered",
            )

        engine, cap = entry
        t0 = time.perf_counter()
        error: Optional[str] = None

        try:
            if asyncio.iscoroutinefunction(engine.process):
                raw = await asyncio.wait_for(
                    engine.process(query, context=context),
                    timeout=self.default_timeout,
                )
            else:
                raw = await asyncio.wait_for(
                    asyncio.to_thread(engine.process, query, context=context),
                    timeout=self.default_timeout,
                )
        except asyncio.TimeoutError:
            raw = ""
            error = f"Timeout after {self.default_timeout}s"
            logger.error("Model '%s' timed out after %.1fs", model_id, self.default_timeout)
        except Exception as exc:
            raw = ""
            error = str(exc)
            logger.exception("Model '%s' raised during process(): %s", model_id, exc)

        elapsed = (time.perf_counter() - t0) * 1000

        if raw is not None and isinstance(raw, str) and len(raw) > 0:
            confidence = cap.min_confidence
        else:
            confidence = 0.0

        return ModelRouteResult(
            model_id=model_id,
            text=raw if isinstance(raw, str) else "",
            confidence=confidence,
            latency_ms=round(elapsed, 3),
            domain=domain,
            error=error,
        )

    @staticmethod
    def _pick_best(results: Dict[str, ModelRouteResult]) -> Dict[str, Any]:
        """Pick the result with the highest confidence."""
        best_id: Optional[str] = None
        best_conf = -1.0

        for mid, r in results.items():
            if r.confidence > best_conf:
                best_conf = r.confidence
                best_id = mid

        if best_id is None:
            return {
                "model_id": "none",
                "confidence": 0.0,
                "reason": "no models produced a result",
            }

        return {
            "model_id": best_id,
            "confidence": best_conf,
            "reason": f"best confidence ({best_conf:.2f}) across {len(results)} model(s)",
        }

    @staticmethod
    def _inject_pattern(engine: Any, trigger: str, response: str) -> bool:
        """Try to add a reflex pattern to an engine that supports it."""
        reflex = getattr(engine, "reflex", None)
        if reflex is not None:
            add = getattr(reflex, "add_pattern", None) or getattr(reflex, "add", None)
            if add is not None:
                add(trigger, response)
                return True
        return False
