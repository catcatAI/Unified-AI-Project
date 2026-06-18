"""
Angela LLM Service - Angela 的智能對話引擎
============================================
這是 Angela 的核心大腦服務，負責：
1. 調用本地或遠端 LLM 模型
2. 整合 Angela 的認知系統
3. 生成符合 Angela 個性的回應

這個服務不是讓模型直接與用戶對話，
而是讓 Angela 作為中介，調用模型來產生回應。
"""

import asyncio
import os
from core.system.config.network_defaults import (
    OLLAMA_HOST,
    LLAMACPP_HOST,
    OPENAI_API_BASE,
    ANTHROPIC_API_BASE,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_GOOGLE_MODEL,
    LLM_REQUEST_TIMEOUT,
)
import time
import random
import re
import logging
from typing import Dict, Any, Optional, List, NamedTuple

from core.interfaces.service_registry import get_registry
from core.interfaces.protocols import ChatMessage, LLMResponse, ChatResponse

try:
    from ai.response.neuro_auto_selector import AutoDecision, AutoBackendChoice
except ImportError:
    AutoDecision = None
    AutoBackendChoice = None

# LLM provider backends
from services.llm.providers.base import BaseLLMBackend
from services.llm.providers.registry import LLMBackend
from services.llm.providers.llamacpp import LlamaCppBackend
from services.llm.providers.ollama import OllamaBackend
from services.llm.providers.openai import OpenAIAPIBackend
from services.llm.providers.anthropic import AnthropicAPIBackend
from services.llm.providers.google import GoogleAPIBackend
from services.llm.providers.ed3n import ED3NBackend
from services.llm.providers.garden import GARDENBackend

# Model Bus pipeline
from ai.core.model_bus import ModelBus
from ai.core.query_classifier import QueryClassifier

# Prompt builder utilities
from services.llm.prompt_builder import (
    get_biological_state,
    get_formula_summaries,
    construct_angela_prompt,
)

# 簡單日誌設置
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("angela_llm")

# Known fallback/error strings from engines — never return these as direct hits
_KNOWN_FALLBACK_RESPONSES = frozenset({
    "抱歉，我没理解你的意思。",
    "抱歉，我沒理解你的意思。",
})


class GenerationParams(NamedTuple):
    """Immutable per-request generation parameters — avoids self._gen_* race condition."""
    timeout: float = 30.0
    temperature: float = 0.7
    max_tokens: int = 512


# Lazy import for memory enhancement system - deferred until first use
_memory_modules_loaded = False
_MEMORY_ENHANCED = None
HAMMemoryManager = None
AngelaState = None
UserImpression = None
MemoryTemplate = None
PrecomputeService = None
PrecomputeTask = None
get_template_library = None
TaskGenerator = None

# New subsystem imports (extracted from this module)
from services.llm.emotion_analyzer import EmotionAnalyzer
from services.llm.memory_integration import MemoryIntegration

def _load_memory_modules() -> str:
    """Lazy load memory enhancement modules on first access"""
    global _memory_modules_loaded, _MEMORY_ENHANCED
    global HAMMemoryManager, AngelaState, UserImpression, MemoryTemplate
    global PrecomputeService, PrecomputeTask, get_template_library, TaskGenerator

    if _memory_modules_loaded:
        return _MEMORY_ENHANCED

    _memory_modules_loaded = True

    try:
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager as _HAM
        from ai.memory.memory_template import (
            AngelaState as _AS,
            UserImpression as _UI,
            MemoryTemplate as _MT,
        )
        from ai.memory.precompute_service import (
            PrecomputeService as _PS,
            PrecomputeTask as _PT,
        )
        from ai.memory.template_library import get_template_library as _GTL
        from ai.memory.task_generator import TaskGenerator as _TG

        HAMMemoryManager = _HAM
        AngelaState = _AS
        UserImpression = _UI
        MemoryTemplate = _MT
        PrecomputeService = _PS
        PrecomputeTask = _PT
        get_template_library = _GTL
        TaskGenerator = _TG

        _MEMORY_ENHANCED = True
        logger.info("Memory enhancement modules loaded successfully")
    except ImportError as e:
        logger.warning(f"Memory enhancement modules not available: {e}", exc_info=True)
        logger.info("Running without memory enhancement (LLM will be called directly)")
        _MEMORY_ENHANCED = False

    return _MEMORY_ENHANCED


def is_memory_enhanced():
    """Lazy check if memory enhancement is available"""
    if _MEMORY_ENHANCED is None:
        _load_memory_modules()
    return _MEMORY_ENHANCED


# For backward compatibility — callable, NOT a bool. Use is_memory_enhanced() for bool checks.
def MEMORY_ENHANCED():
    """Check if memory enhancement modules are available. Must be called: MEMORY_ENHANCED(), not if MEMORY_ENHANCED."""
    return is_memory_enhanced()
