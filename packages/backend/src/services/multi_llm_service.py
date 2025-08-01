"""
多模型 LLM 服务
支持 OpenAI GPT、Google Gemini、Anthropic Claude、Ollama 等主流 AI 模型
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import aiohttp
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai
import cohere
from azure.identity import DefaultAzureCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage

logger = logging.getLogger(__name__)

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
    
    def __init__(self, config: ModelConfig):
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
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT 提供商"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        openai.api_key = config.api_key
        if config.base_url:
            openai.api_base = config.base_url
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=self.config.model_name,
                messages=openai_messages,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
                frequency_penalty=kwargs.get('frequency_penalty', self.config.frequency_penalty),
                presence_penalty=kwargs.get('presence_penalty', self.config.presence_penalty),
                timeout=self.config.timeout
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            usage = response.usage.to_dict()
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.config.model_name,
                provider=ModelProvider.OPENAI,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(),
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
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            stream = await openai.ChatCompletion.acreate(
                model=self.config.model_name,
                messages=openai_messages,
                stream=True,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                timeout=self.config.timeout
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.get("content"):
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = AsyncAnthropic(api_key=config.api_key)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
        try:
            # 转换消息格式
            claude_messages = []
            system_message = None
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    claude_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            response = await self.client.messages.create(
                model=self.config.model_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                system=system_message,
                messages=claude_messages
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.config.model_name,
                provider=ModelProvider.ANTHROPIC,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(),
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
        # 转换消息格式
        claude_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            async with self.client.messages.stream(
                model=self.config.model_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                system=system_message,
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model_name)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
        try:
            # 转换消息格式
            chat_history = []
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
            chat = self.model.start_chat(history=chat_history[:-1] if chat_history else [])
            
            # 发送最后一条消息
            last_message = chat_history[-1]["parts"][0] if chat_history else "Hello"
            response = await chat.send_message_async(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                    temperature=kwargs.get('temperature', self.config.temperature),
                    top_p=kwargs.get('top_p', self.config.top_p),
                )
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            
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
                timestamp=datetime.now(),
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
        # 类似的消息转换逻辑
        chat_history = []
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
            chat = self.model.start_chat(history=chat_history[:-1] if chat_history else [])
            last_message = chat_history[-1]["parts"][0] if chat_history else "Hello"
            
            response = await chat.send_message_async(
                last_message,
                stream=True,
                generation_config=genai.types.GenerationConfig(
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
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
                
                result = await response.json()
                
                latency = (datetime.now() - start_time).total_seconds()
                
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
                    timestamp=datetime.now(),
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
                            if chunk.get("message", {}).get("content"):
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = ChatCompletionsClient(
            endpoint=config.base_url,
            credential=DefaultAzureCredential() if not config.api_key else config.api_key
        )
        self.deployment_name = getattr(config, 'deployment_name', config.model_name)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
        try:
            azure_messages = []
            for msg in messages:
                if msg.role == "system":
                    azure_messages.append(SystemMessage(content=msg.content))
                elif msg.role == "user":
                    azure_messages.append(UserMessage(content=msg.content))
                # Azure 会自动处理 assistant 消息
            
            response = await self.client.complete(
                messages=azure_messages,
                model=self.deployment_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            cost = self._calculate_cost(usage)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.config.model_name,
                provider=ModelProvider.AZURE_OPENAI,
                usage=usage,
                cost=cost,
                latency=latency,
                timestamp=datetime.now(),
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
        # Azure OpenAI 流式实现
        azure_messages = []
        for msg in messages:
            if msg.role == "system":
                azure_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                azure_messages.append(UserMessage(content=msg.content))
        
        try:
            response = await self.client.complete(
                messages=azure_messages,
                model=self.deployment_name,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                stream=True
            )
            
            async for chunk in response:
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = cohere.AsyncClient(api_key=config.api_key)
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        **kwargs
    ) -> LLMResponse:
        start_time = datetime.now()
        
        try:
            # 转换消息格式
            chat_history = []
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
            
            response = await self.client.chat(
                model=self.config.model_name,
                message=user_message or "Hello",
                chat_history=chat_history,
                preamble=locals().get('preamble', ''),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            
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
                timestamp=datetime.now(),
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
        # Cohere 流式实现
        chat_history = []
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
            response = await self.client.chat_stream(
                model=self.config.model_name,
                message=user_message or "Hello",
                chat_history=chat_history,
                preamble=locals().get('preamble', ''),
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
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
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
        start_time = datetime.now()
        
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
                
                result = await response.json()
                
                latency = (datetime.now() - start_time).total_seconds()
                
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
                    timestamp=datetime.now(),
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
        # Hugging Face Inference API 不直接支持流式，这里模拟实现
        response = await self.chat_completion(messages, **kwargs)
        
        # 将完整响应分块返回
        words = response.content.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.05)  # 模拟流式延迟
    
    def _build_prompt(self, messages: List[ChatMessage]) -> str:
        """构建提示文本"""
        prompt_parts = []
        
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

class MultiLLMService:
    """多模型 LLM 服务"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.default_model: Optional[str] = None
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.default_model = config.get('default_model')
            
            for model_id, model_config in config.get('models', {}).items():
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
        
        # 获取或创建提供商
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(config)
        
        provider = self.providers[model_id]
        
        try:
            async with provider:
                response = await provider.chat_completion(messages, **kwargs)
                
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
        
        # 获取或创建提供商
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(config)
        
        provider = self.providers[model_id]
        
        try:
            async with provider:
                async for chunk in provider.stream_completion(messages, **kwargs):
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
            model_id for model_id, config in self.model_configs.items()
            if config.enabled
        ]
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_id not in self.model_configs:
            raise ValueError(f"模型 {model_id} 不存在")
        
        config = self.model_configs[model_id]
        stats = self.usage_stats.get(model_id, {})
        
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
        total_requests = sum(stats['total_requests'] for stats in self.usage_stats.values())
        total_tokens = sum(stats['total_tokens'] for stats in self.usage_stats.values())
        total_cost = sum(stats['total_cost'] for stats in self.usage_stats.values())
        total_errors = sum(stats['error_count'] for stats in self.usage_stats.values())
        
        return {
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'total_errors': total_errors,
            'models': {
                model_id: self.get_model_info(model_id)
                for model_id in self.model_configs.keys()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {}
        
        for model_id, config in self.model_configs.items():
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
    
    async def close(self):
        """关闭所有连接"""
        for provider in self.providers.values():
            if hasattr(provider, 'session') and provider.session:
                await provider.session.close()
        
        self.providers.clear()

# 全局服务实例
_multi_llm_service: Optional[MultiLLMService] = None

def get_multi_llm_service() -> MultiLLMService:
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