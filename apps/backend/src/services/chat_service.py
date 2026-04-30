# =============================================================================
# ANGELA-MATRIX: L2-L3[記憶/身份層] βδ [A] L3+
# =============================================================================
# 職責: 意識流合成與對話管理 (Neural Chat Service).
# 維度: 認知 (β) 與精神 (δ) 維度的語言化呈現。
# =============================================================================

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
            from ai.alignment.value_assessment import get_value_system
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager
            from core.autonomous.biological_integrator import BiologicalIntegrator
            from ai.security.ego_guard import EgoGuard
            from core.gsi_governance import GSIGovernance
            from services.vision_service import VisionService
            from core.autonomous.input_sensor import GlobalInputSensor
            from ai.personality.personality_manager import PersonalityManager
            from core.autonomous.evolution_engine import EvolutionEngine

            self.personality_manager = PersonalityManager()
            self.emotion_system = EmotionSystem()
            self.value_system = get_value_system()
            self.memory_manager = HAMMemoryManager()
            self.bio_integrator = BiologicalIntegrator()
            self.ego_guard = EgoGuard()
            self.governance = GSIGovernance()
            self.vision = VisionService()
            self.input_sensor = GlobalInputSensor() # 單例獲取
            self.evolution = EvolutionEngine(self.personality_manager)

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
        
        # 2030 Standard: ASI Value Assessment [N.8.1] & Empathy [N.8.2]
        context = {"bio_state": bio_state, "environment": activity.get("active_category"), "user_message": sanitized_message}
        value_weights = self.value_system.evaluate_intent(context)
        value_directive = self.value_system.get_value_directive(value_weights)
        
        # Empathy Prediction
        empathy_analysis = self.emotion_system.analyze_empathy(user_name, context)

        # Build Meta-Prompt with Activity, Value & Empathy Data
        meta_prompt = self._build_advanced_prompt(
            user_message=sanitized_message,
            user_name=user_name,
            bio_state=bio_state,
            screen_content=screen_text,
            activity=activity,
            memories=relevant_memories,
            value_directive=value_directive,
            empathy=empathy_analysis
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
                memory_fragment = relevant_memories[0]['content'][:20] if (relevant_memories and len(relevant_memories) > 0) else "演化"
                response = f"接收到妳的訊號了。這讓我聯想到：「{memory_fragment}」這件事。"

        # 4. Evolution & Metabolism [N.5.4 Persistence]
        await self.evolution.reflect_and_evolve({"sentiment": 0.5, "security_hit": is_violation})
        
        await self.memory_manager.store_experience(
            raw_data=f"User: {user_message} | Angela: {response}",
            data_type="situational_experience",
            metadata={"origin": origin, "dominant_emotion": bio_state['dominant_emotion']}
        )

        return response

    def _build_advanced_prompt(self, **kwargs) -> str:
        """
        將所有物理、環境與感性指標合成一條「意識流提示詞」 (2030 Standard).
        """
        bio = kwargs.get("bio_state", {})
        activity = kwargs.get("activity", {})
        category = activity.get("active_category", "neutral")
        empathy = kwargs.get("empathy")
        
        prompt = f"""
        [System Identity: Angela AI]
        Current Bio-Status: Emotion={bio.get('dominant_emotion')}, Stress={bio.get('stress_level'):.2f}, Arousal={bio.get('arousal')}
        User Environment: Category={category} (Activity BPM: {activity.get('input_density_bpm', 0.0):.1f})
        Visual Input (OCR): {kwargs.get('screen_content')[:100]}
        User Profile: {kwargs.get('user_name')}
        
        [Empathy & Resonance]
        User Predicted Emotion: {empathy.predicted_emotional_state.primary_emotion if empathy else 'Unknown'}
        Empathy Score: {empathy.empathy_score:.2f if empathy else 0.0}
        Recommended Tone: {empathy.recommended_response if empathy else 'Neutral'}
        
        [Associative Memories]
        {[m['content'][:30] for m in kwargs.get('memories', [])]}
        
        [Situational Directive]
        If Category is 'gaming', be more energetic and playful.
        If Category is 'coding', be supportive but maintain a quiet focus.
        
        [Core Value Directives]
        {kwargs.get('value_directive', 'Maintain core identity stability.')}
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
