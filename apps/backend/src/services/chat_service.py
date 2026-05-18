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

        from core.config_loader import get_angela_config
        self._angela_config = get_angela_config()

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

        file_op_intent = self._detect_file_op_intent(sanitized_message)
        if file_op_intent:
            response = await self._handle_file_op_intent(sanitized_message, file_op_intent)
        drive_intent = self._detect_drive_intent(sanitized_message)
        if drive_intent:
            response = await self._handle_drive_intent(sanitized_message, drive_intent)
        web_search_intent = self._detect_web_search_intent(sanitized_message)
        if web_search_intent:
            response = await self._handle_web_search_intent(sanitized_message, web_search_intent)
        if not (file_op_intent or drive_intent or web_search_intent):
            learning_intent = self._detect_learning_intent(sanitized_message)
            if learning_intent:
                response = await self._handle_learning_intent(sanitized_message, learning_intent)
            elif math_intent:
                response = await self._handle_math_intent(sanitized_message, math_intent, complexity)
            elif code_intent:
                response = await self._handle_code_intent(sanitized_message, code_intent)
            else:
                response = await self._handle_general_intent(
                    sanitized_message, user_name, origin, bio_state, screen_text,
                    current_activity, relevant_memories, value_directive, empathy_analysis,
                    meta_prompt=self.state_matrix.export_for_llm(self.state_adapter.eta),
                )

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

        await self._record_learning_event(sanitized_message, response, complexity)

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
        for name, detector in [
            ("math", self._detect_math_intent),
            ("code", self._detect_code_intent),
            ("file_op", self._detect_file_op_intent),
            ("google_drive", self._detect_drive_intent),
            ("web_search", self._detect_web_search_intent),
            ("learning", self._detect_learning_intent),
        ]:
            if detector(text):
                return name
        return "general"

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
        scores = {}
        anchor_keywords = {
            "alpha": ["能量", "疲憊", "身體", "累", "餓", "渴", "健康", "energy", "tired", "body", "sick", "rest", "sleep"],
            "beta": ["思考", "學習", "專注", "好奇", "困惑", "理解", "think", "learn", "focus", "curious", "understand", "decide"],
            "gamma": ["開心", "難過", "生氣", "害怕", "愛", "情緒", "happy", "sad", "angry", "fear", "love", "emotion", "feel"],
            "delta": ["社交", "信任", "連接", "朋友", "alone", "social", "trust", "bond", "friend", "connection", "together"],
            "epsilon": ["計算", "邏輯", "數字", "精確", "calculate", "logic", "number", "math", "precise", "compute"],
            "theta": ["複雜", "新穎", "創造", "策略", "分析", "元認知", "complex", "novel", "create", "strategy", "analyze"],
            "zeta": ["記憶", "時間", "故事", "身份", "連續", "memory", "time", "story", "identity", "history", "narrative"],
            "eta": ["執行", "成功率", "漂移", "迭代", "execute", "success", "drift", "iteration", "iterate"],
        }
        text_lower = text.lower()
        for axis, keywords in anchor_keywords.items():
            scores[axis] = sum(1 for kw in keywords if kw in text_lower) / max(1, len(keywords))
        if dim_fit > 0.15:
            dominant_axis = max(scores, key=scores.get)
            self.state_adapter.anchor_learning.on_axis_update(dominant_axis, {"dimension_fit_boost": 0.01}, is_stable=True)

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

    def _detect_drive_intent(self, text: str) -> Optional[str]:
        keywords = self._angela_config.get_intent_keywords("google_drive")
        for kw in keywords:
            if kw in text:
                return "google_drive"
        return None

    async def _handle_drive_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("delta", {"connection": 0.02, "resource_access": 0.01}, is_stable=True)
        try:
            import httpx
            base_url = "http://127.0.0.1:8000/api/v1"

            status_resp = httpx.get(f"{base_url}/drive/status", timeout=10)
            status_data = status_resp.json()

            if not status_data.get("authenticated"):
                return "（Google Drive 未認證）我還沒連上妳的 Google Drive 喔。要不要讓我生出授權連結給妳？只要去 `/model` 那邊看一下 Drive 狀態就可以開始了～"

            ops = self._angela_config.get_drive_all_operations()
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
                    sync_resp = httpx.post(f"{base_url}/drive/files/sync", json={"file_ids": file_ids, "folder_path": "data/drive_downloads"}, timeout=30)
                    result = sync_resp.json()
                    count = result.get("synced", 0)
                    return f"（Google Drive 同步完成）已下載 {count} 個檔案到 data/drive_downloads/，並存入了我的記憶。"

            for kw in analyze_kws:
                if kw in text:
                    analyze_resp = httpx.post(f"{base_url}/drive/analyze", json={"limit": 3}, timeout=60)
                    result = analyze_resp.json()
                    analysis = result.get("analysis", "無法分析")
                    return f"（Google Drive 分析）\n{analysis[:1000]}"

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

    async def _handle_file_op_intent(self, text: str, intent: str) -> str:
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
                self.state_adapter.anchor_learning.on_axis_update("epsilon", {"logic": 0.03, "task_completion": 0.02}, is_stable=True)
                return f"（代碼解析完成）函數：{funcs}，類：{classes}，行數：{lines}。ε 複雜度已更新。"
            except SyntaxError as se:
                self.state_matrix.beta.values["confusion"] = min(1.0, self.state_matrix.beta.values.get("confusion", 0) + 0.1)
                self.state_adapter.anchor_learning.on_axis_update("epsilon", {"fatigue": 0.03}, is_stable=False)
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
        if self.eta_state.execution_count > 0:
            self.state_adapter.anchor_learning.on_axis_update("zeta", {"temporal_coherence": 0.005, "narrative_flow": 0.005}, is_stable=True)

    async def _handle_file_op_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("delta", {"connection": 0.01}, is_stable=True)
        try:
            from core.autonomous.desktop_interaction import DesktopInteraction
            desktop = DesktopInteraction()
            organize_kws = ["整理", "organize", "清理桌面"]
            search_kws = ["找", "搜尋", "search", "find"]
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
            results = search.search(query, num_results=3)
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
                    return f"（已記住）我記住了：{topic_text[:50]}。"
                except Exception:
                    pass
        for kw in teach_kws:
            if kw in text:
                return "（教育模式）想學什麼呢？數學、代碼、創意寫作...告訴我，我會用心教妳。"
        return "（學習意圖識別）"

    def _build_advanced_prompt(self, **kwargs) -> str:
        """
        將所有物理、環境與感性指標合成一條「意識流提示詞」 (2030 Standard).
        """
        bio = kwargs.get("bio_state", {})
        activity = kwargs.get("activity", {})
        category = activity.get("active_category", "neutral")
        empathy = kwargs.get("empathy")
        memories_str = str([m['content'][:30] for m in kwargs.get('memories', [])])
        prompt = f"""
        [System Identity: Angela AI]
        Current Bio-Status: Emotion={bio.get('dominant_emotion')}, Stress={bio.get('stress_level'):.2f}, Arousal={bio.get('arousal')}
        User Environment: Category={category} (Activity BPM: {activity.get('input_density_bpm', 0.0):.1f})
        Visual Input (OCR): {kwargs.get('screen_content')[:100]}
        User Profile: {kwargs.get('user_name')}

        [Angela 8D State — Natural Context]
        {self._build_anchor_context_for_llm(kwargs.get('model_core_state', {}))}

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

