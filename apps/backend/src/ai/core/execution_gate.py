# =============================================================================
# ANGELA-MATRIX: L3-L4 [βδ] [A] L3
# =============================================================================
#
# 职责: 执行闸门 — 基于可逆性×影响度×明确度决定是否执行
# 维度: 认知维度 (β) 用于执行评估，精神维度 (δ) 用于意图理解
# 安全: 使用 Key A (后端控制)
# 成熟度: L3+ 等级才能理解执行门控逻辑
#
# =============================================================================

import re
from dataclasses import dataclass
from typing import Optional

from ai.core.query_classifier import _NEGATION_WORDS

# 可逆性分数表
REVERSIBILITY = {
    "read":     1.0,   # 读取类：完全可逆（没改变任何东西）
    "create":   0.9,   # 建立类：可逆（可删除）
    "modify":   0.6,   # 修改类：可逆但有成本
    "delete":   0.2,   # 删除类：不可逆
    "send":     0.1,   # 传送类：不可逆
    "system":   0.0,   # 系统类：不可逆且影响大
    "none":     1.0,   # 无操作
}


@dataclass
class GateDecision:
    """执行闸门决策"""
    action: str                    # "auto_execute" | "confirm_then_execute" | "reject"
    score: float                   # 执行分数
    handler: Optional[str] = None  # handler ID（auto_execute/confirm 时）
    reason: str = ""
    confirm_message: str = ""      # 确认讯息（confirm 时）
    impact_info: str = ""          # 影响说明（confirm 时）
    action_type: str = "none"      # 操作类型
    original_query: str = ""       # 原始查询（等确认后执行用）


