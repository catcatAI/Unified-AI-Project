# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend abstract base class"""

import logging
from abc import ABC, abstractmethod

from core.interfaces.protocols import LLMResponse

logger = logging.getLogger(__name__)


class BaseLLMBackend(ABC):
    """LLM 後端抽象基類"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回應"""

    @abstractmethod
    async def check_health(self) -> bool:
        """檢查後端健康狀態"""
