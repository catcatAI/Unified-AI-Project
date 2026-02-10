"""
Multi-LLM Service - 多模型 LLM 服務
===================================
為 Angela AI 提供統一的 LLM 調用接口，支援多種後端：
- llama.cpp (本地)
- Ollama (本地)
- OpenAI GPT-4/3.5
- Anthropic Claude
- Google Gemini
- Azure OpenAI
- HuggingFace

此模組還與 Angela 的認知矩陣系統集成，確保對話：
1. 經過 UCC (統一控制中心) 的認知處理
2. 存儲到 HAM (分層記憶系統)
3. 經過情感系統調整

硬件自適應：
- 自動檢測 NVIDIA, AMD, Intel, Apple Silicon, CPU
- 根據可用 VRAM/RAM 推薦最佳配置
- 處理層級、維度兼容性問題
"""

import asyncio
import json
import logging
import time
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

# 使用統一的硬件資源總控中心
try:
    from core.hardware import (
        UnifiedHardwareCenter,
        HardwareDetector,
        AcceleratorType,
        PrecisionLevel,
        get_hardware_center,
        HardwareProfile
    )
    HARDWARE_CENTER_AVAILABLE = True
except ImportError:
    HARDWARE_CENTER_AVAILABLE = False
    logger.warning("Hardware center not available, using fallback")


class ModelProvider(Enum):
    """支援的 LLM 提供者"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """對話消息"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    timestamp: Optional[datetime] = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )


@dataclass
class LLMResponse:
    """LLM 回應"""
    content: str
    model: str
    provider: str
    token_usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "token_usage": self.token_usage,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ModelConfig:
    """模型配置"""
    model_id: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window: int = 8192
    cost_per_1k_tokens: float = 0.0
    enabled: bool = True
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "model_name": self.model_name,
            "api_key": "***" if self.api_key else None,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": self.context_window,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "enabled": self.enabled,
            "capabilities": self.capabilities
        }


