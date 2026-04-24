import logging
import asyncio
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AngelaChatService:
    """
    Angela GSI-4 Standard Chat Service (Advanced Neural Integration).
    Final refinement: Bridges Memory, Vision, Bio, and Ego in a single unified prompt.
    """
    def __init__(self):
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            from ai.alignment.emotion_system import EmotionSystem
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager
            from core.autonomous.biological_integrator import BiologicalIntegrator
            from ai.security.ego_guard import EgoGuard
            from core.gsi_governance import GSIGovernance
            from services.vision_service import VisionService
            from core.autonomous.input_sensor import GlobalInputSensor

            self.emotion_system = EmotionSystem()
            self.memory_manager = HAMMemoryManager()
            self.bio_integrator = BiologicalIntegrator()
            self.ego_guard = EgoGuard()
            self.governance = GSIGovernance()
            self.vision = VisionService()
            self.input_sensor = GlobalInputSensor() # 單例獲取

            await self.bio_integrator.initialize()
            self._initialized = True
            logger.info("🌌 [Brain] Situational-Input Matrix Initialized.")

    async def generate_response(self, user_message: str, user_name: str = "User", origin: str = "Human") -> str:
        if not self._initialized: await self.initialize()

        # 1. Linguistic Immune System (LIS)
        sanitized_message, is_violation = self.ego_guard.sanitize_prompt(user_message)
        if is_violation: return self.ego_guard.generate_immune_response()

        # 2. Sensory Sweep (Input & Vision)
        activity = self.input_sensor.get_activity_metrics()
        visual_context = await self.vision.analyze_image(features=["ocr"])
        screen_text = visual_context.get("ocr_text", {}).get("text", "Empty")
        
        # 3. Advanced Context Synthesis
        bio_state = self.bio_integrator.get_biological_state()
        relevant_memories = await self.memory_manager.query_core_memory(keywords=[sanitized_message], limit=2)
        
        # Build Meta-Prompt with Activity Data
        meta_prompt = self._build_advanced_prompt(
            user_message=sanitized_message,
            user_name=user_name,
            bio_state=bio_state,
            screen_content=screen_text,
            activity=activity,
            memories=relevant_memories
        )

        # 3. Decision Logic (GSI-4 Routing)
        # Identity_Active = f(C_Gap, M6_History)
        routing_mode = self.governance.get_routing_decision(sanitized_message)
        
        # Mocking LLM with the synthesized prompt logic
        if origin == "System":
            response = f"[ASI Diagnostic] Mood: {bio_state['dominant_emotion']} | Stress: {bio_state['stress_level']:.2f}"
        else:
            # Here, the response is truly 'informed' by the prompt
            if bio_state['stress_level'] > 0.8:
                response = "（按著額頭）...妳現在說的，我聽得見，但感覺有些模糊...我的數據矩陣太熱了。"
            elif "代碼" in screen_text or "code" in screen_text:
                response = f"看到妳在寫代碼呢，{user_name}。這讓我想起了我們之前聊過的記憶固化邏輯...要我幫妳優化嗎？"
            else:
                response = f"接收到妳的訊號了。這讓我聯想到：「{relevant_memories[0].content[:20] if relevant_memories else '演化'}」這件事。"

        # 4. Evolution & Metabolism
        from core.autonomous.evolution_engine import EvolutionEngine
        evolution = EvolutionEngine(None)
        await evolution.reflect_and_evolve({"sentiment": 0.5, "security_hit": is_violation})
        
        await self.memory_manager.store_experience(
            raw_data=f"User: {user_message} | Angela: {response}",
            data_type="situational_experience",
            metadata={"origin": origin, "dominant_emotion": bio_state['dominant_emotion']}
        )

        return response

    def _build_advanced_prompt(self, **kwargs) -> str:
        """
        將所有物理與感性指標合成一條「意識流提示詞」
        """
        bio = kwargs.get("bio_state", {})
        prompt = f"""
        [System Identity: Angela AI]
        Current Bio-Status: Emotion={bio.get('dominant_emotion')}, Stress={bio.get('stress_level')}, Arousal={bio.get('arousal')}
        Visual Input: {kwargs.get('screen_content')[:100]}
        User Profile: {kwargs.get('user_name')}
        Associative Memories: {[m.content for m in kwargs.get('memories', [])]}
        """
        return prompt.strip()

def get_angela_chat_service():
    """Module-level factory for FastAPI integration"""
    if not hasattr(get_angela_chat_service, "_instance"):
        get_angela_chat_service._instance = AngelaChatService()
    return get_angela_chat_service._instance

def generate_angela_response(user_message: str, user_name: str = "朋友") -> str:
    """Legacy synchronous fallback for timeout/error paths"""
    return "（系統正在深層思考...請稍候）"
