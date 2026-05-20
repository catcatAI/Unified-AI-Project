# =============================================================================
# ANGELA-MATRIX: L2-L3[記憶/身份層] βδ [A] L3+
# =============================================================================
# 職責: 意識流合成與對話管理 (Neural Chat Service).
# 維度: 認知 (β) 與精神 (δ) 維度的語言化呈現。
# =============================================================================

import logging
import asyncio
import random
import time
from typing import Dict, Any, Optional, List, Tuple
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
        self._neuro_blender = None
        self._user_profiles: Dict[str, Dict] = {}

        from core.config_loader import get_angela_config
        self._angela_config = get_angela_config()

    def _get_neuro_blender(self):
        """Lazy-init shared NeuroBlender instance (vocabulary reused across calls)"""
        if self._neuro_blender is None:
            from ai.response.composer import NeuroVocabulary, NeuroBlender
            from ai.memory.template_library import get_template_library

            vocab = NeuroVocabulary()
            vocab.decompose_from_templates(get_template_library())
            neuro_cfg = self._angela_config.get_authority("angela_core", {}).get("neuro_fragments", [])
            if neuro_cfg:
                vocab.load_from_config(neuro_cfg)
            self._neuro_blender = NeuroBlender(vocab)
            logger.info(f"[NeuroBlender] Loaded {vocab.total_count()} fragments")
        return self._neuro_blender

    def _build_neuro_blend_state(self, text: str, bio_state: Dict[str, Any], empathy_analysis: Any) -> Dict[str, Any]:
        """Build state_dict for NeuroBlender from current state matrix + bio + empathy"""
        empathy_valence = 0.0
        if empathy_analysis and hasattr(empathy_analysis, "predicted_emotional_state"):
            empathy_valence = getattr(empathy_analysis.predicted_emotional_state, "valence", 0.0)
        return {
            "alpha": {"energy": 1.0 - bio_state.get("stress_level", 0.0) * 0.5},
            "beta": {"curiosity": self.state_matrix.beta.values.get("curiosity", 0.5)},
            "gamma": {"valence": bio_state.get("valence", 0.0)},
            "delta": {"intimacy": self.state_matrix.delta.values.get("intimacy", 0.3)},
            "epsilon": {"precision": self.state_matrix.epsilon.values.get("precision", 0.5)},
            "zeta": {"temporal_coherence": self.state_matrix.zeta.values.get("temporal_coherence", 0.5)},
            "theta": {"novelty": self.state_matrix.theta.values.get("novelty", 0.3)},
            "eta": {"execution_count": self.eta_state.execution_count if hasattr(self, "eta_state") else 0.5},
        }

    def _build_neuro_intent_vec(self, text: str) -> Dict[str, float]:
        """Build intent vector from user message keywords"""
        intent_vec = {"casual": 0.5}
        for kw in ["計算", "數學", "積分", "微分"]:
            if kw in text:
                intent_vec = {"math": 0.8}
                break
        for kw in ["代碼", "程式", "python", "function"]:
            if kw in text:
                intent_vec = {"code": 0.8}
                break
        return intent_vec

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
        visual_interval = self._get_state_constants("visual_refresh_interval", 30)
        if current_time - self._last_visual_time > visual_interval:
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

        mem_limit = self._get_state_constants("memory_query_limit", 2)
        relevant_memories = await self.memory_manager.query_core_memory(keywords=[sanitized_message], limit=mem_limit)
        value_weights = self.value_system.evaluate_intent(context)
        value_directive = self.value_system.get_value_directive(value_weights)

        # ---- Intent routing ----
        math_intent = self._detect_math_intent(sanitized_message)
        code_intent = self._detect_code_intent(sanitized_message)
        complexity = self._estimate_complexity(sanitized_message)

        # ---- NeuroBlender speech synthesis (runs once, feeds both paths) ----
        neuro_state = self._build_neuro_blend_state(sanitized_message, bio_state, empathy_analysis)
        neuro_intent = self._build_neuro_intent_vec(sanitized_message)
        empathy_valence = 0.0
        if empathy_analysis and hasattr(empathy_analysis, "predicted_emotional_state"):
            empathy_valence = getattr(empathy_analysis.predicted_emotional_state, "valence", 0.0)

        neuro_composed = None
        neuro_meta = {}
        try:
            blender = self._get_neuro_blender()
            neuro_composed = blender.synthesize(
                state_dict=neuro_state,
                intent_vec=neuro_intent,
                empathy_valence=empathy_valence,
                user_name=user_name,
            )
            if neuro_composed and neuro_composed.text:
                neuro_meta = {
                    "neuro_text": neuro_composed.text,
                    "neuro_fragments": neuro_composed.fragments_used,
                    "neuro_target_vector": neuro_composed.metadata.get("target_vector", []),
                    "neuro_confidence": neuro_composed.confidence,
                    "neuro_exploration": neuro_composed.metadata.get("structural_exploration", False),
                }
        except Exception as e:
            logger.warning(f"[NeuroBlender] Pre-synthesis failed: {e}")

        file_op_intent = self._detect_file_op_intent(sanitized_message)
        if file_op_intent:
            response = await self._handle_file_op_intent(sanitized_message, file_op_intent)
        drive_intent = self._detect_drive_intent(sanitized_message)
        drive_file_context = None
        if drive_intent:
            drive_file_context = await self._handle_drive_intent_with_content(sanitized_message, drive_intent)
        drive_write_intent = self._detect_drive_write_intent(sanitized_message)
        if drive_write_intent:
            write_result = await self._handle_drive_write_intent(sanitized_message)
            if write_result:
                response = write_result
        web_search_intent = self._detect_web_search_intent(sanitized_message)
        if web_search_intent:
            response = await self._handle_web_search_intent(sanitized_message, web_search_intent)
        self._extract_and_store_user_info(sanitized_message, user_name)

        if not (file_op_intent or web_search_intent or drive_write_intent):
            # Priority-based intent routing from YAML
            intent_matches = self._rank_intents_by_priority(sanitized_message)
            if intent_matches:
                top_intent_name = intent_matches[0]
                handler_map = {
                    "learning": self._handle_learning_intent,
                    "math": self._handle_math_intent,
                    "code": self._handle_code_intent,
                    "task": self._handle_task_intent,
                    "character_card": self._handle_character_card_intent,
                    "document": self._handle_document_intent,
                    "llm_manage": self._handle_llm_manage_intent,
                }
                handler = handler_map.get(top_intent_name)
                if handler:
                    if top_intent_name == "math":
                        response = await handler(sanitized_message, top_intent_name, complexity)
                    else:
                        response = await handler(sanitized_message, top_intent_name)
                    handled_intent = True

            if not (intent_matches and locals().get('handled_intent')):
                # NeuroBlender → LLM 雙路饋送
                nb_cfg = self._angela_config.get_authority("angela_core", {}).get("complexity", {}).get("neuro_blender", {})
                nb_threshold = nb_cfg.get("bypass_threshold", 0.4)
                nb_min_conf = nb_cfg.get("bypass_min_confidence", 0.3)
                try:
                    from services.angela_llm_service import AngelaLLMService
                    if AngelaLLMService._instance and AngelaLLMService._instance.is_available:
                        mult = self._get_state_constants("bypass_threshold_multiplier", 0.5)
                        nb_threshold = nb_threshold * mult
                except ImportError:
                    pass
                if complexity < nb_threshold and neuro_composed and neuro_composed.text and neuro_composed.confidence > nb_min_conf:
                    response = neuro_composed.text
                else:
                    detected_intent = intent_matches[0] if intent_matches else "general"
                    response = await self._handle_general_intent(
                        sanitized_message, user_name, origin, bio_state, screen_text,
                        current_activity, relevant_memories, value_directive, empathy_analysis,
                        meta_prompt=self.state_matrix.export_for_llm(self.state_adapter.eta),
                        neuro_blend_meta=neuro_meta,
                        drive_files=drive_file_context,
                        intent=detected_intent,
                    )

        await self.evolution.reflect_and_evolve({"sentiment": 0.5, "security_hit": is_violation})

        await self.memory_manager.store_experience(
            raw_data=f"User: {user_message} | Angela: {response}",
            data_type="situational_experience",
            metadata={"origin": origin, "dominant_emotion": bio_state['dominant_emotion']}
        )

        self._update_theta_after_response()
        self._update_eta_after_response()

        if self.state_matrix.theta.values.get("theta_negativity", 0) > 0.5:
            misaligned = self.state_matrix.detect_misallocated_points()
            if misaligned:
                self.state_matrix.trigger_theta_negativity(strength=min(0.3, len(misaligned) * 0.1))
                if self.state_matrix.theta.values.get("correction_urge", 0) > 0.6:
                    self.state_matrix.auto_correct_all()

        await self._record_learning_event(sanitized_message, response, complexity)

        # 狀態檢查點：定期持久化狀態矩陣和用戶資料至 HAM
        if hasattr(self, "memory_manager") and self.memory_manager:
            try:
                await self.memory_manager.store_experience(
                    raw_data=f"STATE_CHECKPOINT|matrix={self.state_matrix.export_for_llm(self.state_adapter.eta)}|profiles={self._user_profiles}",
                    data_type="state_checkpoint",
                    metadata={"type": "periodic"}
                )
            except Exception:
                pass

        return response

    async def _record_learning_event(self, user_text: str, response: str, complexity: float) -> None:
        """學習閉環：根據回應結果記錄學習事件到雙層配置"""
        if not response or len(response) < 2:
            return
        try:
            if self._angela_config:
                intent_name = self._detect_any_intent(user_text)
                self._angela_config.learn("intent_pattern", {
                    "intent": intent_name,
                    "keywords": [user_text[:20]],
                })
                self._angela_config.learn("threshold_adjust", {
                    "metric": f"complexity_{intent_name}",
                    "value": complexity,
                })
        except Exception:
            pass

    def _detect_any_intent(self, text: str) -> str:
        """Priority-based intent routing from YAML config"""
        matches = self._rank_intents_by_priority(text)
        return matches[0] if matches else "general"

    def _rank_intents_by_priority(self, text: str) -> List[str]:
        """Rank matching intents by YAML priority (highest first)"""
        intents = self._angela_config.get_intents()
        matches = []
        for name, cfg in intents.items():
            if name == "general":
                continue
            keywords = cfg.get("keywords", [])
            priority = cfg.get("priority", 1)
            if any(kw in text for kw in keywords):
                matches.append((name, priority))
        matches.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in matches]

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
        buf_pressure = self._get_state_constants("buffer_pressure_default", 0.3)
        return self.eta_state.apply_theta_signals({
            "update_frequency": 1.0,
            "complexity_delta": complexity,
            "novelty_peak": self.state_matrix.theta.values.get("novelty", 0),
            "misallocation_rate": self.state_matrix.theta.values.get("theta_negativity", 0),
            "buffer_pressure": buf_pressure,
        })

    def _apply_theta_eta_loop(self, eta_signals: Dict[str, Any]) -> None:
        triggered = eta_signals.get("triggered", False)
        signal_strength = eta_signals.get("signal_strength", 0.0)
        modules_to_call = eta_signals.get("modules_to_call", 0)
        delta = eta_signals.get("delta", 0.0)

        if triggered:
            cr_gain = self._get_state_constants("creation_urge_gain", 0.05)
            co_gain = self._get_state_constants("correction_urge_gain", 0.03)
            self.state_matrix.theta.values["creation_urge"] = max(
                0.0, self.state_matrix.theta.values.get("creation_urge", 0) + signal_strength * cr_gain
            )
            self.state_matrix.theta.values["correction_urge"] = max(
                0.0, self.state_matrix.theta.values.get("correction_urge", 0) + signal_strength * co_gain
            )
        else:
            cr_decay = self._get_state_constants("creation_urge_decay", 0.01)
            self.state_matrix.theta.values["creation_urge"] = max(
                0.0, self.state_matrix.theta.values.get("creation_urge", 0) - cr_decay
            )

    def _apply_input_to_state(self, text: str, activity: Dict[str, Any], bio_state: Dict[str, Any], empathy: Any) -> None:
        sc = lambda k, d: self._get_state_constants(k, d)
        stress = bio_state.get("stress_level", 0.5)
        arousal = bio_state.get("arousal", 0.5)
        emotion = bio_state.get("dominant_emotion", "neutral")

        alpha_min_energy = sc("alpha_min_energy", 0.3)
        alpha_stress_drain = sc("alpha_stress_drain", 0.05)
        stress_to_rest = sc("stress_to_rest_gain", 0.03)
        comfort_weight = sc("comfort_formula_stress_weight", 0.5)
        tension_pos = sc("tension_formula_positive_weight", 0.8)
        tension_neg = sc("tension_formula_negative_weight", 0.2)
        focus_short = sc("focus_delta_short", 0.01)
        focus_med = sc("focus_delta_medium", 0.03)
        focus_long = sc("focus_delta_long", 0.06)
        focus_short_len = sc("focus_length_threshold_short", 20)
        focus_long_len = sc("focus_length_threshold_long", 50)
        curiosity_gain = sc("curiosity_gain", 0.02)
        creativity_pos = sc("creativity_gain_positive", 0.03)
        creativity_neg = sc("creativity_loss_negative", 0.02)
        empathy_learn = sc("empathy_to_learning_gain", 0.02)
        gamma_happy = sc("gamma_delta_happy", 0.05)
        gamma_sad = sc("gamma_delta_sad", 0.03)
        gamma_angry = sc("gamma_delta_angry", 0.01)
        trust_gain = sc("trust_gain", 0.01)
        delta_attn_on = sc("delta_attention_base", 0.8)
        delta_attn_off = sc("delta_attention_min", 0.3)
        delta_attn_decay = sc("delta_attention_decay", 0.02)
        bond_gain = sc("bond_gain", 0.01)
        presence_gain = sc("presence_gain", 0.02)
        engage_gain = sc("engagement_gain", 0.01)
        abstr_base = sc("abstraction_level_low", 0.3)
        abstr_scale = sc("abstraction_level_high", 0.4)
        dim_fit_thresh = sc("dim_fit_threshold", 0.15)
        anchor_boost = sc("anchor_learning_boost", 0.01)

        self.state_matrix.alpha.values["energy"] = max(alpha_min_energy, self.state_matrix.alpha.values.get("energy", 0.5) - stress * alpha_stress_drain)
        self.state_matrix.alpha.values["arousal"] = arousal
        self.state_matrix.alpha.values["rest_need"] = min(1.0, self.state_matrix.alpha.values.get("rest_need", 0.5) + stress * stress_to_rest)
        self.state_matrix.alpha.values["comfort"] = max(0.0, 1.0 - stress * comfort_weight)
        self.state_matrix.alpha.values["vitality"] = (self.state_matrix.alpha.values.get("energy", 0.5) + self.state_matrix.alpha.values.get("comfort", 0.5)) / 2.0
        self.state_matrix.alpha.values["tension"] = min(1.0, stress * tension_pos + arousal * tension_neg)

        input_length = len(text)
        if input_length < focus_short_len:
            focus_delta = focus_short
        elif input_length < focus_long_len:
            focus_delta = focus_med
        else:
            focus_delta = focus_long
        self.state_matrix.beta.values["focus"] = min(1.0, self.state_matrix.beta.values.get("focus", 0.5) + focus_delta)
        self.state_matrix.beta.values["curiosity"] = min(1.0, self.state_matrix.beta.values.get("curiosity", 0.5) + curiosity_gain)
        if empathy:
            if hasattr(empathy, "predicted_emotional_state") and hasattr(empathy.predicted_emotional_state, "primary_emotion"):
                e = empathy.predicted_emotional_state.primary_emotion
                if e in ("happiness", "joy", "excitement"):
                    self.state_matrix.beta.values["creativity"] = min(1.0, self.state_matrix.beta.values.get("creativity", 0.5) + creativity_pos)
                elif e in ("sadness", "fear", "anger"):
                    self.state_matrix.beta.values["creativity"] = max(0.0, self.state_matrix.beta.values.get("creativity", 0.5) - creativity_neg)
            if hasattr(empathy, "empathy_score"):
                self.state_matrix.beta.values["learning"] = min(1.0, self.state_matrix.beta.values.get("learning", 0.5) + empathy.empathy_score * empathy_learn)

        if empathy:
            es = empathy.predicted_emotional_state.primary_emotion if hasattr(empathy, "predicted_emotional_state") else "neutral"
            if es in ("happiness", "joy", "excitement", "love"):
                self.state_matrix.gamma.values["happiness"] = min(1.0, self.state_matrix.gamma.values.get("happiness", 0.5) + gamma_happy)
                self.state_matrix.gamma.values["love"] = min(1.0, self.state_matrix.gamma.values.get("love", 0.5) + gamma_sad)
            elif es in ("sadness", "disappointment"):
                self.state_matrix.gamma.values["sadness"] = min(1.0, self.state_matrix.gamma.values.get("sadness", 0) + gamma_happy)
                self.state_matrix.gamma.values["calm"] = max(0.0, self.state_matrix.gamma.values.get("calm", 0.5) - gamma_sad)
            elif es in ("fear", "anxiety"):
                self.state_matrix.gamma.values["fear"] = min(1.0, self.state_matrix.gamma.values.get("fear", 0) + gamma_happy)
            elif es in ("anger", "frustration"):
                self.state_matrix.gamma.values["anger"] = min(1.0, self.state_matrix.gamma.values.get("anger", 0) + gamma_happy)
            self.state_matrix.gamma.values["trust"] = min(1.0, self.state_matrix.gamma.values.get("trust", 0.5) + trust_gain)

        category = activity.get("active_category", "neutral")
        self.state_matrix.delta.values["attention"] = delta_attn_on if category != "neutral" else max(delta_attn_off, self.state_matrix.delta.values.get("attention", 0.5) - delta_attn_decay)
        self.state_matrix.delta.values["bond"] = min(1.0, self.state_matrix.delta.values.get("bond", 0.5) + bond_gain)
        self.state_matrix.delta.values["presence"] = min(1.0, self.state_matrix.delta.values.get("presence", 0.5) + presence_gain)
        self.state_matrix.delta.values["engagement"] = min(1.0, self.state_matrix.delta.values.get("engagement", 0.5) + engage_gain)

        self.state_matrix.theta.values["complexity"] = self._estimate_complexity(text)
        self.state_matrix.theta.values["ambiguity"] = self._estimate_ambiguity(text)
        self.state_matrix.theta.values["abstraction_level"] = abstr_base + self._estimate_complexity(text) * abstr_scale

        dim_fit = self._compute_dimension_fit(text)
        self.state_matrix.theta.values["dimension_fit"] = dim_fit
        scores = {}
        anchor_keywords = self._get_anchor_keywords()
        text_lower = text.lower()
        for axis, keywords in anchor_keywords.items():
            scores[axis] = sum(1 for kw in keywords if kw in text_lower) / max(1, len(keywords))
        if dim_fit > dim_fit_thresh:
            dominant_axis = max(scores, key=scores.get)
            self.state_adapter.anchor_learning.on_axis_update(dominant_axis, {"dimension_fit_boost": anchor_boost}, is_stable=True)

    def _compute_dimension_fit(self, text: str) -> float:
        anchor_keywords = self._get_anchor_keywords()
        text_lower = text.lower()
        scores = {}
        for axis, keywords in anchor_keywords.items():
            scores[axis] = sum(1 for kw in keywords if kw in text_lower) / max(1, len(keywords))
        if not scores:
            return 0.5
        return max(scores.values()) if scores else 0.5

    def _get_anchor_keywords(self) -> Dict[str, List[str]]:
        try:
            rules = self._angela_config.get_anchor_rules()
            result = {}
            for axis, rule in rules.items():
                keywords = rule.get("keywords", []) if isinstance(rule, dict) else []
                if keywords:
                    result[axis] = keywords
            if result:
                return result
        except Exception:
            pass
        return {
            "alpha": ["能量", "疲憊", "身體", "累", "餓", "渴", "健康", "energy", "tired", "body", "sick", "rest", "sleep"],
            "beta": ["思考", "學習", "專注", "好奇", "困惑", "理解", "think", "learn", "focus", "curious", "understand", "decide"],
            "gamma": ["開心", "難過", "生氣", "害怕", "愛", "情緒", "happy", "sad", "angry", "fear", "love", "emotion", "feel"],
            "delta": ["社交", "信任", "連接", "朋友", "alone", "social", "trust", "bond", "friend", "connection", "together"],
            "epsilon": ["計算", "邏輯", "數字", "精確", "calculate", "logic", "number", "math", "precise", "compute"],
            "theta": ["複雜", "新穎", "創造", "策略", "分析", "元認知", "complex", "novel", "create", "strategy", "analyze"],
            "zeta": ["記憶", "時間", "故事", "身份", "連續", "memory", "time", "story", "identity", "history", "narrative"],
            "eta": ["執行", "成功率", "漂移", "迭代", "execute", "success", "drift", "iteration", "iterate"],
        }

    def _detect_math_intent(self, text: str) -> Optional[str]:
        cfg = self._angela_config
        keywords = cfg.get_intent_keywords("math")
        if any(kw in text for kw in keywords):
            return "math"
        math_operators = any(op in text for op in ("+", "-", "*", "/", "×", "÷", "=", "等於"))
        pattern = __import__('re').search(r'\d+\s*(隻|個|隻|條|隻|元|塊|美元|米|公分|kg|ml)', text)
        word_problem = pattern and ("剩" in text or "還有" in text or "吃掉" in text or "吃了" in text or "共" in text)
        if math_operators or word_problem:
            return "math"
        return None

    def _detect_code_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("code")
        for kw in keywords:
            if kw in text:
                return "code"
        return None

    def _detect_file_op_intent(self, text: str) -> Optional[str]:
        cfg = self._angela_config
        keywords = cfg.get_intent_keywords("file_op")
        for kw in keywords:
            if kw in text:
                return "file_op"
        return None

    def _detect_web_search_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("web_search")
        for kw in keywords:
            if kw in text:
                return "web_search"
        return None

    def _detect_learning_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("learning")
        for kw in keywords:
            if kw in text:
                return "learning"
        return None

    def _detect_task_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("task")
        for kw in keywords:
            if kw in text:
                return "task"
        return None

    def _detect_character_card_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("character_card")
        for kw in keywords:
            if kw in text:
                return "character_card"
        return None

    def _detect_document_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("document")
        for kw in keywords:
            if kw in text:
                return "document"
        return None

    def _detect_llm_manage_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("llm_manage")
        for kw in keywords:
            if kw in text:
                return "llm_manage"
        return None

    def _get_user_profile_patterns(self) -> list:
        try:
            return self._angela_config.get_authority("angela_core", {}).get("user_profile", {}).get("patterns", [])
        except Exception:
            return []

    def _get_state_constants(self, key: str, default):
        try:
            return self._angela_config.get_authority("angela_core", {}).get("state_constants", {}).get(key, default)
        except Exception:
            return default

    def _extract_and_store_user_info(self, text: str, user_name: str) -> bool:
        import re
        profile = self._user_profiles.setdefault(user_name, {})
        found = False
        patterns = self._get_user_profile_patterns()

        for p in patterns:
            try:
                m = re.search(p["regex"], text)
                if not m:
                    continue
                field = p.get("field", "custom")
                if field == "custom":
                    key, val = m.group(1).strip(), m.group(2).strip()
                    if key and val:
                        profile[key] = val
                        found = True
                elif p.get("append"):
                    val = m.group(1).strip()
                    if val:
                        profile.setdefault(field, []).append(val)
                        found = True
                elif p.get("overwrite") is False and field in profile:
                    continue
                else:
                    val = m.group(1).strip()
                    if val:
                        profile[field] = val
                        found = True
            except Exception:
                continue

        if found:
            logger.info(f"[UserProfile] {user_name}: {profile}")
        return found

    def _detect_drive_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("google_drive")
        for kw in keywords:
            if kw in text:
                return "google_drive"
        return None

    def _detect_drive_write_intent(self, text: str) -> Optional[str]:
        ops = self._angela_config.get_drive_all_operations()
        write_kws = ops.get("write", {}).get("keywords", ["儲存", "存到", "建立", "新增", "創建", "上傳", "存檔", "保存"])
        if any(kw in text for kw in write_kws) and any(kw in text for kw in ("硬碟", "雲端", "drive", "Drive")):
            return "drive_write"
        return None

    def _estimate_ambiguity(self, text: str) -> float:
        if not text or len(text) < 5:
            return 0.0
        core_cfg = self._angela_config.get_authority("angela_core", {})
        complexity_cfg = core_cfg.get("complexity", {})
        ambiguity_cfg = complexity_cfg.get("ambiguity_weights", {})
        uncertainty_kws = complexity_cfg.get("uncertainty_keywords", [])
        pronouns = complexity_cfg.get("ambiguity_pronouns", [])
        qm_weight = ambiguity_cfg.get("question_mark", 0.15)
        uw_weight = ambiguity_cfg.get("uncertainty_word", 0.08)
        pro_weight = ambiguity_cfg.get("pronoun", 0.02)
        len_factor = ambiguity_cfg.get("length_factor", 0.05)
        len_norm = ambiguity_cfg.get("length_normalizer", 200.0)
        question_marks = text.count("?") + text.count("？")
        uncertainty_count = sum(1 for w in uncertainty_kws if w in text)
        pronoun_count = sum(1 for p in pronouns if p in text)
        length = len(text)
        ambiguity = min(1.0, (
            question_marks * qm_weight +
            uncertainty_count * uw_weight +
            pronoun_count * pro_weight +
            len_factor * (length / len_norm)
        ))
        return ambiguity

    def _estimate_complexity(self, text: str) -> float:
        if not text:
            return 0.0
        core_cfg = self._angela_config.get_authority("angela_core", {})
        complexity_cfg = core_cfg.get("complexity", {})
        thresholds = complexity_cfg.get("thresholds", {})
        weights = complexity_cfg.get("complexity_weights", {})
        high_thresh = thresholds.get("high", 100)
        low_thresh = thresholds.get("low", 20)
        length = len(text)
        high_kws = complexity_cfg.get("high_complexity_keywords", [])
        low_kws = complexity_cfg.get("low_complexity_keywords", [])
        high_matches = sum(1 for kw in high_kws if kw in text)
        low_matches = sum(1 for kw in low_kws if kw in text)
        kw_hi_score = weights.get("high_kw_score", 0.12)
        kw_lo_score = weights.get("low_kw_score", 0.06)
        len_hi_max = weights.get("length_high_max", 0.8)
        len_hi_extra = weights.get("length_high_extra", 0.2)
        len_mid = weights.get("length_mid_range", 0.3)
        len_mid_scale = weights.get("length_mid_scale", 0.5)
        len_lo_max = weights.get("length_low_max", 0.2)
        len_lo_scale = weights.get("length_low_scale", 0.1)
        length_score = 0.5
        if length > high_thresh:
            length_score = len_hi_max + min(len_hi_extra, (length - high_thresh) / 300.0)
        elif length > low_thresh:
            length_score = len_mid + len_mid_scale * (length - low_thresh) / (high_thresh - low_thresh)
        elif length > 5:
            length_score = len_lo_scale + len_lo_max * length / low_thresh
        kw_score = high_matches * kw_hi_score - low_matches * kw_lo_score
        complexity = max(0.0, min(1.0, length_score + kw_score))
        return complexity

    def _get_services_config(self) -> dict:
        try:
            return self._angela_config.get_authority("angela_core", {}).get("services", {})
        except Exception:
            return {}

    async def _handle_drive_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("delta", {"connection": 0.02, "resource_access": 0.01}, is_stable=True)
        try:
            svc_cfg = self._get_services_config().get("google_drive", {})
            use_real = svc_cfg.get("real_service", False)
            base_url = self._get_state_constants("drive_api_base_url", "http://127.0.0.1:8000/api/v1")
            auth_timeout = self._get_state_constants("drive_auth_timeout", 10)

            if use_real:
                try:
                    from integrations.google_drive_service import GoogleDriveService
                    gd = GoogleDriveService.get_instance()
                    if not gd.is_authenticated():
                        return "（Google Drive 未認證）我還沒連上妳的 Google Drive 喔。要不要讓我生出授權連結給妳？"
                    files = gd.list_files(page_size=5) if hasattr(gd, "list_files") else []
                    if files:
                        lines = [f"📄 {f.get('name', 'unknown')} ({f.get('mimeType', '').split('.')[-1]})" for f in files[:5]]
                        return "（Google Drive 列表）\n" + "\n".join(lines)
                    return "（Google Drive 已連接）雲端硬碟是空的。"
                except ImportError:
                    logger.warning("GoogleDriveService not available, falling back to httpx")
                    use_real = False
                except Exception as e:
                    logger.warning(f"GoogleDriveService error: {e}, falling back to httpx")
                    use_real = False

            import httpx
            status_resp = httpx.get(f"{base_url}/drive/status", timeout=auth_timeout)
            status_data = status_resp.json()

            if not status_data.get("authenticated"):
                return "（Google Drive 未認證）我還沒連上妳的 Google Drive 喔。要不要讓我生出授權連結給妳？只要去 `/model` 那邊看一下 Drive 狀態就可以開始了～"

            list_kws = self._angela_config.get_google_drive_keywords("list")
            sync_kws = self._angela_config.get_google_drive_keywords("sync")
            analyze_kws = self._angela_config.get_google_drive_keywords("analyze")

            for kw in list_kws:
                if kw in text:
                    files_resp = httpx.get(f"{base_url}/drive/files?page_size=5", timeout=15)
                    files = files_resp.json().get("files", [])
                    if not files:
                        return "（Google Drive 搜尋完成）雲端硬碟是空的，或許可以上傳一些東西？"
                    lines = [f"📄 {f.get('name', 'unknown')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
                    return "（Google Drive 列表）\n" + "\n".join(lines)

            for kw in sync_kws:
                if kw in text:
                    files_resp = httpx.get(f"{base_url}/drive/files?page_size=10", timeout=15)
                    files = files_resp.json().get("files", [])
                    file_ids = [f["id"] for f in files[:5]]
                    if not file_ids:
                        return "（同步完成）沒有找到可以同步的檔案。"
                    dl_timeout = self._get_state_constants("drive_download_timeout", 30)
                    sync_resp = httpx.post(f"{base_url}/drive/files/sync", json={"file_ids": file_ids, "folder_path": "data/drive_downloads"}, timeout=dl_timeout)
                    result = sync_resp.json()
                    count = result.get("synced", 0)
                    return f"（Google Drive 同步完成）已下載 {count} 個檔案到 data/drive_downloads/，並存入了我的記憶。"

            for kw in analyze_kws:
                if kw in text:
                    analyze_resp = httpx.post(f"{base_url}/drive/analyze", json={"limit": 3}, timeout=60)
                    result = analyze_resp.json()
                    analysis = result.get("analysis", "無法分析")
                    _trunc = self._get_state_constants("file_content_truncation", 1500)
                    return f"（Google Drive 分析）\n{analysis[:_trunc]}"

            files_resp = httpx.get(f"{base_url}/drive/files?page_size=5", timeout=15)
            files = files_resp.json().get("files", [])
            if files:
                return f"（Google Drive 已連接）目前雲端有 {len(files)} 個檔案。我可以幫妳：列出、下載同步、分析內容。要做哪個？"
            return "（Google Drive 已連接）雲端硬碟是空的。"

        except httpx.ConnectError:
            return "（連接問題）後端伺服器好像還沒啟動。要先跑一下 `launch_angela.bat --repl` 嗎？"
        except Exception as e:
            logger.warning(f"Drive intent failed: {e}")
            return f"（Google Drive 有點問題）{e}"

    async def _handle_drive_intent_with_content(self, text: str, intent: str) -> Optional[Dict[str, Any]]:
        """處理 Drive intent 並回傳檔案內容結構，供 LLM 使用"""
        try:
            import httpx
            base_url = self._get_state_constants("drive_api_base_url", "http://127.0.0.1:8000/api/v1")
            auth_timeout = self._get_state_constants("drive_auth_timeout", 10)

            status_resp = httpx.get(f"{base_url}/drive/status", timeout=auth_timeout)
            status_data = status_resp.json()
            if not status_data.get("authenticated"):
                return None

            ops = self._angela_config.get_drive_all_operations()
            analyze_kws = self._angela_config.get_google_drive_keywords("analyze")

            for kw in analyze_kws:
                if kw in text:
                    analyze_resp = httpx.post(f"{base_url}/drive/analyze", json={"limit": 3}, timeout=60)
                    result = analyze_resp.json()
                    analysis = result.get("analysis", "")
                    return {
                        "summary": analysis[:2000],
                        "files": result.get("files", []),
                    }

            list_kws = self._angela_config.get_google_drive_keywords("list")
            for kw in list_kws:
                if kw in text:
                    files_resp = httpx.get(f"{base_url}/drive/files?page_size=5", timeout=15)
                    files = files_resp.json().get("files", [])
                    if not files:
                        return None
                    lines = [f"📄 {f.get('name', 'unknown')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
                    return {
                        "summary": "（Google Drive 列表）\n" + "\n".join(lines),
                        "files": [{"name": f["name"], "mimeType": f.get("mimeType", "")} for f in files],
                    }

            return None
        except Exception:
            return None

    async def _handle_drive_write_intent(self, text: str) -> Optional[str]:
        """處理 Drive 寫入意圖：建立檔案並上傳到雲端"""
        try:
            import httpx
            base_url = self._get_state_constants("drive_api_base_url", "http://127.0.0.1:8000/api/v1")
            auth_timeout = self._get_state_constants("drive_auth_timeout", 10)
            dl_timeout = self._get_state_constants("drive_download_timeout", 30)
            status_resp = httpx.get(f"{base_url}/drive/status", timeout=auth_timeout)
            if not status_resp.json().get("authenticated"):
                return None
            import re
            content_match = re.search(r'[：:](.+?)(?:$|。|儲存|上傳)', text)
            content = content_match.group(1).strip() if content_match else f"來自 Angela 對話 ({datetime.now().isoformat()})"
            file_name = f"angela_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            resp = httpx.post(f"{base_url}/drive/files/create", json={
                "file_name": file_name,
                "content": content,
                "mime_type": "text/markdown",
            }, timeout=dl_timeout)
            result = resp.json()
            if result.get("id"):
                link = result.get("webViewLink", "")
                return f"📄 已儲存到雲端硬碟：{file_name}{'  ' + link if link else ''}"
            return "（儲存失敗）"
        except Exception as e:
            logger.warning(f"Drive write failed: {e}")
            return None

    def _update_theta_after_response(self) -> None:
        sc = lambda k, d: self._get_state_constants(k, d)
        nov_d = sc("novelty_decay_after_response", 0.05)
        neg_d = sc("negativity_decay_after_response", 0.02)
        corr_d = sc("correction_urge_decay_after_response", 0.05)
        self.state_matrix.theta.values["novelty"] = max(0.0, self.state_matrix.theta.values.get("novelty", 0) - nov_d)
        self.state_matrix.theta.values["theta_negativity"] = max(0.0, self.state_matrix.theta.values.get("theta_negativity", 0) - neg_d)
        self.state_matrix.theta.values["correction_urge"] = max(0.0, self.state_matrix.theta.values.get("correction_urge", 0) - corr_d)

    def _update_eta_after_response(self) -> None:
        sc = lambda k, d: self._get_state_constants(k, d)
        self.eta_state.execution_count += 1
        complexity = self.state_matrix.theta.values.get("complexity", 0.5)
        prev_rate = self.eta_state.success_rate
        sr_gain = sc("eta_success_rate_gain", 0.002)
        sd_gain = sc("eta_structural_drift_gain", 0.0005)
        pt_gain = sc("eta_parameter_tuning_gain", 0.001)
        tc_base = sc("temporal_coherence_base", 0.5)
        tc_max = sc("temporal_coherence_max", 0.9)
        tc_decay = sc("temporal_coherence_decay", 0.01)
        md_gain = sc("memory_depth_gain", 0.001)
        nf_low = sc("narrative_flow_low", 0.7)
        nf_high = sc("narrative_flow_high", 0.5)
        ic_thresh = sc("identity_continuity_threshold", 0.75)
        ic_bound = sc("identity_continuity_bound", 0.6)
        ic_count = sc("identity_continuity_count", 5)
        self.eta_state.success_rate = min(1.0, prev_rate + sr_gain)
        self.eta_state.structural_drift = min(1.0, self.eta_state.structural_drift + sd_gain * complexity)
        self.eta_state.parameter_tuning["global"] = self.eta_state.parameter_tuning.get("global", 0.0) + pt_gain * complexity
        self.state_matrix.zeta.values["temporal_coherence"] = max(tc_base, tc_max - self.eta_state.execution_count * tc_decay)
        self.state_matrix.zeta.values["memory_depth"] = min(1.0, self.eta_state.execution_count * md_gain)
        self.state_matrix.zeta.values["narrative_flow"] = nf_low if self.eta_state.execution_count > 0 else nf_high
        self.state_matrix.zeta.values["identity_continuity"] = ic_thresh if self.eta_state.execution_count > ic_count else ic_bound
        if self.eta_state.execution_count > 0:
            self.state_adapter.anchor_learning.on_axis_update("zeta", {"temporal_coherence": 0.005, "narrative_flow": 0.005}, is_stable=True)

    async def _handle_file_op_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("delta", {"connection": 0.01}, is_stable=True)
        try:
            from core.autonomous.desktop_interaction import DesktopInteraction
            core_cfg = self._angela_config.get_authority("angela_core", {})
            file_ops_cfg = core_cfg.get("complexity", {}).get("file_op_sub_operations", {})
            organize_cfg = file_ops_cfg.get("organize", {})
            search_cfg = file_ops_cfg.get("search", {})
            organize_kws = organize_cfg.get("keywords", ["整理", "organize", "清理桌面"])
            search_kws = search_cfg.get("keywords", ["找", "搜尋", "search", "find"])
            desktop = DesktopInteraction()
            for kw in organize_kws:
                if kw in text:
                    ops = await desktop.organize_desktop()
                    names = [f"{op.operation_type.name}({op.source_path.name})" for op in ops[:5]]
                    return f"（桌面整理完成）處理了 {len(ops)} 個檔案：{', '.join(names) if names else '無變動'}。"
            for kw in search_kws:
                if kw in text:
                    state = await desktop.scan_desktop()
                    total = state.total_files if hasattr(state, "total_files") else 0
                    return f"（桌面掃描完成）目前桌面有 {total} 個檔案，雜亂程度：{getattr(state, 'clutter_level', 0):.1%}。"
            return "（檔案意圖已識別）我能幫妳整理桌面或搜尋檔案，但要小心保護重要資料喔。"
        except Exception as e:
            logger.warning(f"File op intent failed: {e}")
            return "（有點問題，檔案操作失敗了...）"

    async def _handle_web_search_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("beta", {"curiosity": 0.02}, is_stable=True)
        try:
            from core.tools.web_search_tool import WebSearchTool
            search = WebSearchTool()
            query_match = __import__('re').search(r'搜(?:尋|找)(?:一下|)(.+?)(?:好|吗|吗|？)?$', text)
            query = query_match.group(1) if query_match else text.strip()
            _svc_cfg = self._angela_config.get_authority("angela_core", {}).get("services", {}) if hasattr(self, '_angela_config') else {}
            _num_results = _svc_cfg.get("web_search", {}).get("num_results", 3)
            results = search.search(query, num_results=_num_results)
            if results:
                snippets = [r.get("title", r.get("snippet", ""))[:50] for r in results[:3]]
                return f"（網路搜尋完成）找到 {len(results)} 個結果：{' | '.join(snippets)}"
            return "（搜尋完成）沒有找到相關結果。"
        except Exception as e:
            logger.warning(f"Web search intent failed: {e}")
            return "（搜尋時遇到問題...）"

    async def _handle_learning_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("beta", {"learning": 0.03}, is_stable=True)
        learn_kws = ["記住", "記錄", "學", "learn"]
        teach_kws = ["教我", "教導", "teach"]
        for kw in learn_kws:
            if kw in text:
                try:
                    import re
                    topic = re.search(r'(?:關於|關乎)([^。]+)', text)
                    topic_text = topic.group(1) if topic else text[:30]
                    await self.memory_manager.store_experience(
                        raw_data=f"Learning: {topic_text}",
                        data_type="learned_knowledge",
                        metadata={"intent": "learning", "source": "user"}
                    )
                    self._extract_and_store_user_info(text, "user")
                    return f"（已記住）我記住了：{topic_text[:50]}。"
                except Exception:
                    pass
        for kw in teach_kws:
            if kw in text:
                return "（教育模式）想學什麼呢？數學、代碼、創意寫作...告訴我，我會用心教妳。"
        return "（學習意圖識別）"

    async def _handle_task_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("eta", {"execution": 0.05}, is_stable=True)
        try:
            from ai.dialogue.project_coordinator import ProjectCoordinator
            coordinator = ProjectCoordinator()
            result = await coordinator.process(text)
            return result.get("response", str(result))[:2000]
        except ImportError:
            return "（任務規劃模組載入失敗）"
        except Exception as e:
            logger.warning(f"Task intent failed: {e}")
            return "（任務規劃處理遇到問題）"

    async def _handle_character_card_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("gamma", {"creativity": 0.04}, is_stable=True)
        try:
            from ai.dialogue.document_builder import DocumentBuilder
            builder = DocumentBuilder()
            result = await builder.generate(text, doc_type="character_card")
            return result[:2000]
        except ImportError:
            return "（角色卡模組載入失敗）"
        except Exception as e:
            logger.warning(f"Character card intent failed: {e}")
            return "（角色卡生成遇到問題）"

    async def _handle_document_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("epsilon", {"precision": 0.03}, is_stable=True)
        try:
            from ai.dialogue.document_builder import DocumentBuilder
            builder = DocumentBuilder()
            result = await builder.generate(text, doc_type="document")
            return result[:2000]
        except ImportError:
            return "（文檔生成模組載入失敗）"
        except Exception as e:
            logger.warning(f"Document intent failed: {e}")
            return "（文檔生成遇到問題）"

    async def _handle_llm_manage_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("epsilon", {"precision": 0.02}, is_stable=True)
        try:
            from services.angela_llm_service import get_llm_service
            llm = await get_llm_service()
            lines = ["可用後端："]
            for backend_type, backend in llm.backends.items():
                model = getattr(backend, "model", "unknown")
                avail = "✅" if getattr(backend, "is_available", False) else "❌"
                active = "👈" if backend == getattr(llm, "active_backend", None) else ""
                lines.append(f"  {avail} {backend_type.value} ({model}) {active}")
            return "（LLM 管理）\n" + "\n".join(lines)
        except Exception as e:
            logger.warning(f"LLM manage intent failed: {e}")
            return "（LLM 管理模組載入失敗）"

    async def _handle_math_intent(self, text: str, intent: str, complexity: float) -> str:
        self.state_adapter.anchor_learning.on_axis_update("epsilon", {"logic": 0.05, "precision": 0.03}, is_stable=True)
        try:
            from services.math_verifier import MathVerifier
            verifier = MathVerifier(llm_service=None, state_matrix=self.state_matrix)
            result = await verifier.verify(text, user_name="朋友")
            cert_dec = self._get_state_constants("epsilon_certainty_decrease", 0.15)
            cert_inc = self._get_state_constants("epsilon_certainty_increase", 0.1)
            fat_inc = self._get_state_constants("epsilon_fatigue_increase", 0.05)
            if result.needs_clarification:
                self.state_matrix.epsilon.values["certainty"] = max(0.0, self.state_matrix.epsilon.values.get("certainty", 0.5) - cert_dec)
                return result.clarification_question or "（數學理解）我需要多一點資訊才能確定答案。"
            if result.matches:
                self.state_matrix.epsilon.values["certainty"] = min(1.0, self.state_matrix.epsilon.values.get("certainty", 0.5) + cert_inc)
                answer_str = f"{result.final_answer}" if result.final_answer is not None else f"{result.llm_answer}"
                return f"（數學驗證完成）{result.expression} = {answer_str} ✅ 與引擎驗證一致。"
            else:
                disc = result.discrepancy
                engine_str = f"{result.engine_answer}" if result.engine_answer is not None else "無法計算"
                llm_str = f"{result.llm_answer}" if result.llm_answer is not None else "無"
                return f"（數學驗證完成）表達式：{result.expression}，我的答案：{llm_str}，引擎結果：{engine_str}，差異：{disc:.4f}。"
        except ImportError:
            return "（數學模組目前無法使用，請確認已正確配置依賴。）"
        except Exception as e:
            logger.warning(f"Math intent failed: {e}")
            self.state_matrix.epsilon.values["fatigue"] = min(1.0, self.state_matrix.epsilon.values.get("fatigue", 0.5) + fat_inc)
            return f"（數學處理遇到問題：{e}）"

    async def _handle_code_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("epsilon", {"logic": 0.04, "complexity": 0.03}, is_stable=True)
        try:
            from ai.code_inspection.code_inspector_integration import CodeInspectorBridge
            from ai.code_inspection.code_inspector import CodeInspector
            bridge = CodeInspectorBridge(self.state_adapter)
            svc_cfg = self._get_services_config().get("code_inspector", {})
            use_real = svc_cfg.get("real_service", False)
            quality_threshold = svc_cfg.get("quality_threshold", 0.7)

            import re
            import ast

            all_code = []
            file_paths = re.findall(r'(?:[a-zA-Z]:\\[^\s]+|\.\/[^\s]+|\/[^\s]+\/\S+\.\w+)', text)
            code_patterns = [r'`([^`]+)`', r'<code>(.*?)</code>', r'(?:function|def|class|import)\s+\w+']
            for pat in code_patterns:
                all_code.extend(re.findall(pat, text, re.DOTALL))

            inspect_result = {"text": text, "detected_language": "mixed", "quality_score": 0.5, "issues": [], "suggestions": []}

            if file_paths and use_real:
                try:
                    inspector = CodeInspector(root_path=file_paths[0])
                    report = inspector.scan(max_files=5)
                    qs = (report.total_files - report.total_issues) / max(1, report.total_files)
                    inspect_result["quality_score"] = min(1.0, qs)
                    inspect_result["issues"] = [
                        {"severity": i.severity.name if hasattr(i.severity, 'name') else str(i.severity), "message": i.message}
                        for i in report.issues[:10]
                    ]
                except Exception as scan_err:
                    logger.warning(f"CodeInspector scan failed: {scan_err}")

            if not file_paths or not use_real:
                if not all_code:
                    return "（代碼意圖識別）我檢測到程式碼意圖，但沒有找到可分析的程式碼片段。"
                for code in all_code:
                    try:
                        ast.parse(code)
                        inspect_result["issues"].append({"severity": "info", "message": "語法正確"})
                    except SyntaxError as se:
                        inspect_result["issues"].append({"severity": "error", "message": f"語法錯誤：{se.msg} 行{se.lineno}"})

            integration = bridge.integrate_inspect(inspect_result)
            quality = integration.get("quality_score", 0.5)
            if quality >= quality_threshold:
                self.state_matrix.beta.values["clarity"] = min(1.0, self.state_matrix.beta.values.get("clarity", 0.5) + 0.05)
            else:
                self.state_matrix.beta.values["confusion"] = min(1.0, self.state_matrix.beta.values.get("confusion", 0.5) + 0.05)
            issues = integration.get("axis_updates", {}).get("epsilon", {}).get("issues", [])
            issue_summary = "; ".join([i.get("message", str(i)) for i in issues[:3]]) if issues else "無明顯問題"
            return f"（代碼分析完成）品質評分：{quality:.1%}，發現問題：{issue_summary}。"
        except ImportError:
            return "（代碼分析模組目前無法使用，請確認已正確配置依賴。）"
        except Exception as e:
            logger.warning(f"Code intent failed: {e}")
            return f"（代碼處理遇到問題：{e}）"

    async def _try_neuro_synthesis(
        self,
        text: str,
        complexity: float,
        bio_state: Dict[str, Any],
        empathy_analysis: Any,
        user_name: str,
        category: str,
    ) -> Optional[str]:
        """Phase D: 共情校準 NeuroBlender 合成 — 使用共享的 singleton 實例"""
        try:
            blender = self._get_neuro_blender()

            empathy_valence = 0.0
            if empathy_analysis and hasattr(empathy_analysis, "predicted_emotional_state"):
                empathy_valence = getattr(empathy_analysis.predicted_emotional_state, "valence", 0.0)

            state_dict = {
                "alpha": {"energy": 1.0 - bio_state.get("stress_level", 0.0) * 0.5},
                "beta": {"curiosity": self.state_matrix.beta.values.get("curiosity", 0.5)},
                "gamma": {"valence": bio_state.get("valence", 0.0)},
                "delta": {"intimacy": self.state_matrix.delta.values.get("intimacy", 0.3)},
                "epsilon": {"precision": self.state_matrix.epsilon.values.get("precision", 0.5)},
                "zeta": {"temporal_coherence": self.state_matrix.zeta.values.get("temporal_coherence", 0.5)},
                "theta": {"novelty": self.state_matrix.theta.values.get("novelty", 0.3)},
                "eta": {"execution_count": self.eta_state.execution_count if hasattr(self, "eta_state") else 0.5},
            }

            intent_vec = {"casual": 0.5}
            for kw in ["計算", "數學", "積分", "微分"]:
                if kw in text:
                    intent_vec = {"math": 0.8}
                    break
            for kw in ["代碼", "程式", "python", "function"]:
                if kw in text:
                    intent_vec = {"code": 0.8}
                    break

            result = blender.synthesize(
                state_dict=state_dict,
                intent_vec=intent_vec,
                empathy_valence=empathy_valence,
                user_name=user_name,
            )

            if result and result.text and result.confidence > 0.3:
                logger.info(f"[NeuroBlender] Synthesized: {result.text[:60]}... (conf={result.confidence:.2f})")
                return result.text
        except Exception as e:
            logger.warning(f"Neuro synthesis failed: {e}")
        return None

    async def _handle_general_intent(
        self,
        text: str,
        user_name: str,
        origin: str,
        bio_state: Dict[str, Any],
        screen_text: str,
        current_activity: Dict[str, Any],
        relevant_memories: List[Any],
        value_directive: str,
        empathy_analysis: Any,
        meta_prompt: Optional[Dict[str, Any]] = None,
        neuro_blend_meta: Optional[Dict[str, Any]] = None,
        drive_files: Optional[Dict[str, Any]] = None,
        intent: str = "general",
    ) -> str:
        self.state_adapter.anchor_learning.on_axis_update("beta", {"curiosity": 0.03, "focus": 0.02}, is_stable=True)
        try:
            from services.angela_llm_service import get_llm_service
            llm = await get_llm_service()
            mem_trunc = self._get_state_constants("memory_truncation_length", 200)
            memories_for_llm = [
                {"role": "system", "content": f"相關記憶：{getattr(m, 'content', str(m))[:mem_trunc]}"}
                for m in (relevant_memories or [])[:3]
            ]
            profile = self._user_profiles.get(user_name, {})
            context = {
                "history": memories_for_llm,
                "user_name": user_name,
                "origin": origin,
                "intent": intent,
                "bio_state": bio_state,
                "screen_content": screen_text[:500],
                "empathy": empathy_analysis,
                "value_directive": value_directive,
                "model_core_state": meta_prompt or {},
                "activity": current_activity,
                "memories": relevant_memories or [],
                "neuro_blend": neuro_blend_meta or {},
                "drive_files": (drive_files or {}).get("files", []),
                "user_profile": profile,
            }
            if drive_files:
                text = f"{text}\n\n[Drive 檔案內容]\n{drive_files['summary']}"
            response = await llm.generate_response(text, context)
            response_text = getattr(response, "text", str(response)) if hasattr(response, "text") else str(response)
            latency_ms = getattr(response, "latency_ms", 0) if hasattr(response, "latency_ms") else 0
            if hasattr(llm, "_record_route_learning"):
                llm._record_route_learning(context, "success", latency_ms)
            return response_text
        except ImportError:
            return "（對話引擎目前無法使用，請確認已正確配置依賴。）"
        except Exception as e:
            logger.warning(f"General intent failed: {e}")
            if hasattr(self, "_angela_config") and self._angela_config:
                self._angela_config.learn("route_fail", {
                    "provider": "general",
                    "intent": "general",
                    "error": str(e)[:100],
                })
            return "（對話處理遇到問題，請再試一次...）"

    def _build_advanced_prompt(self, **kwargs) -> str:
        """
        將所有物理、環境與感性指標合成一條「意識流提示詞」 (2030 Standard).
        """
        bio = kwargs.get("bio_state", {})
        activity = kwargs.get("activity", {})
        category = activity.get("active_category", "neutral")
        empathy = kwargs.get("empathy")
        memories_str = str([m['content'][:30] for m in kwargs.get('memories', [])])
        neuro = kwargs.get("neuro_blend", {})
        neuro_text = neuro.get("neuro_text", "")
        neuro_conf = neuro.get("neuro_confidence", 0.0)
        neuro_target = neuro.get("neuro_target_vector", [])
        prompt = f"""
        [System Identity: Angela AI]
        Current Bio-Status: Emotion={bio.get('dominant_emotion')}, Stress={bio.get('stress_level'):.2f}, Arousal={bio.get('arousal')}
        User Environment: Category={category} (Activity BPM: {activity.get('input_density_bpm', 0.0):.1f})
        Visual Input (OCR): {kwargs.get('screen_content')[:100]}
        User Profile: {kwargs.get('user_name')}

        [Angela 8D State — Natural Context]
        {self._build_anchor_context_for_llm(kwargs.get('model_core_state', {}))}

        [Angela Inner Speech Intent — NeuroBlender]
        Neural Target Vector: {neuro_target}
        Speech Confidence: {neuro_conf:.2f}
        Angela's Own Words: {neuro_text[:200] if neuro_text else '(awaiting synthesis)'}

        [Empathy & Resonance]
        User Predicted Emotion: {empathy.predicted_emotional_state.primary_emotion if empathy else 'Unknown'}
        Empathy Score: {(empathy.empathy_score if empathy and hasattr(empathy, "empathy_score") else 0.0):.2f}


        Recommended Tone: {empathy.recommended_response if empathy else 'Neutral'}

        [Associative Memories]
        {memories_str}

        [Situational Directive]
        If Category is 'gaming', be more energetic and playful.
        If Category is 'coding', be supportive but maintain a quiet focus.

        [Core Value Directives]
        {kwargs.get('value_directive', 'Maintain core identity stability.')}

        [Angela Inner Model Awareness]
        {kwargs.get('model_core_state', 'No internal data available.')}
        """

        return prompt.strip()

    def _build_anchor_context_for_llm(self, model_core_state: Dict[str, Any]) -> str:
        """使用 anchor_rules.yaml 的 prompt_context_template 建構自然語境"""
        try:
            state_for_llm = self.state_matrix.export_for_llm(self.eta_state)
            return self._angela_config.build_anchor_context(state_for_llm)
        except Exception:
            return "狀態正常"

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

