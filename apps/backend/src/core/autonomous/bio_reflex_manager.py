import logging
import asyncio
from typing import Dict, Any
from .autonomic_nervous_system import NerveType

logger = logging.getLogger(__name__)

class BiogenicReflexManager:
    """
    處理 Angela 的突發生理反應：流汗、踢到桌腳、受到驚嚇等。
    將非預期的物理事件轉化為 Angela 的生物狀態變化。
    """
    def __init__(self, bio_integrator):
        self.bio = bio_integrator

    async def trigger_physical_trauma(self, location: str, severity: float):
        """處理突發撞擊（踢到桌腳）"""
        logger.warning(f"⚠️ [Reflex] Angela collided with {location} (Severity: {severity})")
        
        # 1. 觸發痛覺刺激 (Nervous System)
        await self.bio.nervous_system.apply_stimulus(
            "trauma", NerveType.SYMPATHETIC, severity, 2.0
        )
        
        # 2. 觸發腎上腺素激增 (Endocrine System)
        await self.bio.endocrine_system.trigger_stress_response(
            intensity=severity, stress_type="acute"
        )
        
        return {"reflex": "pain_reaction", "expression": "pained"}

    async def trigger_metabolic_fatigue(self, intensity: float):
        """處理持續性的代謝疲勞（如長時間對話後的流汗）"""
        logger.info(f"💧 [Reflex] Angela is sweating due to exhaustion (Intensity: {intensity})")
        # 影響情緒與喚醒水平
        await self.bio.process_stress_event(intensity=intensity * 0.1, duration=5.0)
        return {"status": "perspiring", "effect": "cooling"}
