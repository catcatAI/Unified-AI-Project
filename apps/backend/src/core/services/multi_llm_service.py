"""
Multi-Model LLM Service - Rewritten Version v2.0

Supports: OpenAI GPT, Anthropic Claude, Google Gemini, Ollama, llama.cpp
Features:
- Dual-track local models (Ollama + llama.cpp via config)
- Triple key management (ENV > .env file > config file)
- Integrated PolicyRouter for auto model selection
- Config-driven for Lite/Standard/Extended modes

Architecture based on LLM_ROUTING_AND_ADAPTATION_PLAN.md
"""

import os
import logging
import json
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path

import aiohttp
from aiolimiter import AsyncLimiter

# Optional imports - will be loaded dynamically
OptionalImports = {}

def _load_optional_imports():
    """Lazy load optional dependencies"""
    global OptionalImports
    try:
        from openai import AsyncOpenAI
        OptionalImports['openai'] = AsyncOpenAI
    except ImportError:
        pass
    
    try:
        from anthropic import AsyncAnthropic
        OptionalImports['anthropic'] = AsyncAnthropic
    except ImportError:
        pass
    
    try:
        import google.generativeai as genai
        OptionalImports['google'] = genai
    except ImportError:
        pass
    
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
        OptionalImports['azure'] = (ChatCompletionsClient, AzureKeyCredential)
    except ImportError:
        pass


logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Model provider enumeration"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"  # NEW: llama.cpp support
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


@dataclass
class ModelConfig:
    """Model configuration with secure key handling"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None  # Environment variable name for key
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
    capabilities: Dict[str, bool] = field(default_factory=dict)
    # For local models: backend_type ('ollama' or 'llamacpp')
    backend_type: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization: resolve API key from various sources"""
        if self.api_key is None and self.provider != ModelProvider.OLLAMA and self.provider != ModelProvider.LLAMACPP:
            self.api_key = self._resolve_api_key()
    
    def _resolve_api_key(self) -> Optional[str]:
        """
        Resolve API key from multiple sources (in priority order):
        1. Environment variable (api_key_env or default name)
        2. .env file
        3. Return None (will be loaded from secure storage later)
        """
        # Priority 1: Environment variable
        env_var = self.api_key_env or f"{self.provider.value.upper()}_API_KEY"
        key = os.getenv(env_var)
        if key:
            logger.debug(f"API key loaded from environment variable: {env_var}")
            return key
        
        # Priority 2: .env file
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)  # Don't override existing env vars
            key = os.getenv(env_var)
            if key:
                logger.debug(f"API key loaded from .env file: {env_var}")
                return key
        except ImportError:
            pass
        
        # Priority 3: Return None - key will be loaded from config file by MultiLLMService
        logger.warning(f"No API key found for {self.provider.value} in environment or .env")
        return None


