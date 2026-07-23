"""
Stream Producers

Multi-source token producers for predictive, retrieval, and generative streams.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

from .token_stream import TokenStream, StreamToken, TokenType

if TYPE_CHECKING:
    from ai.garden.garden_engine import GARDENEngine
    from ai.ed3n.ed3n_engine import ED3NEngine
    from services.multimodal_service import MultimodalService
    from services.llm.router import LLMRouter


@dataclass
class ProducerConfig:
    """Base producer configuration."""
    enabled: bool = True
    max_tokens: int = 512
    chunk_size: int = 32
    min_chunk_size: int = 8
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProducer:
    """Abstract base producer."""
    
    def __init__(self, stream: "TokenStream", config: Optional["ProducerConfig"] = None):
        from .token_stream import TokenStream
        self.stream = stream
        self.config = config or ProducerConfig()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    @property
    def running(self) -> bool:
        return self._running
    
    @abstractmethod
    async def produce(self, input_text: str, context: Dict[str, Any]) -> None:
        """Produce tokens into the stream."""
        pass
    
    async def start(self, input_text: str, context: Dict[str, Any]) -> None:
        """Start producer."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self.produce(input_text, context))
    
    async def stop(self) -> None:
        """Stop producer."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def _chunk_text(self, text: str, chunk_size: int, min_chunk: int) -> List[str]:
        """Split text into chunks."""
        if len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        sentences = re.split(r'(?<=[.!?。！？])\s*', text)
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.config.chunk_size:
                current += sent + " "
            else:
                if current:
                    chunks.append(current.strip())
                current = sent + " "
        if current:
            chunks.append(current.strip())
        
        # Ensure minimum chunk size
        final = []
        for chunk in chunks:
            if len(chunk) >= self.config.min_chunk_size or not final:
                final.append(chunk)
            else:
                final[-1] += " " + chunk
        return final


class PredictiveProducer:
    """Predictive producer using lightweight models/heuristics."""
    
    def __init__(self, stream: "TokenStream", 
                 garden_engine: Optional[Any] = None,
                 config: Optional["ProducerConfig"] = None):
        from .token_stream import TokenStream
        self.stream = stream
        self.config = config or ProducerConfig()
        self.garden_engine = None
        self._quick_patterns = self._load_quick_patterns()
    
    async def produce(self, input_text: str, context: Dict[str, Any]) -> None:
        """Produce predictive tokens."""
        from .token_stream import StreamToken, TokenType
        
        start = time.time()
        
        # 1. Quick heuristic patterns (immediate)
        quick_pred = self._quick_predict(input_text)
        if quick_pred:
            for chunk in self._chunk(quick_pred, self.config.chunk_size):
                token = StreamToken.create_predicted(
                    content=chunk,
                    source="predictor_quick",
                    confidence=0.5,
                    metadata={"stage": "quick", "latency_ms": (time.time() - start) * 1000}
                )
                await self.stream.put(token)
        
        # 2. Heuristic domain prediction
        domain_pred = self._domain_predict(input_text)
        if domain_pred:
            for chunk in self._chunk(domain_pred, self.config.chunk_size):
                token = StreamToken.create_predicted(
                    content=chunk,
                    source="predictor_domain",
                    confidence=0.65,
                    metadata={"stage": "domain", "latency_ms": (time.time() - start) * 1000}
                )
                await self.stream.put(token)
    
    def _load_quick_patterns(self) -> Dict[str, str]:
        """Load quick response patterns."""
        return {
            "你好": "你好！很高兴见到你！",
            "你好啊": "你好！有什么我可以帮你的吗？",
            "谢谢": "不客气！很高兴能帮到你！",
            "再见": "再见！期待下次再见！",
            "你是谁": "我是Angela AI，很高兴认识你！",
            "你叫什么": "我是Angela，你的AI助手。",
            "干嘛": "我在思考如何更好地帮助你呢！",
            "在吗": "在的，随时为你服务！",
        }
    
    def _quick_predict(self, text: str) -> Optional[str]:
        """Fast pattern matching for common inputs."""
        lower = text.lower().strip()
        for pattern, response in self._quick_patterns.items():
            if pattern in lower:
                return response
        return None
    
    def _domain_predict(self, text: str) -> Optional[str]:
        """Domain-based prediction."""
        lower = text.lower()
        # Math
        if any(op in lower for op in ['+', '-', '*', '/', '加', '减', '乘', '除', '等于', '多少']):
            return "这是一个数学问题，让我计算一下..."
        # Code
        if any(kw in lower for kw in ['代码', '编程', 'python', 'java', '函数', '变量']):
            return "这涉及编程，我可以帮你分析代码或提供建议..."
        # Search
        if any(kw in lower for kw in ['搜索', '查找', '是什么', '怎么', '为什么', '怎么做']):
            return "这需要搜索信息，让我帮你查找..."
        return None
    
    def _chunk(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks."""
        if len(text) <= self.config.chunk_size:
            return [text] if text else []
        chunks = []
        for i in range(0, len(text), self.config.chunk_size):
            chunk = text[i:i + self.config.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks


class RetrievalProducer:
    """Retrieval producer using existing MultimodalService."""
    
    def __init__(self, stream: "TokenStream", 
                 multimodal_service: Optional[Any] = None,
                 config: Optional["ProducerConfig"] = None):
        from .token_stream import TokenStream
        self.stream = stream
        self.config = config or ProducerConfig()
        self.multimodal = multimodal_service
    
    async def produce(self, input_text: str, context: Dict[str, Any]) -> None:
        """Produce retrieved tokens."""
        from .token_stream import StreamToken
        
        start = time.time()
        
        # Attempt retrieval from MultimodalService if available
        retrieved_chunks = []
        if self.multimodal and hasattr(self.multimodal, "retrieve"):
            try:
                results = await self.multimodal.retrieve(input_text, top_k=3)
                if results:
                    retrieved_chunks = [str(r)[:200] for r in results if r]
            except Exception as e:
                logger.warning("Multimodal retrieval failed: %s", e, exc_info=True)
        
        # Fallback: use context memory if available
        if not retrieved_chunks:
            memories = context.get("memories", []) or context.get("conversation_memory", [])
            if memories:
                retrieved_chunks = [str(m)[:200] for m in memories[:3]]
        
        # Emit tokens for each retrieved chunk
        for chunk in retrieved_chunks:
            token = StreamToken.create_retrieved(
                content=chunk,
                source="retrieval_multi",
                confidence=0.8,
                metadata={"stage": "retrieval", "latency_ms": (time.time() - start) * 1000}
            )
            await self.stream.put(token)


class GenerativeProducer:
    """Generative producer wrapping LLM router."""
    
    def __init__(self, stream: "TokenStream", 
                 llm_router: Optional[Any] = None,
                 config: Optional["ProducerConfig"] = None):
        self.stream = stream
        self.config = config or ProducerConfig()
        self.router = llm_router
    
    async def produce(self, input_text: str, context: Dict[str, Any]) -> None:
        """Produce generated tokens."""
        from .token_stream import StreamToken
        
        start = time.time()
        response_text = None
        
        # Attempt generation via LLM router if available
        if self.router and hasattr(self.router, "generate"):
            try:
                response_text = await self.router.generate(input_text, context)
            except Exception as e:
                logger.warning("LLM router generation failed: %s", e, exc_info=True)
        
        # Fallback: use response from context if pre-generated
        if not response_text:
            response_text = context.get("generated_text") or context.get("response")
        
        if not response_text:
            logger.debug("GenerativeProducer: no text available to emit")
            return
        
        # Chunk and emit tokens
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', str(response_text))
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.config.chunk_size:
                current += sent + " "
            else:
                if current:
                    chunks.append(current.strip())
                current = sent + " "
        if current:
            chunks.append(current.strip())
        
        for chunk in chunks:
            token = StreamToken.create_generated(
                content=chunk,
                source="generator_llm",
                confidence=0.9,
                metadata={"stage": "generation", "latency_ms": (time.time() - start) * 1000}
            )
            await self.stream.put(token)


def create_producers(
    stream: "TokenStream",
    garden_engine: Optional[Any] = None,
    multimodal_service: Optional[Any] = None,
    llm_router: Optional[Any] = None,
    config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Create all producers."""
    producers = {}
    
    predictive = PredictiveProducer(stream, garden_engine)
    producers["predictive"] = predictive
    
    retrieval = RetrievalProducer(stream, multimodal_service)
    producers["retrieval"] = retrieval
    
    generative = GenerativeProducer(stream, llm_router)
    producers["generative"] = generative
    
    return producers