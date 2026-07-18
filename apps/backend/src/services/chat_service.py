# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 職責: 聊天與對話服務 (Chat Service)
# 管理 Angela 的對話邏輯、意圖識別與回應合成。
# =============================================================================

import asyncio
import io
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服務 — 透過 AngelaLLMService 生成回應。"""

    def __init__(self, llm_service=None):
        self._llm_service = llm_service
        self._initialized = False
        self._continuous_learning = None
        self._garden_engine = None
        self._garden_learn_count = 0
        self._ed3n_learning_integration = None
        self._ham_sync_task: Optional[asyncio.Task] = None
        self._ham_sync_interval: int = 3600
        self._vector_store = None
        self._ham_memory = None
        self._training_coordinator = None
        self._cl_state_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "cl_state"
        )
        self._cultural_context = None

    @property
    def model_bus(self):
        """Return the ModelBus from the underlying LLM router, if available."""
        if self._llm_service and hasattr(self._llm_service, "model_bus"):
            return self._llm_service.model_bus
        return None

    def _detect_drive_intent(self, text: str) -> Optional[str]:
        """Detect a Google Drive intent from user text via config keywords.

        Returns ``"google_drive"`` when a configured drive keyword matches,
        otherwise ``None``.
        """
        if not text:
            return None
        try:
            from core.config_loader import get_angela_config

            keywords = get_angela_config().get_intent_keywords("google_drive")
        except Exception:
            keywords = []
        lowered = text.lower()
        for kw in keywords:
            if not kw:
                continue
            if kw.lower() in lowered:
                return "google_drive"
        return None

    async def _ham_sync_loop(self) -> None:
        """Background task: sync ED3N dictionary to HAM memory periodically."""
        while True:
            try:
                await asyncio.sleep(self._ham_sync_interval)
                if self._ed3n_learning_integration:
                    result = self._ed3n_learning_integration.synchronize_knowledge()
                    synced = result.get("synced", 0)
                    errors = result.get("errors", [])
                    if synced > 0:
                        logger.info("HAM sync: %d ED3N entries synchronized", synced)
                    if errors:
                        logger.warning("HAM sync errors: %s", errors[:3])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("HAM sync loop error: %s", e)

    async def initialize(self) -> None:
        if self._initialized:
            return
        if self._llm_service is None:
            from services.llm.router import get_llm_service

            self._llm_service = await get_llm_service()
        try:
            from ai.ed3n.continuous_learning import ContinuousLearningPipeline
            from ai.ed3n.ed3n_engine import ED3NEngine

            engine = ED3NEngine.get_shared()
            from ai.ed3n.ed3n_trainer import ED3NTrainer

            trainer = ED3NTrainer(engine)
            state_path = os.path.join(self._cl_state_dir, "cl_state.json")
            if await asyncio.to_thread(os.path.exists, state_path):
                self._continuous_learning = ContinuousLearningPipeline.load(
                    self._cl_state_dir, engine=engine, trainer=trainer
                )
                logger.info("Loaded CL state from %s", state_path)
            else:
                self._continuous_learning = ContinuousLearningPipeline(
                    engine=engine,
                    trainer=trainer,
                    growth_interval=15,
                    train_interval=50,
                    min_examples_for_train=30,
                )
                engine._continuous_learning = self._continuous_learning
            logger.info("CLP wired into ED3NEngine for _maybe_learn()")
        except Exception as e:
            logger.warning("Continuous learning init skipped: %s", e)
        # Initialize TrainingCoordinator for domain training orchestration
        try:
            from api.lifespan import get_training_coordinator

            self._training_coordinator = get_training_coordinator()
            logger.info("TrainingCoordinator wired into ChatService")
        except Exception as e:
            logger.debug("TrainingCoordinator not available: %s", e)
        # Initialize GARDEN engine for continuous learning (Phase 4.5)
        try:
            from ai.garden.garden_engine import GARDENEngine

            self._garden_engine = GARDENEngine(compatibility_mode=True)
            self._garden_engine.load_presets()
            logger.info("GARDEN engine initialized for continuous learning")
        except Exception as e:
            logger.warning("GARDEN engine init skipped: %s", e)
        # Initialize ED3N learning integration for HAM sync (Phase 5.2)
        try:
            from ai.ed3n.learning_integration import ED3NLearningIntegration

            cl_engine = self._continuous_learning.engine if self._continuous_learning else None
            self._ed3n_learning_integration = ED3NLearningIntegration(engine=cl_engine)
            logger.info("ED3N learning integration initialized")
        except Exception as e:
            logger.warning("ED3N learning integration init skipped: %s", e)
        # Initialize VectorMemoryStore for semantic memory retrieval (Phase 5.3)
        try:
            from ai.memory.vector_store import VectorMemoryStore

            self._vector_store = VectorMemoryStore()
            logger.info("VectorStore initialized with %d vectors", self._vector_store.vector_count)
        except Exception as e:
            logger.warning("VectorStore init skipped: %s", e)
        # Initialize HAM memory for template-based retrieval (Phase 5.3)
        try:
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager

            self._ham_memory = HAMMemoryManager()
            stats = self._ham_memory.get_stats()
            logger.info(
                "HAM memory initialized: %d templates, %d conversations",
                stats.get("template_count", 0),
                stats.get("conversation_count", 0),
            )
        except Exception as e:
            logger.warning("HAM memory init skipped: %s", e)
        # Initialize CulturalContextModule
        try:
            from ai.context.cultural_context import CulturalContextModule

            self._cultural_context = CulturalContextModule()
            logger.info("CulturalContextModule initialized")
        except Exception as e:
            logger.debug("CulturalContextModule init skipped: %s", e)
        self._initialized = True
        logger.info("ChatService initialized")
        # Start periodic HAM sync background task (Phase 5.2)
        if self._ed3n_learning_integration:
            self._ham_sync_task = asyncio.create_task(self._ham_sync_loop())

    async def generate_response(self, user_message: str, user_name: str = "", context: dict = None):
        """Generate Angela's response to a user message."""
        if not self._initialized:
            await self.initialize()

        merged_context = context or {}
        merged_context.setdefault("user_name", user_name)

        merged_context = self._inject_cultural_context(merged_context, user_message)
        merged_context = await self._inject_memory_context(merged_context, user_message)
        merged_context, mm_adapter = await self._inject_multimodal_context(
            merged_context, user_message
        )
        merged_context = self._inject_grounded_context(merged_context, user_message)
        merged_context = await self._maybe_search_and_ground(user_message, merged_context)

        response = await self._llm_service.generate_response(user_message, merged_context)
        response = self._post_process_response(response, merged_context)

        await self._process_multimodal_output(response, merged_context, mm_adapter)
        await self._process_continuous_learning(user_message, response, merged_context)
        await self._process_garden_learning(user_message, response)
        self._schedule_grounded_learning(user_message, response)
        await self._store_interaction_memories(user_message, response)

        return response

    def _inject_cultural_context(self, merged_context: dict, user_message: str) -> dict:
        if self._cultural_context is None:
            return merged_context
        try:
            lang = merged_context.get("language", "")
            return self._cultural_context.enrich_context(
                merged_context, user_message, language_code=lang
            )
        except Exception as e:
            logger.debug("Cultural context enrichment skipped: %s", e)
        return merged_context

    async def _inject_memory_context(self, merged_context: dict, user_message: str) -> dict:
        if self._vector_store is not None:
            try:
                # Vector search is an enrichment only — never block the answer path.
                # Some backends (e.g. chromadb PersistentClient) are pathologically
                # slow to query in certain environments, so bound it tightly and
                # degrade gracefully when it overruns.
                vs_results = await asyncio.wait_for(
                    self._vector_store.semantic_search(user_message, 3),
                    timeout=1.0,
                )
                docs = vs_results.get("documents", [[]])[0]
                knowledge = [str(d)[:200] for d in docs if d and isinstance(d, str)]
                if knowledge:
                    merged_context["dictionary_context"] = knowledge
            except asyncio.TimeoutError:
                logger.debug("VectorStore query skipped (exceeded 1.0s budget)")
            except Exception as e:
                logger.debug("VectorStore query failed: %s", e)
        if self._ham_memory is not None:
            try:
                ham_results = await self._ham_memory.retrieve_response_templates(
                    user_message, top_k=3, min_score=0.3
                )
                memories = []
                for tpl, score in ham_results:
                    content = tpl.get("content", "")
                    if content:
                        memories.append(f"[past:{score:.2f}] {str(content)[:200]}")
                if memories:
                    merged_context["conversation_memory"] = memories
            except Exception as e:
                logger.debug("HAM memory query failed: %s", e)
        if "dictionary_context" in merged_context or "conversation_memory" in merged_context:
            logger.debug(
                "Memory context injected: dict=%d, conv=%d",
                len(merged_context.get("dictionary_context", [])),
                len(merged_context.get("conversation_memory", [])),
            )
        return merged_context

    async def _inject_multimodal_context(self, merged_context: dict, user_message: str):
        image_analysis = merged_context.get("image_analysis")
        mm_adapter = None
        if image_analysis and isinstance(image_analysis, dict):
            image_data = image_analysis.get("image_data")
            if image_data:
                try:
                    from ai.multimodal.multimodal_ed3n_adapter import MultimodalED3NAdapter

                    mm_adapter = MultimodalED3NAdapter()
                    mm_adapter.index_image_for_retrieval(
                        image_data,
                        key=f"chat_{abs(hash(image_data[:100])) & 0xFFFFFFFF:08x}",
                        label=merged_context.get("user_name", "user"),
                        metadata={"source": "chat_service", "message": user_message[:100]},
                    )
                    merged_context = mm_adapter.inject_into_context(
                        merged_context, image_data=image_data, top_k=3
                    )
                except Exception as e:
                    logger.debug("Multimodal retrieval failed (non-critical): %s", e)
        return merged_context, mm_adapter

    def _inject_grounded_context(self, merged_context: dict, user_message: str) -> dict:
        """Inject VERIFIED grounded-knowledge snippets (cheap local lookup)."""
        try:
            from ai.memory.grounded_learning_manager import get_grounded_learning_manager

            block = get_grounded_learning_manager().get_grounded_context(user_message)
            if block:
                merged_context["grounded_context"] = block
                logger.debug("Grounded context injected (%d chars)", len(block))
        except Exception as e:
            logger.debug("Grounded context injection skipped: %s", e)
        return merged_context

    async def _maybe_search_and_ground(self, user_message: str, merged_context: dict) -> dict:
        """Proactively web-search to ground an uncertain factual query.

        Only triggers when: (1) the query looks like a factual question, (2) we have
        NO verified knowledge for it yet (grounded_context empty), and (3) it is not an
        explicit search intent (WebSearchHandler owns those). The search result is
        injected as ``web_search_context`` for THIS answer and stored as VERIFIED knowledge
        so future identical queries skip the live search.

        Runs with a tight timeout so the answer path stays within seconds. Any failure
        is swallowed - the LLM still answers unaugmented.
        """
        try:
            from ai.memory.claim_extractor import is_searchable_query

            if not is_searchable_query(user_message):
                return merged_context
            # already have verified knowledge -> no need to search again
            if merged_context.get("grounded_context"):
                return merged_context

            from ai.memory.grounded_learning_manager import get_grounded_learning_manager
            from core.tools.web_search_tool import WebSearchTool

            tool = WebSearchTool()
            ws_cfg = {}
            try:
                from core.system.config.tiered_loader import get_config

                ws_cfg = get_config("system/llm").get("web_search", {}) or {}
            except Exception:
                pass
            ws_timeout = float(ws_cfg.get("timeout", 2.5))
            ws_top = int(ws_cfg.get("max_results", 3))
            results = await asyncio.wait_for(
                asyncio.to_thread(tool.search, user_message, ws_top), timeout=ws_timeout
            )
            usable = [r for r in results if isinstance(r, dict) and "error" not in r]
            if not usable:
                return merged_context

            lines = []
            for r in usable[:ws_top]:
                title = r.get("title", "")
                snippet = (r.get("snippet") or "").strip()
                url = r.get("url", "")
                line = f"- {title}"
                if snippet:
                    line += f": {snippet}"
                if url:
                    line += f" ({url})"
                lines.append(line)
            merged_context["web_search_context"] = "\n".join(lines)

            # remember as verified knowledge (sources = the search hits)
            get_grounded_learning_manager().learn_verified_from_search(user_message, usable)
            logger.debug("Proactive web grounding applied (%d results)", len(usable))
        except Exception as e:
            logger.debug("Proactive web grounding skipped: %s", e)
        return merged_context

    async def _process_multimodal_output(self, response, merged_context: dict, mm_adapter) -> None:
        if mm_adapter is None or not merged_context.get("multimodal_entries"):
            return
        try:
            top_entry = merged_context["multimodal_entries"][0]
            latent = top_entry.get("vector")
            if latent and len(latent) >= 64:
                from ai.multimodal.multimodal_bridge import MultimodalBridge

                bridge = MultimodalBridge()
                decoded_img = bridge.decode_latent_to_image(latent[:64])
                if decoded_img is not None:
                    buf = io.BytesIO()
                    decoded_img.save(buf, format="PNG")
                    response.metadata["generated_image"] = buf.getvalue().hex()
                decoded_wav = bridge.decode_latent_to_waveform(latent[:64])
                if decoded_wav is not None:
                    response.metadata["generated_audio"] = decoded_wav[:16000]
        except Exception as e:
            logger.debug("Multimodal decode output failed (non-critical): %s", e)

    async def _process_continuous_learning(
        self, user_message: str, response, merged_context: dict
    ) -> None:
        if not self._continuous_learning:
            return
        try:
            if self._training_coordinator:
                if await self._training_coordinator.should_skip("general", user_message):
                    logger.debug("Skipping continuous learning — duplicate input")
                    return
            await self._continuous_learning.process_interaction_async(
                user_message, response.text, merged_context
            )
            if self._training_coordinator:
                await self._training_coordinator.record_training(
                    "general",
                    "ed3n",
                    1,
                    0.5,
                    [{"input": user_message, "output": response.text}],
                )
        except Exception as e:
            logger.warning("Continuous learning interaction failed: %s", e)

    async def _process_garden_learning(self, user_message: str, response) -> None:
        if not self._garden_engine:
            return
        try:
            if self._training_coordinator:
                if await self._training_coordinator.should_skip("knowledge", user_message):
                    logger.debug("Skipping GARDEN learning — duplicate input")
                    return
            self._garden_engine.learn_from_interaction(user_message, response.text)
            self._garden_learn_count += 1
            if self._training_coordinator:
                await self._training_coordinator.record_training(
                    "knowledge",
                    "garden",
                    1,
                    0.5,
                    [{"input": user_message, "output": response.text}],
                )
            if self._garden_learn_count % 100 == 0:
                garden_state_dir = os.path.join(self._cl_state_dir, "garden_state")
                await asyncio.to_thread(os.makedirs, garden_state_dir, exist_ok=True)
                await asyncio.to_thread(self._garden_engine.save, garden_state_dir)
                logger.info("GARDEN engine saved after %d interactions", self._garden_learn_count)
        except Exception as e:
            logger.debug("GARDEN learning failed: %s", e)

    def _schedule_grounded_learning(self, user_message: str, response) -> None:
        """Fire-and-forget: extract claims and verify them in the background.

        Must NOT be awaited — verification runs web searches off the answer
        path so the user-perceived latency stays within seconds.
        """
        try:
            from ai.memory.grounded_learning_manager import get_grounded_learning_manager

            mgr = get_grounded_learning_manager()
            resp_text = getattr(response, "text", str(response))
            asyncio.create_task(mgr.queue_claims(user_message, resp_text))
        except Exception as e:
            logger.debug("Grounded learning schedule skipped: %s", e)

    async def _store_interaction_memories(self, user_message: str, response) -> None:
        # Vector-store writes are best-effort and must NOT block the answer path.
        # chromadb PersistentClient.add can take several seconds in some
        # environments, so we offload it to a background task (fire-and-forget),
        # mirroring how grounded-learning verification is already decoupled.
        if self._vector_store is not None:
            try:
                import uuid as _uuid

                memory_id = f"chat_{_uuid.uuid4().hex[:12]}"
                content = f"User: {user_message}\nAngela: {response.text}"
                asyncio.create_task(
                    self._vector_store.add_memory(memory_id, content, {"type": "conversation"})
                )
            except Exception as e:
                logger.debug("VectorStore memory store failed: %s", e)
        if getattr(self._llm_service, "enable_memory_enhancement", False):
            try:
                mm = getattr(self._llm_service, "memory_manager", None)
                if mm:
                    asyncio.create_task(
                        mm.store_experience(
                            raw_data={"user": user_message, "assistant": response.text},
                            data_type="conversation",
                        )
                    )
            except Exception as e:
                logger.debug("Memory store failed: %s", e)

    def _post_process_response(self, response, context: dict):
        """Enrich response with biological/emotional state context.

        Stores bio_state snapshot in response metadata for all routes.
        Does NOT modify the response text — enrichment is metadata-only.
        """
        if not response or not response.text:
            return response

        bio_state = context.get("bio_state")
        emotion = context.get("emotion")

        if bio_state and hasattr(response, "bio_state"):
            response.bio_state = bio_state

        if emotion:
            if hasattr(response, "emotion"):
                response.emotion = emotion.get("emotion", "neutral")
            if hasattr(response, "emotion_confidence"):
                response.emotion_confidence = emotion.get("confidence", 0.5)
            if hasattr(response, "emotion_intensity"):
                response.emotion_intensity = emotion.get("intensity", 0.5)

        if response.metadata is None:
            response.metadata = {}
        response.metadata["bio_enriched"] = bool(bio_state)

        return response

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """Generate text via the underlying LLM service.

        Proxies to AngelaLLMService.generate_text() for use by
        document_router and other subsystems that need raw text
        generation without full chat context injection.
        """
        if not self._llm_service:
            logger.warning("ChatService.generate_text: LLM service not available")
            return None
        try:
            if not hasattr(self._llm_service, "generate_text"):
                logger.warning("ChatService.generate_text: LLM service has no generate_text method")
                return None
            return await self._llm_service.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.warning("ChatService.generate_text failed: %s", e)
            return None

    async def shutdown(self) -> None:
        self._initialized = False
        # Stop HAM sync background task (Phase 5.2)
        if self._ham_sync_task:
            self._ham_sync_task.cancel()
            try:
                await self._ham_sync_task
            except asyncio.CancelledError:
                pass
        # Final HAM sync on shutdown
        if self._ed3n_learning_integration:
            try:
                result = self._ed3n_learning_integration.synchronize_knowledge()
                logger.info("Final HAM sync on shutdown: %d entries", result.get("synced", 0))
            except Exception as e:
                logger.debug("Final HAM sync failed: %s", e)
        if self._continuous_learning:
            report = self._continuous_learning.get_learning_report()
            logger.info("Continuous learning final report:\n%s", report)
            try:
                await asyncio.to_thread(self._continuous_learning.save, self._cl_state_dir)
            except Exception as e:
                logger.warning("Failed to save CL state: %s", e)
        # Save GARDEN engine state
        if self._garden_engine:
            try:
                garden_state_dir = os.path.join(self._cl_state_dir, "garden_state")
                await asyncio.to_thread(os.makedirs, garden_state_dir, exist_ok=True)
                await asyncio.to_thread(self._garden_engine.save, garden_state_dir)
                logger.info("GARDEN engine saved on shutdown")
            except Exception as e:
                logger.warning("Failed to save GARDEN state: %s", e)
        logger.info("ChatService shutdown")


# Backward-compatible alias (historical public name).
AngelaChatService = ChatService

__all__ = ["ChatService", "AngelaChatService"]
