# =============================================================================
# ANGELA-MATRIX: L1-L6[小腦] γ [A] L3
# =============================================================================
# 職責: 小腦反射系統 (Tickle Reflex System).
# 維度: 物理維度 (γ) 的觸覺反射、快速回應與安全邊界。
# 設計: 配置驅動、雙層安全、Phase1(反射) + Phase2(LLM)
# =============================================================================

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from core.interfaces.service_registry import get_registry

logger = logging.getLogger(__name__)


class TickleReflexSystem:
    """
    小腦反射系統：處理搔癢觸發的雙層反射。

    Phase 1 (t < 50ms): 硬編反射 — 即時安全
    Phase 2 (t < 2000ms): LLM 生成 — 有意義回應

    安全邊界：
    - 敏感部位（chest/shoulders）祇觸發 comfort_seek
    - intense 模式（>= 0.8）限制輸出長度與類型
    - sustained 模式（> 5s）自動切換到安全回應
    """

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        from core.config_loader import get_angela_config
        self._cfg = get_angela_config()
        self._tickle = self._cfg.get_tickle_config()
        self._intensity_thresholds = self._tickle.get("intensity_thresholds", {})
        self._body_parts = self._tickle.get("body_parts", {})
        self._safety = self._tickle.get("safety", {})
        self._gamma_invasion = self._tickle.get("gamma_invasion", {})
        self._animations = self._tickle.get("animations", {})
        self._sensitive_parts = self._tickle.get("sensitive_parts", [])
        self._sensitive_fallback = self._tickle.get("sensitive_part_fallback", {})

        self._light_threshold = self._intensity_thresholds.get("light", 0.25)
        self._medium_threshold = self._intensity_thresholds.get("medium", 0.60)
        self._intense_threshold = self._intensity_thresholds.get("intense", 0.80)
        self._sustained_seconds = self._intensity_thresholds.get("sustained_seconds", 5.0)
        self._reflex_timeout_ms = self._safety.get("reflex_timeout_ms", 2000)
        self._max_llm_words = self._safety.get("max_llm_words", 20)
        self._output_modes = self._safety.get("output_modes", ["speak", "scream", "silence", "comfort_seek"])
        self._intense_allowed = self._safety.get("intense_allowed_types", ["short_scream", "plea", "no_stop", "comfort_request"])

        self._stimulus_history: Dict[str, Dict[str, Any]] = {}

        try:
            from core.autonomous.cerebellum_engine import CerebellumEngine
            self._cerebellum = CerebellumEngine()
        except Exception:
            self._cerebellum = None

        logger.info("[TickleReflex] Initialized. Body parts: %s, Sensitive: %s",
                    list(self._body_parts.keys()), self._sensitive_parts)

    def get_intensity_level(self, intensity: float) -> str:
        """根據強度值返回級別標籤"""
        if intensity >= self._intense_threshold:
            return "intense"
        elif intensity >= self._medium_threshold:
            return "medium"
        elif intensity >= self._light_threshold:
            return "light"
        return "none"

    async def trigger_tickles(
        self,
        body_part: str,
        intensity: float,
        duration_seconds: float = 0.0,
        origin: str = "Human",
        state_matrix: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        觸發搔癢反射。返回 Phase 1 + 可選 Phase 2 結果。

        Args:
            body_part: 觸發部位（如 "abdomen", "feet", "neck"）
            intensity: 強度值 0.0–1.0
            duration_seconds: 持續刺激時間（秒），0 表示一次性觸碰
            origin: 觸發來源（"Human" / "System"）
            state_matrix: 可選 StateMatrix4D 引用（用於 γ 軸更新）

        Returns:
            Phase 1: immediate_reflex (animation + expression)
            Phase 2: llm_response (if enabled and not sensitive part)
        """
        start_time = time.time()

        part_config = self._body_parts.get(body_part)
        sensitivity = 0.5
        reflex_type = "generic_twitch"
        allowed_responses = ["giggle", "laughing"]

        if part_config:
            sensitivity = part_config.get("sensitivity", 0.5)
            reflex_type = part_config.get("reflex_type", reflex_type)
            allowed_responses = part_config.get("allowed_responses", allowed_responses)
        else:
            part_config = {"sensitivity": 0.3, "reflex_type": "generic_twitch", "allowed_responses": ["giggle"]}

        effective_intensity = intensity * sensitivity
        intensity_level = self.get_intensity_level(effective_intensity)

        is_sensitive = body_part in self._sensitive_parts
        sustained = duration_seconds >= self._sustained_seconds

        self._update_stimulus_history(body_part, intensity, duration_seconds, origin)

        phase1_result = self._phase1_reflex(
            body_part, reflex_type, effective_intensity, intensity_level,
            is_sensitive, sustained, state_matrix
        )

        phase2_result = {"triggered": False, "response": None}
        if not is_sensitive and intensity_level != "none":
            phase2_result = await self._phase2_llm_response(
                body_part, effective_intensity, intensity_level,
                allowed_responses, sustained, start_time, state_matrix
            )

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "status": "completed",
            "body_part": body_part,
            "intensity": effective_intensity,
            "intensity_level": intensity_level,
            "is_sensitive": is_sensitive,
            "sustained": sustained,
            "phase1": phase1_result,
            "phase2": phase2_result,
            "elapsed_ms": round(elapsed_ms, 1),
            "origin": origin,
        }

    def _phase1_reflex(
        self,
        body_part: str,
        reflex_type: str,
        intensity: float,
        level: str,
        is_sensitive: bool,
        sustained: bool,
        state_matrix: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Phase 1: 即時反射（<50ms）

        規則：
        - intense (>=0.8) → scream / comfort_seek
        - sustained (>5s) → comfort_seek
        - sensitive part → comfort_seek
        - 正常 → giggle / laugh / squirm / flinch
        """
        if is_sensitive or sustained:
            output_mode = "comfort_seek"
        elif level == "intense":
            output_mode = self._safety.get("intense_output_mode", "scream")
        elif level == "medium":
            output_mode = "speak"
        else:
            output_mode = "speak"

        anim_config = self._animations.get(reflex_type, {})
        animation = {
            "motion_name": anim_config.get("motion_name", reflex_type),
            "duration_ms": anim_config.get("duration_ms", 150),
            "expression": anim_config.get("expression", "laughing"),
            "audio": anim_config.get("audio", "none"),
        }

        if state_matrix and (is_sensitive or sustained):
            gamma = getattr(state_matrix, "gamma", None)
            if gamma and hasattr(gamma, "values"):
                gamma.values["fear"] = min(1.0, gamma.values.get("fear", 0) + 0.1)
                gamma.values["trust"] = max(0.0, gamma.values.get("trust", 0.5) - 0.05)
                gamma.values["calm"] = max(0.0, gamma.values.get("calm", 0.5) - 0.08)
                logger.info("[TickleReflex] γ-axis invaded: fear+0.1, trust-0.05")

        return {
            "output_mode": output_mode,
            "animation": animation,
            "elapsed_ms": 10,
        }

    async def _phase2_llm_response(
        self,
        body_part: str,
        intensity: float,
        level: str,
        allowed_responses: List[str],
        sustained: bool,
        start_time: float,
        state_matrix: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Phase 2: LLM 回應（可配置超時）

        安全限制：
        - intense 模式：限制單詞數量、限制回應類型
        - sustained：自動 comfort_seek
        - 敏感部位：不做 LLM 回應
        """
        remaining_ms = self._reflex_timeout_ms - (time.time() - start_time) * 1000
        if remaining_ms <= 0:
            return {"triggered": False, "response": None, "reason": "timeout"}

        response_type = "normal"
        max_words = 50

        if level == "intense":
            response_type = "intense"
            max_words = self._max_llm_words
        elif sustained:
            response_type = "comfort_seek"
            max_words = 15

        prompt = self._build_reflex_prompt(
            body_part, intensity, level, allowed_responses,
            response_type, max_words, state_matrix
        )

        try:
            response_text = await self._call_llm(prompt, remaining_ms / 1000)
            try:
                from ai.security.ego_guard import EgoGuard
                ego = EgoGuard()
                dummy_phase1 = {"output_mode": response_type, "animation": {}}
                filtered, modified = ego.check_tickle_phase2(response_text, dummy_phase1)
                if modified:
                    response_text = filtered
            except Exception:
                pass
            return {
                "triggered": True,
                "response": response_text[:200],
                "response_type": response_type,
                "words_used": len(response_text.split()),
            }
        except asyncio.TimeoutError:
            return {"triggered": False, "response": None, "reason": "llm_timeout"}
        except Exception as e:
            logger.warning(f"[TickleReflex] LLM response failed: {e}")
            return {"triggered": False, "response": None, "reason": str(e)}

    def _build_reflex_prompt(
        self,
        body_part: str,
        intensity: float,
        level: str,
        allowed: List[str],
        response_type: str,
        max_words: int,
        state_matrix: Optional[Any],
    ) -> str:
        """建構反射回應提示詞"""
        part_cn = {"abdomen": "腹部", "feet": "腳底", "neck": "脖子",
                   "back": "背部", "sides": "腰部", "face": "臉", "hands": "手"}.get(body_part, body_part)

        allowed_str = "/".join(allowed) if allowed else "giggle/laughing"

        base = f"Angela 被觸碰了{part_cn}，強度={intensity:.1f}，級別={level}。"

        if response_type == "intense":
            base += f" 請用短句回應（最多{max_words}字），類型可選：{allowed_str}。"
        elif response_type == "comfort_seek":
            base += " 請用安慰/求饒短語回應（最多15字）。"
        else:
            base += f" 請用正常回應（最多{max_words}字），類型可選：{allowed_str}。"

        if state_matrix:
            try:
                gamma = state_matrix.gamma
                if hasattr(gamma, "values"):
                    trust = gamma.values.get("trust", 0.5)
                    fear = gamma.values.get("fear", 0)
                    if fear > 0.3:
                        base += f"（當前 γ 軸：恐懼={fear:.2f}，信任={trust:.2f}，考慮安撫）"
            except Exception:
                pass

        return base

    async def _call_llm(self, prompt: str, timeout_seconds: float) -> str:
        """呼叫 LLM 生成回應（超時保護）"""
        from services.angela_llm_service import get_llm_service
        llm = await get_llm_service()
        return await asyncio.wait_for(
            llm.generate_text(prompt, max_tokens=256, temperature=0.7),
            timeout=timeout_seconds,
        )

    def _update_stimulus_history(
        self, body_part: str, intensity: float, duration: float, origin: str
    ) -> None:
        """更新刺激歷史（用於 sustained 檢測）"""
        now = time.time()
        if body_part not in self._stimulus_history:
            self._stimulus_history[body_part] = {"last_time": 0.0, "total_duration": 0.0}

        entry = self._stimulus_history[body_part]
        if now - entry["last_time"] > self._sustained_seconds * 2:
            entry["total_duration"] = 0.0
        entry["total_duration"] += duration
        entry["last_time"] = now

    def get_reflex_config(self, body_part: str) -> Dict[str, Any]:
        """獲取部位反射配置"""
        return self._body_parts.get(body_part, {})

    def get_all_body_parts(self) -> List[str]:
        """獲取所有配置的身體部位"""
        return list(self._body_parts.keys())

    def get_sensitive_parts(self) -> List[str]:
        """獲取敏感部位列表"""
        return list(self._sensitive_parts)

    def is_sensitive(self, body_part: str) -> bool:
        """檢查是否為敏感部位"""
        return body_part in self._sensitive_parts

    def get_intensity_thresholds(self) -> Dict[str, float]:
        """獲取強度閾值"""
        return dict(self._intensity_thresholds)


_reflex_instance: Optional[TickleReflexSystem] = None


def get_reflex_system() -> TickleReflexSystem:
    """單例工廠"""
    global _reflex_instance
    if _reflex_instance is None:
        _reflex_instance = TickleReflexSystem()
        get_registry().register("tickle_reflex_system", _reflex_instance)
    return _reflex_instance