@dataclass
class ChatMessage:
    """Chat message"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    provider: ModelProvider
    usage: Dict[str, int]
    cost: float
    latency: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Base LLM provider class"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = AsyncLimiter(max_rate=10, time_period=1)  # 10 requests per second
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """Chat completion"""
        pass
    
    @abstractmethod
    async def stream_completion(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion"""
        pass
    
    async def close(self):
        """Close provider resources"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage"""
        total_tokens = usage.get('total_tokens', 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        _load_optional_imports()
        self.client = None
        if 'openai' in OptionalImports:
            self.client = OptionalImports['openai'](api_key=config.api_key)
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        if not self.client:
            raise RuntimeError("OpenAI client not available. Install with: pip install openai")
        
        start_time = datetime.now()
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
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
            
            latency = (datetime.now() - start_time).total_seconds()
            
            usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.config.model_name,
                provider=ModelProvider.OPENAI,
                usage=usage,
                cost=self._calculate_cost(usage),
                latency=latency,
                timestamp=datetime.now(),
                metadata={'finish_reason': response.choices[0].finish_reason}
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        if not self.client:
            raise RuntimeError("OpenAI client not available")
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=openai_messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        _load_optional_imports()
        self.client = None
        if 'anthropic' in OptionalImports:
            self.client = OptionalImports['anthropic'](api_key=config.api_key)
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        if not self.client:
            raise RuntimeError("Anthropic client not available. Install with: pip install anthropic")
        
        start_time = datetime.now()
        
        # Convert messages to Anthropic format
        system_msg = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})
        
        try:
            params = {
                "model": self.config.model_name,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                "temperature": kwargs.get('temperature', self.config.temperature),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "timeout": self.config.timeout
            }
            if system_msg:
                params["system"] = system_msg
            
            response = await self.client.messages.create(**params)
            
            latency = (datetime.now() - start_time).total_seconds()
            
            usage = {
                'prompt_tokens': response.usage.input_tokens if response.usage else 0,
                'completion_tokens': response.usage.output_tokens if response.usage else 0,
                'total_tokens': (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
            }
            
            content = "".join([block.text for block in response.content if hasattr(block, 'text')])
            
            return LLMResponse(
                content=content,
                model=self.config.model_name,
                provider=ModelProvider.ANTHROPIC,
                usage=usage,
                cost=self._calculate_cost(usage),
                latency=latency,
                timestamp=datetime.now(),
                metadata={'stop_reason': response.stop_reason}
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        if not self.client:
            raise RuntimeError("Anthropic client not available")
        
        system_msg = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})
        
        params = {
            "model": self.config.model_name,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "stream": True
        }
        if system_msg:
            params["system"] = system_msg
        
        try:
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        _load_optional_imports()
        self.genai = OptionalImports.get('google')
        if self.genai:
            self.genai.configure(api_key=config.api_key)
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        if not self.genai:
            raise RuntimeError("Google Generative AI not available. Install with: pip install google-generativeai")
        
        start_time = datetime.now()
        
        # Convert messages
        gemini_messages = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                gemini_messages.append({"role": msg.role, "parts": [msg.content]})
        
        try:
            model = self.genai.GenerativeModel(
                model_name=self.config.model_name,
                system_instruction=system_instruction
            )
            
            generation_config = self.genai.GenerationConfig(
                max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p)
            )
            
            chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
            
            response = await chat.send_message_async(
                last_message,
                generation_config=generation_config
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            
            usage = {
                'prompt_tokens': 0,  # Gemini doesn't always provide token counts
                'completion_tokens': 0,
                'total_tokens': 0
            }
            
            return LLMResponse(
                content=response.text,
                model=self.config.model_name,
                provider=ModelProvider.GOOGLE,
                usage=usage,
                cost=self._calculate_cost(usage),
                latency=latency,
                timestamp=datetime.now(),
                metadata={'candidates': len(response.candidates) if hasattr(response, 'candidates') else 1}
            )
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        if not self.genai:
            raise RuntimeError("Google Generative AI not available")
        
        gemini_messages = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                gemini_messages.append({"role": msg.role, "parts": [msg.content]})
        
        try:
            model = self.genai.GenerativeModel(
                model_name=self.config.model_name,
                system_instruction=system_instruction
            )
            
            chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
            
            response = await chat.send_message_async(
                last_message,
                stream=True,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens)
                )
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Google Gemini streaming error: {e}")
            raise


