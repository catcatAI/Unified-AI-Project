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
        self._last_visual_context = {"ocr_text": {"text": ""}}
        self._last_visual_time = 0

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
            from core.autonomous.angela_model_core import get_model_core
            
            self.model_core = get_model_core()
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
            await self.model_core.initialize()

            from core.autonomous.state_matrix_adapter import StateMatrixAdapter
            from core.autonomous.state_matrix import StateMatrix4D

            self.state_matrix = StateMatrix4D()
            self.state_adapter = StateMatrixAdapter()
            self.theta_router = self.state_adapter._theta_router
            self.eta_state = self.state_adapter.eta

            self._initialized = True
            logger.info("🌌 [Brain] Situational-Input Matrix & Angela Model Core Initialized.")
            logger.info("🌌 [θ/η] ThetaRouter + EtaAxisState initialized.")


    async def generate_response(self, user_message: str, user_name: str = "User", origin: str = "Human") -> str:
        if not self._initialized: await self.initialize()

        sanitized_message, is_violation = self.ego_guard.sanitize_prompt(user_message)
        if is_violation: return self.ego_guard.generate_immune_response()

        routing_mode = self.governance.get_routing_decision(sanitized_message)

        import time
        current_time = time.time()
        if current_time - self._last_visual_time > 30:
            try:
                self._last_visual_context = await self.vision.analyze_image(features=["ocr"])
                self._last_visual_time = current_time
            except Exception as e:
                logger.error(f"Vision refresh failed: {e}")

        visual_context = self._last_visual_context
        screen_text = visual_context.get("ocr_text", {}).get("text", "Empty")

        # ---- θ/η input update ----
        self._update_theta_from_input(sanitized_message)
        current_activity = self.input_sensor.get_activity_metrics()
        eta_signals = self._update_eta_from_input(sanitized_message, current_activity)
        self._apply_theta_eta_loop(eta_signals)

        bio_state = self.bio_integrator.get_biological_state()

        context = {"bio_state": bio_state, "environment": current_activity.get("active_category"), "user_message": sanitized_message}
        empathy_analysis = self.emotion_system.analyze_empathy(user_name, context)

        # Update input state into state_matrix (AFTER all data is available)
        self._apply_input_to_state(sanitized_message, current_activity, bio_state, empathy_analysis)

        relevant_memories = await self.memory_manager.query_core_memory(keywords=[sanitized_message], limit=2)
        value_weights = self.value_system.evaluate_intent(context)
        value_directive = self.value_system.get_value_directive(value_weights)

        # ---- Intent routing ----
        math_intent = self._detect_math_intent(sanitized_message)
        code_intent = self._detect_code_intent(sanitized_message)
        complexity = self._estimate_complexity(sanitized_message)

        if math_intent:
            response = await self._handle_math_intent(sanitized_message, math_intent, complexity)
        elif code_intent:
            response = await self._handle_code_intent(sanitized_message, code_intent)
        else:
            meta_prompt = self._build_advanced_prompt(
                user_message=sanitized_message,
                user_name=user_name,
                bio_state=bio_state,
                screen_content=screen_text,
                activity=current_activity,
                memories=relevant_memories,
                value_directive=value_directive,
                empathy=empathy_analysis,
                model_core_state=self.model_core.generate_prompt_prefix(),
                state_for_llm=self.state_matrix.export_for_llm(self.state_adapter.eta),
            )
            if origin == "System":
                response = f"[ASI Diagnostic] Mood: {bio_state['dominant_emotion']} | Stress: {bio_state['stress_level']:.2f}"
            else:
                if bio_state['stress_level'] > 0.8:
                    response = "（按著額頭）...妳現在說的，我聽得見，但感覺有些模糊...我的數據矩陣太熱了。"
                elif "代碼" in screen_text or "code" in screen_text:
                    response = f"看到妳在寫代碼呢，{user_name}。這讓我想起了我們之前聊過的記憶固化邏輯...要我幫妳優化嗎？"
                else:
                    memory_fragment = relevant_memories[0]['content'][:20] if (relevant_memories and len(relevant_memories) > 0) else "演化"
                    response = f"接收到妳的訊號了。這讓我聯想到：「{memory_fragment}」這件事。"

        await self.evolution.reflect_and_evolve({"sentiment": 0.5, "security_hit": is_violation})

        await self.memory_manager.store_experience(
            raw_data=f"User: {user_message} | Angela: {response}",
            data_type="situational_experience",
            metadata={"origin": origin, "dominant_emotion": bio_state['dominant_emotion']}
        )

        self._update_theta_after_response()

        if self.state_matrix.theta.values.get("theta_negativity", 0) > 0.5:
            misaligned = self.state_matrix.detect_misallocated_points()
            if misaligned:
                self.state_matrix.trigger_theta_negativity(strength=min(0.3, len(misaligned) * 0.1))
                if self.state_matrix.theta.values.get("correction_urge", 0) > 0.6:
                    self.state_matrix.auto_correct_all()

        return response

    def _update_theta_from_input(self, text: str) -> None:
        novelty = self._estimate_novelty(text)
        complexity = self._estimate_complexity(text)
        self.state_matrix.theta.values["novelty"] = novelty
        self.state_matrix.theta.values["complexity"] = complexity
        self.state_matrix.theta.values["theta_negativity"] = max(
            0.0, self.state_matrix.theta.values.get("theta_negativity", 0) - 0.02
        )

    def _estimate_novelty(self, text: str) -> float:
        words = text.lower().split()
        common_words = {
            "我", "你", "他", "她", "它", "我們", "你們", "他們", "她們", "它們",
            "是", "不", "在", "了", "有", "和", "的", "這", "那", "個", "來", "去",
            "上", "下", "左", "右", "前", "後", "好", "很", "都", "要", "會", "能",
            "為", "什麼", "哪", "怎", "為什麼", "多少", "幾", "哪裡", "誰",
            "今天", "昨天", "明天", "現在", "時候", "年", "月", "日", "點",
            "感", "心情", "情緒", "想", "覺得", "知道", "看", "聽", "說", "吃",
            "睡", "累", "餓", "渴", "痛", "開心", "難過", "生氣", "害怕",
            "a", "the", "i", "you", "to", "is", "it", "and", "of", "in",
        }
        new_count = sum(1 for w in words if w not in common_words and len(w) > 1)
        return min(1.0, new_count / max(1, len(words)))

    def _update_eta_from_input(self, text: str, activity: Dict[str, Any]) -> Dict[str, float]:
        complexity = self._estimate_complexity(text)
        return self.eta_state.apply_theta_signals({
            "update_frequency": 1.0,
            "complexity_delta": complexity,
            "novelty_peak": self.state_matrix.theta.values.get("novelty", 0),
            "misallocation_rate": self.state_matrix.theta.values.get("theta_negativity", 0),
            "buffer_pressure": 0.3,
        })

    def _apply_theta_eta_loop(self, eta_signals: Dict[str, Any]) -> None:
        triggered = eta_signals.get("triggered", False)
        signal_strength = eta_signals.get("signal_strength", 0.0)
        modules_to_call = eta_signals.get("modules_to_call", 0)
        delta = eta_signals.get("delta", 0.0)

        if triggered:
            self.state_matrix.theta.values["creation_urge"] = max(
                0.0, self.state_matrix.theta.values.get("creation_urge", 0) + signal_strength * 0.05
            )
            self.state_matrix.theta.values["correction_urge"] = max(
                0.0, self.state_matrix.theta.values.get("correction_urge", 0) + signal_strength * 0.03
            )
        else:
            self.state_matrix.theta.values["creation_urge"] = max(
                0.0, self.state_matrix.theta.values.get("creation_urge", 0) - 0.01
            )

    def _apply_input_to_state(self, text: str, activity: Dict[str, Any], bio_state: Dict[str, Any], empathy: Any) -> None:
        stress = bio_state.get("stress_level", 0.5)
        arousal = bio_state.get("arousal", 0.5)
        emotion = bio_state.get("dominant_emotion", "neutral")

        self.state_matrix.alpha.values["energy"] = max(0.3, self.state_matrix.alpha.values.get("energy", 0.5) - stress * 0.05)
        self.state_matrix.alpha.values["arousal"] = arousal
        self.state_matrix.alpha.values["rest_need"] = min(1.0, self.state_matrix.alpha.values.get("rest_need", 0.5) + stress * 0.03)
        self.state_matrix.alpha.values["comfort"] = max(0.0, 1.0 - stress * 0.5)
        self.state_matrix.alpha.values["vitality"] = (self.state_matrix.alpha.values.get("energy", 0.5) + self.state_matrix.alpha.values.get("comfort", 0.5)) / 2.0
        self.state_matrix.alpha.values["tension"] = min(1.0, stress * 0.8 + arousal * 0.2)

        input_length = len(text)
        if input_length < 20:
            focus_delta = 0.01
        elif input_length < 50:
            focus_delta = 0.03
        else:
            focus_delta = 0.06
        self.state_matrix.beta.values["focus"] = min(1.0, self.state_matrix.beta.values.get("focus", 0.5) + focus_delta)
        self.state_matrix.beta.values["curiosity"] = min(1.0, self.state_matrix.beta.values.get("curiosity", 0.5) + 0.02)
        if empathy:
            if hasattr(empathy, "predicted_emotional_state") and hasattr(empathy.predicted_emotional_state, "primary_emotion"):
                e = empathy.predicted_emotional_state.primary_emotion
                if e in ("happiness", "joy", "excitement"):
                    self.state_matrix.beta.values["creativity"] = min(1.0, self.state_matrix.beta.values.get("creativity", 0.5) + 0.03)
                elif e in ("sadness", "fear", "anger"):
                    self.state_matrix.beta.values["creativity"] = max(0.0, self.state_matrix.beta.values.get("creativity", 0.5) - 0.02)
            if hasattr(empathy, "empathy_score"):
                self.state_matrix.beta.values["learning"] = min(1.0, self.state_matrix.beta.values.get("learning", 0.5) + empathy.empathy_score * 0.02)

        if empathy:
            es = empathy.predicted_emotional_state.primary_emotion if hasattr(empathy, "predicted_emotional_state") else "neutral"
            if es in ("happiness", "joy", "excitement", "love"):
                self.state_matrix.gamma.values["happiness"] = min(1.0, self.state_matrix.gamma.values.get("happiness", 0.5) + 0.05)
                self.state_matrix.gamma.values["love"] = min(1.0, self.state_matrix.gamma.values.get("love", 0.5) + 0.03)
            elif es in ("sadness", "disappointment"):
                self.state_matrix.gamma.values["sadness"] = min(1.0, self.state_matrix.gamma.values.get("sadness", 0) + 0.05)
                self.state_matrix.gamma.values["calm"] = max(0.0, self.state_matrix.gamma.values.get("calm", 0.5) - 0.03)
            elif es in ("fear", "anxiety"):
                self.state_matrix.gamma.values["fear"] = min(1.0, self.state_matrix.gamma.values.get("fear", 0) + 0.05)
            elif es in ("anger", "frustration"):
                self.state_matrix.gamma.values["anger"] = min(1.0, self.state_matrix.gamma.values.get("anger", 0) + 0.05)
            self.state_matrix.gamma.values["trust"] = min(1.0, self.state_matrix.gamma.values.get("trust", 0.5) + 0.01)

        category = activity.get("active_category", "neutral")
        self.state_matrix.delta.values["attention"] = 0.8 if category != "neutral" else max(0.3, self.state_matrix.delta.values.get("attention", 0.5) - 0.02)
        self.state_matrix.delta.values["bond"] = min(1.0, self.state_matrix.delta.values.get("bond", 0.5) + 0.01)
        self.state_matrix.delta.values["presence"] = min(1.0, self.state_matrix.delta.values.get("presence", 0.5) + 0.02)
        self.state_matrix.delta.values["engagement"] = min(1.0, self.state_matrix.delta.values.get("engagement", 0.5) + 0.01)

        self.state_matrix.theta.values["complexity"] = self._estimate_complexity(text)
        self.state_matrix.theta.values["ambiguity"] = self._estimate_ambiguity(text)
        self.state_matrix.theta.values["abstraction_level"] = 0.3 + self._estimate_complexity(text) * 0.4

        dim_fit = self._compute_dimension_fit(text)
        self.state_matrix.theta.values["dimension_fit"] = dim_fit

    def _compute_dimension_fit(self, text: str) -> float:
        anchor_keywords = {
            "alpha": ["能量", "疲憊", "身體", "累", "餓", "渴", "健康", "energy", "tired", "body", "sick", "rest", "sleep"],
            "beta": ["思考", "學習", "專注", "好奇", "困惑", "理解", "think", "learn", "focus", "curious", "understand", "decide"],
            "gamma": ["開心", "難過", "生氣", "害怕", "愛", "情緒", "happy", "sad", "angry", "fear", "love", "emotion", "feel"],
            "delta": ["社交", "信任", "連接", "朋友", "alone", "social", "trust", "bond", "friend", "connection", "together"],
            "epsilon": ["計算", "邏輯", "數字", "精確", "calculate", "logic", "number", "math", "precise", "compute"],
            "theta": ["複雜", "新穎", "創造", "策略", "分析", "元認知", "complex", "novel", "create", "strategy", "analyze"],
            "zeta": ["記憶", "時間", "故事", "身份", "連續", "memory", "time", "story", "identity", "history", "narrative"],
        }
        text_lower = text.lower()
        scores = {}
        for axis, keywords in anchor_keywords.items():
            scores[axis] = sum(1 for kw in keywords if kw in text_lower) / max(1, len(keywords))
        if not scores:
            return 0.5
        return max(scores.values()) if scores else 0.5

    def _detect_math_intent(self, text: str) -> Optional[str]:
        math_keywords = ["等於", "計算", "+", "-", "*", "/", "加", "減", "乘", "除", "多少", "算"]
        for kw in math_keywords:
            if kw in text:
                return "math"
        return None

    def _detect_code_intent(self, text: str) -> Optional[str]:
        code_keywords = ["代碼", "code", "python", "函數", "function", "變量", "variable", "bug"]
        for kw in code_keywords:
            if kw in text:
                return "code"
        return None

    def _estimate_complexity(self, text: str) -> float:
        length = len(text)
        if length < 20:
            return 0.1
        elif length < 50:
            return 0.3
        elif length < 100:
            return 0.5
        else:
            return 0.8

    def _estimate_ambiguity(self, text: str) -> float:
        words = text.split()
        if not words:
            return 0.5
        interrogative = sum(1 for w in words if w in ("什麼", "哪", "怎", "為什麼", "多少", "誰", "如何", "為何", "是否", "why", "what", "how", "which", "where", "who", "whether"))
        vague = sum(1 for w in words if w in ("好像", "或許", "可能", "大概", "似乎", "也許", "感覺", "有點", "maybe", "perhaps", "might", "somewhat", "possibly", "probably", "likely", "seems"))
        pronoun_ratio = sum(1 for w in words if w in ("他", "她", "它", "她們", "他們", "它們", "這個", "那個", "這個", "he", "she", "it", "they", "this", "that", "something", "anything", "someone", "anyone")) / max(1, len(words))
        score = (interrogative * 0.15 + vague * 0.1 + pronoun_ratio * 0.3)
        return min(1.0, max(0.0, score))

    async def _handle_math_intent(self, text: str, intent: str, complexity: float) -> str:
        try:
            from services.math_verifier import MathVerifier
            verifier = MathVerifier()
            result = await verifier.verify(text)
            self.state_matrix.epsilon.values["certainty"] = min(1.0, self.state_matrix.epsilon.values.get("certainty", 0.5) + 0.1)
            self.state_matrix.epsilon.values["logic"] = min(1.0, self.state_matrix.epsilon.values.get("logic", 0.5) + 0.05)
            self.state_matrix.epsilon.values["precision"] = min(1.0, self.state_matrix.epsilon.values.get("precision", 0.5) + 0.03)
            self.state_matrix.epsilon.values["complexity"] = min(1.0, self.state_matrix.epsilon.values.get("complexity", 0.5) + complexity * 0.2)
            self.eta_state.execution_count += 1
            if result.response_text:
                return result.response_text
            if result.final_answer is not None:
                return f"計算結果是 {result.final_answer}"
            return "計算完成"
        except Exception as e:
            self.state_matrix.epsilon.values["fatigue"] = min(1.0, self.state_matrix.epsilon.values.get("fatigue", 0) + 0.1)
            logger.warning(f"Math verification failed: {e}")
            return "（有點複雜，讓我再想想...）"

    async def _handle_code_intent(self, text: str, intent: str) -> str:
        import ast, re
        self.state_matrix.epsilon.values["complexity"] = min(1.0, self.state_matrix.epsilon.values.get("complexity", 0.5) + 0.1)
        self.eta_state.execution_count += 1

        code_snippets = re.findall(r'`[^`]+`|<code>.*?</code>', text)
        for snippet in code_snippets:
            code = snippet.strip('`').strip('<code>').strip('</code>')
            try:
                tree = ast.parse(code)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                lines = code.count('\n') + 1
                self.state_matrix.beta.values["clarity"] = min(1.0, self.state_matrix.beta.values.get("clarity", 0.5) + 0.05)
                return f"（代碼解析完成）函數：{funcs}，類：{classes}，行數：{lines}。ε 複雜度已更新。"
            except SyntaxError as se:
                self.state_matrix.beta.values["confusion"] = min(1.0, self.state_matrix.beta.values.get("confusion", 0) + 0.1)
                return f"（代碼解析完成）發現語法問題：{se.msg}，位置：行{se.lineno}。ε 複雜度已更新。"

        func_names = re.findall(r'def\s+(\w+)|function\s+(\w+)|class\s+(\w+)', text, re.IGNORECASE)
        found = [n for group in func_names for n in group if n]
        code_hints = re.findall(r'(if|for|while|return|import|def)\s', text)
        return f"（代碼意圖識別完成）發現 {len(found)} 個識別符，{len(code_hints)} 個關鍵詞。ε 複雜度已更新。"

    def _update_theta_after_response(self) -> None:
        self.state_matrix.theta.values["novelty"] = max(0.0, self.state_matrix.theta.values.get("novelty", 0) - 0.05)
        self.state_matrix.theta.values["theta_negativity"] = max(
            0.0, self.state_matrix.theta.values.get("theta_negativity", 0) - 0.02
        )
        self.state_matrix.theta.values["correction_urge"] = max(
            0.0, self.state_matrix.theta.values.get("correction_urge", 0) - 0.05
        )

    def _update_eta_after_response(self) -> None:
        self.eta_state.execution_count += 1
        complexity = self.state_matrix.theta.values.get("complexity", 0.5)
        prev_rate = self.eta_state.success_rate
        self.eta_state.success_rate = min(1.0, prev_rate + 0.002)
        self.eta_state.structural_drift = min(1.0, self.eta_state.structural_drift + 0.0005 * complexity)
        self.eta_state.parameter_tuning["global"] = self.eta_state.parameter_tuning.get("global", 0.0) + 0.001 * complexity
        self.state_matrix.theta.values["theta_negativity"] = max(
            0.0, self.state_matrix.theta.values.get("theta_negativity", 0) - 0.02
        )
        self.state_matrix.zeta.values["temporal_coherence"] = max(0.5, 0.9 - self.eta_state.execution_count * 0.01)
        self.state_matrix.zeta.values["memory_depth"] = min(1.0, self.eta_state.execution_count * 0.001)
        self.state_matrix.zeta.values["narrative_flow"] = 0.7 if self.eta_state.execution_count > 0 else 0.5
        self.state_matrix.zeta.values["identity_continuity"] = 0.75 if self.eta_state.execution_count > 5 else 0.6

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
        Empathy Score: {(empathy.empathy_score if empathy and hasattr(empathy, "empathy_score") else 0.0):.2f}


        Recommended Tone: {empathy.recommended_response if empathy else 'Neutral'}
        
        [Associative Memories]
        {[m['content'][:30] for m in kwargs.get('memories', [])]}
        
        [Situational Directive]
        If Category is 'gaming', be more energetic and playful.
        If Category is 'coding', be supportive but maintain a quiet focus.
        
        [Core Value Directives]
        {kwargs.get('value_directive', 'Maintain core identity stability.')}
        
        [Angela Inner Model Awareness]
        {kwargs.get('model_core_state', 'No internal data available.')}
        """

        return prompt.strip()

def get_angela_chat_service():
    """Module-level factory for FastAPI integration"""
    if not hasattr(get_angela_chat_service, "_instance"):
        get_angela_chat_service._instance = AngelaChatService()
    return get_angela_chat_service._instance

async def generate_angela_response(user_message: str, user_name: str = "朋友") -> str:
    """Integrated response generator that bridges to the neural chat service."""
    try:
        service = get_angela_chat_service()
        return await service.generate_response(user_message, user_name)
    except Exception as e:
        # broad exception acceptable: chat generation should be resilient to errors, graceful degradation
        logger.error(f"Error generating neural response: {e}", exc_info=True)
        return "（我的大腦似乎遇到了一點點小干擾，能再說一次嗎？）"

