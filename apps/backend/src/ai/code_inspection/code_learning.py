"""
Angela Code Learning System - 代碼學習系統
==========================================

核心設計：
  - 純演算法，從人類反饋中學習
  - 不依賴 LLM，工具級精確度
  - 學習模式：直接學習自己的代碼庫

學習流程：
  1. 檢查代碼 → 識別問題
  2. 修復問題 → 應用修復
  3. 人類反饋 → 更新知識
  4. 持續改進 → 自我提升

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path

logger = logging.getLogger("angela_code_learning")


@dataclass
class LearnedPattern:
    id: str
    name: str
    description: str
    fix_template: str
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class LearningFeedback:
    timestamp: str
    issue_id: str
    original_fix: str
    human_feedback: str
    accepted: bool
    correction: Optional[str] = None


class CodeLearningEngine:
    """
    代碼學習引擎
    =============

    從人類反饋中學習，修復模式逐步完善
    """

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.patterns: Dict[str, LearnedPattern] = {}
        self.feedback_history: List[LearningFeedback] = []
        self.max_feedback_history = 500

        self._init_builtin_patterns()

    def _init_builtin_patterns(self):
        """初始化內置模式"""
        builtin_patterns = [
            LearnedPattern(
                id="PAT-001",
                name="除零保護",
                description="在除法運算前檢查除數是否為零",
                fix_template="check_divisor_nonzero",
                confidence=0.95,
            ),
            LearnedPattern(
                id="PAT-002",
                name="空值檢查",
                description="在訪問字典/列表前檢查是否為 None/空",
                fix_template="check_none_or_empty",
                confidence=0.92,
            ),
            LearnedPattern(
                id="PAT-003",
                name="索引邊界檢查",
                description="在訪問列表元素前檢查索引是否越界",
                fix_template="check_index_bounds",
                confidence=0.90,
            ),
            LearnedPattern(
                id="PAT-004",
                name="類型一致性",
                description="確保前後端類型/介面一致",
                fix_template="sync_type_across_modules",
                confidence=0.88,
            ),
            LearnedPattern(
                id="PAT-005",
                name="異常處理",
                description="非空異常處理块包含日誌或重拋",
                fix_template="non_empty_except",
                confidence=0.93,
            ),
            LearnedPattern(
                id="PAT-006",
                name="歷史快照完整性",
                description="_record_history 包含所有軸的快照",
                fix_template="complete_history_snapshot",
                confidence=0.97,
            ),
            LearnedPattern(
                id="PAT-007",
                name="Theta軸初始化",
                description="StateMatrix4D 初始化時創建所有6個軸",
                fix_template="init_all_axes",
                confidence=0.96,
            ),
        ]

        for pat in builtin_patterns:
            self.patterns[pat.id] = pat

    def learn_from_feedback(
        self,
        issue_id: str,
        original_fix: str,
        human_feedback: str,
        accepted: bool,
        correction: Optional[str] = None,
    ) -> LearnedPattern:
        """
        從人類反饋中學習

        Args:
            issue_id: 問題ID
            original_fix: Angela 原始修復
            human_feedback: 人類反饋
            accepted: 修復是否被接受
            correction: 如果不被接受，人類的修正

        Returns:
            學習到的模式
        """
        from datetime import datetime
        feedback = LearningFeedback(
            timestamp=datetime.now().isoformat(),
            issue_id=issue_id,
            original_fix=original_fix,
            human_feedback=human_feedback,
            accepted=accepted,
            correction=correction,
        )
        self.feedback_history.append(feedback)
        if len(self.feedback_history) > self.max_feedback_history:
            self.feedback_history = self.feedback_history[-self.max_feedback_history:]

        pattern_id = self._infer_pattern_id(human_feedback, correction)
        if pattern_id and pattern_id in self.patterns:
            pat = self.patterns[pattern_id]
            if accepted:
                pat.success_count += 1
            else:
                pat.failure_count += 1
                if correction:
                    pat.fix_template = correction
            pat.confidence = 0.5 + pat.success_rate * 0.5

            logger.info(f"[Learning] Pattern {pat.id} updated: success={pat.success_count}, failure={pat.failure_count}, confidence={pat.confidence:.2f}")
            return pat

        return None

    def _infer_pattern_id(self, feedback: str, correction: Optional[str]) -> Optional[str]:
        """從反饋推斷模式ID"""
        feedback_lower = feedback.lower()
        correction_lower = (correction or "").lower()

        if "除零" in feedback or "divisor" in feedback_lower or "zero" in feedback_lower:
            return "PAT-001"
        if "none" in feedback_lower or "空值" in feedback or "null" in feedback_lower:
            return "PAT-002"
        if "index" in feedback_lower or "索引" in feedback or "越界" in feedback:
            return "PAT-003"
        if "一致" in feedback or "sync" in feedback_lower or "frontend" in feedback_lower:
            return "PAT-004"
        if "except" in feedback_lower or "異常" in feedback:
            return "PAT-005"
        if "history" in feedback_lower or "快照" in feedback:
            return "PAT-006"
        if "axis" in feedback_lower or "θ" in feedback or "theta" in feedback_lower:
            return "PAT-007"

        return None

    def get_pattern_by_id(self, pattern_id: str) -> Optional[LearnedPattern]:
        return self.patterns.get(pattern_id)

    def get_all_patterns(self) -> List[LearnedPattern]:
        return list(self.patterns.values())

    def get_high_confidence_patterns(self, threshold: float = 0.8) -> List[LearnedPattern]:
        return [p for p in self.patterns.values() if p.confidence >= threshold]

    def get_feedback_stats(self) -> Dict[str, Any]:
        """獲取學習統計"""
        total = len(self.feedback_history)
        accepted = sum(1 for f in self.feedback_history if f.accepted)
        return {
            "total_feedback": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "acceptance_rate": accepted / total if total > 0 else 0.0,
            "patterns_count": len(self.patterns),
            "high_confidence_patterns": len(self.get_high_confidence_patterns()),
        }

    def export_patterns(self) -> List[Dict[str, Any]]:
        """導出所有模式（用於持久化）"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "fix_template": p.fix_template,
                "confidence": p.confidence,
                "success_count": p.success_count,
                "failure_count": p.failure_count,
                "success_rate": p.success_rate,
            }
            for p in self.patterns.values()
        ]

    def import_patterns(self, patterns_data: List[Dict[str, Any]]):
        """從持久化數據導入模式"""
        for data in patterns_data:
            pat = LearnedPattern(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                fix_template=data["fix_template"],
                confidence=data.get("confidence", 0.5),
                success_count=data.get("success_count", 0),
                failure_count=data.get("failure_count", 0),
            )
            self.patterns[pat.id] = pat


