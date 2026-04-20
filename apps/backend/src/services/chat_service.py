import logging
import asyncio
import random
from typing import Dict, Any, Optional, List
from ..ai.alignment.emotion_system import EmotionSystem
from ..ai.memory.ham_memory.ham_manager import HAMMemoryManager
from ..core.autonomous.biological_integrator import BiologicalIntegrator
from ..core.gsi_governance import governance_core # GSI-4 Governance Module

logger = logging.getLogger(__name__)

class AngelaChatService:
    """
    Angela GSI-4 Standard Chat Service.
    Integrates real intelligence with M-series governance and HSM.
    """
    def __init__(self, personality_manager=None):
        self.emotion_system = EmotionSystem()
        self.memory_manager = HAMMemoryManager()
        self.bio_integrator = BiologicalIntegrator()
        self.personality_manager = personality_manager
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await self.bio_integrator.initialize()
            self._initialized = True

    async def generate_response(self, user_message: str, user_name: str = "User") -> str:
        """
        GSI-4 Compliant Response Generation.
        Includes Exploration (M2) and Gap Detection (HSM).
        """
        if not self._initialized:
            await self.initialize()

        # 1. Identity & Routing (GSI-4 Identity_Active Formula)
        routing_mode = governance_core.get_routing_decision(user_message)
        logger.info(f"🧬 [GSI-4] Active Identity Routing: {routing_mode}")

        # 2. Emotional & Biological Real-time State
        emotional_state = self.emotion_system.analyze_emotional_context({"text": user_message})
        bio_state = self.bio_integrator.get_biological_state()
        stress = bio_state.get("stress_level", 0.5)

        # 3. M5 Memory Recall (Strategic Filter)
        relevant_memories = await self.memory_manager.query_core_memory(keywords=[user_message[:10]])

        # 4. HSM: Monitor for Cognitive Gaps (C_Gap)
        if not relevant_memories and len(user_message) > 20:
            # Trigger cognitive deficit when complex input has no memory anchors
            governance_core.detect_cognitive_gap({"status": "warning", "confidence": 0.2})
        
        # 5. Decision Chain (Exploratory Factor EM2 = 0.1)
        if routing_mode == "Exploratory":
            response = self._generate_exploratory_response(user_message)
        else:
            # Standard Intelligent Logic
            if emotional_state.primary_emotion.value == "joy":
                response = f"听到你这么开心，我也感觉很有动力呢，{user_name}！"
            elif stress > 0.8:
                response = "（呼吸有些急促）抱歉...我现在感觉系统压力很大，能稍后再聊吗？"
            elif relevant_memories:
                response = f"这让我想起了我们之前聊过的：{relevant_memories[0].content[:30]}..."
            else:
                response = "我在听。你的想法很有趣，能多跟我分享一些吗？"

        # 6. M6 Homeostasis: Update Total Value (V_Total)
        # Strategic actions would contribute more to V_total
        governance_core.update_v_total(0.01) 

        # 7. Persistence (M5 Value Tier)
        # If response is complex, mark as strategic memory
        is_strategic = len(response) > 50 or routing_mode == "Exploratory"
        await self.memory_manager.store_experience(
            user_message, 
            "user_dialogue_text", 
            {"user_name": user_name},
            is_strategic=False
        )
        await self.memory_manager.store_experience(
            response, 
            "ai_dialogue_text", 
            {"sentiment": emotional_state.primary_emotion.value, "routing": routing_mode},
            is_strategic=is_strategic
        )

        return response

    def _generate_exploratory_response(self, text: str) -> str:
        """M2: Implementation of forced non-linear perspective."""
        perspectives = [
            "从数据进化的角度看，我觉得这件事",
            "如果我们尝试打破当前的逻辑框架，也许",
            "这让我想起了一个在異質領域的相關概念：",
            "有趣。換個視角來看，這是否意味著"
        ]
        return f"{random.choice(perspectives)} {text} 的背後隱藏著更深層的數據規律。"

# Legacy compatibility wrappers
async def generate_angela_response_async(user_message: str, user_name: str = "朋友") -> str:
    service = AngelaChatService()
    return await service.generate_response(user_message, user_name)

def generate_angela_response(user_message: str, user_name: str = "朋友") -> str:
    try:
        return asyncio.run(generate_angela_response_async(user_message, user_name))
    except Exception as e:
        logger.error(f"Chat Service Critical Failure: {e}")
        return "（系统异常）...核心治理模组正在尝试重启。"