class ExecutionGate:
    """执行闸门：基于可逆性×影响度×明确度决定是否执行"""

    AUTO_EXECUTE = 0.6
    CONFIRM_THRESHOLD = 0.2

    # Handler 映射
    HANDLER_MAP = {
        "file": "file_ops",
        "search": "web_search",
        "code": "code_exec",
        "execute": "code_exec",
        "system": "system_cmd",
        "task": "task_mgr",
        "vision": "vision",
    }

    def __init__(self, model_bus=None):
        self._model_bus = model_bus
        self._config = self._load_config()

    def _load_config(self):
        """Load execution gate config from JSON file."""
        import json
        import os
        config_path = os.path.join(os.path.dirname(__file__), "execution_gate_config.json")
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "scope_words": {"max_impact": ["全部", "所有", "整个", "all"], "min_impact": ["一个", "单一", "this"]},
                "clarity": {
                    "clear_verbs": ["search", "delete", "open", "run", "read", "write", "create", "edit"],
                    "vague_words": ["一下", "看看", "处理", "弄", "搞", "整", "试试"],
                },
                "confirm_messages": {"read": "读取", "create": "建立", "modify": "修改", "delete": "删除", "send": "传送", "system": "执行系统操作", "default": "执行操作"},
                "warnings": {"delete": "\n⚠️ 删除后无法复原。", "send": "\n⚠️ 传送后无法撤回。", "system": "\n⚠️ 系统操作可能影响其他程序。", "modify": "\n 修改会覆盖原始内容。"},
                "confirm_suffix": "\n确认后我会执行。",
                "no_handler_message": "你想要我做什么？可以更具體說明嗎？",
            }

    def decide(self, query_type: str, action_type: str, user_message: str,
               confidence: float, context: dict) -> GateDecision:
        """决定是否执行"""
        score = self._calculate_exec_score(action_type, user_message, query_type, confidence)

        # 否定词强制 reject
        if any(neg in user_message for neg in _NEGATION_WORDS):
            return GateDecision(
                action="reject", score=score,
                reason="negation_detected",
                original_query=user_message,
            )

        # 检查是否有 handler
        handler_id = self.HANDLER_MAP.get(query_type)

        # For knowledge/creative/greeting queries, skip confirmation and let LLM handle
        if query_type in ("knowledge", "creative", "greeting", "opinion"):
            return GateDecision(
                action="reject", score=score,
                reason=f"non_actionable_query_type_{query_type}",
                original_query=user_message,
            )

        if score >= self.AUTO_EXECUTE and handler_id:
            return GateDecision(
                action="auto_execute", score=score,
                handler=handler_id,
                action_type=action_type,
                reason=f"exec_score={score} >= {self.AUTO_EXECUTE}",
                original_query=user_message,
            )

        if score >= self.CONFIRM_THRESHOLD:
            if handler_id:
                return GateDecision(
                    action="confirm_then_execute", score=score,
                    handler=handler_id,
                    action_type=action_type,
                    reason=f"exec_score={score} in [{self.CONFIRM_THRESHOLD}, {self.AUTO_EXECUTE})",
                    confirm_message=self._build_confirm(action_type, user_message),
                    impact_info=self._describe_impact(action_type, user_message),
                    original_query=user_message,
                )
            # 有分数但没 handler → 问用户要做什么
            return GateDecision(
                action="confirm_then_execute", score=score,
                action_type=action_type,
                reason="has_score_but_no_handler",
                confirm_message=self._config.get("no_handler_message", "你想要我做什么？"),
                original_query=user_message,
            )

        if handler_id:
            return GateDecision(
                action="confirm_then_execute", score=score,
                handler=handler_id,
                action_type=action_type,
                reason=f"low_score_with_handler={score}",
                confirm_message=self._build_confirm(action_type, user_message),
                impact_info=self._describe_impact(action_type, user_message),
                original_query=user_message,
            )

        return GateDecision(
            action="reject", score=score,
            reason=f"exec_score={score} < {self.CONFIRM_THRESHOLD}",
            original_query=user_message,
        )

    def _calculate_exec_score(self, action_type: str, user_message: str,
                              query_type: str, confidence: float) -> float:
        """执行分数 = 可逆性 × 影响度 × 明确度"""
        reversibility = REVERSIBILITY.get(action_type, 0.5)
        impact = self._estimate_impact(action_type, user_message)
        clarity = self._estimate_clarity(user_message, query_type, confidence)
        return round(reversibility * impact * clarity, 3)

    def _estimate_impact(self, action_type: str, user_message: str) -> float:
        """根据操作类型和范围估计影响度。范围 0.0(影响大) ~ 1.0(无影响)"""
        base = {
            "read": 1.0, "create": 0.9, "modify": 0.7,
            "delete": 0.4, "send": 0.3, "system": 0.2, "none": 1.0,
        }.get(action_type, 0.5)

        scope = self._config.get("scope_words", {})
        # 全部/所有 → 影响更大
        if any(w in user_message for w in scope.get("max_impact", [])):
            base = max(0.1, base - 0.3)
        # 单一/一个 → 影响较小
        if any(w in user_message for w in scope.get("min_impact", [])):
            base = min(1.0, base + 0.1)

        return base

    def _estimate_clarity(self, text: str, query_type: str, confidence: float) -> float:
        """用户意图有多清晰。范围 0.0(模糊) ~ 1.0(明确)"""
        clarity = confidence

        clarity_cfg = self._config.get("clarity", {})
        # 包含明确动作动词 → 更清晰
        clear_verbs = clarity_cfg.get("clear_verbs", [])
        if any(v in text for v in clear_verbs):
            clarity = min(1.0, clarity + 0.1)

        # 包含明确对象（文件路径、URL）→ 更清晰
        if re.search(r'[\w/\\]+\.\w+', text):
            clarity = min(1.0, clarity + 0.1)
        if re.search(r'https?://', text):
            clarity = min(1.0, clarity + 0.1)

        # 模糊词 → 不清晰
        vague_words = clarity_cfg.get("vague_words", [])
        if any(w in text for w in vague_words):
            clarity = max(0.1, clarity - 0.2)

        # 太短 → 不清晰
        if len(text) < 5:
            clarity = max(0.2, clarity - 0.1)

        return clarity

    def _build_confirm(self, action_type: str, user_message: str) -> str:
        """构建确认讯息"""
        confirm_msgs = self._config.get("confirm_messages", {})
        desc = confirm_msgs.get(action_type, confirm_msgs.get("default", "执行操作"))
        msg = f"你想要{desc}吗？"
        warnings = self._config.get("warnings", {})
        if action_type in warnings:
            msg += warnings[action_type]
        msg += self._config.get("confirm_suffix", "\n确认后我会执行。")
        return msg

    def _describe_impact(self, action_type: str, user_message: str) -> str:
        """描述影响范围"""
        parts = []
        scope = self._config.get("scope_words", {})
        if any(w in user_message for w in scope.get("max_impact", [])):
            parts.append("⚠️ 这会影响所有项目")
        if action_type == "delete":
            parts.append("此操作无法撤销")
        return "；".join(parts)