class BaseLLMBackend(ABC):
    """LLM 後端基礎類"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.is_available = False

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化後端"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """聊天補全"""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """健康檢查"""
        pass


class OpenAIBackend(BaseLLMBackend):
    """OpenAI GPT 後端"""

    async def initialize(self) -> bool:
        if not self.config.api_key:
            logger.warning(f"OpenAI API key not set for {self.config.model_id}")
            return False
        self.is_available = True
        return True

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()

        url = f"{self.config.base_url or 'https://api.openai.com/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_id or self.config.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            provider="openai",
            token_usage={
                "prompt": data["usage"]["prompt_tokens"],
                "completion": data["usage"]["completion_tokens"],
                "total": data["usage"]["total_tokens"]
            },
            latency_ms=latency_ms
        )

    async def check_health(self) -> bool:
        if not self.config.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.config.api_key}"}
                )
                return response.status_code == 200
        except Exception:
            return False


class AnthropicBackend(BaseLLMBackend):
    """Anthropic Claude 後端"""

    ANTHROPIC_URL = "https://api.anthropic.com/v1"

    async def initialize(self) -> bool:
        if not self.config.api_key:
            logger.warning(f"Anthropic API key not set for {self.config.model_id}")
            return False
        self.is_available = True
        return True

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()

        url = f"{self.ANTHROPIC_URL}/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model_id or self.config.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data["content"][0]["text"],
            model=data["model"],
            provider="anthropic",
            token_usage={
                "input_tokens": data["usage"]["input_tokens"],
                "output_tokens": data["usage"]["output_tokens"]
            },
            latency_ms=latency_ms
        )

    async def check_health(self) -> bool:
        if not self.config.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ANTHROPIC_URL}/messages", headers={
                    "x-api-key": self.config.api_key
                })
                return response.status_code == 200
        except Exception:
            return False


class OllamaBackend(BaseLLMBackend):
    """Ollama 本地後端"""

    async def initialize(self) -> bool:
        self.is_available = await self.check_health()
        return self.is_available

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()

        base_url = self.config.base_url or "http://localhost:11434"
        model = model_id or self.config.model_name

        payload = {
            "model": model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data["message"]["content"],
            model=model,
            provider="ollama",
            latency_ms=latency_ms
        )

    async def check_health(self) -> bool:
        base_url = self.config.base_url or "http://localhost:11434"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


class LlamaCppBackend(BaseLLMBackend):
    """ llama.cpp 伺服器後端 """

    async def initialize(self) -> bool:
        self.is_available = await self.check_health()
        return self.is_available

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()

        base_url = self.config.base_url or "http://localhost:8080"
        model = model_id or self.config.model_name

        payload = {
            "model": model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{base_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=model,
            provider="llama_cpp",
            token_usage=data.get("usage", {}),
            latency_ms=latency_ms
        )

    async def check_health(self) -> bool:
        base_url = self.config.base_url or "http://localhost:8080"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/v1/models")
                return response.status_code == 200
        except Exception:
            return False


class MultiLLMService:
    """
    多模型 LLM 服務管理器

    職責：
    1. 管理多個 LLM 後端
    2. 根據配置選擇最佳後端
    3. 實現回退機制
    4. 追蹤使用統計
    5. 硬件自適應配置
    """

    def __init__(self, config_path: Optional[str] = None):
        self.backends: Dict[str, BaseLLMBackend] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.default_model: Optional[str] = None
        self._initialize_lock = asyncio.Lock()
        
        # 硬件檢測結果
        self.hardware_info = None
        self.ollama_settings = {}
        
        # 嘗試舊的硬件檢測作為 fallback (同步版本)
        try:
            from .hardware_detector import HardwareDetector, HardwareAdapter
            detector = HardwareDetector()
            self.hardware_info = detector.detect()
            adapter = HardwareAdapter(self.hardware_info)
            self.ollama_settings = adapter.get_recommended_settings()
            logger.info(f"Hardware detected (fallback): {self.hardware_info.accelerator_type.value}")
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}, using default settings")

        if config_path:
            self._load_config(config_path)
        else:
            # 自動配置 Ollama
            self._auto_configure_ollama()

    def _load_config(self, config_path: str) -> None:
        """從 JSON 配置文件加載配置"""
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for model_id, model_config in config.get("models", {}).items():
                self.model_configs[model_id] = ModelConfig(
                    model_id=model_id,
                    provider=model_config.get("provider", "openai"),
                    model_name=model_config.get("model_name", model_id),
                    api_key=model_config.get("api_key"),
                    base_url=model_config.get("base_url"),
                    max_tokens=model_config.get("max_tokens", 4096),
                    temperature=model_config.get("temperature", 0.7),
                    context_window=model_config.get("context_window", 8192),
                    cost_per_1k_tokens=model_config.get("cost_per_1k_tokens", 0.0),
                    enabled=model_config.get("enabled", True),
                    capabilities=model_config.get("capabilities", [])
                )

                if model_config.get("enabled", True):
                    self.default_model = model_id

            logger.info(f"Loaded {len(self.model_configs)} model configs from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")

    def _auto_configure_ollama(self) -> None:
        """根據硬件自動配置 Ollama 後端"""
        # 檢查 Ollama 是否可用
        ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
        try:
            import httpx
            response = httpx.get(f"{ollama_url}/api/version", timeout=5.0)
            if response.status_code == 200:
                logger.info("Ollama server detected, configuring...")
            else:
                logger.warning("Ollama server not responding")
                return
        except Exception:
            logger.warning("Ollama not available")
            return
        
        # 根據硬件推薦選擇模型
        if self.hardware_info:
            recommendations = self.ollama_settings.get("model_recommendations", [])
            if recommendations:
                recommended_model = recommendations[0]
                model_name = recommended_model.get("name", "llama3.2:1b")
                
                # 創建 Ollama 配置
                ollama_config = ModelConfig(
                    model_id="ollama-local",
                    provider="ollama",
                    model_name=model_name,
                    base_url=ollama_url,
                    max_tokens=2048,
                    temperature=0.7,
                    context_window=4096,
                    enabled=True,
                    capabilities=["chat", "reasoning", "code"]
                )
                
                self.model_configs["ollama-local"] = ollama_config
                self.default_model = "ollama-local"
                
                logger.info(f"Auto-configured Ollama with model: {model_name}")
                logger.info(f"Reason: {recommended_model.get('notes', '')}")
                
                # 記錄性能備註
                for note in self.ollama_settings.get("performance_notes", []):
                    logger.info(f"Performance note: {note}")
        else:
            # 使用默認配置
            ollama_config = ModelConfig(
                model_id="ollama-local",
                provider="ollama",
                model_name="llama3.2:1b",
                base_url="http://localhost:11434",
                max_tokens=2048,
                temperature=0.7,
                context_window=4096,
                enabled=True,
                capabilities=["chat", "reasoning", "code"]
            )
            self.model_configs["ollama-local"] = ollama_config
            self.default_model = "ollama-local"
            logger.info("Auto-configured Ollama with default model: llama3.2:1b")

    async def initialize(self) -> None:
        """初始化所有可用的後端"""
        async with self._initialize_lock:
            # 使用統一的硬件資源總控中心 (異步初始化)
            if HARDWARE_CENTER_AVAILABLE:
                try:
                    center = await get_hardware_center()
                    if center.hardware_profile:
                        self.hardware_info = center.hardware_profile
                        accelerator = center.hardware_profile.accelerator
                        if accelerator:
                            logger.info(f"Hardware detected: {accelerator.type.value} - {accelerator.name}")
                except Exception as e:
                    logger.warning(f"Hardware center init failed: {e}")
            
            # 初始化所有可用的後端
            for model_id, config in self.model_configs.items():
                if not config.enabled:
                    continue

                backend = self._create_backend(config)
                if await backend.initialize():
                    self.backends[model_id] = backend
                    logger.info(f"Backend {model_id} ({config.provider}) initialized successfully")
                else:
                    logger.warning(f"Backend {model_id} ({config.provider}) initialization failed")

    def _create_backend(self, config: ModelConfig) -> BaseLLMBackend:
        """根據配置創建後端"""
        provider = config.provider.lower()

        if provider in ("openai", "azure_openai"):
            return OpenAIBackend(config)
        elif provider == "anthropic":
            return AnthropicBackend(config)
        elif provider == "ollama":
            return OllamaBackend(config)
        elif provider in ("llama_cpp", "llamacpp"):
            return LlamaCppBackend(config)
        else:
            logger.warning(f"Unknown provider {provider}, using OpenAI backend")
            return OpenAIBackend(config)

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """聊天補全 - 自動選擇可用後端"""
        if not self.backends:
            raise RuntimeError("No LLM backends available. Please initialize the service first.")

        target_model = model_id or self.default_model

        if target_model and target_model in self.backends:
            backend = self.backends[target_model]
            if backend.is_available:
                return await backend.chat_completion(messages, model_id, **kwargs)

        for model_id, backend in self.backends.items():
            if backend.is_available:
                logger.info(f"Falling back to {model_id}")
                return await backend.chat_completion(messages, model_id, **kwargs)

        raise RuntimeError("No available LLM backends")

    async def check_health(self) -> Dict[str, bool]:
        """檢查所有後端的健康狀態"""
        health_status = {}
        for model_id, backend in self.backends.items():
            health_status[model_id] = await backend.check_health()
        return health_status

    def list_available_models(self) -> List[ModelConfig]:
        """列出所有可用的模型配置"""
        return [cfg for cfg in self.model_configs.values() if cfg.enabled]

    def add_model(self, config: ModelConfig) -> None:
        """添加新模型配置"""
        self.model_configs[config.model_id] = config

    def remove_model(self, model_id: str) -> bool:
        """移除模型配置"""
        if model_id in self.model_configs:
            del self.model_configs[model_id]
            if model_id in self.backends:
                del self.backends[model_id]
            return True
        return False

    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """獲取模型配置"""
        return self.model_configs.get(model_id)