class AngelaLLMService:
    """
    Angela 的 LLM 服務 - 核心大腦
    ================================
    這個服務不是讓模型直接與用戶對話，
    而是讓 Angela 作為中介，調用模型來產生回應。

    設計原則：
    1. Angela 是對話的中介者
    2. 模型回應必須經過 Angela 的個性化處理
    3. 整合 Angela 的認知和情感系統
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化 LLM 服務"""
        if getattr(self, "_initialized", False):
            return

        self.config = config or self._get_default_config()
        self.backends: Dict[LLMBackend, BaseLLMBackend] = {}
        self.active_backend: Optional[BaseLLMBackend] = None

        self.enable_memory_enhancement = self.config.get("enable_memory_enhancement", True)
        self.is_available = False

        # [auto] LLM mode
        self.llm_mode = self.config.get("llm_mode", "standard")
        self.auto_selector = None

        self._initialized = True

        # Model Bus capability-based routing
        self.model_bus: Optional[ModelBus] = None
        self.query_classifier: Optional[QueryClassifier] = None

        # 初始化各後端
        self._init_backends()

        # ========== 基础统计信息（无条件初始化）==========
        # 修复：无论 MEMORY_ENHANCED 如何，都必须初始化 stats
        # 否则在 generate_response 中访问 self.stats 会导致 AttributeError
        self.stats = {
            "total_requests": 0,
            "memory_hits": 0,
            "llm_calls": 0,
            "memory_hit_rate": 0.0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "composed_responses": 0,
            "hybrid_responses": 0,
            "token_savings_rate": 0.0,
        }

        # ========== P0-2: Response Composition & Matching System ==========
        self._init_response_system()

        # ========== 情感识别系统（委派到 EmotionAnalyzer）==========
        self.emotion_analyzer = EmotionAnalyzer()

        # ========== 记忆集成系统（委派到 MemoryIntegration）==========
        self.memory_integration = MemoryIntegration(self)

        self._angela_routing = self.config.get("_routing_policy", {})
        self._angela_fallback_chain = self.config.get("_fallback_chain", [])
        self._angela_intent_routing = self.config.get("_intent_routing", {})

    def _init_response_system(self) -> None:
        """初始化 P0-2 响应组合与匹配系统"""
        try:
            from ai.response.template_matcher import TemplateMatcher
            from ai.response.composer import ResponseComposer
            from ai.response.deviation_tracker import DeviationTracker, ResponseRoute

            self.template_matcher = TemplateMatcher()
            self.response_composer = ResponseComposer()
            self.deviation_tracker = DeviationTracker()
            self.ResponseRoute = ResponseRoute

            logger.info("P0-2 Response Composition & Matching System initialized")
        except ImportError as e:
            logger.warning(f"Failed to initialize P0-2 response system: {e}", exc_info=True)
            self.template_matcher = None
            self.response_composer = None
            self.deviation_tracker = None

    def _load_templates_to_matcher(self) -> None:
        """加载模板库到匹配器"""
        if not hasattr(self, "template_matcher"):
            return

        try:
            if hasattr(self, "template_library"):
                templates = self.template_library.get_all_templates()
                for template in templates:
                    self.template_matcher.add_template(
                        template_id=template.id,
                        content=template.content,
                        patterns=[template.id],
                        keywords=template.keywords,
                        metadata=template.metadata,
                    )
                logger.info(f"Loaded {len(templates)} templates to matcher")
        except Exception as e:
            logger.warning(f"Failed to load templates to matcher: {e}", exc_info=True)

    def _init_memory_enhancement(self) -> None:
        """初始化记忆增强系统（HAM + LU + CDM + 预计算 + 模板库）"""
        if not is_memory_enhanced():
            self.enable_memory_enhancement = False
            return

        try:
            self.memory_manager = HAMMemoryManager()
            self.enable_memory_enhancement = True

            try:
                from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator
                logic_unit = None
                cdm_model = None
                try:
                    from ai.memory.lu_logic.logic_unit import LogicUnit
                    logic_unit = LogicUnit(max_rules=500)
                except Exception as e:
                    logger.warning("Failed to import LogicUnit: %s", e, exc_info=True)
                try:
                    from core.cdm_dividend_model import CDMCognitiveDividendModel
                    cdm_model = CDMCognitiveDividendModel()
                except Exception as e:
                    logger.warning("Failed to import CDMCognitiveDividendModel: %s", e, exc_info=True)
                self.memory_coordinator = UnifiedMemoryCoordinator(
                    memory_manager=self.memory_manager,
                    logic_unit=logic_unit,
                    cdm_model=cdm_model,
                )
                logger.info("[C1] UnifiedMemoryCoordinator initialized")
            except Exception as e:
                logger.warning(f"[C1] UnifiedMemoryCoordinator unavailable: {e}", exc_info=True)
                self.memory_coordinator = None

            _mem_cfg = _get_llm_config("memory", {})
            self.precompute_service = PrecomputeService(config=_mem_cfg)

            self.template_library = get_template_library()
            self._load_templates_to_matcher()

            self.task_generator = TaskGenerator(config={"max_tasks": 10})

            logger.info("Memory enhancement system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize memory enhancement: {e}", exc_info=True)
            self.enable_memory_enhancement = False


    def _get_default_config(self) -> Dict[str, Any]:
        """從分層配置系統讀取 LLM 配置 [Phase 7]"""
        from core.system.config.tiered_loader import get_config
        config = get_config("system/llm")
        if config:
            logger.info(f"LLM 配置已從 TieredConfig 載入 ({len(config)} items)")
            return config

        # Fallback to absolute bare-minimum if even TieredConfig fails
        return {
            "ollama": {
                "provider": "ollama",
                "base_url": OLLAMA_HOST,
                "model_name": DEFAULT_OLLAMA_MODEL,
                "enabled": True,
            },
            "_fallback_chain": ["ollama"],
        }

    def reload_config(self, new_config: Optional[Dict[str, Any]] = None) -> None:
        """
        [Phase 6] 熱加載配置。
        允許在不重啟進程的情況下演化 LLM 後端。
        """
        logger.info("🔄 [LLMService] Reloading configuration...")
        if new_config:
            self.config = new_config
        else:
            self.config = self._get_default_config()

        # 清空舊後端並重新初始化
        self.backends = {}
        self._init_backends()

        # 更新狀態廣播
        from core.system.state_store import state_store
        state_store.update_state("hardware", {"active_llm": getattr(self.active_backend, "model", "unknown")})
        logger.info("✅ [LLMService] Configuration hot-reloaded.")

    def _init_backends(self) -> None:
        """初始化可用的後端（支援所有 provider 類型）"""
        for backend_id, backend_config in self.config.items():
            if not isinstance(backend_config, dict):
                continue
            if not backend_config.get("enabled", False):
                continue

            provider = backend_config.get("provider", "").lower()
            base_url = backend_config.get("base_url", "")
            model_name = backend_config.get("model_name", "")
            api_key = backend_config.get("api_key", "") or os.environ.get(backend_config.get("api_key_env", ""), "")

            if provider in ("llama_cpp", "llamacpp") or backend_id == "llamacpp-local":
                self.backends[LLMBackend.LLAMA_CPP] = LlamaCppBackend(
                    base_url=base_url or LLAMACPP_HOST,
                    model=model_name,
                    timeout=backend_config.get("timeout", LLM_REQUEST_TIMEOUT),
                )
                logger.info(f"已注冊 llama.cpp 後端: {model_name}")

            elif provider == "ollama" or backend_id.startswith("ollama"):
                if LLMBackend.OLLAMA not in self.backends:
                    self.backends[LLMBackend.OLLAMA] = OllamaBackend(
                        base_url=base_url or OLLAMA_HOST,
                        model=model_name or DEFAULT_OLLAMA_MODEL,
                        api_key=api_key,
                        timeout=backend_config.get("timeout", LLM_REQUEST_TIMEOUT),
                    )
                    logger.info(f"已注冊 Ollama 後端: {model_name}")

            elif provider == "openai" and api_key:
                self.backends[LLMBackend.OPENAI] = OpenAIAPIBackend(
                    api_key=api_key,
                    base_url=base_url or OPENAI_API_BASE,
                    model=model_name or DEFAULT_OPENAI_MODEL,
                    timeout=backend_config.get("timeout", LLM_REQUEST_TIMEOUT),
                )
                logger.info(f"已注冊 OpenAI 後端: {model_name}")

            elif provider == "anthropic" and api_key:
                self.backends[LLMBackend.ANTHROPIC] = AnthropicAPIBackend(
                    api_key=api_key,
                    base_url=base_url or ANTHROPIC_API_BASE,
                    model=model_name or DEFAULT_ANTHROPIC_MODEL,
                    timeout=backend_config.get("timeout", LLM_REQUEST_TIMEOUT),
                )
                logger.info(f"已注冊 Anthropic 後端: {model_name}")

            elif provider == "google" and api_key:
                self.backends[LLMBackend.GOOGLE] = GoogleAPIBackend(
                    api_key=api_key,
                    model=model_name or DEFAULT_GOOGLE_MODEL,
                    timeout=backend_config.get("timeout", LLM_REQUEST_TIMEOUT),
                )
                logger.info(f"已注冊 Google Gemini 後端: {model_name}")

            elif provider == "ed3n":
                self.backends[LLMBackend.ED3N] = ED3NBackend(
                    base_url=base_url or "",
                    model=model_name or "ed3n-v1",
                    timeout=backend_config.get("timeout", 30.0),
                )
                logger.info(f"已注冊 ED3N 後端: {model_name or 'ed3n-v1'}")

            elif provider == "garden":
                self.backends[LLMBackend.GARDEN] = GARDENBackend(
                    model=model_name or "garden-1g",
                    checkpoint=backend_config.get("checkpoint", ""),
                    timeout=backend_config.get("timeout", 30.0),
                )
                logger.info(f"已注冊 GARDEN 後端: {model_name or 'garden-1g'}")

    async def initialize(self) -> bool:
        """初始化服務，檢測可用的後端
        返回: 是否至少有一個可用的後端
        """
        logger.info("正在初始化 Angela LLM 服務...")

        # 初始化記憶增強系統
        self._init_memory_enhancement()

        # [auto] mode: use NeuroAutoSelector for initial backend selection
        if self.llm_mode == "auto":
            try:
                from ai.response.neuro_auto_selector import NeuroAutoSelector

                self.auto_selector = NeuroAutoSelector(config=self.config)
                result = await self.auto_selector.decide(context={})

                if result.backend.value != "neuroblender":
                    # Map AutoBackendChoice to LLMBackend
                    backend_map = {
                        "ollama": LLMBackend.OLLAMA,
                        "llamacpp": LLMBackend.LLAMA_CPP,
                        "openai": LLMBackend.OPENAI,
                        "anthropic": LLMBackend.ANTHROPIC,
                        "google": LLMBackend.GOOGLE,
                    }
                    mapped = backend_map.get(result.backend.value)
                    if mapped and mapped in self.backends:
                        self.active_backend = self.backends[mapped]
                        self.active_backend_type = mapped
                        self.is_available = True
                        logger.info(
                            f"[auto] 初始化完成，使用 {result.backend.value}/{result.model} "
                            f"(hw={result.hw_score:.0f}, budget={result.time_budget_ms}ms)"
                        )
                        return True

                logger.warning("[auto] NeuroAutoSelector 未能選擇可用後端，使用標準初始化", exc_info=True)
            except Exception as e:
                logger.warning(f"[auto] NeuroAutoSelector 初始化失敗: {e}，使用標準初始化", exc_info=True)

        # 標準初始化：檢查各後端健康狀態
        available_backends = []

        for backend_type, backend in self.backends.items():
            if await backend.check_health():
                available_backends.append(backend_type)
                logger.info(f"✓ {backend_type.value} 後端可用")

        if available_backends:
            # 選擇最佳後端 (優先順序: llama.cpp > Ollama > OpenAI > Anthropic > Google)
            priority = [
                LLMBackend.LLAMA_CPP,
                LLMBackend.OLLAMA,
                LLMBackend.OPENAI,
                LLMBackend.ANTHROPIC,
                LLMBackend.GOOGLE,
                LLMBackend.GARDEN,
                LLMBackend.ED3N,
            ]
            for backend_type in priority:
                if backend_type in available_backends:
                    self.active_backend = self.backends[backend_type]
                    self.active_backend_type = backend_type
                    break

            # Initialize Model Bus
            try:
                self.model_bus = ModelBus()
                self.query_classifier = QueryClassifier()

                # Register ED3N if available
                if LLMBackend.ED3N in self.backends:
                    ed3n_backend = self.backends[LLMBackend.ED3N]
                    if hasattr(ed3n_backend, '_engine') and ed3n_backend._engine:
                        self.model_bus.register_ed3n(ed3n_backend._engine)
                    else:
                        from ai.ed3n.ed3n_engine import ED3NEngine
                        self.model_bus.register_ed3n(ED3NEngine.get_shared())

                # Register GARDEN if available
                if LLMBackend.GARDEN in self.backends:
                    garden_backend = self.backends[LLMBackend.GARDEN]
                    if hasattr(garden_backend, '_engine') and garden_backend._engine:
                        self.model_bus.register_garden(garden_backend._engine)
                    else:
                        from ai.garden.garden_engine import GARDENEngine
                        engine = GARDENEngine(compatibility_mode=True)
                        engine.load_presets()
                        self.model_bus.register_garden(engine)

                # Register active backend as cloud
                if self.active_backend:
                    self.model_bus.register_cloud(self.active_backend)

                # Register handlers for FILE/SEARCH/CODE/TASK/VISION intents
                try:
                    from services.handlers.file_operation_handler import FileOperationHandler
                    from services.handlers.web_search_handler import WebSearchHandler
                    from services.handlers.code_execution_handler import CodeExecutionHandler
                    from services.handlers.system_command_handler import SystemCommandHandler
                    from services.handlers.task_manager_handler import TaskManagerHandler
                    from services.handlers.vision_handler import VisionHandler
                    self.model_bus.register_handler("file_ops", FileOperationHandler(), ["file"])
                    self.model_bus.register_handler("web_search", WebSearchHandler(), ["search"])
                    self.model_bus.register_handler("code_exec", CodeExecutionHandler(), ["code", "execute"])
                    self.model_bus.register_handler("system_cmd", SystemCommandHandler(), ["system"])
                    self.model_bus.register_handler("task_mgr", TaskManagerHandler(), ["task"])
                    self.model_bus.register_handler("vision", VisionHandler(), ["vision"])
                    logger.info("Model Bus handlers registered: file_ops, web_search, code_exec, system_cmd, task_mgr, vision")
                except Exception as e:
                    logger.warning(f"Model Bus handler registration skipped: {e}")

                logger.info("Model Bus initialized with %d models", len(self.model_bus._registry))
            except Exception as e:
                logger.warning(f"Model Bus initialization skipped: {e}")

            self.is_available = True
            backend_name = self.active_backend_type.value if self.active_backend_type else "none"
            logger.info(f"Angela LLM 服務初始化完成，使用 {backend_name} 後端")
            logger.info(f"可用後端: {[b.value for b in available_backends]}")
            return True
        else:
            logger.warning("沒有可用的 LLM 後端，將使用備份回應機制", exc_info=True)
            self.enable_memory_enhancement = self.config.get("enable_memory_enhancement", True)
            self.is_available = False
            return False

    async def shutdown(self) -> None:
        """Close all backend HTTP sessions during app shutdown."""
        for backend_type, backend in self.backends.items():
            try:
                if hasattr(backend, 'close'):
                    await backend.close()
            except Exception as e:
                logger.debug(f"Backend {backend_type.value} close error: {e}")
        self.backends.clear()

    def _get_biological_state(self) -> str:
        """Wrapper — delegates to standalone function for A3 split compatibility"""
        return get_biological_state()

    def _get_formula_summaries(self) -> str:
        """Wrapper — delegates to standalone function for A3 split compatibility"""
        return get_formula_summaries()

    def _construct_angela_prompt(
        self, user_message: str, context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Wrapper — delegates to standalone function for A3 split compatibility"""
        nv = None
        if self.__class__._neuro_vocab_instance is not None:
            nv = self.__class__._neuro_vocab_instance[0]
        return construct_angela_prompt(user_message, context, neuro_vocabulary=nv)

    async def generate_response(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> LLMResponse:
        """
        生成 Angela 的回應
        ==================
        這是核心方法：
        1. 建構提示詞（讓模型扮演 Angela）
        2. 調用 LLM
        3. 回應經過 Angela 的處理

        用戶不是直接與模型對話，而是透過 Angela。

        增强功能（如果启用）：
        1. 先尝试从记忆系统检索模板
        2. 如果命中记忆，直接返回模板回應
        3. 否则调用 LLM 生成
        4. 将新回應存储为模板候选
        """

        context = context or {}
        start_time = time.time()

        # 更新统计信息
        self.stats["total_requests"] += 1

        # 记录活动（用于预计算）
        if hasattr(self, "precompute_service") and self.precompute_service._running:
            pass  # stub 暂不支持 record_activity

        # 使用 caller 提供的 session 歷史（不覆蓋、不維護全域歷史）
        # context["history"] 由 chat_routes / websocket_manager 設定

        # ========== P0-2: Template Matching & Routing ==========
        template_result = await self._try_template_match(user_message, context, start_time)
        if template_result is not None:
            return template_result

        # ========== Ensemble Mode (multi-model voting) ==========
        if context and context.get("use_ensemble"):
            try:
                from ai.ensemble import ModelEnsemble, ModelWeight
                ensemble = ModelEnsemble(self)
                weights = context.get("ensemble_weights", [
                    ModelWeight("gpt-4o", 0.4),
                    ModelWeight("claude-3-opus", 0.4),
                    ModelWeight("mixtral-local", 0.2),
                ])
                ensemble.configure_ensemble(weights)
                result = await ensemble.ensemble_generate(
                    user_message,
                    fusion_strategy=context.get("fusion_strategy", "best_single"),
                )
                from core.interfaces.protocols import LLMResponse
                return LLMResponse(
                    text=result.content,
                    model="ensemble",
                    response_time_ms=result.latency * 1000,
                    tokens_used=result.token_usage.get("total_tokens", 0),
                    metadata={"ensemble_votes": result.model_votes, "confidence": result.confidence},
                )
            except Exception as e:
                logger.warning(f"Ensemble generation failed, falling back to single model: {e}")

        # ========== 记忆检索（如果启用）==========
        if self.enable_memory_enhancement:
            try:
                # 尝试从记忆检索
                memory_response = await self.memory_integration.try_memory_retrieval(user_message, context)

                if memory_response:
                    # 记忆命中
                    self.stats["memory_hits"] += 1
                    response_time = (time.time() - start_time) * 1000

                    # 更新统计
                    self.stats["total_response_time"] += response_time
                    self.stats["average_response_time"] = (
                        self.stats["total_response_time"] / self.stats["total_requests"]
                    )
                    self.stats["memory_hit_rate"] = (
                        self.stats["memory_hits"] / self.stats["total_requests"]
                    )

                    logger.info(f"Memory hit: {response_time:.0f}ms")
                    return memory_response
            except Exception as e:
                # broad exception acceptable: memory retrieval is best-effort, fallback to LLM
                logger.warning(f"Memory retrieval failed: {e}", exc_info=True)

        # 如果沒有可用的後端，使用備份機制 (try Model Bus first)
        if not self.is_available or self.active_backend is None:
            bus_result = await self._try_model_bus(user_message, context)
            if bus_result is not None:
                return bus_result
            return await self._fallback_response(user_message, context)

        # ========== LLM 生成 ==========
        try:
            response = await self._generate_with_llm(user_message, context)

            # 歷史由 caller 維護（websocket_manager / chat_routes），router 不再追加

            # 更新统计
            self.stats["llm_calls"] += 1
            response_time = (time.time() - start_time) * 1000
            self.stats["total_response_time"] += response_time
            self.stats["average_response_time"] = (
                self.stats["total_response_time"] / self.stats["total_requests"]
            )
            self.stats["memory_hit_rate"] = self.stats["memory_hits"] / self.stats["total_requests"]

            # 记录 LLM_FULL 路由的偏差追踪
            if hasattr(self, "deviation_tracker"):
                self.deviation_tracker.record(
                    user_input=user_message,
                    match_score=0.0,
                    route=self.ResponseRoute.LLM_FULL,
                    response_text=response.text,
                    tokens_used=response.tokens_used or 600,
                    response_time_ms=response_time,
                    composition_time_ms=0.0,
                    match_time_ms=0.0,
                )

            # 将新回應存储为模板候选
            if self.enable_memory_enhancement and not response.error:
                await self._store_response_as_template(user_message, response, context)

            logger.info(f"Angela 回應生成完成 (LLM_FULL) ({response_time:.0f}ms)")
            self._record_route_learning(context, "success", response_time)
            return response

        except Exception as e:
            # broad exception acceptable: response generation must be resilient to any backend failure
            logger.error(f"生成回應時出錯: {e}", exc_info=True)
            bus_result = await self._try_model_bus(user_message, context)
            if bus_result is not None:
                return bus_result
            return await self._fallback_response(user_message, context)

    async def _try_template_match(self, user_message: str, context: Dict[str, Any], start_time: float) -> Optional[LLMResponse]:
        """Try template match or ModelBus fast-path/drafting."""
        
        # ========== P0: ModelBus Fast-Path & Drafting ==========
        # Check ModelBus for reflex/knowledge hits or drafts for refinement
        if hasattr(self, "model_bus") and self.model_bus:
            try:
                query_type = context.get("intent", "auto")
                decision = await self.model_bus.route(user_message, query_type, context)
                
                if decision.selected_model != "none":
                    result = decision.results.get(decision.selected_model)
                    if result and result.text and result.text not in _KNOWN_FALLBACK_RESPONSES:
                        # Case A: High confidence -> Direct return (Reflex)
                        if decision.confidence >= 0.8:
                            logger.info(f"ModelBus direct hit: {decision.selected_model} (conf={decision.confidence:.2f})")
                            return LLMResponse(
                                text=result.text,
                                confidence=decision.confidence,
                                model=decision.selected_model,
                                backend="model_bus",
                                response_time_ms=decision.total_latency_ms
                            )
                        
                        # Case B: Medium confidence -> Draft for LLM refinement
                        elif 0.4 <= decision.confidence < 0.8:
                            logger.info(f"ModelBus draft provided: {decision.selected_model} (conf={decision.confidence:.2f}) for LLM refinement")
                            context["draft_response"] = result.text
                            context["draft_model"] = decision.selected_model
            except Exception as e:
                logger.warning(f"ModelBus pre-match failed: {e}", exc_info=True)

        # ========== P1: Traditional Template Matching ==========
        if not hasattr(self, "template_matcher") or not self.template_matcher:
            return None
        try:
            match_result = self.template_matcher.match(user_message, context)
            match_score = match_result.score

            tmpl_cfg = _get_llm_config("template_match", {})
            composed_thresh = tmpl_cfg.get("composed", 0.8)
            hybrid_thresh = tmpl_cfg.get("hybrid", 0.5)
            if match_score > composed_thresh:
                composed_response = self.response_composer.compose_response(
                    match_result.template_content, match_score, context
                )

                response_time = (time.time() - start_time) * 1000
                self.stats["composed_responses"] += 1

                if hasattr(self, "deviation_tracker"):
                    self.deviation_tracker.record(
                        user_input=user_message,
                        match_score=match_score,
                        route=self.ResponseRoute.COMPOSED,
                        response_text=composed_response.text,
                        tokens_used=50,
                        response_time_ms=response_time,
                        composition_time_ms=composed_response.composition_time_ms,
                        match_time_ms=match_result.match_time_ms,
                        quality_score=composed_response.confidence,
                    )

                self.template_matcher.record_template_usage(match_result.template_id, True)

                logger.info(
                    f"COMPOSED route: {response_time:.0f}ms, match_score={match_score:.2f}"
                )

                return ChatResponse(
                    text=composed_response.text,
                    backend="composed-template",
                    model="template-based",
                    tokens_used=50,
                    response_time_ms=response_time,
                    confidence=composed_response.confidence,
                    hit_score=match_score,
                    hit_source="template",
                    route="COMPOSED",
                    metadata={
                        "route": "COMPOSED",
                        "match_score": match_score,
                        "template_id": match_result.template_id,
                    },
                )

            elif match_score > hybrid_thresh:
                composed_response = self.response_composer.compose_response(
                    match_result.template_content, match_score, context
                )

                llm_response = await self._generate_with_llm(user_message, context)

                if not llm_response.error:
                    _comp = composed_response.text.rstrip()
                    _llm = llm_response.text.lstrip()
                    _sep = "\n" if len(_comp) > 20 else " "
                    hybrid_text = f"{_comp}{_sep}{_llm}"
                else:
                    hybrid_text = composed_response.text

                response_time = (time.time() - start_time) * 1000
                self.stats["hybrid_responses"] += 1

                if hasattr(self, "deviation_tracker"):
                    self.deviation_tracker.record(
                        user_input=user_message,
                        match_score=match_score,
                        route=self.ResponseRoute.HYBRID,
                        response_text=hybrid_text,
                        tokens_used=200,
                        response_time_ms=response_time,
                        composition_time_ms=composed_response.composition_time_ms,
                        match_time_ms=match_result.match_time_ms,
                    )

                logger.info(
                    f"HYBRID route: {response_time:.0f}ms, match_score={match_score:.2f}"
                )

                return ChatResponse(
                    text=hybrid_text,
                    backend="hybrid",
                    model="template+llm",
                    tokens_used=200,
                    response_time_ms=response_time,
                    confidence=0.85,
                    hit_score=match_score,
                    hit_source="template",
                    route="HYBRID",
                    metadata={
                        "route": "HYBRID",
                        "match_score": match_score,
                    },
                )

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.warning(f"P0-2 template matching failed: {e}", exc_info=True)
        return None

    async def _try_model_bus(self, user_message: str, context: Dict[str, Any]) -> Optional[LLMResponse]:
        """Try Model Bus for capability-based routing, returns None if unavailable or fails"""
        if self.model_bus and self.query_classifier:
            try:
                classify_result = self.query_classifier.classify(user_message)
                query_type = classify_result.primary_type.value
                decision = await self.model_bus.route(user_message, query_type, context)
                if decision.selected_model != "none":
                    result = decision.results[decision.selected_model]
                    return LLMResponse(
                        text=result.text,
                        backend=result.model_id,
                        model=result.model_id,
                        tokens_used=0,
                        response_time_ms=result.latency_ms,
                        confidence=result.confidence,
                        metadata={"bus_route": True, "query_type": query_type, "route_reason": decision.reason},
                    )
            except Exception as e:
                logger.warning(f"Model Bus route failed: {e}", exc_info=True)
        return None

    async def _fallback_response(self, user_message: str, context: Dict[str, Any]) -> LLMResponse:
        """
        備份回應機制
        優先使用 Model Bus 路由，其次已註冊的 ED3N 或 GARDEN 後端，降級至 NeuroBlender，最後使用純模板。
        """
        # Tier 0: Model Bus capability-based routing
        bus_result = await self._try_model_bus(user_message, context)
        if bus_result is not None:
            return bus_result

        # Tier 1: Registered ED3N/GARDEN backends (reuse singleton to avoid redundant init)
        for tier_backend, tier_name in [(LLMBackend.ED3N, "ed3n"), (LLMBackend.GARDEN, "garden")]:
            backend = self.backends.get(tier_backend)
            if backend:
                try:
                    result = await backend.generate(user_message, context=context)
                    if result and result.text:
                        result.metadata = result.metadata or {}
                        result.metadata["fallback"] = True
                        result.metadata["tier"] = tier_name
                        return result
                except Exception as e:
                    logger.warning(f"{tier_name} fallback failed: {e}", exc_info=True)

        # Tier 2: NeuroBlender
        try:
            result = await self._try_neuro_blender(user_message, context)
            if result:
                return result
        except Exception as e:
            logger.warning(f"NeuroBlender fallback failed: {e}", exc_info=True)

        # Tier 3: pure template
        try:
            from ai.memory.template_library import get_template_library
            from ai.memory.memory_template import ResponseCategory
            library = get_template_library()

            emotion = context.get("bio_state", {}).get("dominant_emotion", "neutral").lower()

            category_map = {
                "happy": ResponseCategory.SMALL_TALK,
                "sad": ResponseCategory.SUPPORT,
                "angry": ResponseCategory.CASUAL,
                "neutral": ResponseCategory.SMALL_TALK,
                "calm": ResponseCategory.SMALL_TALK,
                "fear": ResponseCategory.SUPPORT,
                "surprise": ResponseCategory.CURIOSITY
            }

            target_category = category_map.get(emotion, ResponseCategory.SMALL_TALK)
            templates = library.get_by_category(target_category)

            if not templates:
                templates = library.get_by_category(ResponseCategory.SMALL_TALK)

            if templates:
                template = random.choice(templates)
                text = template.content.replace("{user_name}", context.get("user_name", "朋友"))
            else:
                text = "（核心 LLM 目前離線中，但我依然能感受到妳。能稍微等我一下嗎？）"

            return LLMResponse(
                text=text,
                backend="local-fallback",
                model="template-engine",
                confidence=0.5,
                metadata={"fallback": True},
            )
        except Exception as e:
            logger.error(f"Ultimate fallback failure: {e}", exc_info=True)
            return LLMResponse(
                text="（系統核心對話模組載入失敗，請檢查後端日誌。）",
                backend="error",
                model="error",
                confidence=0.0,
                error=str(e),
            )

    # ── NeuroBlender fallback helper ──────────────────────────────────────

    _neuro_vocab_instance = None

    async def _try_neuro_blender(self, user_message: str, context: Dict[str, Any]) -> Optional[LLMResponse]:
        """尝试使用 NeuroBlender 合成回复"""
        # Lazy initialize NeuroVocabulary from TemplateLibrary
        if self.__class__._neuro_vocab_instance is None:
            from ai.response.composer import NeuroVocabulary, NeuroBlender
            from ai.memory.template_library import get_template_library

            vocab = NeuroVocabulary()
            library = get_template_library()
            count = vocab.decompose_from_templates(library)
            logger.info(f"[NeuroBlender] Decomposed {count} fragments from TemplateLibrary")

            # Try loading config fragments
            from core.config_loader import get_angela_config
            cfg = get_angela_config()
            neuro_cfg = cfg.get_authority("angela_core", {}).get("neuro_fragments", [])
            if neuro_cfg:
                vocab.load_from_config(neuro_cfg)
                logger.info(f"[NeuroBlender] Loaded {len(neuro_cfg)} config fragments")

            self.__class__._neuro_vocab_instance = (vocab, NeuroBlender(vocab))

        vocab, blender = self.__class__._neuro_vocab_instance

        # Build state_dict from context with dynamic values
        bio = context.get("bio_state", {})
        axes = context.get("state_for_llm", {}).get("axes", {})
        state_dict = {
            "alpha": {"energy": axes.get("alpha", {}).get("values", {}).get("energy", 0.6 - 0.3 * bio.get("stress_level", 0.0))},
            "beta": {"curiosity": axes.get("beta", {}).get("values", {}).get("curiosity", 0.5)},
            "gamma": {"valence": axes.get("gamma", {}).get("values", {}).get("valence", bio.get("valence", 0.0))},
            "delta": {"intimacy": axes.get("delta", {}).get("values", {}).get("intimacy", 0.4)},
            "epsilon": {"precision": axes.get("epsilon", {}).get("values", {}).get("precision", 0.4)},
            "zeta": {"temporal_coherence": axes.get("zeta", {}).get("values", {}).get("temporal_coherence", 0.5)},
            "theta": {"novelty": axes.get("theta", {}).get("values", {}).get("novelty", 0.3)},
            "eta": {"execution_count": axes.get("eta", {}).get("values", {}).get("execution_count", 0.5)},
        }

        # Build intent_vec dynamically from user_message keywords
        intent_vec = {"casual": 0.5}
        emotion = bio.get("dominant_emotion", "").lower()
        if emotion in ("sad", "fear", "angry"):
            intent_vec["support"] = 0.7
        if emotion in ("happy", "surprise"):
            intent_vec["excited"] = 0.6
        math_kws = ["計算", "數學", "積分", "微分", "math", "calculate"]
        code_kws = ["代碼", "程式", "python", "function", "code", "program"]
        for kw in math_kws:
            if kw in user_message:
                intent_vec["math"] = 0.8
                break
        for kw in code_kws:
            if kw in user_message:
                intent_vec["code"] = 0.8
                break

        empathy_valence = bio.get("valence", 0.0)
        user_name = context.get("user_name", "朋友")

        result = blender.synthesize(
            state_dict=state_dict,
            intent_vec=intent_vec,
            empathy_valence=empathy_valence,
            user_name=user_name,
        )

        return LLMResponse(
            text=result.text,
            backend="local-fallback",
            model="neuro-blender",
            confidence=result.confidence,
            metadata={"fallback": True, "neuro_blend": True, "fragments": result.fragments_used},
        )

    # ========== 记忆增强系统 - 辅助方法 ==========


    async def _prepare_generation_context(
        self, user_message: str, context: Dict[str, Any]
    ) -> tuple:
        defaults = _get_llm_config("defaults", {})
        gen_timeout = getattr(self.active_backend, "timeout", defaults.get("timeout_default", 30.0))
        gen_temperature = defaults.get("temperature", 0.7)
        gen_max_tokens = defaults.get("max_tokens", 512)

        if self.llm_mode == "auto" and self.auto_selector is not None:
            try:
                from ai.response.neuro_auto_selector import AutoDecision, AutoBackendChoice

                ctx = {
                    "intent": context.get("intent", "general"),
                    "complexity": context.get("complexity", 0.5),
                    "user_message": user_message,
                    "energy": context.get("energy"),
                }
                auto_result = await self.auto_selector.decide(context=ctx)

                if auto_result.backend.value == "neuroblender":
                    logger.info("[auto] 預算不足，使用 NeuroBlender 降級")
                    params = GenerationParams(gen_timeout, gen_temperature, gen_max_tokens)
                    return await self._fallback_response(user_message, context), params

                if auto_result.backend.value != (self.active_backend_type.value if self.active_backend_type else ""):
                    backend_map = {
                        "ollama": LLMBackend.OLLAMA,
                        "llamacpp": LLMBackend.LLAMA_CPP,
                        "openai": LLMBackend.OPENAI,
                        "anthropic": LLMBackend.ANTHROPIC,
                        "google": LLMBackend.GOOGLE,
                    }
                    mapped = backend_map.get(auto_result.backend.value)
                    if mapped and mapped in self.backends:
                        prev = self.active_backend_type.value if self.active_backend_type else "none"
                        self.active_backend = self.backends[mapped]
                        self.active_backend_type = mapped
                        logger.info(f"[auto] 切換後端: {prev} → {mapped.value}")

                gen_timeout = auto_result.time_budget_ms / 1000.0
                gen_temperature = auto_result.temperature
                gen_max_tokens = auto_result.max_tokens
            except Exception as e:
                logger.warning(f"[auto] 動態決策失敗: {e}，使用默認參數", exc_info=True)

        return None, GenerationParams(gen_timeout, gen_temperature, gen_max_tokens)

    async def _call_llm_backend(self, user_message: str, context: Dict[str, Any], params: GenerationParams) -> LLMResponse:
        messages = self._construct_angela_prompt(user_message, context)

        try:
            from core.waiting_scheduler import get_waiting_scheduler
            scheduler = get_waiting_scheduler()

            coro = self.active_backend.generate(
                prompt=messages[-1]["content"],
                messages=messages,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )

            response = await scheduler.submit(
                coro,
                timeout=params.timeout,
                label=f"llm:{self.active_backend_type.value if self.active_backend_type else 'gen'}"
            )

            if response is None:
                raise asyncio.TimeoutError("WaitingScheduler returned empty response (timeout/error)")

        except (ImportError, AttributeError) as e:
            logger.warning(f"WaitingScheduler 調度失敗，回退至直接調用: {e}", exc_info=True)
            response = await asyncio.wait_for(
                self.active_backend.generate(
                    prompt=messages[-1]["content"],
                    messages=messages,
                    temperature=params.temperature,
                    max_tokens=params.max_tokens,
                ),
                timeout=params.timeout,
            )

        return response

    async def _post_process_response(
        self, response: LLMResponse, user_message: str, context: Dict[str, Any], start_time: float
    ) -> LLMResponse:
        if self.llm_mode == "auto" and self.auto_selector is not None and AutoDecision is not None:
            elapsed = (time.time() - start_time) * 1000
            self.auto_selector.record_result(
                AutoDecision(backend=AutoBackendChoice(self.active_backend_type.value)),
                actual_ms=elapsed,
                success=not response.error,
            )

        if response.error:
            logger.warning(f"LLM 回應錯誤: {response.error}", exc_info=True)
            if self._angela_fallback_chain:
                return await self._try_fallback_chain(user_message, context, self._angela_fallback_chain)
            return await self._fallback_response(user_message, context)

        return response

    async def _generate_with_llm(self, user_message: str, context: Dict[str, Any]) -> LLMResponse:
        start_time = time.time()

        early, gen_params = await self._prepare_generation_context(user_message, context)
        if early is not None:
            return early

        try:
            response = await self._call_llm_backend(user_message, context, gen_params)
            return await self._post_process_response(response, user_message, context, start_time)

        except asyncio.TimeoutError:
            logger.warning("LLM generation timeout", exc_info=True)
            self._record_route_learning(context, "timeout", gen_params.timeout * 1000)
            if self.llm_mode == "auto" and self.auto_selector is not None and AutoDecision is not None:
                elapsed = (time.time() - start_time) * 1000
                self.auto_selector.record_result(
                    AutoDecision(backend=AutoBackendChoice(self.active_backend_type.value)),
                    actual_ms=elapsed,
                    success=False,
                )
            if self._angela_fallback_chain:
                return await self._try_fallback_chain(user_message, context, self._angela_fallback_chain)
            return await self._fallback_response(user_message, context)
        except Exception as e:
            logger.error(f"LLM generation error: {e}", exc_info=True)
            self._record_route_learning(context, "error", 0.0)
            if self._angela_fallback_chain:
                return await self._try_fallback_chain(user_message, context, self._angela_fallback_chain)
            return await self._fallback_response(user_message, context)

    async def _try_fallback_chain(
        self, user_message: str, context: Dict[str, Any], chain: List[str]
    ) -> LLMResponse:
        """嘗試降級鏈中的後端"""
        for backend_name in chain:
            for btype, bobj in self.backends.items():
                bname_str = btype.name.lower()
                if backend_name.lower() in bname_str or bname_str in backend_name.lower():
                    try:
                        full_prompt = self._construct_angela_prompt(user_message, context)
                        response = await asyncio.wait_for(
                            bobj.generate(
                                prompt=full_prompt[-1]["content"],
                                messages=full_prompt,
                                temperature=0.7, max_tokens=512,
                            ),
                            timeout=30.0,
                        )
                        self.active_backend = bobj
                        logger.info(f"[Fallback] Switched to {btype.name}")
                        return response
                    except Exception:
                        logger.warning(
                            "[Fallback] Backend %s failed, trying next fallback",
                            btype.name,
                            exc_info=True,
                        )
                        continue
        return await self._fallback_response(user_message, context)

    def _record_route_learning(self, context: Dict[str, Any], status: str, latency_ms: float) -> None:
        """學習閉環：記錄 LLM 路由結果到雙層配置"""
        try:
            from core.config_loader import get_angela_config
            cfg = get_angela_config()
            provider = self.active_backend.__class__.__name__ if self.active_backend else "unknown"
            intent = context.get("intent", context.get("origin", "general")) if context else "general"
            if status == "success":
                cfg.learn("route_success", {
                    "provider": provider, "intent": intent, "latency_ms": latency_ms
                })
            else:
                cfg.learn("route_fail", {
                    "provider": provider, "intent": intent, "error": status
                })
        except Exception as e:
            logger.warning("Failed to learn route_fail: %s", e, exc_info=True)

    async def _store_response_as_template(
        self, user_message: str, response: LLMResponse, context: Dict[str, Any]
    ) -> None:
        """
        将新回應存储为模板候选，并从中萃取數值→語意映射（C6）

        Args:
            user_message: 用户消息
            response: LLM 回應
            context: 上下文
        """
        try:
            # 只有当回應质量较高时才存储
            if response.confidence < 0.5:
                return

            # C6: 從回應文本萃取自我描述句，學習數值→語意映射
            if self.__class__._neuro_vocab_instance is not None:
                import re as _re
                nv = self.__class__._neuro_vocab_instance[0]
                state_for_llm = context.get("state_for_llm")
                if state_for_llm and response.text:
                    sentences = _re.split(r'(?<=[。！？.!?\n])\s*', response.text)
                    desc_pattern = _re.compile(r'(我感覺|像是|有點|好像|覺得|似乎|彷彿)')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence or len(sentence) < 4:
                            continue
                        match = desc_pattern.search(sentence)
                        if not match:
                            continue
                        desc_text = sentence[:80]
                        # 映射到最近一次軸點位數值
                        axes = state_for_llm.get("axes", {})
                        for axis_name, ax in axes.items():
                            vals = ax.get("values", {})
                            for k, v in vals.items():
                                nv.learn_mapping(f"{axis_name}.{k}", v, desc_text)
                    # C6 Phase 4: sync learned mappings to StateStore for persistence
                    nv.sync_to_state_store()

            # 创建模板
            from ai.memory.memory_template import ResponseCategory, create_template

            template = create_template(
                content=response.text,
                category=ResponseCategory.SMALL_TALK,  # 默认类别
                keywords=self._extract_keywords(user_message),
                metadata={
                    "llm_generated": True,
                    "llm_backend": response.backend,
                    "llm_model": response.model,
                    "original_query": user_message,
                    "created_at": time.time(),
                },
            )

            # 存储到记忆系统
            if hasattr(self, 'memory_manager') and self.memory_manager is not None:
                await self.memory_manager.store_template(template)

            # C1: 通过协调器记录认知投入（如果 CDM 可用）
            if hasattr(self, 'memory_coordinator') and self.memory_coordinator is not None:
                try:
                    from core.cdm_dividend_model import CognitiveActivity
                    await self.memory_coordinator.store_experience(
                        raw_data=response.text,
                        data_type="response_template",
                        metadata={"llm_generated": True},
                        activity_type=CognitiveActivity.LEARNING,
                        duration=2.0,
                        intensity=response.confidence,
                        context={"user_message": user_message},
                    )
                except Exception as e:
                    logger.warning("Failed to record cognitive activity: %s", e, exc_info=True)

            logger.debug(f"Stored new template for query: '{user_message}'")

        except (IOError, KeyError, AttributeError, ValueError) as e:
            # template storage is best-effort, non-critical
            logger.warning(f"Failed to store response as template: {e}", exc_info=True)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        stopwords = {
            "你",
            "我",
            "他",
            "她",
            "的",
            "了",
            "吗",
            "呢",
            "吧",
            "啊",
            "是",
            "在",
            "有",
        }
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords[:5]

    def _ed3n_fallback_text(self, text: str) -> str:
        """Fallback text generation via ED3N engine"""
        try:
            # Reuse the ED3N instance from ModelBus if available
            engine = self.model_bus._registry.get("ed3n", (None,))[0]
            if engine is None:
                from ai.ed3n.ed3n_engine import ED3NEngine
                engine = ED3NEngine.get_shared()
            result = engine.process(text, depth="shallow")
            return result if result else ""
        except Exception as e:
            logger.warning(f"ED3N fallback text failed: {e}", exc_info=True)
            return ""

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        system_prompt: str = "",
    ) -> str:
        """
        純文字生成介面（供 ProjectCoordinator 等內部元件使用）
        不走 Angela 風格包裝，直接返回 LLM 原始文字。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if not self.is_available or self.active_backend is None:
            ed3n_text = self._ed3n_fallback_text(prompt)
            return ed3n_text

        try:
            response = await asyncio.wait_for(
                self.active_backend.generate(
                    prompt=messages[-1]["content"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=60.0,
            )
            return response.text if not response.error else self._ed3n_fallback_text(prompt)
        except asyncio.TimeoutError:
            logger.warning("generate_text timeout", exc_info=True)
            return self._ed3n_fallback_text(prompt)
        except Exception as e:
            logger.error(f"generate_text error: {e}", exc_info=True)
            return self._ed3n_fallback_text(prompt)

    async def chat_completion(
        self, messages: List[ChatMessage], model_id: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """
        聊天補全介面（遷移自 multi_llm_adapter.py，thin wrapper）
        用於向後相容需要 chat_completion() 的消費者。
        """
        if not self.is_available or self.active_backend is None:
            last_content = messages[-1].content if isinstance(messages[-1], ChatMessage) else (str(messages[-1]) if messages else "")
            text = self._ed3n_fallback_text(last_content)
            return LLMResponse(text=text, backend="ed3n", model="ed3n-v1", confidence=0.6)

        # P6-1: fire on_message pipeline for plugin system (handlers can annotate/modify data)
        try:
            from core.plugin import plugin_manager as _pm
            user_text = messages[-1].content if isinstance(messages[-1], ChatMessage) else str(messages[-1]) if messages else ""
            if user_text:
                await _pm.execute_pipeline('on_message', {
                    'user_message': user_text,
                    'model_id': model_id,
                })
        except Exception as e:
            logger.warning("Failed to execute on_message plugin pipeline: %s", e, exc_info=True)

        try:
            converted_messages = []
            for msg in messages:
                if isinstance(msg, ChatMessage):
                    converted_messages.append({"role": msg.role, "content": msg.content})
                elif isinstance(msg, dict):
                    converted_messages.append(msg)
                else:
                    converted_messages.append({"role": "user", "content": str(msg)})

            max_tokens = kwargs.get("max_tokens", 256)
            temperature = kwargs.get("temperature", 0.7)

            text = await asyncio.wait_for(
                self.active_backend.generate(
                    prompt=converted_messages[-1]["content"],
                    messages=converted_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=60.0,
            )

            # P7: fire on_response pipeline for plugin system
            try:
                from core.plugin import plugin_manager as _pm
                await _pm.execute_pipeline('on_response', {
                    'response_text': text.text if not text.error else "",
                    'model_id': model_id,
                    'tokens_used': text.tokens_used,
                })
            except Exception as e:
                logger.warning("Failed to execute on_response plugin pipeline: %s", e, exc_info=True)

            return LLMResponse(
                text=text.text if not text.error else "",
                backend=text.backend,
                model=text.model,
                tokens_used=text.tokens_used,
                response_time_ms=text.response_time_ms,
                confidence=text.confidence,
                error=text.error,
            )

        except asyncio.TimeoutError:
            logger.warning("chat_completion timeout", exc_info=True)
            last_content = messages[-1].content if isinstance(messages[-1], ChatMessage) else (str(messages[-1]) if messages else "")
            text = self._ed3n_fallback_text(last_content)
            return LLMResponse(text=text, backend="ed3n", model="ed3n-v1", confidence=0.6)
        except Exception as e:
            logger.error(f"chat_completion error: {e}", exc_info=True)
            last_content = messages[-1].content if isinstance(messages[-1], ChatMessage) else (str(messages[-1]) if messages else "")
            text = self._ed3n_fallback_text(last_content)
            return LLMResponse(text=text, backend="ed3n", model="ed3n-v1", confidence=0.6)
def _get_llm_config(key: str, default=None):
    """Get llm config."""
    try:
        from core.config_loader import get_angela_config
        return get_angela_config().get_authority("angela_core", {}).get("llm", {}).get(key, default)
    except Exception:
        logger.warning(f"_get_llm_config({key}) failed, using default", exc_info=True)
        return default

# 全局實例
_llm_service: Optional[AngelaLLMService] = None
_llm_service_lock: Optional[asyncio.Lock] = None


async def get_llm_service(force_reload: bool = False) -> AngelaLLMService:
    """獲取全局 LLM 服務實例"""
    global _llm_service, _llm_service_lock

    if _llm_service_lock is None:
        _llm_service_lock = asyncio.Lock()

    async with _llm_service_lock:
        if _llm_service is None or force_reload:
            _llm_service = AngelaLLMService()
            await _llm_service.initialize()
            get_registry().register("angela_llm_service", _llm_service)

    return _llm_service
async def angela_llm_response(
    user_message: str, history: List[Dict[str, str]] = None, user_name: str = "朋友", origin: str = "Human"
) -> str:
    """
    生成 Angela 的回應（便捷接口 - 2030 Standard）
    """
    service = await get_llm_service()

    context = {"history": history or [], "user_name": user_name, "origin": origin}

    response = await service.generate_response(user_message, context)

    if response.error:
        logger.warning(f"LLM 響應錯誤: {response.error}", exc_info=True)

    return response.text