class CodeInspectorInterface:
    """
    檢查器介面 — 將 Inspector、Fixer、Learning 整合為統一介面
    """

    def __init__(self, root_path: str):
        self.root_path = root_path

        from ai.code_inspection.code_inspector import CodeInspector, CodeFixer, ProjectInspector
        self.inspector = CodeInspector(root_path)
        self.project_inspector = ProjectInspector(root_path)
        self.fixer = CodeFixer()

        from ai.code_inspection.knowledge_graph import KnowledgeGraph
        self.knowledge_graph = KnowledgeGraph(root_path)

        self.learning = CodeLearningEngine(self.knowledge_graph)

        self._init_report_id = 0

    def inspect(self, scope: str = "full") -> Dict[str, Any]:
        """
        執行檢查

        Args:
            scope: "full" / "module" / "file"

        Returns:
            檢查報告
        """
        self._init_report_id += 1
        report = self.project_inspector.check_all()
        report.summary["report_id"] = self._init_report_id
        return {
            "report": report,
            "total_issues": len(report.issues),
            "auto_fixable": len(self.inspector.get_auto_fixable()),
            "critical": report.critical_count,
            "high": report.high_count,
            "medium": report.medium_count,
            "low": report.low_count,
        }

    def fix(
        self,
        issue_id: str,
        dry_run: bool = True,
    ) -> Tuple[bool, str]:
        """
        修復指定問題

        Args:
            issue_id: 問題ID
            dry_run: 是否只報告不實際修復

        Returns:
            (成功標記, 消息)
        """
        report = self.project_inspector.check_all()
        target = None
        for issue in report.issues:
            if issue.id == issue_id:
                target = issue
                break

        if not target:
            return False, f"Issue {issue_id} not found"

        if not target.auto_fixable:
            return False, f"Issue {issue_id} is not auto-fixable"

        return self.fixer.apply_fix(target, dry_run)

    def fix_all_auto(self, dry_run: bool = True) -> Dict[str, Any]:
        """自動修復所有可自動修復的問題"""
        report = self.project_inspector.check_all()
        auto_fixable = self.inspector.get_auto_fixable()

        results = []
        for issue in auto_fixable:
            success, msg = self.fixer.apply_fix(issue, dry_run)
            results.append({
                "issue_id": issue.id,
                "file": issue.file,
                "line": issue.line,
                "success": success,
                "message": msg,
            })

        return {
            "total_auto_fixable": len(auto_fixable),
            "results": results,
            "applied": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
        }

    def learn(
        self,
        issue_id: str,
        original_fix: str,
        human_feedback: str,
        accepted: bool,
        correction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """記錄學習反饋"""
        pattern = self.learning.learn_from_feedback(
            issue_id, original_fix, human_feedback, accepted, correction
        )
        return {
            "pattern_id": pattern.id if pattern else None,
            "confidence": pattern.confidence if pattern else 0.0,
            "stats": self.learning.get_feedback_stats(),
        }

    def get_status(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        graph_stats = self.knowledge_graph.get_statistics()
        learning_stats = self.learning.get_feedback_stats()

        return {
            "knowledge_graph": graph_stats,
            "learning": learning_stats,
            "patterns": len(self.learning.patterns),
            "high_confidence_patterns": len(self.learning.get_high_confidence_patterns()),
        }

    def ask_human(self, question: str) -> str:
        """生成向人類提問的文本"""
        return f"[Angela Question] {question}\n\nPlease respond with your feedback so I can learn."

    def explain_fix(self, issue_id: str) -> str:
        """解釋修復邏輯"""
        report = self.project_inspector.check_all()
        target = None
        for issue in report.issues:
            if issue.id == issue_id:
                target = issue
                break

        if not target:
            return f"Issue {issue_id} not found in report."

        return (
            f"Issue: {target.id}\n"
            f"File: {target.file}:{target.line}\n"
            f"Description: {target.description}\n"
            f"Severity: {target.severity.value}\n"
            f"Confidence: {target.confidence:.0%}\n"
            f"Suggestion: {target.suggestion}\n"
            f"Auto-fixable: {target.auto_fixable}\n"
            f"Fix template: {target.fix_template or 'N/A'}"
        )


def create_inspector(root_path: str) -> CodeInspectorInterface:
    """工廠函數：創建檢查器介面"""
    return CodeInspectorInterface(root_path)