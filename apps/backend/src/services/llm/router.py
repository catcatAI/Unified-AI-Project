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
import json
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
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

import aiohttp
from core.interfaces.service_registry import get_registry
from core.interfaces.protocols import ChatMessage, LLMResponse, ModelProvider

# LLM provider backends
from services.llm.providers.base import BaseLLMBackend
from services.llm.providers.registry import LLMBackend
from services.llm.providers.llamacpp import LlamaCppBackend
from services.llm.providers.ollama import OllamaBackend
from services.llm.providers.openai import OpenAIAPIBackend
from services.llm.providers.anthropic import AnthropicAPIBackend
from services.llm.providers.google import GoogleAPIBackend

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


def _load_memory_modules():
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


# For backward compatibility with code that checks MEMORY_ENHANCED
MEMORY_ENHANCED = lambda: is_memory_enhanced()
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

        # 对话历史（无条件初始化）
        self.conversation_history: List[Dict[str, str]] = []

        # ========== 情感识别系统（新增）==========
        self._init_emotion_recognition()

        self._angela_routing = self.config.get("_routing_policy", {})
        self._angela_fallback_chain = self.config.get("_fallback_chain", [])
        self._angela_intent_routing = self.config.get("_intent_routing", {})

    def _init_response_system(self):
        """初始化 P0-2 响应组合与匹配系统"""
        try:
            from ai.response.template_matcher import TemplateMatcher
            from ai.response.composer import ResponseComposer
            from ai.response.deviation_tracker import DeviationTracker, ResponseRoute

            self.template_matcher = TemplateMatcher()
            self.response_composer = ResponseComposer()
            self.deviation_tracker = DeviationTracker()
            self.ResponseRoute = ResponseRoute

            self._load_templates_to_matcher()

            logger.info("P0-2 Response Composition & Matching System initialized")
        except ImportError as e:
            logger.warning(f"Failed to initialize P0-2 response system: {e}", exc_info=True)
            self.template_matcher = None
            self.response_composer = None
            self.deviation_tracker = None

    def _load_templates_to_matcher(self):
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
            # broad exception acceptable: template loading failure should not block initialization
            logger.warning(f"Failed to load templates to matcher: {e}", exc_info=True)

        # ========== 记忆增强系统初始化 ==========
        if is_memory_enhanced():
            try:
                # 初始化记忆管理器
                self.memory_manager = HAMMemoryManager()
                self.enable_memory_enhancement = True

                # C1: 初始化统一记忆协调器（HAM + 可选 LU + 可选 CDM）
                try:
                    from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator
                    logic_unit = None
                    cdm_model = None
                    try:
                        from ai.memory.lu_logic.logic_unit import LogicUnit
                        logic_unit = LogicUnit(max_rules=500)
                    except Exception:
                        pass
                    try:
                        from core.cdm_dividend_model import CDMCognitiveDividendModel
                        cdm_model = CDMCognitiveDividendModel()
                    except Exception:
                        pass
                    self.memory_coordinator = UnifiedMemoryCoordinator(
                        memory_manager=self.memory_manager,
                        logic_unit=logic_unit,
                        cdm_model=cdm_model,
                    )
                    logger.info("[C1] UnifiedMemoryCoordinator initialized")
                except Exception as e:
                    logger.warning(f"[C1] UnifiedMemoryCoordinator unavailable: {e}", exc_info=True)
                    self.memory_coordinator = None

                # 初始化预计算服务
                _mem_cfg = _get_llm_config("memory", {})
                self.precompute_service = PrecomputeService(
                    llm_service=self,
                    memory_manager=self.memory_manager,
                    idle_threshold=_mem_cfg.get("precompute_idle_threshold", 5.0),
                    cpu_threshold=_mem_cfg.get("precompute_cpu_threshold", 70.0),
                    max_queue_size=_mem_cfg.get("precompute_max_queue_size", 50),
                    llm_timeout=_mem_cfg.get("precompute_llm_timeout", 180.0),
                )

                # 初始化模板库
                self.template_library = get_template_library()

                # 初始化任务生成器
                self.task_generator = TaskGenerator(max_tasks=10)

                logger.info("Memory enhancement system initialized")
            except Exception as e:
                # broad exception acceptable: memory enhancement is optional, graceful degradation on failure
                logger.warning(f"Failed to initialize memory enhancement: {e}", exc_info=True)
                self.enable_memory_enhancement = False
        else:
            self.enable_memory_enhancement = False

    def _init_emotion_recognition(self):
        """初始化情感识别系统"""
        # 基于关键词的情感识别（备选方案）- 支持简繁体中文
        self.emotion_keywords = {
            "happy": {
                "positive": [
                    # 简体
                    "开心",
                    "快乐",
                    "高兴",
                    "喜欢",
                    "爱",
                    "棒",
                    "好",
                    "赞",
                    "哈哈",
                    "美好",
                    "幸福",
                    "满意",
                    "欣赏",
                    "感谢",
                    "谢谢",
                    # 繁体
                    "開心",
                    "快樂",
                    "高興",
                    "喜歡",
                    "愛",
                    "棒",
                    "好",
                    "讚",
                    "哈哈",
                    "美好",
                    "幸福",
                    "滿意",
                    "欣賞",
                    "感謝",
                    "謝謝",
                    # 程度词
                    "好开心",
                    "好喜欢",
                    "太开心",
                    "太喜欢",
                    "真开心",
                    "真喜欢",
                    "好開心",
                    "好喜歡",
                    "太開心",
                    "太喜歡",
                    "真開心",
                    "真喜歡",
                    # 表情
                    "😊",
                    "😄",
                    "🎉",
                ],
                "weight": 1.0,
            },
            "sad": {
                "negative": [
                    # 简体
                    "难过",
                    "伤心",
                    "悲伤",
                    "哭",
                    "痛苦",
                    "难受",
                    "失望",
                    "遗憾",
                    "郁闷",
                    "糟糕",
                    "不开心",
                    "不喜欢",
                    "讨厌",
                    # 繁体
                    "難過",
                    "傷心",
                    "悲傷",
                    "哭",
                    "痛苦",
                    "難受",
                    "失望",
                    "遺憾",
                    "鬱悶",
                    "糟糕",
                    "不開心",
                    "不喜歡",
                    "討厭",
                    # 程度词
                    "好难过",
                    "好伤心",
                    "好悲伤",
                    "好難過",
                    "好傷心",
                    "好悲傷",
                    # 表情
                    "😢",
                    "😭",
                ],
                "weight": 1.0,
            },
            "angry": {
                "negative": [
                    # 简体
                    "生气",
                    "愤怒",
                    "讨厌",
                    "恨",
                    "烦",
                    "气死",
                    "火大",
                    "愤怒",
                    "生气",
                    "讨厌",
                    # 繁体
                    "生氣",
                    "憤怒",
                    "討厭",
                    "恨",
                    "煩",
                    "氣死",
                    "火大",
                    "憤怒",
                    "生氣",
                    "討厭",
                    # 程度词
                    "好生气",
                    "好愤怒",
                    "好生氣",
                    "好憤怒",
                    # 表情
                    "😡",
                    "😠",
                ],
                "weight": 1.2,  # 愤怒情感权重更高
            },
            "fear": {
                "negative": [
                    # 简体
                    "害怕",
                    "恐惧",
                    "担心",
                    "焦虑",
                    "紧张",
                    # 繁体
                    "害怕",
                    "恐懼",
                    "擔心",
                    "焦慮",
                    "緊張",
                    # 表情
                    "😨",
                    "😱",
                ],
                "weight": 1.1,
            },
            "surprise": {
                "neutral": [
                    # 简体
                    "惊讶",
                    "意外",
                    "哇",
                    "天哪",
                    # 繁体
                    "驚訝",
                    "意外",
                    "哇",
                    "天哪",
                    # 表情
                    "😲",
                    "😮",
                ],
                "weight": 0.9,
            },
            "curious": {
                "neutral": [
                    # 简体
                    "好奇",
                    "想知道",
                    "问",
                    "什么",
                    "怎么",
                    "为什么",
                    "想了解",
                    "好奇宝宝",
                    "很好奇",
                    # 繁体
                    "好奇",
                    "想知道",
                    "問",
                    "什麼",
                    "怎麼",
                    "為什麼",
                    "想了解",
                    "好奇寶寶",
                    "很好奇",
                ],
                "weight": 1.0,  # 提高权重，避免被误识别为 happy
            },
            "calm": {
                "neutral": [
                    # 简体
                    "平静",
                    "安静",
                    "放松",
                    "休息",
                    # 繁体
                    "平靜",
                    "安靜",
                    "放鬆",
                    "休息",
                ],
                "weight": 0.7,
            },
        }

        logger.info(
            "Emotion recognition system initialized (supporting Simplified and Traditional Chinese)"
        )

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

        # 從環境變量加載 API 密鑰
        for backend_name, backend_config in config.items():
            if not isinstance(backend_config, dict):
                continue
            if "api_key_env" in backend_config:
                env_var = backend_config["api_key_env"]
                api_key = os.environ.get(env_var)
                if api_key:
                    backend_config["api_key"] = api_key
                    logger.info(
                        f"Loaded API key from environment variable {env_var} for {backend_name}"
                    )
                else:
                    logger.debug(f"Environment variable {env_var} not set for {backend_name}")
            elif "api_key" in backend_config and backend_config["api_key"] in ("", "YOUR_API_KEY"):
                # 移除空或佔位符 API 密鑰
                del backend_config["api_key"]

        return config

    def reload_config(self, new_config: Optional[Dict[str, Any]] = None):
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

    def _init_backends(self):
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


    async def initialize(self) -> bool:
        """初始化服務，檢測可用的後端
        返回: 是否至少有一個可用的後端
        """
        logger.info("正在初始化 Angela LLM 服務...")

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
            ]
            for backend_type in priority:
                if backend_type in available_backends:
                    self.active_backend = self.backends[backend_type]
                    self.active_backend_type = backend_type
                    break

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
        if hasattr(self, "precompute_service") and self.precompute_service.is_running:
            self.precompute_service.record_activity()

        # 更新对话历史
        if hasattr(self, "conversation_history"):
            self.conversation_history.append({"role": "user", "content": user_message})
            # 限制历史长度
            max_hist = _get_llm_config("defaults", {}).get("max_conversation_history", 50)
            if len(self.conversation_history) > max_hist:
                self.conversation_history = self.conversation_history[-max_hist:]

        # ========== P0-2: Template Matching & Routing ==========
        template_result = await self._try_template_match(user_message, context, start_time)
        if template_result is not None:
            return template_result

        # ========== 记忆检索（如果启用）==========
        if self.enable_memory_enhancement:
            try:
                # 尝试从记忆检索
                memory_response = await self._try_memory_retrieval(user_message, context)

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

        # 如果沒有可用的後端，使用備份機制
        if not self.is_available or self.active_backend is None:
            return await self._fallback_response(user_message, context)

        # ========== LLM 生成 ==========
        try:
            response = await self._generate_with_llm(user_message, context)

            # 更新对话历史
            if hasattr(self, "conversation_history"):
                self.conversation_history.append({"role": "assistant", "content": response.text})

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
            return await self._fallback_response(user_message, context)

    async def _try_template_match(self, user_message: str, context: Dict[str, Any], start_time: float) -> Optional[LLMResponse]:
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

                return LLMResponse(
                    text=composed_response.text,
                    backend="composed-template",
                    model="template-based",
                    tokens_used=50,
                    response_time_ms=response_time,
                    confidence=composed_response.confidence,
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
                    hybrid_text = f"{composed_response.text} {llm_response.text}"
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

                return LLMResponse(
                    text=hybrid_text,
                    backend="hybrid",
                    model="template+llm",
                    tokens_used=200,
                    response_time_ms=response_time,
                    confidence=0.85,
                    metadata={
                        "route": "HYBRID",
                        "match_score": match_score,
                    },
                )

        except Exception as e:
            logger.warning(f"P0-2 template matching failed: {e}", exc_info=True)
        return None

    async def _fallback_response(self, user_message: str, context: Dict[str, Any]) -> LLMResponse:
        """
        備份回應機制
        當沒有可用的 LLM 後端時，使用 NeuroBlender 或簡單模板。
        """
        try:
            # Try NeuroBlender first
            result = await self._try_neuro_blender(user_message, context)
            if result:
                return result
        except Exception as e:
            logger.warning(f"NeuroBlender fallback failed: {e}", exc_info=True)

        # Ultimate fallback: pure template
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

        # Build state_dict from context
        bio = context.get("bio_state", {})
        state_dict = {
            "alpha": {"energy": 0.6 - 0.3 * bio.get("stress_level", 0.0)},
            "beta": {"curiosity": 0.5},
            "gamma": {"valence": bio.get("valence", 0.0)},
            "delta": {"intimacy": 0.4},
            "epsilon": {"precision": 0.4},
            "zeta": {"temporal_coherence": 0.5},
            "theta": {"novelty": 0.3},
            "eta": {"execution_count": 0.5},
        }

        # Build intent_vec from user_message keywords
        intent_vec = {"casual": 0.5}
        math_kws = ["計算", "數學", "積分", "微分"]
        code_kws = ["代碼", "程式", "python", "function"]
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

    async def _try_memory_retrieval(
        self, user_message: str, context: Dict[str, Any]
    ) -> Optional[LLMResponse]:
        """
        尝试从记忆系统检索回應

        Args:
            user_message: 用户消息
            context: 上下文

        Returns:
            Optional[LLMResponse]: 如果找到匹配的模板，返回回應；否则返回 None
        """
        try:
            # 1. 获取 Angela 当前状态
            angela_state = AngelaState()  # 简化版本，使用默认状态

            # 2. 获取用户印象
            user_impression = UserImpression()  # 简化版本，使用默认印象

            # 3. 检索模板
            results = await self.memory_manager.retrieve_response_templates(
                query=user_message,
                angela_state=angela_state,
                user_impression=user_impression,
                limit=5,
                min_score=0.7,
            )

            if results and len(results) > 0:
                # 4. 选择最佳匹配
                best_template, score = results[0]

                # 5. 更新使用统计
                best_template.record_usage(success=True)
                await self.memory_manager.update_template(best_template)

                # 6. 返回模板回應
                return LLMResponse(
                    text=best_template.content,
                    backend="memory-template",
                    model="template-based",
                    confidence=score,
                    metadata={
                        "template_id": best_template.id,
                        "template_score": score,
                        "memory_hit": True,
                    },
                )

            return None

        except Exception as e:
            # broad exception acceptable: memory retrieval error should not crash main flow
            logger.warning(f"Memory retrieval error: {e}", exc_info=True)
            return None

    async def _generate_with_llm(self, user_message: str, context: Dict[str, Any]) -> LLMResponse:
        """
        使用 LLM 生成回應

        Args:
            user_message: 用户消息
            context: 上下文

        Returns:
            LLMResponse: LLM 生成的回應
        """
        start_time = time.time()

        defaults = _get_llm_config("defaults", {})
        timeout_seconds = getattr(self.active_backend, "timeout", defaults.get("timeout_default", 30.0))
        temperature = defaults.get("temperature", 0.7)
        max_tokens = defaults.get("max_tokens", 512)

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
                    return await self._fallback_response(user_message, context)

                # 如果需要切換後端
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

                # 使用動態參數
                timeout_seconds = auto_result.time_budget_ms / 1000.0
                temperature = auto_result.temperature
                max_tokens = auto_result.max_tokens
            except Exception as e:
                logger.warning(f"[auto] 動態決策失敗: {e}，使用默認參數", exc_info=True)

        try:
            # 建構提示詞
            messages = self._construct_angela_prompt(user_message, context)

            # [Phase 8 Activation] 使用 WaitingScheduler 調度 LLM 調用，防止阻塞主事件循環
            try:
                from core.waiting_scheduler import get_waiting_scheduler
                scheduler = get_waiting_scheduler()

                # 提交生成任務
                coro = self.active_backend.generate(
                    prompt=messages[-1]["content"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 透過排程器執行（內建超時管理）
                response = await scheduler.submit(
                    coro,
                    timeout=timeout_seconds,
                    label=f"llm:{self.active_backend_type.value if self.active_backend_type else 'gen'}"
                )

                if response is None:
                    # 排程器回傳 None 通常代表超時或內部失敗
                    raise asyncio.TimeoutError("WaitingScheduler returned empty response (timeout/error)")

            except (ImportError, AttributeError) as e:
                logger.warning(f"WaitingScheduler 調度失敗，回退至直接調用: {e}", exc_info=True)
                # 降級：直接調用
                response = await asyncio.wait_for(
                    self.active_backend.generate(
                        prompt=messages[-1]["content"],
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=timeout_seconds,
                )

            # [auto] record result
            if self.llm_mode == "auto" and self.auto_selector is not None:
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

        except asyncio.TimeoutError:
            logger.warning("LLM generation timeout", exc_info=True)
            self._record_route_learning(context, "timeout", timeout_seconds * 1000)
            # [auto] record timeout
            if self.llm_mode == "auto" and self.auto_selector is not None:
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
            # broad exception acceptable: LLM generation must be resilient, fallback on any error
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
                        prev = self.active_backend
                        self.active_backend = bobj
                        full_prompt = self._construct_angela_prompt(user_message, context)
                        response = await asyncio.wait_for(
                            bobj.generate(
                                prompt=full_prompt[-1]["content"],
                                messages=full_prompt,
                                temperature=0.7, max_tokens=512,
                            ),
                            timeout=30.0,
                        )
                        logger.info(f"[Fallback] Switched from {prev} to {btype.name}")
                        return response
                    except Exception:
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
        except Exception:
            pass

    async def _store_response_as_template(
        self, user_message: str, response: LLMResponse, context: Dict[str, Any]
    ):
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
                except Exception:
                    pass

            logger.debug(f"Stored new template for query: '{user_message}'")

        except Exception as e:
            # broad exception acceptable: template storage is best-effort, non-critical
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
        words = text.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords[:5]

    async def start_precompute(self):
        """启动预计算服务"""
        if self.enable_memory_enhancement and hasattr(self, "precompute_service"):
            await self.precompute_service.start()
            logger.info("Precompute service started")

    async def stop_precompute(self):
        """停止预计算服务"""
        if self.enable_memory_enhancement and hasattr(self, "precompute_service"):
            await self.precompute_service.stop()
            logger.info("Precompute service stopped")

    async def add_precompute_task(self, task: "PrecomputeTask"):
        """添加预计算任务"""
        if self.enable_memory_enhancement and hasattr(self, "precompute_service"):
            return self.precompute_service.add_precompute_task(task)
        return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = {
            "enable_memory_enhancement": self.enable_memory_enhancement,
            "llm_stats": self.stats.copy(),
        }

        if self.enable_memory_enhancement:
            if hasattr(self, "precompute_service"):
                stats["precompute"] = self.precompute_service.get_stats()
            if hasattr(self, "template_library"):
                stats["templates"] = {
                    "total": self.template_library.get_template_count(),
                    "by_category": {
                        cat.value: count
                        for cat, count in self.template_library.get_category_counts().items()
                    },
                }

        if hasattr(self, "template_matcher"):
            stats["template_matcher"] = self.template_matcher.get_stats()

        if hasattr(self, "response_composer"):
            stats["response_composer"] = self.response_composer.get_stats()

        if hasattr(self, "deviation_tracker"):
            stats["deviation_tracker"] = self.deviation_tracker.get_stats()

        return stats

    def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        active_backend_type = getattr(self, "active_backend_type", None)
        if active_backend_type and self.active_backend:
            active_backend_name = active_backend_type.value
        else:
            active_backend_name = None
        return {
            "is_available": self.is_available,
            "active_backend": active_backend_name,
            "available_backends": [b.value for b in self.backends.keys()],
            "backends_health": {},
        }

    # ========== 情感识别系统（新增）==========

    def _load_emotion_config(self) -> tuple:
        try:
            from core.hsp.utils.fallback_config_loader import get_config_loader
            _cfg = get_config_loader()
            _em = _cfg.get_authority("angela_core", {}).get("llm", {}).get("emotion", {})
        except Exception:
            _em = {}
        negation_words = _em.get("negation_words", ["不", "沒", "没", "别", "別", "非", "無", "无", "未"])
        intensifier_words = _em.get("intensifier_words", [
            "好", "很", "太", "非常", "超级", "特別", "特别", "真", "超", "極", "极", "格外", "尤其",
        ])
        return negation_words, intensifier_words

    def _score_keyword_match(self, text: str, keyword: str, negation_words: list, intensifier_words: list) -> tuple:
        keyword_pos = text.find(keyword)
        has_negation = False
        for neg_word in negation_words:
            neg_pos = text.find(neg_word)
            if neg_pos != -1 and neg_pos < keyword_pos and (keyword_pos - neg_pos) <= 3:
                has_negation = True
                break
        has_intensifier = False
        for int_word in intensifier_words:
            int_pos = text.find(int_word)
            if int_pos != -1 and int_pos < keyword_pos and (keyword_pos - int_pos) <= 3:
                has_intensifier = True
                break
        return has_negation, has_intensifier

    def _score_emotion_keywords(self, text: str, keywords_data: dict, negation_words: list, intensifier_words: list) -> tuple:
        score = 0.0
        match_count = 0
        for keyword in keywords_data.get("positive", []):
            if keyword in text:
                has_negation, has_intensifier = self._score_keyword_match(text, keyword, negation_words, intensifier_words)
                if has_negation:
                    score -= 0.5
                else:
                    if has_intensifier:
                        score += 1.5
                    else:
                        score += 1.0
                    match_count += 1
        for keyword in keywords_data.get("negative", []):
            if keyword in text:
                has_negation, has_intensifier = self._score_keyword_match(text, keyword, negation_words, intensifier_words)
                if has_negation:
                    score -= 0.5
                else:
                    if has_intensifier:
                        score += 1.5
                    else:
                        score += 1.0
                    match_count += 1
        for keyword in keywords_data.get("neutral", []):
            if keyword in text:
                score += 0.8
                match_count += 1
        return score, match_count

    def _compute_emotion_result(self, emotion_scores: Dict[str, float]) -> Dict[str, Any]:
        if not emotion_scores or all(score <= 0 for score in emotion_scores.values()):
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }
        positive_emotions = {k: v for k, v in emotion_scores.items() if v > 0}
        if not positive_emotions:
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }
        sorted_emotions = sorted(positive_emotions.items(), key=lambda x: x[1], reverse=True)
        primary_emotion, primary_score = sorted_emotions[0]
        if len(sorted_emotions) > 1:
            second_score = sorted_emotions[1][1]
            confidence = min(1.0, primary_score / (primary_score + second_score + 0.1))
        else:
            confidence = min(1.0, primary_score / (primary_score + 0.5))
        intensity = min(1.0, primary_score / 3.0)
        secondary_emotions = [
            {"emotion": emotion, "score": score}
            for emotion, score in sorted_emotions[1:3]
            if score > 0.5
        ]
        return {
            "emotion": primary_emotion,
            "confidence": confidence,
            "intensity": intensity,
            "secondary_emotions": secondary_emotions,
        }

    def analyze_emotion(self, text: str, response_text: str = None) -> Dict[str, Any]:
        """
        分析情感状态（基于关键词的多维情感分析）

        Args:
            text: 用户输入文本
            response_text: Angela 的响应文本（可选）

        Returns:
            Dict[str, Any]: 包含情感分析结果的字典
                - emotion: 主要情感 (happy, sad, angry, fear, surprise, curious, calm)
                - confidence: 情感置信度 (0-1)
                - intensity: 情感强度 (0-1)
                - secondary_emotions: 次要情感列表
        """
        negation_words, intensifier_words = self._load_emotion_config()

        emotion_scores = {}
        for emotion, keywords_data in self.emotion_keywords.items():
            score, match_count = self._score_emotion_keywords(text, keywords_data, negation_words, intensifier_words)
            if match_count > 0 or score != 0:
                emotion_scores[emotion] = score * keywords_data["weight"]

        return self._compute_emotion_result(emotion_scores)

    def analyze_response_emotion(self, response_text: str) -> Dict[str, Any]:
        """
        分析 Angela 响应的情感（用于调整 Angela 的表达）

        Args:
            response_text: Angela 的响应文本

        Returns:
            Dict[str, Any]: 包含情感分析结果的字典
        """
        return self.analyze_emotion(response_text, response_text)

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
            return ""

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
            return response.text if not response.error else ""
        except asyncio.TimeoutError:
            logger.warning("generate_text timeout", exc_info=True)
            return ""
        except Exception as e:
            logger.error(f"generate_text error: {e}", exc_info=True)
            return ""

    async def chat_completion(
        self, messages: List[ChatMessage], model_id: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """
        聊天補全介面（遷移自 multi_llm_adapter.py，thin wrapper）
        用於向後相容需要 chat_completion() 的消費者。
        """
        if not self.is_available or self.active_backend is None:
            return LLMResponse(text="", backend="none", model="unknown", error="No backend available")

        # P6-1: fire on_message pipeline for plugin system (handlers can annotate/modify data)
        try:
            from core.plugin import plugin_manager as _pm
            user_text = messages[-1].content if isinstance(messages[-1], ChatMessage) else str(messages[-1]) if messages else ""
            if user_text:
                await _pm.execute_pipeline('on_message', {
                    'user_message': user_text,
                    'model_id': model_id,
                })
        except Exception:
            pass

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
            except Exception:
                pass

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
            return LLMResponse(text="", backend=self.active_backend.__class__.__name__, model="unknown", error="timeout")
        except Exception as e:
            logger.error(f"chat_completion error: {e}", exc_info=True)
            return LLMResponse(text="", backend="unknown", model="unknown", error=str(e))
def _get_llm_config(key: str, default=None):
    try:
        from core.config_loader import get_angela_config
        return get_angela_config().get_authority("angela_core", {}).get("llm", {}).get(key, default)
    except Exception:
        return default

# 全局實例
_llm_service: Optional[AngelaLLMService] = None
async def get_llm_service(force_reload: bool = False) -> AngelaLLMService:
    """獲取全局 LLM 服務實例"""
    global _llm_service

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
