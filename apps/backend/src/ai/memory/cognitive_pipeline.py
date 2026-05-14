"""
Angela Unified Cognitive Pipeline v6.2.1 - 統一認知管線
=====================================================

核心流程：axis-first pathfinding + attractor hit + θ meta-allocation + code inspection
  1. 解析用戶輸入 → 定位當前狀態點 (αβγδεθ)
  2. θ (Meta-Cognitive) 分析輸入 → 決定分配方式（assign/composite/create/defer）
  3. MathRippleEngine 分析是否含數學運算
  4. 計算跨軸漣漪，更新 ε 維度
  5. GradientField 計算梯度，定位最近的吸引子
  6. 沿梯度導航，觸發行為輸出
  7. 觸發 epsilon-influence → γ 情緒漣漪
  8. [v6.2.1] CodeInspector 原生代碼檢查（0 LLM）

θ 軸職責：
  - 分析輸入與現有軸的語義相似度
  - 決定：高匹配→分配、模糊→組合、高新穎→創建、懸決→緩存
  - 追蹤 buffer_tracking，累積足够則觸發 creation_urge → 自動創建新軸

效率：5步 × 6維 ≈ 30億次操作
     vs LLM 576層 × 12288維 ≈ 2.1萬億次

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Tuple, Any

try:
    from core.autonomous.state_matrix import AllocateDecision
except ImportError:
    class AllocateDecision:
        def __init__(self, action="", **kwargs):
            self.action = action
            for k, v in kwargs.items():
                setattr(self, k, v)
        def to_dict(self):
            return {"action": self.action}

logger = logging.getLogger("angela_cognitive_pipeline")


class CognitivePipeline:
    """
    統一認知管線
    =============

    整合：
      - StateMatrix4D（6維狀態空間 αβγδεθ）
      - MathRippleEngine（數學-認知同構）
      - GradientField（記憶吸引子梯度場）
      - θ (Meta-Cognitive) 元認知分配決策
    """

    def __init__(
        self,
        state_matrix=None,
        attractor_field=None,
        math_ripple_engine=None,
        llm_service=None,
        code_inspector=None,
        root_path=None,
    ):
        self.state_matrix = state_matrix
        self.attractor_field = attractor_field
        self.math_engine = math_ripple_engine
        self.code_inspector = code_inspector
        self.root_path = root_path

        self._init_subsystems()

    def _init_subsystems(self):
        if not self.attractor_field:
            try:
                from ai.memory.attractor_field import GradientField
                self.attractor_field = GradientField()
            except ImportError:
                logger.warning("[CognitivePipeline] GradientField not available")
                self.attractor_field = None

        if not self.math_engine:
            try:
                from ai.memory.math_ripple_engine import MathRippleEngine
                self.math_engine = MathRippleEngine(self.state_matrix)
            except ImportError:
                logger.warning("[CognitivePipeline] MathRippleEngine not available")
                self.math_engine = None

        if not self.code_inspector and self.root_path:
            try:
                from ai.code_inspection import CodeInspectorInterface
                self.code_inspector = CodeInspectorInterface(self.root_path)
            except ImportError:
                logger.warning("[CognitivePipeline] CodeInspector not available")
                self.code_inspector = None

    def get_current_state(self) -> List[float]:
        """獲取當前狀態座標"""
        if not self.state_matrix:
            return [0.5] * 5

        return [
            self.state_matrix.alpha.values.get("energy", 0.5),
            self.state_matrix.beta.values.get("focus", 0.5),
            self.state_matrix.gamma.values.get("happiness", 0.5),
            self.state_matrix.delta.values.get("bond", 0.5),
            self.state_matrix.epsilon.values.get("certainty", 0.5),
        ]

    async def process(self, user_message: str, user_name: str = "朋友") -> Dict[str, Any]:
        """
        主處理流程（整合 θ 元認知軸）

        θ 決策流程：
          1. 解析用戶輸入為語義向量
          2. θ.meta_allocate 分析相似度 → 決策
          3. 執行決策（分配/組合/創建/緩存）
          4. MathRippleEngine 分析數學運算
          5. GradientField 導航到吸引子
          6. 生成回應

        Returns:
            {
                "response": str,
                "behavior": str,
                "tone": BehaviorTone,
                "state": List[float],
                "math_result": Optional[float],
                "ripples": List[RippleEffect],
                "navigation_steps": int,
                "triggered_attractor": str,
                "theta_decision": AllocateDecision,
                "theta_analysis": Dict,
            }
        """
        theta_decision = None
        theta_analysis = {}
        allocation_results = {}

        if self.state_matrix and hasattr(self.state_matrix, "theta"):
            try:
                label = self._extract_label(user_message)
                semantic_vector = self.state_matrix._text_to_vector(label, 32)
                theta_decision = self.state_matrix.meta_allocate(semantic_vector, label)
                allocation_results = self.state_matrix.execute_decision(theta_decision, semantic_vector)
                theta_analysis = self.state_matrix.get_theta_analysis()

                logger.info(f"θ [Pipeline] Decision: {theta_decision.action} | "
                            f"confidence={theta_decision.confidence:.2f} | "
                            f"reasoning: {theta_decision.reasoning}")
            except Exception as e:
                logger.warning(f"θ [Pipeline] Meta-allocate failed: {e}")

        current_state = self.get_current_state()

        math_result = None
        ripples = []
        cognitive_summary = ""

        if self.math_engine:
            math_analysis = self.math_engine.analyze_expression(user_message)
            math_result = math_analysis.get("result")
            ripples = math_analysis.get("ripples", [])
            cognitive_summary = math_analysis.get("cognitive_summary", "")

            if math_result is not None:
                logger.info(f"🧮 [Pipeline] Math: {user_message} = {math_result}")
                logger.info(f"   Ripple: {cognitive_summary}")

        if self.attractor_field:
            if ripples:
                if self.state_matrix:
                    for r in ripples:
                        self._apply_ripple_to_state(r)

            current_state = self.get_current_state()
            new_state, gradient_result = self.attractor_field.navigate(
                current_state, max_steps=5, dt=0.15
            )

            response = self._generate_response(
                user_message=user_message,
                gradient_result=gradient_result,
                math_result=math_result,
                cognitive_summary=cognitive_summary,
                user_name=user_name
            )

            return {
                "response": response,
                "behavior": gradient_result.blended_behavior,
                "tone": gradient_result.blended_tone.value,
                "state": new_state,
                "math_result": math_result,
                "ripples": ripples,
                "navigation_steps": gradient_result.navigation_steps,
                "gradient_strength": gradient_result.gradient_strength,
                "certainty": gradient_result.certainty,
                "triggered_attractor": gradient_result.nearest_attractors[0][0].description if gradient_result.nearest_attractors else "none",
                "cognitive_summary": cognitive_summary,
                "theta_decision": theta_decision.to_dict() if theta_decision else None,
                "theta_analysis": theta_analysis,
                "allocation_results": allocation_results,
            }

        return {
            "response": f"計算結果是 {math_result}。" if math_result else "我聽到了。",
            "behavior": "",
            "tone": "warm",
            "state": current_state,
            "math_result": math_result,
            "ripples": ripples,
            "navigation_steps": 0,
            "gradient_strength": 0.0,
            "certainty": 0.5,
            "triggered_attractor": "none",
            "cognitive_summary": cognitive_summary,
            "theta_decision": theta_decision.to_dict() if theta_decision else None,
            "theta_analysis": theta_analysis,
            "allocation_results": allocation_results,
        }

    def _apply_ripple_to_state(self, ripple: Dict[str, Any]):
        if not self.state_matrix:
            return

        if hasattr(self.state_matrix, "alpha"):
            arousal = ripple.get("alpha_arousal", 0.0)
            if arousal > 0:
                self.state_matrix.alpha.values["arousal"] = min(
                    1.0, self.state_matrix.alpha.values.get("arousal", 0.5) + arousal
                )

        if hasattr(self.state_matrix, "beta"):
            focus = ripple.get("beta_focus", 0.0)
            if focus > 0:
                self.state_matrix.beta.values["focus"] = min(
                    1.0, self.state_matrix.beta.values.get("focus", 0.5) + focus
                )

        if hasattr(self.state_matrix, "gamma"):
            excitement = ripple.get("gamma_excitement", 0.0)
            if excitement > 0:
                self.state_matrix.gamma.values["happiness"] = min(
                    1.0, self.state_matrix.gamma.values.get("happiness", 0.5) + excitement
                )

        if ripple.get("overload"):
            self._apply_cognitive_overload()
        if ripple.get("fear"):
            self._apply_division_fear()

    def _apply_cognitive_overload(self):
        if not self.state_matrix:
            return
        if hasattr(self.state_matrix, "beta"):
            self.state_matrix.beta.values["confusion"] = min(
                1.0, self.state_matrix.beta.values.get("confusion", 0.0) + 0.3
            )

    def _apply_division_fear(self):
        if not self.state_matrix:
            return
        if hasattr(self.state_matrix, "gamma"):
            self.state_matrix.gamma.values["fear"] = min(
                1.0, self.state_matrix.gamma.values.get("fear", 0.0) + 0.3
            )

    def _generate_response(
        self,
        user_message: str,
        gradient_result,
        math_result: Optional[float],
        cognitive_summary: str,
        user_name: str,
    ) -> str:
        """根據梯度結果生成回應"""

        if math_result is not None:
            if cognitive_summary and "過載" in cognitive_summary:
                return f"等等... 數字實在太大了（{math_result}），我需要緩一緩..."
            elif cognitive_summary and "恐懼" in cognitive_summary:
                return f"嗯... {math_result}... 這個結果讓我有點不安。"
            elif cognitive_summary and "趨近零" in cognitive_summary:
                return f"答案是 {math_result:.4f}... 幾乎什麼都沒有了。"

        tone = gradient_result.blended_tone.value
        attractor_desc = (
            gradient_result.nearest_attractors[0][0].description
            if gradient_result.nearest_attractors
            else ""
        )

        if math_result is not None:
            if gradient_result.certainty > 0.7:
                return f"計算結果是 {math_result}。（我的狀態很穩定）"
            else:
                return f"嗯... {math_result}... 我來確認一下。{gradient_result.blended_behavior}"

        if tone == "sympathetic":
            return f"{user_name}... {gradient_result.blended_behavior}"
        elif tone == "excited":
            return gradient_result.blended_behavior
        elif tone == "hesitant":
            return f"讓我想想... {gradient_result.blended_behavior}"
        elif tone == "curious":
            return f"{gradient_result.blended_behavior}"
        elif tone == "certain":
            return f"{gradient_result.blended_behavior}"
        else:
            return f"{gradient_result.blended_behavior}"

    def _extract_label(self, message: str) -> str:
        """从消息中提取关键词作为语义标签"""
        words = message.lower().split()
        keywords = []
        for w in words:
            clean = ''.join(c for c in w if c.isalnum())
            if len(clean) > 2:
                keywords.append(clean)
        return ' '.join(keywords[:8]) if keywords else message[:50]

    def query_attractors(self, current_state: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """查詢當前狀態最近的吸引子"""
        if not self.attractor_field:
            return []

        state = current_state or self.get_current_state()
        result = self.attractor_field.compute_gradient(state)

        return [
            {
                "description": a.description,
                "tags": a.tags,
                "tone": a.tone.value,
                "distance": d,
                "mass": a.mass,
                "behavior": a.behavior
            }
            for a, d in result.nearest_attractors
        ]

    def inspect_code(self, scope: str = "full") -> Dict[str, Any]:
        """執行代碼檢查（整合 CodeInspectorInterface）"""
        if not self.code_inspector:
            return {"error": "CodeInspector not initialized"}

        result = self.code_inspector.inspect(scope)
        return {
            "total_issues": result["total_issues"],
            "auto_fixable": result["auto_fixable"],
            "critical": result["critical"],
            "high": result["high"],
            "medium": result["medium"],
            "low": result["low"],
            "issues_summary": self._summarize_issues(result["report"].issues) if "report" in result else {},
        }

    def _summarize_issues(self, issues: List) -> Dict[str, int]:
        by_cat = {}
        for issue in issues:
            cat = getattr(issue, "category", "unknown").value if hasattr(getattr(issue, "category", None), "value") else str(getattr(issue, "category", "unknown"))
            by_cat[cat] = by_cat.get(cat, 0) + 1
        return by_cat

    def apply_auto_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """自動修復所有可修復的問題"""
        if not self.code_inspector:
            return {"error": "CodeInspector not initialized"}

        return self.code_inspector.fix_all_auto(dry_run)

    def learn_from_fix_feedback(
        self,
        issue_id: str,
        original_fix: str,
        feedback: str,
        accepted: bool,
        correction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """從修復反饋中學習"""
        if not self.code_inspector:
            return {"error": "CodeInspector not initialized"}

        return self.code_inspector.learn(issue_id, original_fix, feedback, accepted, correction)

    def get_inspector_status(self) -> Dict[str, Any]:
        """獲取代碼檢查系統狀態"""
        if not self.code_inspector:
            return {"error": "CodeInspector not initialized"}

        return self.code_inspector.get_status()