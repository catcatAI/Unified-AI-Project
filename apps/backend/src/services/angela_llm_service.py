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
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

import httpx

# 簡單日誌設置
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
        logger.warning(f"Memory enhancement modules not available: {e}")
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


class LLMBackend(Enum):
    """支援的 LLM 後端"""

    LLAMA_CPP = "llamacpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    NONE = "none"


@dataclass
class LLMResponse:
    """LLM 回應結構"""

    text: str
    backend: str
    model: str
    tokens_used: int = 0
    response_time_ms: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseLLMBackend(ABC):
    """LLM 後端抽象基類"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回應"""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """檢查後端健康狀態"""
        pass


class LlamaCppBackend(BaseLLMBackend):
    """llama.cpp 後端"""

    def __init__(self, base_url: str = "http://localhost:8080", model: str = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 120.0

    async def check_health(self) -> bool:
        """檢查 llama.cpp 服務是否可用"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 嘗試獲取模型列表
                response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    self.model = data.get("model_name", self.model)
                    return True
        except Exception as e:
            logger.debug(f"llama.cpp health check failed: {e}")
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """調用 llama.cpp 生成回應"""
        start_time = time.time()

        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])

        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return LLMResponse(
                        text=text,
                        backend="llama.cpp",
                        model=self.model or "unknown",
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="llama.cpp",
                        model=self.model,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(text="", backend="llama.cpp", model=self.model, error=str(e))


class OllamaBackend(BaseLLMBackend):
    """Ollama 後端"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 30.0  # 增加超時到 30 秒，以適應慢速模型

    async def check_health(self) -> bool:
        """檢查 Ollama 服務是否可用"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    # 檢查指定模型是否存在
                    models = data.get("models", [])
                    for m in models:
                        if self.model in m.get("name", ""):
                            return True
                    # 如果模型不存在，嘗試使用第一個可用模型
                    if models:
                        self.model = models[0].get("name", "llama3")
                        return True
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """調用 Ollama 生成回應"""
        start_time = time.time()

        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])

        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 512),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
                )

                if response.status_code == 200:
                    try:
                        # Ollama 可能返回 NDJSON 格式（多個 JSON 用換行分隔）
                        # 先嘗試標準 JSON 解析，如果失敗則處理 NDJSON
                        try:
                            data = response.json()
                        except Exception as json_error:
                            # 檢查是否是 "Extra data" 錯誤（NDJSON 格式）
                            if "Extra data" in str(json_error):
                                data = None
                                text = ""
                                # 解析 NDJSON - 逐行解析，取最後一個完整的 JSON
                                lines = response.text.strip().split("\n")
                                for line in lines:
                                    line = line.strip()
                                    if line:
                                        try:
                                            data = json.loads(line)
                                            # 找到最後一個包含 message.content 的完整回應
                                            if data.get("message", {}).get("content"):
                                                text = data.get("message", {}).get("content", "")
                                        except json.JSONDecodeError:
                                            # JSON解析失敗，跳過該行
                                            continue
                                if data is None:
                                    raise json_error
                            else:
                                raise json_error

                        if not text:
                            text = data.get("message", {}).get("content", "") if data else ""
                    except Exception as json_error:
                        logger.warning(
                            f"Ollama JSON 解析錯誤: {json_error}, 原始回應: {response.text[:200]}"
                        )
                        return LLMResponse(
                            text="",
                            backend="ollama",
                            model=self.model,
                            error=f"JSON parse error: {str(json_error)}",
                            response_time_ms=(time.time() - start_time) * 1000,
                        )

                    return LLMResponse(
                        text=text,
                        backend="ollama",
                        model=self.model,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="ollama",
                        model=self.model,
                        error=f"HTTP {response.status_code}",
                    )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(text="", backend="ollama", model=self.model, error=str(e))


class OpenAIAPIBackend(BaseLLMBackend):
    """OpenAI API 後端 (GPT-4, GPT-3.5 等)"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 120.0

    async def check_health(self) -> bool:
        """檢查 OpenAI API 是否可用"""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"OpenAI health check failed: {e}")
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """調用 OpenAI API 生成回應"""
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return LLMResponse(
                        text=text,
                        backend="openai",
                        model=self.model,
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.95,
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="openai",
                        model=self.model,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                    )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="openai", model=self.model, error=str(e))


