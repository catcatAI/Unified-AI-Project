"""
多模型 LLM 服务
支持 OpenAI GPT、Google Gemini、Anthropic Claude、Ollama 等主流 AI 模型
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Coroutine, AsyncGenerator

import aiohttp
# 修复：添加条件导入以避免导入错误
try:
    import openai
except ImportError:
    openai = None

try:
    import cohere
except ImportError:
    cohere = None

try:
    from azure.identity import DefaultAzureCredential
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
except ImportError:
    DefaultAzureCredential = None
    AzureKeyCredential = None
    ChatCompletionsClient = None
    SystemMessage = None
    UserMessage = None

try:
    from aiolimiter import AsyncLimiter
except ImportError:
    AsyncLimiter = None

# 修复：添加 Anthropic 条件导入
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

# 修复：添加 Google GenerativeAI 条件导入
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None
    GenerationConfig = None

logger: logging.Logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"

@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    enabled: bool = True
    cost_per_1k_tokens: float = 0.0
    context_window: int = 4096

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: ModelProvider
    usage: Dict[str, int]
    cost: float
    latency: float
    timestamp: datetime
    metadata: Dict[str, Any]

class BaseLLMProvider(ABC):
    """LLM 提供商基类"""
    
    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        """聊天完成"""
        pass
    
    @abstractmethod
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        pass
    
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            _ = await self.session.close

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        # 修复：使用正确的 OpenAI 客户端初始化方式，添加条件检查
        if openai is not None:
            self.client = openai.AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        else:
            self.client = None
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        try:
            openai_messages = 
            for msg in messages:
                # Check if msg is a dictionary or ChatMessage object
                if isinstance(msg, dict):
                    openai_messages.append({"role": msg["role"], "content": msg["content"]})
                else:
                    openai_messages.append({"role": msg.role, "content": msg.content})
            
            # Mock fallback for tests when no/invalid key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "dummy_key":
                return LLMResponse(
                    content="Mock response (no API key)",
                    model=self.config.model_name,
                    provider=ModelProvider.OPENAI,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    cost=0.0,
                    latency=0.1,
                    timestamp=datetime.now,
                    metadata=
                )
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("OpenAI 客户端未正确初始化")
            
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=openai_messages,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
                frequency_penalty=kwargs.get('frequency_penalty', self.config.frequency_penalty),
                presence_penalty=kwargs.get('presence_penalty', self.config.presence_penalty),
                timeout=self.config.timeout
            )
            
            latency = (datetime.now - start_time).total_seconds
            usage_dict = response.usage.model_dump if response.usage else 
            usage: Dict[str, int] = {
                "prompt_tokens": usage_dict.get("prompt_tokens", 0),
                "completion_tokens": usage_dict.get("completion_tokens", 0),
                "total_tokens": usage_dict.get("total_tokens", 0)
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.config.model_name,
                provider=ModelProvider.OPENAI,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            logger.error(f"OpenAI API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        openai_messages = 
        for msg in messages:
            # Check if msg is a dictionary or ChatMessage object
            if isinstance(msg, dict):
                openai_messages.append({"role": msg["role"], "content": msg["content"]})
            else:
                openai_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("OpenAI 客户端未正确初始化")
            
            stream = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=openai_messages,
                stream=True,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                timeout=self.config.timeout
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        if AsyncAnthropic is not None:
            self.client = AsyncAnthropic(api_key=config.api_key)
        else:
            self.client = None
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        try:
            # 转换消息格式
            claude_messages = 
            system_message = None
            
            for msg in messages:
                # Check if msg is a dictionary or ChatMessage object
                if isinstance(msg, dict):
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        claude_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                else:
                    if msg.role == "system":
                        system_message = msg.content
                    else:
                        claude_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
            
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("Anthropic 客户端未正确初始化")
            
            response = await self.client.messages.create(
                model=self.config.model_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                system=system_message or "",
                messages=claude_messages
            )
            
            latency = (datetime.now - start_time).total_seconds
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            cost = self._calculate_cost(usage)
            
            # 获取 Claude 响应的文本内容
            content_text = ""
            if response.content and len(response.content) > 0:
                # 安全地提取文本内容
                content_item = response.content[0]
                if hasattr(content_item, 'text'):
                    content_text = str(getattr(content_item, 'text', ''))
            
            return LLMResponse(
                content=content_text,
                model=self.config.model_name,
                provider=ModelProvider.ANTHROPIC,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now,
                metadata={"stop_reason": response.stop_reason}
            )
            
        except Exception as e:
            logger.error(f"Anthropic API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 转换消息格式
        claude_messages = 
        system_message = None
        
        for msg in messages:
            # Check if msg is a dictionary or ChatMessage object
            if isinstance(msg, dict):
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            else:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    claude_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
        
        try:
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("Anthropic 客户端未正确初始化")
            
            async with self.client.messages.stream(
                model=self.config.model_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                system=system_message or "",
                messages=claude_messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens

class GoogleProvider(BaseLLMProvider):
    """Google Gemini 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model_name)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        try:
            # 转换消息格式
            chat_history = 
            user_message = ""
            
            for msg in messages:
                if msg.role == "system":
                    # Gemini 没有 system role，将其作为第一条用户消息
                    chat_history.append({
                        "role": "user",
                        "parts": [msg.content]
                    })
                    chat_history.append({
                        "role": "model",
                        "parts": ["我理解了这些指示。"]
                    })
                elif msg.role == "user":
                    user_message = msg.content
                elif msg.role == "assistant":
                    chat_history.append({
                        "role": "user",
                        "parts": [user_message] if user_message else ["继续"]
                    })
                    chat_history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
                    user_message = ""
            
            # 如果有最后的用户消息，添加到历史中
            if user_message:
                chat_history.append({
                    "role": "user",
                    "parts": [user_message]
                })
            
            # 创建聊天会话
            chat = self.model.start_chat(history=chat_history[:-1] if chat_history else )
            
            # 发送最后一条消息
            last_message = chat_history[-1]["parts"][0] if chat_history else "Hello"
            response = await chat.send_message_async(
                last_message,
                generation_config=GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                    temperature=kwargs.get('temperature', self.config.temperature),
                    top_p=kwargs.get('top_p', self.config.top_p),
                )
            )
            
            latency = (datetime.now - start_time).total_seconds
            
            # Gemini 不提供详细的 token 使用信息
            usage = {
                "prompt_tokens": len(last_message) // 4,  # 估算
                "completion_tokens": len(response.text) // 4,  # 估算
                "total_tokens": (len(last_message) + len(response.text)) // 4
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.text,
                model=self.config.model_name,
                provider=ModelProvider.GOOGLE,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now,
                metadata={"finish_reason": "stop"}
            )
            
        except Exception as e:
            logger.error(f"Google Gemini API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 类似的消息转换逻辑
        chat_history = 
        user_message = ""
        
        for msg in messages:
            if msg.role == "system":
                chat_history.append({
                    "role": "user",
                    "parts": [msg.content]
                })
                chat_history.append({
                    "role": "model",
                    "parts": ["我理解了这些指示。"]
                })
            elif msg.role == "user":
                user_message = msg.content
            elif msg.role == "assistant":
                chat_history.append({
                    "role": "user",
                    "parts": [user_message] if user_message else ["继续"]
                })
                chat_history.append({
                    "role": "model",
                    "parts": [msg.content]
                })
                user_message = ""
        
        if user_message:
            chat_history.append({
                "role": "user",
                "parts": [user_message]
            })
        
        try:
            chat = self.model.start_chat(history=chat_history[:-1] if chat_history else )
            last_message = chat_history[-1]["parts"][0] if chat_history else "Hello"
            
            response = await chat.send_message_async(
                last_message,
                stream=True,
                generation_config=GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                    temperature=kwargs.get('temperature', self.config.temperature),
                )
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Google Gemini 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens

class OllamaProvider(BaseLLMProvider):
    """Ollama 本地模型提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        # 确保会话已初始化
        if not self.session:
            self.session = aiohttp.ClientSession
        
        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            payload = {
                "model": self.config.model_name,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API 错误: {response.status}")
                
                result = await response.json
                
                latency = (datetime.now - start_time).total_seconds
                
                # Ollama 提供的使用统计
                usage = {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }
                
                return LLMResponse(
                    content=result["message"]["content"],
                    model=self.config.model_name,
                    provider=ModelProvider.OLLAMA,
                    usage=usage,
                    cost=0.0,  # 本地模型无成本
                    latency=latency,
                    timestamp=datetime.now,
                    metadata={
                        "done": result.get("done", True),
                        "total_duration": result.get("total_duration", 0),
                        "load_duration": result.get("load_duration", 0),
                        "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                        "eval_duration": result.get("eval_duration", 0)
                    }
                )
                
        except Exception as e:
            logger.error(f"Ollama API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 确保会话已初始化
        if not self.session:
            self.session = aiohttp.ClientSession
            
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.config.model_name,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API 错误: {response.status}")
                
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if chunk.get("message", ).get("content"):
                                yield chunk["message"]["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Ollama 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """本地模型无成本"""
        return 0.0

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        # 修复凭据处理
        if config.api_key:
            credential = AzureKeyCredential(config.api_key)
        else:
            credential = DefaultAzureCredential
            
        self.client = ChatCompletionsClient(
            endpoint=config.base_url or "",
            credential=credential
        )
        self.deployment_name = getattr(config, 'deployment_name', config.model_name)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        try:
            azure_messages = 
            for msg in messages:
                if msg.role == "system":
                    azure_messages.append(SystemMessage(content=msg.content))
                elif msg.role == "user":
                    azure_messages.append(UserMessage(content=msg.content))
                # Azure 会自动处理 assistant 消息
            
            response = self.client.complete(
                messages=azure_messages,
                model=self.deployment_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
            )
            
            latency = (datetime.now - start_time).total_seconds
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.config.model_name,
                provider=ModelProvider.AZURE_OPENAI,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # Azure OpenAI 流式实现
        azure_messages = 
        for msg in messages:
            if msg.role == "system":
                azure_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                azure_messages.append(UserMessage(content=msg.content))
        
        try:
            response = self.client.complete(
                messages=azure_messages,
                model=self.deployment_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Azure OpenAI 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens

class CohereProvider(BaseLLMProvider):
    """Cohere 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        if cohere is not None:
            self.client = cohere.AsyncClient(api_key=config.api_key)
        else:
            self.client = None
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        try:
            # 转换消息格式
            chat_history = 
            user_message = ""
            
            for msg in messages:
                if msg.role == "system":
                    # Cohere 使用 preamble 作为系统消息
                    preamble = msg.content
                elif msg.role == "user":
                    user_message = msg.content
                elif msg.role == "assistant":
                    if user_message:
                        chat_history.append({"role": "USER", "message": user_message})
                        chat_history.append({"role": "CHATBOT", "message": msg.content})
                        user_message = ""
            
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("Cohere 客户端未正确初始化")
            
            response = await self.client.chat(
                model=self.config.model_name,
                message=user_message or "Hello",
                chat_history=chat_history,
                preamble=locals.get('preamble', ''),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
            )
            
            latency = (datetime.now - start_time).total_seconds
            
            # Cohere 不提供详细的 token 使用信息
            usage = {
                "prompt_tokens": len(user_message) // 4,  # 估算
                "completion_tokens": len(response.text) // 4,  # 估算
                "total_tokens": (len(user_message) + len(response.text)) // 4
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.text,
                model=self.config.model_name,
                provider=ModelProvider.COHERE,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now,
                metadata={"finish_reason": "COMPLETE"}
            )
            
        except Exception as e:
            logger.error(f"Cohere API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # Cohere 流式实现
        chat_history = 
        user_message = ""
        
        for msg in messages:
            if msg.role == "system":
                preamble = msg.content
            elif msg.role == "user":
                user_message = msg.content
            elif msg.role == "assistant":
                if user_message:
                    chat_history.append({"role": "USER", "message": user_message})
                    chat_history.append({"role": "CHATBOT", "message": msg.content})
                    user_message = ""
        
        try:
            # 检查客户端是否已正确初始化
            if self.client is None:
                raise Exception("Cohere 客户端未正确初始化")
            
            response = self.client.chat_stream(
                model=self.config.model_name,
                message=user_message or "Hello",
                chat_history=chat_history,
                preamble=locals.get('preamble', ''),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
            )
            
            async for chunk in response:
                if chunk.event_type == "text-generation":
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Cohere 流式 API 错误: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens

class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face 提供商"""
    
    def __init__(self, config: ModelConfig) -> None:
        super.__init__(config)
        self.base_url = config.base_url or "https://api-inference.huggingface.co/models/"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now
        
        # 确保会话已初始化
        if not self.session:
            self.session = aiohttp.ClientSession
        
        try:
            # 构建提示文本
            prompt = self._build_prompt(messages)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "return_full_text": False
                }
            }
            
            async with self.session.post(
                f"{self.base_url}{self.config.model_name}",
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Hugging Face API 错误: {response.status}")
                
                result = await response.json
                
                latency = (datetime.now - start_time).total_seconds
                
                # 提取生成的文本
                generated_text = result[0]["generated_text"] if isinstance(result, list) else result["generated_text"]
                
                # 估算 token 使用
                usage = {
                    "prompt_tokens": len(prompt) // 4,
                    "completion_tokens": len(generated_text) // 4,
                    "total_tokens": (len(prompt) + len(generated_text)) // 4
                }
                
                return LLMResponse(
                    content=generated_text,
                    model=self.config.model_name,
                    provider=ModelProvider.HUGGINGFACE,
                    usage=usage,
                    cost=0.0,  # Hugging Face Inference API 通常免费
                    latency=latency,
                    timestamp=datetime.now,
                    metadata={"finish_reason": "stop"}
                )
                
        except Exception as e:
            logger.error(f"Hugging Face API 错误: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        async for chunk in self._stream_impl(messages, **kwargs):
            yield chunk
    
    async def _stream_impl(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 确保会话已初始化
        if not self.session:
            self.session = aiohttp.ClientSession
            
        # Hugging Face Inference API 不直接支持流式，这里模拟实现
        response = await self.chat_completion(messages, **kwargs)
        
        # 将完整响应分块返回
        words = response.content.split
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            _ = await asyncio.sleep(0.05)  # 模拟流式延迟
    
    def _build_prompt(self, messages: List[ChatMessage]) -> str:
        """构建提示文本"""
        prompt_parts = 
        
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Hugging Face Inference API 通常免费"""
        return 0.0

LLM_ROUTER_ENABLED = os.getenv('LLM_ROUTER_ENABLED', 'true').lower == 'true'

class MultiLLMService:
    """多模型 LLM 服务"""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.providers: Dict[str, BaseLLMProvider] = 
        self.model_configs: Dict[str, ModelConfig] = 
        self.default_model: Optional[str] = None
        self.usage_stats: Dict[str, Dict[str, Any]] = 
        self.limiters: Dict[str, AsyncLimiter] = 
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.default_model = config.get('default_model')

            # Load rate limiting config
            rate_limit_config = config.get('rate_limiting', )
            if rate_limit_config.get('enabled', False):
                rpm_map = rate_limit_config.get('requests_per_minute', )
                for provider_name, rpm in rpm_map.items:
                    self.limiters[provider_name] = AsyncLimiter(rpm, 60)
            
            for model_id, model_config in config.get('models', ).items:
                provider = ModelProvider(model_config['provider'])
                
                self.model_configs[model_id] = ModelConfig(
                    provider=provider,
                    model_name=model_config['model_name'],
                    api_key=os.getenv(model_config.get('api_key_env', '')),
                    base_url=model_config.get('base_url'),
                    max_tokens=model_config.get('max_tokens', 4096),
                    temperature=model_config.get('temperature', 0.7),
                    top_p=model_config.get('top_p', 1.0),
                    frequency_penalty=model_config.get('frequency_penalty', 0.0),
                    presence_penalty=model_config.get('presence_penalty', 0.0),
                    timeout=model_config.get('timeout', 60),
                    enabled=model_config.get('enabled', True),
                    cost_per_1k_tokens=model_config.get('cost_per_1k_tokens', 0.0),
                    context_window=model_config.get('context_window', 4096)
                )
                
                # 初始化使用统计
                self.usage_stats[model_id] = {
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'average_latency': 0.0,
                    'error_count': 0
                }
                
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _create_provider(self, config: ModelConfig) -> BaseLLMProvider:
        """创建提供商实例"""
        if config.provider == ModelProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == ModelProvider.ANTHROPIC:
            return AnthropicProvider(config)
        elif config.provider == ModelProvider.GOOGLE:
            return GoogleProvider(config)
        elif config.provider == ModelProvider.OLLAMA:
            return OllamaProvider(config)
        elif config.provider == ModelProvider.AZURE_OPENAI:
            return AzureOpenAIProvider(config)
        elif config.provider == ModelProvider.COHERE:
            return CohereProvider(config)
        elif config.provider == ModelProvider.HUGGINGFACE:
            return HuggingFaceProvider(config)
        else:
            raise ValueError(f"不支持的提供商: {config.provider}")
    
    def _ensure_router(self):
        try:
            from apps.backend.src.core_ai.language_models.registry import ModelRegistry
            from apps.backend.src.core_ai.language_models.router import PolicyRouter, RoutingPolicy
        except Exception:
            return None, None, None
        registry = ModelRegistry(self.model_configs)
        router = PolicyRouter(registry)
        return registry, router, RoutingPolicy

    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        model_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """聊天完成"""
        model_id = model_id or self.default_model
        if not model_id or model_id not in self.model_configs:
            raise ValueError(f"模型 {model_id} 不存在")
        
        config = self.model_configs[model_id]
        if not config.enabled:
            raise ValueError(f"模型 {model_id} 已禁用")
        
        # Rate limiting
        provider_name = config.provider.value
        if provider_name in self.limiters:
            async with self.limiters[provider_name]:
                return await self._execute_chat_completion(model_id, messages, **kwargs)
        else:
            return await self._execute_chat_completion(model_id, messages, **kwargs)

    async def _execute_chat_completion(
        self,
        model_id: str,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        # 获取或创建提供商
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(self.model_configs[model_id])
        
        provider = self.providers[model_id]
        
        try:
            async with provider:
                response = await provider.chat_completion(messages, **kwargs)
                
                # 确保响应是LLMResponse对象而不是字典
                if isinstance(response, dict):
                    # 如果是字典，转换为LLMResponse对象
                    usage_data = response.get('usage', )
                    # 确保usage是一个字典
                    if not isinstance(usage_data, dict):
                        usage_data = {'total_tokens': 0}
                    
                    response = LLMResponse(
                        content=response.get('content', ''),
                        model=response.get('model', model_id),
                        provider=response.get('provider', self.model_configs[model_id].provider),
                        usage=usage_data,
                        cost=response.get('cost', 0.0),
                        latency=response.get('latency', 0.0),
                        timestamp=response.get('timestamp', datetime.now),
                        metadata=response.get('metadata', )
                    )
                
                # 更新使用统计
                self._update_usage_stats(model_id, response)
                
                return response
                
        except Exception as e:
            self.usage_stats[model_id]['error_count'] += 1
            logger.error(f"模型 {model_id} 请求失败: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[ChatMessage], 
        model_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        model_id = model_id or self.default_model
        if not model_id or model_id not in self.model_configs:
            raise ValueError(f"模型 {model_id} 不存在")
        
        config = self.model_configs[model_id]
        if not config.enabled:
            raise ValueError(f"模型 {model_id} 已禁用")
        
        # Rate limiting
        provider_name = config.provider.value
        if provider_name in self.limiters:
            async with self.limiters[provider_name]:
                async for chunk in self._execute_stream_completion(model_id, messages, **kwargs):
                    yield chunk
        else:
            async for chunk in self._execute_stream_completion(model_id, messages, **kwargs):
                yield chunk

    async def _execute_stream_completion(
        self,
        model_id: str,
        messages: List[ChatMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # 获取或创建提供商
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(self.model_configs[model_id])
        
        provider = self.providers[model_id]
        
        try:
            async with provider:
                # 获取流式响应协程并等待它
                stream_coroutine = provider.stream_completion(messages, **kwargs)
                stream_generator = await stream_coroutine
                # 正确迭代流式响应
                async for chunk in stream_generator:
                    yield chunk
        except Exception as e:
            self.usage_stats[model_id]['error_count'] += 1
            logger.error(f"模型 {model_id} 流式请求失败: {e}")
            raise
    
    def _update_usage_stats(self, model_id: str, response: LLMResponse):
        """更新使用统计"""
        stats = self.usage_stats[model_id]
        stats['total_requests'] += 1
        stats['total_tokens'] += response.usage.get('total_tokens', 0)
        stats['total_cost'] += response.cost
        
        # 更新平均延迟
        current_avg = stats['average_latency']
        total_requests = stats['total_requests']
        stats['average_latency'] = (
            (current_avg * (total_requests - 1) + response.latency) / total_requests
        )
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return [
            model_id for model_id, config in self.model_configs.items
            if config.enabled
        ]
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_id not in self.model_configs:
            raise ValueError(f"模型 {model_id} 不存在")
        
        config = self.model_configs[model_id]
        stats = self.usage_stats.get(model_id, )
        
        return {
            'model_id': model_id,
            'provider': config.provider.value,
            'model_name': config.model_name,
            'enabled': config.enabled,
            'max_tokens': config.max_tokens,
            'context_window': config.context_window,
            'cost_per_1k_tokens': config.cost_per_1k_tokens,
            'usage_stats': stats
        }
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """获取使用摘要"""
        total_requests = sum(stats['total_requests'] for stats in self.usage_stats.values)
        total_tokens = sum(stats['total_tokens'] for stats in self.usage_stats.values)
        total_cost = sum(stats['total_cost'] for stats in self.usage_stats.values)
        total_errors = sum(stats['error_count'] for stats in self.usage_stats.values)
        
        return {
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'total_errors': total_errors,
            'models': {
                model_id: self.get_model_info(model_id)
                for model_id in self.model_configs.keys
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = 
        
        for model_id, config in self.model_configs.items:
            if not config.enabled:
                health_status[model_id] = {'status': 'disabled'}
                continue
            
            try:
                # 发送简单的测试消息
                test_messages = [ChatMessage(role="user", content="Hello")]
                
                if model_id not in self.providers:
                    self.providers[model_id] = self._create_provider(config)
                
                provider = self.providers[model_id]
                async with provider:
                    response = await provider.chat_completion(test_messages, max_tokens=10)
                    health_status[model_id] = {
                        'status': 'healthy',
                        'latency': response.latency
                    }
                    
            except Exception as e:
                health_status[model_id] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return health_status
    
    async def generate_response(self, prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response from a prompt (compatibility method for existing code)
        
        Args:
            prompt: The input prompt
            model_id: Optional model ID to use
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, model_id=model_id, **kwargs)
        return response.content

    async def close(self):
        """关闭所有连接"""
        for provider in self.providers.values:
            if hasattr(provider, 'session') and provider.session:
                _ = await provider.session.close
        
        self.providers.clear

# 全局服务实例
_multi_llm_service: Optional[MultiLLMService] = None

def get_multi_llm_service -> MultiLLMService:
    """获取全局多模型 LLM 服务实例"""
    global _multi_llm_service
    if _multi_llm_service is None:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'configs', 'multi_llm_config.json'
        )
        _multi_llm_service = MultiLLMService(config_path)
    return _multi_llm_service

async def initialize_multi_llm_service(config_path: Optional[str] = None):
    """初始化多模型 LLM 服务"""
    global _multi_llm_service
    _multi_llm_service = MultiLLMService(config_path)
    return _multi_llm_service