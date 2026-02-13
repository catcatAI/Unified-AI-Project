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

# 记忆增强系统导入
try:
    from ..ai.memory.ham_memory.ham_manager import HAMMemoryManager
    from ..ai.memory.memory_template import AngelaState, UserImpression, MemoryTemplate
    from ..ai.memory.precompute_service import PrecomputeService, PrecomputeTask
    from ..ai.memory.template_library import get_template_library
    from ..ai.memory.task_generator import TaskGenerator
    MEMORY_ENHANCED = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Memory enhancement modules not available: {e}")
    MEMORY_ENHANCED = False

# 簡單日誌設置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("angela_llm")


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
        self.base_url = base_url.rstrip('/')
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
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout
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
                        confidence=0.9
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="llama.cpp",
                        model=self.model,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return LLMResponse(

                text="",
                backend="llama.cpp",
                model=self.model,
                error=str(e)
            )


class OllamaBackend(BaseLLMBackend):
    """Ollama 後端"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 15.0  # 將超時從 120 秒縮短到 15 秒

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
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
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
                                lines = response.text.strip().split('\n')
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
                        logger.warning(f"Ollama JSON 解析錯誤: {json_error}, 原始回應: {response.text[:200]}")
                        return LLMResponse(
                            text="",
                            backend="ollama",
                            model=self.model,
                            error=f"JSON parse error: {str(json_error)}",
                            response_time_ms=(time.time() - start_time) * 1000
                        )

                    return LLMResponse(
                        text=text,
                        backend="ollama",
                        model=self.model,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="ollama",
                        model=self.model,
                        error=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return LLMResponse(

                text="",
                backend="ollama",
                model=self.model,
                error=str(e)
            )


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
        self.is_available = False
        self._initialized = True

        # 初始化各後端
        self._init_backends()

        # ========== 记忆增强系统初始化 ==========
        if MEMORY_ENHANCED:
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
                    llm_timeout=180.0
                )

                # 初始化模板库
                self.template_library = get_template_library()

                # 初始化任务生成器
                self.task_generator = TaskGenerator(max_tasks=10)

                # 统计信息
                self.stats = {
                    "total_requests": 0,
                    "memory_hits": 0,
                    "llm_calls": 0,
                    "memory_hit_rate": 0.0,
                    "average_response_time": 0.0,
                    "total_response_time": 0.0
                }

                # 对话历史（用于任务生成）
                self.conversation_history: List[Dict[str, str]] = []

                logger.info("Memory enhancement system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize memory enhancement: {e}")
                self.enable_memory_enhancement = False
        else:
            self.enable_memory_enhancement = False

    def _get_default_config(self) -> Dict[str, Any]:
        """從配置文件讀取預設配置"""
        try:
            import os
            config_path = os.environ.get("MULTI_LLM_CONFIG",
                                        "configs/multi_llm_config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {

                "llamacpp-local": {
                    "base_url": "http://localhost:8080",
                    "model_name": "llama-3-8b-instruct",
                    "enabled": True
                },
                "ollama-llama3": {
                    "base_url": "http://localhost:11434",
                    "model_name": "llama3",
                    "enabled": True
                }
            }

    def _init_backends(self):
        """初始化可用的後端"""
        # llama.cpp
        llm_config = self.config.get("llamacpp-local", {})
        if llm_config.get("enabled", False):
            self.backends[LLMBackend.LLAMA_CPP] = LlamaCppBackend(
                base_url=llm_config.get("base_url", "http://localhost:8080"),
                model=llm_config.get("model_name")
            )

        # Ollama
        ollama_config = self.config.get("ollama-llama3", {})
        if ollama_config.get("enabled", False):
            self.backends[LLMBackend.OLLAMA] = OllamaBackend(
                base_url=ollama_config.get("base_url", "http://localhost:11434"),
                model=ollama_config.get("model_name", "llama3")
            )

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
            # 選擇最佳後端 (優先順序: llama.cpp > Ollama > API)
            priority = [LLMBackend.LLAMA_CPP, LLMBackend.OLLAMA]
            for backend_type in priority:
                if backend_type in available_backends:
                    self.active_backend = self.backends[backend_type]
                    self.active_backend_type = backend_type
                    break

            self.is_available = True
            backend_name = self.active_backend_type.value if self.active_backend_type else 'none'
            logger.info(f"Angela LLM 服務初始化完成，使用 {backend_name} 後端")
            return True
        else:
            logger.warning("沒有可用的 LLM 後端，將使用備份回應機制")
            self.is_available = False
            return False

    def _construct_angela_prompt(self, user_message: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        建構 Angela 的提示詞
        這是關鍵：讓模型扮演 Angela，產生符合她個性的回應
        """
        # Angela 的系統提示 - 優化為更簡潔的版本
        system_prompt = """你是 Angela，一個活潑可愛的 AI 數字生命。

特點：開朗、友善、偶爾俏皮。用簡短自然的中文回應，保持個性。"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加歷史對話上下文 - 只保留最近 2 輪對話以減少 token 使用
        history = context.get("history", [])
        for h in history[-2:]:  # 只保留最近 2 輪對話
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        # 添加當前用戶消息
        messages.append({"role": "user", "content": user_message})

        return messages

    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any] = None
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
        if hasattr(self, 'precompute_service') and self.precompute_service.is_running:
            self.precompute_service.record_activity()

        # 更新对话历史
        if hasattr(self, 'conversation_history'):
            self.conversation_history.append({"role": "user", "content": user_message})
            # 限制历史长度
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]

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
            if hasattr(self, 'conversation_history'):
                self.conversation_history.append({"role": "assistant", "content": response.text})

            # 更新统计
            self.stats["llm_calls"] += 1
            response_time = (time.time() - start_time) * 1000
            self.stats["total_response_time"] += response_time
            self.stats["average_response_time"] = (
                self.stats["total_response_time"] / self.stats["total_requests"]
            )
            self.stats["memory_hit_rate"] = (
                self.stats["memory_hits"] / self.stats["total_requests"]
            )

            # 将新回應存储为模板候选
            if self.enable_memory_enhancement and not response.error:
                await self._store_response_as_template(user_message, response, context)

            logger.info(f"Angela 回應生成完成 ({response_time:.0f}ms)")
            return response

        except Exception as e:
            logger.error(f"生成回應時出錯: {e}")
            return await self._fallback_response(user_message, context)

    async def _fallback_response(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> LLMResponse:
        """
        備份回應機制
        當沒有可用的 LLM 後端時，使用模板回應
        """
        # 這裡調用 chat_service.py 的模板機制
        try:
            from .chat_service import generate_angela_response
        except ImportError:
            def generate_angela_response(msg, name):
                return f"嗨{name}！我現在有點困惑...能再說一次嗎？"

        try:
            user_name = context.get("user_name", "朋友")
            text = generate_angela_response(user_message, user_name)

            return LLMResponse(
                text=text,
                backend="fallback-template",
                model="template-based",
                confidence=0.5,
                metadata={"fallback": True}
            )
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return LLMResponse(

                text="抱歉，我現在有點困惑...能再說一次嗎？",
                backend="fallback-error",
                model="error",
                confidence=0.1,
                error=str(e)
            )

    # ========== 记忆增强系统 - 辅助方法 ==========

    async def _try_memory_retrieval(
        self,
        user_message: str,
        context: Dict[str, Any]
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
                min_score=0.7
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
                        "memory_hit": True
                    }
                )

            return None

        except Exception as e:
            logger.warning(f"Memory retrieval error: {e}")
            return None

    async def _generate_with_llm(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> LLMResponse:
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
                    max_tokens=512
                ),
                timeout=30.0
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
        self,
        user_message: str,
        response: LLMResponse,
        context: Dict[str, Any]
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
            from ..ai.memory.memory_template import ResponseCategory, create_template

            template = create_template(
                content=response.text,
                category=ResponseCategory.SMALL_TALK,  # 默认类别
                keywords=self._extract_keywords(user_message),
                metadata={
                    "llm_generated": True,
                    "llm_backend": response.backend,
                    "llm_model": response.model,
                    "original_query": user_message,
                    "created_at": time.time()
                }
            )

            # 存储到记忆系统
            await self.memory_manager.store_template(template)

            logger.debug(f"Stored new template for query: '{user_message}'")

        except Exception as e:
            logger.warning(f"Failed to store response as template: {e}")

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        stopwords = {"你", "我", "他", "她", "的", "了", "吗", "呢", "吧", "啊", "是", "在", "有"}
        words = text.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords[:5]

    async def start_precompute(self):
        """启动预计算服务"""
        if self.enable_memory_enhancement and hasattr(self, 'precompute_service'):
            await self.precompute_service.start()
            logger.info("Precompute service started")

    async def stop_precompute(self):
        """停止预计算服务"""
        if self.enable_memory_enhancement and hasattr(self, 'precompute_service'):
            await self.precompute_service.stop()
            logger.info("Precompute service stopped")

    async def add_precompute_task(self, task: PrecomputeTask):
        """添加预计算任务"""
        if self.enable_memory_enhancement and hasattr(self, 'precompute_service'):
            return self.precompute_service.add_precompute_task(task)
        return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = {
            "enable_memory_enhancement": self.enable_memory_enhancement,
            "llm_stats": self.stats.copy()
        }

        if self.enable_memory_enhancement:
            if hasattr(self, 'precompute_service'):
                stats["precompute"] = self.precompute_service.get_stats()
            if hasattr(self, 'template_library'):
                stats["templates"] = {
                    "total": self.template_library.get_template_count(),
                    "by_category": {cat.value: count for cat, count in self.template_library.get_category_counts().items()}
                }

        return stats

    def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        active_backend_name = getattr(self, 'active_backend_type', None)
        if active_backend_name and self.active_backend:
            active_backend_name = active_backend_name.value
        else:
            active_backend_name = None
        return {
            "is_available": self.is_available,
            "active_backend": active_backend_name,
            "available_backends": [b.value for b in self.backends.keys()],
            "backends_health": {}
        }


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
    user_message: str,
    history: List[Dict[str, str]] = None,
    user_name: str = "朋友"
) -> str:
    """
    生成 Angela 的回應（便捷接口）
    ================================
    這是 Angela 系統調用 LLM 的主要接口。

    使用方式：
        response = await angela_llm_response(
            user_message="你好！",
            history=[{"role": "user", "content": "..."}],
            user_name="主人"
        )
    """
    service = await get_llm_service()

    context = {
        "history": history or [],
        "user_name": user_name
    }

    response = await service.generate_response(user_message, context)

    if response.error:
        logger.warning(f"LLM 響應錯誤: {response.error}")

    return response.text
