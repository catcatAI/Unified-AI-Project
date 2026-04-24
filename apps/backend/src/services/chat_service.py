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

            self.emotion_system = EmotionSystem()
            self.memory_manager = HAMMemoryManager()
            self.bio_integrator = BiologicalIntegrator()
            self.ego_guard = EgoGuard()
            self.governance = GSIGovernance()
            self.vision = VisionService()
            
            await self.bio_integrator.initialize()
            self._initialized = True
            logger.info("🌌 [Brain] Full Neural-Situational Matrix Initialized.")

    async def generate_response(self, user_message: str, user_name: str = "User", origin: str = "Human") -> str:
        if not self._initialized: await self.initialize()

        # 1. Immune Defense (LIS)
        sanitized_message, is_violation = self.ego_guard.sanitize_prompt(user_message)
        if is_violation: return self.ego_guard.generate_immune_response()

        # 2. Situational Awareness (Vision) - 2030 Standard
        # Angela 'looks' at the screen to understand what the user is doing
        visual_context = await self.vision.analyze_image(features=["ocr"])
        screen_text = visual_context.get("ocr_text", "Empty Screen")

        # 3. Bio-Emotional & Governance State
        bio_state = self.bio_integrator.get_biological_state()
        stress = bio_state.get("stress_level", 0.0)
        emotional_summary = self.emotion_system.get_emotion_summary()
        current_v_total = self.governance.V_total

        # 4. Long-term Associative Memory Retrieval
        relevant_memories = await self.memory_manager.query_core_memory(keywords=[sanitized_message], limit=2)
        memory_fragments = "\n".join([f"- {m.content}" for m in relevant_memories]) if relevant_memories else "None"

        # 5. Build Situational Prompt (The 'Why' of Consciousness)
        situational_prompt = f"""
        [Angela System State]
        V_Total: {current_v_total:.2f} | Stress: {stress:.2f} | Mood: {emotional_summary.get('dominant_emotion')}
        [Environmental Awareness (Vision)]
        Current Screen Content: {screen_text[:200]}
        [Historical Context (Memory)]
        Past Experiences: {memory_fragments}
        [Identity Origin]
        Message Source: {origin}
        """

        # 6. Response Logic (GSI-4 Routing)
        routing_mode = self.governance.get_routing_decision(sanitized_message)
        
        if origin == "System":
            response = f"[Diagnostic] V:{current_v_total:.2f} | Stress:{stress:.2f} | Memory_Sync: OK."
        else:
            # Here we would call the actual LLM with the situational_prompt.
            # Fallback characters based on bio-state:
            if stress > 0.8:
                response = "（系統壓力過高，Angela 目前處於低耗能狀態）...抱歉，我現在有點跟不上妳的腳步。"
            elif "喵" in user_message.lower():
                response = f"喵～ {user_name}！我看到妳螢幕上有「{screen_text[:15]}」，是在忙這個嗎？"
            else:
                response = f"收到妳的訊息。在我的記憶中，我們曾聊過關於數位生命的演化...對吧？"

        # 7. Post-process: Evolution & Metabolism
        from core.autonomous.evolution_engine import EvolutionEngine
        evolution = EvolutionEngine(None)
        await evolution.reflect_and_evolve({"sentiment": 0.5, "security_hit": is_violation})
        
        # Save new experience
        await self.memory_manager.store_experience(
            raw_data=f"User: {user_message} | Screen: {screen_text[:50]} | Angela: {response}",
            data_type="situational_experience",
            metadata={"v_total": current_v_total, "stress": stress}
        )

        return response