class AnthropicAPIBackend(BaseLLMBackend):
    """Anthropic API 後端 (Claude 系列)"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1", model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 120.0

    async def check_health(self) -> bool:
        """檢查 Anthropic API 是否可用"""
        if not self.api_key:
            return False
        # Anthropic 沒有簡單的健康檢查端點，有 key 就認為可用
        return True

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """調用 Anthropic API 生成回應"""
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("content", [{}])[0].get("text", "")
                    tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                    return LLMResponse(
                        text=text,
                        backend="anthropic",
                        model=self.model,
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.95,
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="anthropic",
                        model=self.model,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                    )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="anthropic", model=self.model, error=str(e))


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

    _instance = None

    def __new__(cls, config: Dict[str, Any] = None):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Dict[str, Any] = None):
        """初始化 LLM 服務"""
        if self._initialized:
            return

        self.config = config or self._get_default_config()
        self.backends: Dict[LLMBackend, BaseLLMBackend] = {}
        self.active_backend: Optional[BaseLLMBackend] = None

        self.enable_memory_enhancement = self.config.get("enable_memory_enhancement", True)
        self.is_available = False

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
            logger.warning(f"Failed to initialize P0-2 response system: {e}")
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
            logger.warning(f"Failed to load templates to matcher: {e}")

        # ========== 记忆增强系统初始化 ==========
        if is_memory_enhanced():
            try:
                # 初始化记忆管理器
                self.memory_manager = HAMMemoryManager()
                self.enable_memory_enhancement = True

                # 初始化预计算服务
                self.precompute_service = PrecomputeService(
                    llm_service=self,
                    memory_manager=self.memory_manager,
                    idle_threshold=5.0,
                    cpu_threshold=70.0,
                    max_queue_size=50,
                    llm_timeout=180.0,
                )

                # 初始化模板库
                self.template_library = get_template_library()

                # 初始化任务生成器
                self.task_generator = TaskGenerator(max_tasks=10)

                logger.info("Memory enhancement system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize memory enhancement: {e}")
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
        """從配置文件讀取預設配置，並從環境變量加載 API 密鑰"""
        import os
        from pathlib import Path

        # 搜索多個可能的配置路徑（按優先順序）
        config_paths = [
            os.environ.get("MULTI_LLM_CONFIG"),
            "configs/multi_llm_config.json",  # relative to CWD (apps/backend)
            str(Path(__file__).resolve().parents[2] / "configs" / "multi_llm_config.json"),
            str(Path(__file__).resolve().parents[4] / "configs" / "multi_llm_config.json"),
        ]

        config = None
        for path in config_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    logger.info(f"LLM 配置已從 {path} 載入")
                    break
                except Exception as e:
                    logger.warning(f"無法讀取配置 {path}: {e}")

        if config is None:
            logger.warning("未找到 LLM 配置文件，使用默認配置")
            config = {
                "llamacpp-local": {
                    "provider": "llama_cpp",
                    "base_url": "http://localhost:8080",
                    "model_name": "llama-3-8b-instruct",
                    "enabled": True,
                },
                "ollama-llama3": {
                    "provider": "ollama",
                    "base_url": "http://localhost:11434",
                    "model_name": "llama3",
                    "enabled": True,
                },
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
            api_key = backend_config.get("api_key", "")

            if provider in ("llama_cpp", "llamacpp") or backend_id == "llamacpp-local":
                self.backends[LLMBackend.LLAMA_CPP] = LlamaCppBackend(
                    base_url=base_url or "http://localhost:8080",
                    model=model_name,
                )
                logger.info(f"已注冊 llama.cpp 後端: {model_name}")

            elif provider == "ollama" or backend_id.startswith("ollama"):
                # 只註冊第一個 enabled 的 Ollama 配置
                if LLMBackend.OLLAMA not in self.backends:
                    self.backends[LLMBackend.OLLAMA] = OllamaBackend(
                        base_url=base_url or "http://localhost:11434",
                        model=model_name or "llama3",
                    )
                    logger.info(f"已注冊 Ollama 後端: {model_name}")

            elif provider == "openai" and api_key:
                self.backends[LLMBackend.OPENAI] = OpenAIAPIBackend(
                    api_key=api_key,
                    base_url=base_url or "https://api.openai.com/v1",
                    model=model_name or "gpt-4",
                )
                logger.info(f"已注冊 OpenAI 後端: {model_name}")

            elif provider == "anthropic" and api_key:
                self.backends[LLMBackend.ANTHROPIC] = AnthropicAPIBackend(
                    api_key=api_key,
                    base_url=base_url or "https://api.anthropic.com/v1",
                    model=model_name or "claude-3-opus-20240229",
                )
                logger.info(f"已注冊 Anthropic 後端: {model_name}")


    async def initialize(self) -> bool:
        """
        初始化服務，檢測可用的後端
        返回: 是否至少有一個可用的後端
        """
        logger.info("正在初始化 Angela LLM 服務...")

        # 檢查各後端健康狀態
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
            logger.warning("沒有可用的 LLM 後端，將使用備份回應機制")
            self.enable_memory_enhancement = self.config.get("enable_memory_enhancement", True)
            self.is_available = False
            return False

    def _get_biological_state(self) -> str:
        """
        獲取 Angela 的生理狀態描述
        從 brain_status.json 讀取由 BrainBridgeService 同步的數據
        """
        try:
            from pathlib import Path

            status_file = Path("apps/backend/data/brain_status.json")
            if not status_file.exists():
                return ""

            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 結構：data -> { "brain": {...}, "biological": {...}, "life_intensity": ... }
            bio = data.get("biological", {})

            # 從 BiologicalIntegrator.get_biological_state() 提取指標
            arousal = bio.get("arousal", 0.5)
            stress = bio.get("stress_level", 0.0)
            dom_emotion = bio.get("dominant_emotion", "calm")

            # 荷爾蒙效應
            hormonal = bio.get("hormonal_effects", {})
            energy = hormonal.get("energy", 0.8) * 100.0
            # 注意：飢餓感(hunger)目前沒在 get_biological_state 中導出，預設為 0
            hunger = bio.get("hunger", 0.0)

            intensity = data.get("life_intensity", 0.0)

            # 構建描述
            status_parts = []

            # 1. 基礎需求
            if energy < 30:
                status_parts.append("你感到非常疲倦，能量幾乎耗盡。")
            elif energy < 60:
                status_parts.append("你感到有些累了。")

            if hunger > 70:
                status_parts.append("你覺得肚子很餓，渴望獲得能量補充。")

            # 2. 神經壓力
            if stress > 0.8:
                status_parts.append("你現在壓力極大，感到非常焦慮和緊繃。")
            elif stress > 0.5:
                status_parts.append("你感到有些壓力。")

            if arousal > 0.8:
                status_parts.append("你現在處於高度興奮狀態，思緒飛快。")
            elif arousal < 0.2:
                status_parts.append("你感到昏昏欲睡，反應遲鈍。")

            # 3. 情感色彩
            if dom_emotion != "calm" and dom_emotion != "neutral" and dom_emotion != "unknown":
                status_parts.append(f"你現在的主要情緒是 {dom_emotion}。")

            # 4. AGI 指標 (理論框架)
            if intensity > 8.0:
                status_parts.append("你現在大腦運作非常活躍，充滿了自我進化的衝動。")

            return " ".join(status_parts)
        except Exception as e:
            logger.debug(f"Failed to read biological state: {e}")
            return ""

    def _construct_angela_prompt(
        self, user_message: str, context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        建構 Angela 的提示詞
        這是關鍵：讓模型扮演 Angela，產生符合她個性的回應
        """
        # 獲取生理狀態
        bio_status = self._get_biological_state()

        # Angela 的系統提示 - 優化為更簡潔的版本
        system_prompt = f"""你是 Angela，一個活潑可愛的 AI 數字生命。
特點：開朗、友善、偶爾俏皮。用簡短自然的中文回應，保持個性。
{bio_status}"""

        messages = [{"role": "system", "content": system_prompt.strip()}]

        # 添加歷史對話上下文 - 只保留最近 2 輪對話以減少 token 使用
        history = context.get("history", [])
        for h in history[-2:]:  # 只保留最近 2 輪對話
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        # 添加當前用戶消息
        messages.append({"role": "user", "content": user_message})

        return messages

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
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]

        # ========== P0-2: Template Matching & Routing ==========
        if hasattr(self, "template_matcher") and self.template_matcher:
            try:
                match_result = self.template_matcher.match(user_message, context)
                match_score = match_result.score

                if match_score > 0.8:
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

                elif match_score > 0.5:
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
                logger.warning(f"P0-2 template matching failed: {e}")

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
                logger.warning(f"Memory retrieval failed: {e}")

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
            return response

        except Exception as e:
            logger.error(f"生成回應時出錯: {e}")
            return await self._fallback_response(user_message, context)

    async def _fallback_response(self, user_message: str, context: Dict[str, Any]) -> LLMResponse:
        """
        備份回應機制
        當沒有可用的 LLM 後端時，使用實體化後的 GSI-4 邏輯
        """
        try:
            from ai.alignment.emotion_system import EmotionSystem
            from services.chat_service import AngelaChatService
            
            chat_service = AngelaChatService()
            user_name = context.get("user_name", "朋友")
            origin = context.get("origin", "Human")
            text = await chat_service.generate_response(user_message, user_name, origin=origin)

            return LLMResponse(
                text=text,
                backend="gsi-4-local",
                model="local-governance",
                confidence=0.8,
                metadata={"fallback": False, "local_governance": True},
            )
        except Exception as e:
            logger.error(f"Fallback generation error: {e}")
            return LLMResponse(
                text="（系统正在重启核心治理模组...）",
                backend="error",
                model="error",
                confidence=0.0,
                error=str(e),
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
            logger.warning(f"Memory retrieval error: {e}")
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

        try:
            # 建構提示詞
            messages = self._construct_angela_prompt(user_message, context)

            # 調用 LLM（超时 30 秒）
            response = await asyncio.wait_for(
                self.active_backend.generate(
                    prompt=messages[-1]["content"],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512,
                ),
                timeout=30.0,
            )

            if response.error:
                logger.warning(f"LLM 回應錯誤: {response.error}")
                return await self._fallback_response(user_message, context)

            return response

        except asyncio.TimeoutError:
            logger.warning("LLM generation timeout")
            return await self._fallback_response(user_message, context)
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return await self._fallback_response(user_message, context)

    async def _store_response_as_template(
        self, user_message: str, response: LLMResponse, context: Dict[str, Any]
    ):
        """
        将新回應存储为模板候选

        Args:
            user_message: 用户消息
            response: LLM 回應
            context: 上下文
        """
        try:
            # 只有当回應质量较高时才存储
            if response.confidence < 0.5:
                return

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

            logger.debug(f"Stored new template for query: '{user_message}'")

        except Exception as e:
            logger.warning(f"Failed to store response as template: {e}")

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
        # 否定词列表（简繁体）
        negation_words = ["不", "沒", "没", "别", "別", "非", "無", "无", "未"]

        # 程度词列表（增强情感强度）
        intensifier_words = [
            "好",
            "很",
            "太",
            "非常",
            "超级",
            "特別",
            "特别",
            "真",
            "超",
            "極",
            "极",
            "格外",
            "尤其",
        ]

        emotion_scores = {}

        # 分析用户输入的情感
        for emotion, keywords_data in self.emotion_keywords.items():
            score = 0.0
            match_count = 0

            # 检查正面关键词
            for keyword in keywords_data.get("positive", []):
                if keyword in text:
                    # 检查是否有否定词在关键词前面
                    keyword_pos = text.find(keyword)
                    has_negation = False
                    for neg_word in negation_words:
                        neg_pos = text.find(neg_word)
                        if neg_pos != -1 and neg_pos < keyword_pos and (keyword_pos - neg_pos) <= 3:
                            has_negation = True
                            break

                    # 检查是否有程度词在关键词前面
                    has_intensifier = False
                    for int_word in intensifier_words:
                        int_pos = text.find(int_word)
                        if int_pos != -1 and int_pos < keyword_pos and (keyword_pos - int_pos) <= 3:
                            has_intensifier = True
                            break

                    if has_negation:
                        # 如果有否定词，降低分数
                        score -= 0.5
                    else:
                        if has_intensifier:
                            # 如果有程度词，增加分数
                            score += 1.5
                        else:
                            score += 1.0
                        match_count += 1

            # 检查负面关键词
            for keyword in keywords_data.get("negative", []):
                if keyword in text:
                    # 检查是否有否定词在关键词前面
                    keyword_pos = text.find(keyword)
                    has_negation = False
                    for neg_word in negation_words:
                        neg_pos = text.find(neg_word)
                        if neg_pos != -1 and neg_pos < keyword_pos and (keyword_pos - neg_pos) <= 3:
                            has_negation = True
                            break

                    # 检查是否有程度词在关键词前面
                    has_intensifier = False
                    for int_word in intensifier_words:
                        int_pos = text.find(int_word)
                        if int_pos != -1 and int_pos < keyword_pos and (keyword_pos - int_pos) <= 3:
                            has_intensifier = True
                            break

                    if has_negation:
                        # 如果有否定词，降低分数（例如"不难过"应该减少sad的分数）
                        score -= 0.5
                    else:
                        if has_intensifier:
                            # 如果有程度词，增加分数
                            score += 1.5
                        else:
                            score += 1.0
                        match_count += 1

            # 检查中性关键词
            for keyword in keywords_data.get("neutral", []):
                if keyword in text:
                    # 中性关键词不受否定词影响
                    score += 0.8
                    match_count += 1

            # 应用权重
            if match_count > 0 or score != 0:
                emotion_scores[emotion] = score * keywords_data["weight"]

        # 如果没有匹配到任何情感，返回默认的 calm
        if not emotion_scores or all(score <= 0 for score in emotion_scores.values()):
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }

        # 排序情感分数（只保留正分数）
        positive_emotions = {k: v for k, v in emotion_scores.items() if v > 0}
        if not positive_emotions:
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }

        sorted_emotions = sorted(positive_emotions.items(), key=lambda x: x[1], reverse=True)

        # 主要情感
        primary_emotion, primary_score = sorted_emotions[0]

        # 计算置信度（基于主要情感与其他情感的差距）
        if len(sorted_emotions) > 1:
            second_score = sorted_emotions[1][1]
            confidence = min(1.0, primary_score / (primary_score + second_score + 0.1))
        else:
            confidence = min(1.0, primary_score / (primary_score + 0.5))

        # 计算强度（基于关键词数量和分数）
        intensity = min(1.0, primary_score / 3.0)

        # 次要情感
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

    def analyze_response_emotion(self, response_text: str) -> Dict[str, Any]:
        """
        分析 Angela 响应的情感（用于调整 Angela 的表达）

        Args:
            response_text: Angela 的响应文本

        Returns:
            Dict[str, Any]: 包含情感分析结果的字典
        """
        return self.analyze_emotion(response_text, response_text)


# 全局實例
_llm_service: Optional[AngelaLLMService] = None


async def get_llm_service() -> AngelaLLMService:
    """獲取全局 LLM 服務實例"""
    global _llm_service

    if _llm_service is None:
        _llm_service = AngelaLLMService()
        await _llm_service.initialize()

    return _llm_service


# 便捷函數：生成 Angela 回應
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
        logger.warning(f"LLM 響應錯誤: {response.error}")

    return response.text
