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

import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

from ai.core.query_classifier import _NEGATION_WORDS
from core.system.state_store.global_store import state_store
from core.utils import any_keyword

logger = logging.getLogger(__name__)

# 可逆性分数表
REVERSIBILITY = {
    "read":     1.0,   # 读取类：完全可逆（没改变任何东西）
    "search":   1.0,   # 搜索类：完全可逆
    "create":   0.9,   # 建立类：可逆（可删除）
    "modify":   0.6,   # 修改类：可逆但有成本
    "delete":   0.2,   # 删除类：不可逆
    "send":     0.1,   # 传送类：不可逆
    "system":   0.0,   # 系统类：不可逆且影响大
    "execute":  0.0,   # 执行类：不可逆
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

    # C³ 6.0: Class-level _results enables cross-instance feedback persistence

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

    # C³ 6.0: Class-level shared results dict for cross-instance feedback persistence.
    # Was instance-level (self._results) — feedback was lost every turn because
    # each _handle_execution_gate() call creates a new ExecutionGate instance.
    _results: Dict[str, Dict[str, int]] = {}

    def __init__(self, model_bus=None):
        self._model_bus = model_bus
        self._config = self._load_config()
        # DO NOT shadow _results with instance var — use class-level shared dict

    def _load_config(self):
        """Load execution gate config from JSON file."""
        import json
        import os
        config_path = os.path.join(os.path.dirname(__file__), "execution_gate_config.json")
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load execution_gate_config.json, using hardcoded defaults: %s", e)
        return {
                "scope_words": {"max_impact": ["全部", "所有", "整个", "all"], "min_impact": ["一个", "单一", "this"]},
                "clarity": {
                    "clear_verbs": ["search", "delete", "open", "run", "read", "write", "create", "edit"],
                    "vague_words": ["一下", "看看", "处理", "弄", "搞", "整", "试试"],
                },
                "confirm_messages": {"read": "读取", "create": "建立", "modify": "修改", "delete": "删除", "send": "传送", "system": "执行系统操作", "default": "执行操作"},
                "warnings": {"delete": "\n⚠️ 删除后无法复原。", "send": "\n⚠️ 传送后无法撤回。", "system": "\n⚠️ 系统操作可能影响其他程序。", "modify": "\n 修改会覆盖原始内容。"},
                "confirm_suffix": "\n确认后我会执行。",
                "no_handler_message": "抱歉，我無法理解您的意圖。請換句話說，或具體描述您想讓我執行的操作（如：讀取檔案、搜尋資料、回答問題等）。",
            }

    def decide(self, query_type: str, action_type: str, user_message: str,
               confidence: float, context: dict) -> GateDecision:
        """决定是否执行"""
        score = self._calculate_exec_score(action_type, user_message, query_type, confidence)

        # 否定词强制 reject
        if any_keyword(user_message, _NEGATION_WORDS):
            state_store.emit_event("execution.gate_decided", {
                "action": "reject", "score": round(score, 3),
                "query_type": query_type, "action_type": action_type,
                "reason": "negation_detected",
            })
            return GateDecision(
                action="reject", score=score,
                reason="negation_detected",
                original_query=user_message,
            )

        # 检查是否有 handler
        handler_id = self.HANDLER_MAP.get(query_type)

        # C³ 6.0: Feedback-based threshold adjustment (class-level _results)
        fb_adj = self._get_feedback_adjustment(handler_id)
        effective_auto = round(self.AUTO_EXECUTE - fb_adj, 3)
        effective_confirm = round(self.CONFIRM_THRESHOLD - fb_adj, 3)

        # For non-actionable queries, skip confirmation and let LLM handle
        if query_type in ("knowledge", "creative", "greeting", "opinion", "unknown", "logic"):
            state_store.emit_event("execution.gate_decided", {
                "action": "reject", "score": round(score, 3),
                "query_type": query_type, "action_type": action_type,
                "reason": f"non_actionable_{query_type}",
            })
            return GateDecision(
                action="reject", score=score,
                reason=f"non_actionable_query_type_{query_type}",
                original_query=user_message,
            )

        if score >= effective_auto and handler_id:
            state_store.emit_event("execution.gate_decided", {
                "action": "auto_execute", "score": round(score, 3),
                "handler": handler_id,
                "query_type": query_type, "action_type": action_type,
                "feedback_adjustment": round(fb_adj, 3),
            })
            return GateDecision(
                action="auto_execute", score=score,
                handler=handler_id,
                action_type=action_type,
                reason=f"exec_score={score} >= auto={effective_auto} (fb_adj={fb_adj})",
                original_query=user_message,
            )

        if score >= effective_confirm:
            if handler_id:
                state_store.emit_event("execution.gate_decided", {
                    "action": "confirm_then_execute", "score": round(score, 3),
                    "handler": handler_id,
                    "query_type": query_type, "action_type": action_type,
                    "feedback_adjustment": round(fb_adj, 3),
                })
                return GateDecision(
                    action="confirm_then_execute", score=score,
                    handler=handler_id,
                    action_type=action_type,
                    reason=f"exec_score={score} in [{effective_confirm}, {effective_auto}) (fb_adj={fb_adj})",
                    confirm_message=self._build_confirm(action_type, user_message),
                    impact_info=self._describe_impact(action_type, user_message),
                    original_query=user_message,
                )
            state_store.emit_event("execution.gate_decided", {
                "action": "confirm_then_execute", "score": round(score, 3),
                "handler": None, "query_type": query_type, "action_type": action_type,
                "reason": "no_handler",
            })
            return GateDecision(
                action="confirm_then_execute", score=score,
                action_type=action_type,
                reason="has_score_but_no_handler",
                confirm_message=self._config.get("no_handler_message", "抱歉，我無法理解您的意圖。請換句話說，或具體描述您想讓我執行的操作（如：讀取檔案、搜尋資料、回答問題等）。"),
                original_query=user_message,
            )

        state_store.emit_event("execution.gate_decided", {
            "action": "reject", "score": round(score, 3),
            "query_type": query_type, "action_type": action_type,
            "reason": f"score_below_confirm_{effective_confirm}",
        })
        return GateDecision(
            action="reject", score=score,
            reason=f"exec_score={score} < confirm={effective_confirm} (fb_adj={fb_adj})",
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
            "read": 1.0, "search": 1.0, "create": 0.9, "modify": 0.7,
            "delete": 0.4, "send": 0.3, "system": 0.2, "execute": 0.2, "none": 1.0,
        }.get(action_type, 0.5)

        scope = self._config.get("scope_words", {})
        # 全部/所有 → 影响更大
        if any_keyword(user_message, tuple(scope.get("max_impact", []))):
            base = max(0.1, base - 0.3)
        # 单一/一个 → 影响较小
        if any_keyword(user_message, tuple(scope.get("min_impact", []))):
            base = min(1.0, base + 0.1)

        return base

    def _estimate_clarity(self, text: str, query_type: str, confidence: float) -> float:
        """用户意图有多清晰。范围 0.0(模糊) ~ 1.0(明确)"""
        clarity = confidence

        clarity_cfg = self._config.get("clarity", {})
        # 包含明确动作动词 → 更清晰
        clear_verbs = clarity_cfg.get("clear_verbs", [])
        if any_keyword(text, tuple(clear_verbs)):
            clarity = min(1.0, clarity + 0.1)

        # 包含明确对象（文件路径、URL）→ 更清晰
        if re.search(r'[\w/\\]+\.\w+', text):
            clarity = min(1.0, clarity + 0.1)
        if re.search(r'https?://', text):
            clarity = min(1.0, clarity + 0.1)

        # 模糊词 → 不清晰
        vague_words = clarity_cfg.get("vague_words", [])
        if any_keyword(text, tuple(vague_words)):
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
        if any_keyword(user_message, tuple(scope.get("max_impact", []))):
            parts.append("⚠️ 这会影响所有项目")
        if action_type == "delete":
            parts.append("此操作无法撤销")
        return "；".join(parts)

    def reset_feedback_stats(self) -> None:
        """Clear all accumulated feedback stats. Useful for testing isolation."""
        self._results.clear()

    # C³ 6.0: Execution result feedback loop (class-level _results)
    def record_result(self, handler: str, success: bool) -> None:
        """Record execution result for feedback-based threshold adjustment."""
        if handler not in self._results:
            self._results[handler] = {"success": 0, "fail": 0}
        if success:
            self._results[handler]["success"] += 1
        else:
            self._results[handler]["fail"] += 1
        r = self._results[handler]
        state_store.emit_event("execution.result_recorded", {
            "handler": handler,
            "success": success,
            "total_success": r["success"],
            "total_fail": r["fail"],
            "success_rate": round(r["success"] / max(r["success"] + r["fail"], 1), 3),
        })

    def get_feedback_stats(self) -> dict:
        """Return execution feedback statistics per handler."""
        return dict(self._results)

    def _get_feedback_adjustment(self, handler: Optional[str]) -> float:
        """Return threshold adjustment based on historical success rate.
        High success → small positive boost (more trust), failures → no boost."""
        if not handler or handler not in self._results:
            return 0.0
        r = self._results[handler]
        total = r["success"] + r["fail"]
        if total < 3:
            return 0.0
        rate = r["success"] / total
        if rate >= 0.9 and total >= 5:
            return 0.05  # Proven reliable → slightly lower threshold
        if rate <= 0.3 and total >= 3:
            return -0.05  # Often fails → slightly higher threshold
        return 0.0