class UnifiedLocalProvider(BaseLLMProvider):
    """
    Unified Local Model Provider - Dual-track support for Ollama and llama.cpp
    
    Uses configuration to switch between:
    - Ollama: /api/chat endpoint
    - llama.cpp: /v1/chat/completions (OpenAI compatible)
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # Determine backend type from config or auto-detect from base_url
        self.backend_type = config.backend_type or self._detect_backend_type(config.base_url)
        self.base_url = config.base_url or self._default_base_url()
        
        logger.info(f"UnifiedLocalProvider initialized with backend: {self.backend_type}")
    
    def _detect_backend_type(self, base_url: Optional[str]) -> str:
        """Auto-detect backend type from URL patterns"""
        if not base_url:
            return 'ollama'  # Default to Ollama
        
        # llama.cpp typically uses port 8080 and OpenAI-compatible endpoints
        if ':8080' in base_url or 'llama' in base_url.lower():
            return 'llamacpp'
        
        return 'ollama'
    
    def _default_base_url(self) -> str:
        """Return default base URL based on backend type"""
        if self.backend_type == 'llamacpp':
            return "http://localhost:8080"
        return "http://localhost:11434"  # Ollama default
    
    async def chat_completion(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        await self._ensure_session()
        
        start_time = datetime.now()
        
        try:
            if self.backend_type == 'llamacpp':
                return await self._llamacpp_chat(messages, **kwargs)
            else:
                return await self._ollama_chat(messages, **kwargs)
        except Exception as e:
            logger.error(f"Local provider ({self.backend_type}) error: {e}")
            raise
    
    async def _ollama_chat(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """Chat using Ollama API"""
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
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            if response.status != 200:
                raise Exception(f"Ollama API error: {response.status}")
            
            result = await response.json()
            latency = (datetime.now() - start_time).total_seconds()
            
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
                cost=0.0,  # Local model - no cost
                latency=latency,
                timestamp=datetime.now(),
                metadata={
                    "done": result.get("done", True),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "eval_duration": result.get("eval_duration", 0),
                    "backend": "ollama"
                }
            )
    
    async def _llamacpp_chat(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """Chat using llama.cpp OpenAI-compatible API"""
        # llama.cpp uses OpenAI-compatible format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.config.model_name,
            "messages": openai_messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "stream": False
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",  # OpenAI compatible endpoint
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"llama.cpp API error: {response.status} - {text}")
            
            result = await response.json()
            latency = (datetime.now() - start_time).total_seconds()
            
            usage = result.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=self.config.model_name,
                provider=ModelProvider.LLAMACPP,
                usage=usage,
                cost=0.0,  # Local model - no cost
                latency=latency,
                timestamp=datetime.now(),
                metadata={
                    "finish_reason": result["choices"][0].get("finish_reason"),
                    "backend": "llamacpp"
                }
            )
    
    async def stream_completion(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        await self._ensure_session()
        
        try:
            if self.backend_type == 'llamacpp':
                async for chunk in self._llamacpp_stream(messages, **kwargs):
                    yield chunk
            else:
                async for chunk in self._ollama_stream(messages, **kwargs):
                    yield chunk
        except Exception as e:
            logger.error(f"Local provider streaming error: {e}")
            raise
    
    async def _ollama_stream(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        """Stream using Ollama API"""
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
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            async for line in response.content:
                if line:
                    try:
                        chunk = json.loads(line)
                        if chunk.get("message", {}).get("content"):
                            yield chunk["message"]["content"]
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def _llamacpp_stream(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        """Stream using llama.cpp OpenAI-compatible API"""
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.config.model_name,
            "messages": openai_messages,
            "temperature": kwargs.get('temperature', self.config.temperature),
            "stream": True
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            async for line in response.content:
                if line:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith("data: "):
                        try:
                            chunk = json.loads(line_text[6:])
                            if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                            if chunk.get("choices") and chunk["choices"][0].get("finish_reason"):
                                break
                        except json.JSONDecodeError:
                            continue


class SecureKeyManager:
    """
    Secure Key Manager - Triple source support
    
    Supports:
    1. Environment variables (highest priority)
    2. .env file
    3. Config file (lowest priority, with security warning)
    
    Privacy: Only tracks "if configured" and "source", never stores/returns key values
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "apps/backend/configs/api_keys.yaml"
        self._key_sources: Dict[str, Dict[str, Any]] = {}
        self._load_dotenv()
        self._scan_sources()
    
    def _load_dotenv(self):
        """Load .env file if available"""
        try:
            from dotenv import load_dotenv
            env_path = Path('.env')
            if env_path.exists():
                load_dotenv(override=False)
                logger.info("Loaded .env file")
        except ImportError:
            logger.debug("python-dotenv not installed, skipping .env loading")
        except Exception as e:
            logger.warning(f"Error loading .env: {e}")
    
    def _scan_sources(self):
        """Scan all providers for key sources (without loading keys into memory)"""
        providers = ['openai', 'anthropic', 'google', 'azure_openai', 'cohere', 'huggingface']
        
        for provider in providers:
            source_info = self._detect_key_source(provider)
            if source_info:
                self._key_sources[provider] = source_info
    
    def _detect_key_source(self, provider: str) -> Optional[Dict[str, Any]]:
        """Detect where a key is configured without loading the key itself"""
        env_var = f"{provider.upper()}_API_KEY"
        
        # Check 1: Environment variable
        if os.getenv(env_var):
            return {
                'configured': True,
                'source': f'Environment variable ({env_var})',
                'secure': True,
                'warning': None
            }
        
        # Check 2: Config file (only check existence, don't read)
        try:
            if Path(self.config_path).exists():
                # Only check if file contains the provider, don't parse the key
                with open(self.config_path, 'r') as f:
                    content = f.read()
                    if provider in content.lower():
                        return {
                            'configured': True,
                            'source': f'Config file ({self.config_path})',
                            'secure': False,
                            'warning': f'API key for {provider} found in config file. For better security, move it to environment variable {env_var}'
                        }
        except Exception:
            pass
        
        return None
    
    def get_key(self, provider: str) -> Optional[str]:
        """
        Get API key from sources (only when actually needed)
        Priority: ENV > .env > config file
        """
        env_var = f"{provider.upper()}_API_KEY"
        
        # Priority 1: Environment variable
        key = os.getenv(env_var)
        if key:
            return key
        
        # Priority 2: Config file (fallback)
        try:
            if Path(self.config_path).exists():
                import yaml
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and provider in config:
                        provider_config = config[provider]
                        if isinstance(provider_config, dict) and 'api_key' in provider_config:
                            logger.warning(f"Using API key from config file for {provider}. Consider using environment variable.")
                            return provider_config['api_key']
                        elif isinstance(provider_config, str):
                            logger.warning(f"Using API key from config file for {provider}. Consider using environment variable.")
                            return provider_config
        except Exception as e:
            logger.debug(f"Could not load key from config file: {e}")
        
        return None
    
    def get_key_info(self, provider: str) -> Dict[str, Any]:
        """
        Get key configuration info (without exposing the key)
        This is what Angela shows to users
        """
        return self._key_sources.get(provider, {
            'configured': False,
            'source': None,
            'secure': False,
            'warning': f'No API key configured for {provider}. Set environment variable {provider.upper()}_API_KEY or add to config file.'
        })
    
    def list_configured_providers(self) -> List[str]:
        """List all providers with configured keys"""
        return [p for p, info in self._key_sources.items() if info.get('configured', False)]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security report for all providers"""
        report = {
            'total_providers': len(self._key_sources),
            'secure_sources': 0,
            'insecure_sources': 0,
            'providers': {}
        }
        
        for provider, info in self._key_sources.items():
            report['providers'][provider] = {
                'configured': info['configured'],
                'source': info['source'],
                'secure': info['secure'],
                'warning': info.get('warning')
            }
            
            if info['configured']:
                if info['secure']:
                    report['secure_sources'] += 1
                else:
                    report['insecure_sources'] += 1
        
        return report


# Import router and registry (already fixed in Phase 1)
try:
    from apps.backend.src.ai.language_models.router import PolicyRouter, RoutingPolicy
    from apps.backend.src.ai.language_models.registry import ModelRegistry, ModelProfile
    ROUTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Router/Registry not available: {e}")
    ROUTER_AVAILABLE = False
    PolicyRouter = None
    RoutingPolicy = None
    ModelRegistry = None
    ModelProfile = None


class MultiLLMService:
    """
    Multi-Model LLM Service - Main Interface
    
    Features:
    - Unified interface for multiple LLM providers
    - Auto-routing via PolicyRouter when model_id not specified
    - Usage tracking and statistics
    - Health checking
    - Secure key management
    """
    
    def __init__(self, config_path: Optional[str] = None, mode: str = 'standard'):
        """
        Initialize MultiLLMService
        
        Args:
            config_path: Path to model configuration JSON/YAML
            mode: Operating mode ('lite', 'standard', 'extended')
        """
        self.config_path = config_path
        self.mode = mode
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self.default_model: Optional[str] = None
        
        # Initialize secure key manager
        self.key_manager = SecureKeyManager()
        
        # Initialize router and registry if available
        self.router: Optional[PolicyRouter] = None
        self.registry: Optional[ModelRegistry] = None
        
        # Rate limiting
        self.rate_limiters: Dict[str, AsyncLimiter] = {}
        
        # LLM_ROUTER_ENABLED flag
        self.router_enabled = os.getenv('LLM_ROUTER_ENABLED', 'true').lower() == 'true'
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load configuration from JSON or YAML file"""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"Config file not found: {config_path}")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            self.default_model = config.get('default_model')
            
            # Load model configurations
            for model_id, model_config in config.get('models', {}).items():
                provider_str = model_config.get('provider', 'openai')
                
                # Convert string to enum
                try:
                    provider = ModelProvider(provider_str)
                except ValueError:
                    logger.warning(f"Unknown provider: {provider_str}")
                    continue
                
                # For local providers (ollama/llamacpp), handle backend_type
                backend_type = None
                if provider in (ModelProvider.OLLAMA, ModelProvider.LLAMACPP):
                    backend_type = model_config.get('backend_type', 'ollama')
                
                # Resolve API key
                api_key = model_config.get('api_key')
                if not api_key or api_key == 'test-key':
                    # Try to get from key manager
                    api_key = self.key_manager.get_key(provider_str)
                
                self.model_configs[model_id] = ModelConfig(
                    provider=provider,
                    model_name=model_config.get('model_name', model_id),
                    api_key=api_key,
                    api_key_env=model_config.get('api_key_env'),
                    base_url=model_config.get('base_url'),
                    max_tokens=model_config.get('max_tokens', 4096),
                    temperature=model_config.get('temperature', 0.7),
                    top_p=model_config.get('top_p', 1.0),
                    frequency_penalty=model_config.get('frequency_penalty', 0.0),
                    presence_penalty=model_config.get('presence_penalty', 0.0),
                    timeout=model_config.get('timeout', 60),
                    enabled=model_config.get('enabled', True),
                    cost_per_1k_tokens=model_config.get('cost_per_1k_tokens', 0.0),
                    context_window=model_config.get('context_window', 4096),
                    capabilities=model_config.get('capabilities', {}),
                    backend_type=backend_type
                )
                
                # Initialize usage stats
                self.usage_stats[model_id] = {
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'error_count': 0,
                    'average_latency': 0.0
                }
            
            # Initialize router and registry
            self._init_router()
            
            logger.info(f"Loaded {len(self.model_configs)} models from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _init_router(self):
        """Initialize PolicyRouter and ModelRegistry"""
        if not ROUTER_AVAILABLE:
            logger.warning("Router/Registry not available, auto-routing disabled")
            return
        
        try:
            self.registry = ModelRegistry(self.model_configs)
            self.router = PolicyRouter(self.registry)
            logger.info("Router and Registry initialized")
        except Exception as e:
            logger.error(f"Error initializing router: {e}")
            self.router = None
            self.registry = None
    
    def _create_provider(self, config: ModelConfig) -> BaseLLMProvider:
        """Create provider instance based on config"""
        if config.provider == ModelProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == ModelProvider.ANTHROPIC:
            return AnthropicProvider(config)
        elif config.provider == ModelProvider.GOOGLE:
            return GoogleProvider(config)
        elif config.provider in (ModelProvider.OLLAMA, ModelProvider.LLAMACPP):
            return UnifiedLocalProvider(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        policy: Optional[Any] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat completion - with auto-routing support
        
        Args:
            messages: List of chat messages
            model_id: Specific model ID (optional, triggers auto-routing if None)
            policy: Routing policy for auto-selection (optional)
            **kwargs: Additional parameters
        """
        # Auto-routing if model_id not provided and router enabled
        if model_id is None and self.router_enabled and self.router and policy:
            model_id = await self._route_with_policy(policy, messages)
        
        # Use default if still no model_id
        if model_id is None:
            model_id = self.default_model
        
        if not model_id:
            raise ValueError("No model specified and no default model configured")
        
        if model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found")
        
        config = self.model_configs[model_id]
        
        if not config.enabled:
            raise ValueError(f"Model {model_id} is disabled")
        
        # Create provider if not exists
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(config)
        
        provider = self.providers[model_id]
        
        try:
            response = await provider.chat_completion(messages, **kwargs)
            self._update_usage_stats(model_id, response)
            return response
        except Exception as e:
            self.usage_stats[model_id]['error_count'] += 1
            logger.error(f"Model {model_id} request failed: {e}")
            raise
    
    async def _route_with_policy(self, policy: Any, messages: List[ChatMessage]) -> Optional[str]:
        """Use PolicyRouter to select best model"""
        try:
            # Calculate input size
            input_chars = sum(len(msg.content) for msg in messages)
            policy.input_chars = input_chars
            
            # Get routing decision
            route_result = self.router.route(policy)
            
            if 'best' in route_result and route_result['best']:
                selected_model = route_result['best']['model_id']
                logger.info(f"Auto-routed to model: {selected_model} (score: {route_result['best'].get('score', 'N/A')})")
                return selected_model
            
            logger.warning("Router could not determine best model, using default")
            return None
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return None
    
    async def stream_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion"""
        if model_id is None:
            model_id = self.default_model
        
        if not model_id or model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found")
        
        config = self.model_configs[model_id]
        
        if model_id not in self.providers:
            self.providers[model_id] = self._create_provider(config)
        
        provider = self.providers[model_id]
        
        try:
            async for chunk in provider.stream_completion(messages, **kwargs):
                yield chunk
        except Exception as e:
            self.usage_stats[model_id]['error_count'] += 1
            logger.error(f"Model {model_id} streaming failed: {e}")
            raise
    
    def _update_usage_stats(self, model_id: str, response: LLMResponse):
        """Update usage statistics"""
        stats = self.usage_stats[model_id]
        stats['total_requests'] += 1
        stats['total_tokens'] += response.usage.get('total_tokens', 0)
        stats['total_cost'] += response.cost
        
        # Update average latency
        current_avg = stats['average_latency']
        total_requests = stats['total_requests']
        stats['average_latency'] = (current_avg * (total_requests - 1) + response.latency) / total_requests
    
    def get_available_models(self) -> List[str]:
        """Get list of available (enabled) models"""
        return [
            model_id for model_id, config in self.model_configs.items()
            if config.enabled
        ]
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information"""
        if model_id not in self.model_configs:
            raise ValueError(f"Model {model_id} not found")
        
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
            'usage_stats': stats,
            'api_key_source': self.key_manager.get_key_info(config.provider.value)['source']
        }
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary across all models"""
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
        """Health check all models"""
        health_status = {}
        
        for model_id, config in self.model_configs.items():
            if not config.enabled:
                health_status[model_id] = {'status': 'disabled'}
                continue
            
            try:
                # Simple test
                test_messages = [ChatMessage(role="user", content="Hi")]
                
                if model_id not in self.providers:
                    self.providers[model_id] = self._create_provider(config)
                
                provider = self.providers[model_id]
                await provider.chat_completion(test_messages, max_tokens=10)
                
                health_status[model_id] = {'status': 'healthy'}
            except Exception as e:
                health_status[model_id] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return health_status
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security report for all providers"""
        return self.key_manager.get_security_report()
    
    async def close(self):
        """Close all providers"""
        for provider in self.providers.values():
            await provider.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())
        except Exception as e:
            logger.error(f"Error closing service: {e}")
