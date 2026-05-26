"""
Code Inspector Integration — 新架構整合橋接
==========================================

將 CodeInspector 的檢查結果與 StateMatrixAdapter 的新架構整合：
- 檢查結果 → TemporalState（代碼質量時間序列）
- 檢查指標 → InfluenceSpace（軸間影響）
- 新模式發現 → AllocationPolicy（分配決策）
- 圖譜演化 → TemporalState（依賴追蹤）
- 自動修復 → RippleNode（漣漪效應）
- 學習反饋 → NegativityDetector（θ 自糾）

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from core.engine.state_matrix_adapter import StateMatrixAdapter

logger = logging.getLogger("angela_code_integration")


class CodeInspectorBridge:
    """
    CodeInspector → StateMatrixAdapter 整合橋接

    將 CodeInspector 的檢查結果轉化為狀態軸的輸入，
    讓代碼檢查不再只是「報告」，而是「驅動狀態」。

    使用方式:
        from ai.code_inspection.code_inspector_integration import CodeInspectorBridge

        bridge = CodeInspectorBridge(state_adapter)
        result = bridge.integrate_inspect(inspector.inspect())
        # result 包含所有軸的狀態更新 + 漣漪觸發 + 分配決策
    """

    COMPLEXITY_WEIGHTS = {
        'critical': 0.4,
        'high': 0.25,
        'medium': 0.15,
        'low': 0.05,
    }

    CATEGORY_TO_AXIS = {
        'syntax': 'beta',
        'type': 'beta',
        'logic': 'epsilon',
        'security': 'alpha',
        'style': 'beta',
        'consistency': 'beta',
        'deprecation': 'epsilon',
    }

    def __init__(self, state_adapter: "StateMatrixAdapter"):
        self._adapter = state_adapter

    def integrate_inspect(self, inspect_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        將檢查結果整合到狀態矩陣

        Args:
            inspect_result: CodeInspectorInterface.inspect() 的返回值

        Returns:
            整合結果摘要
        """
        report = inspect_result.get('report')
        if report is None:
            return {'status': 'skip', 'reason': 'no report'}

        total_issues = inspect_result.get('total_issues', 0)
        critical = inspect_result.get('critical', 0)
        high = inspect_result.get('high', 0)
        medium = inspect_result.get('medium', 0)
        low = inspect_result.get('low', 0)

        complexity_score = self._compute_complexity(inspect_result)

        self._record_to_temporal(report, inspect_result)

        self._update_axis_complexity(report, complexity_score)

        self._apply_category_influence(report)

        ripple_result = self._trigger_fix_ripple(report)

        allocation_decision = self._decide_allocation(
            total_issues, critical, complexity_score
        )

        return {
            'status': 'integrated',
            'total_issues': total_issues,
            'complexity_score': complexity_score,
            'axis_updates': {
                'epsilon.complexity': complexity_score,
                'alpha.stability': self._compute_stability(critical, high),
                'beta.clarity': self._compute_clarity(medium, low),
            },
            'ripple': ripple_result,
            'allocation': {
                'action': allocation_decision.action.value if hasattr(allocation_decision.action, 'value') else str(allocation_decision.action),
                'target': allocation_decision.target,
                'confidence': allocation_decision.confidence,
            },
        }

    def _record_to_temporal(
        self, report: Any, inspect_result: Dict[str, Any]
    ) -> None:
        """將檢查結果記錄到 TemporalState"""
        snapshot = {
            'timestamp': report.timestamp if hasattr(report, 'timestamp') else '',
            'code_inspect': {
                'total_issues': inspect_result.get('total_issues', 0),
                'critical': inspect_result.get('critical', 0),
                'high': inspect_result.get('high', 0),
                'medium': inspect_result.get('medium', 0),
                'low': inspect_result.get('low', 0),
            },
        }

        if hasattr(report, 'issues'):
            issues_by_cat: Dict[str, int] = {}
            for issue in report.issues:
                cat = issue.category.value if hasattr(issue.category, 'value') else str(issue.category)
                issues_by_cat[cat] = issues_by_cat.get(cat, 0) + 1
            snapshot['code_inspect']['by_category'] = issues_by_cat

        self._adapter.temporal.record(snapshot)

    def _update_axis_complexity(self, report: Any, score: float) -> None:
        """更新 epsilon 軸的複雜度"""
        self._adapter.update_epsilon(complexity=min(1.0, score))

    def _apply_category_influence(self, report: Any) -> None:
        """根據問題類別應用到軸"""
        if not hasattr(report, 'issues'):
            return

        category_scores: Dict[str, float] = {}
        for issue in report.issues:
            cat = issue.category.value if hasattr(issue.category, 'value') else 'logic'
            sev = issue.severity.value if hasattr(issue.severity, 'value') else 'medium'
            weight = self.COMPLEXITY_WEIGHTS.get(sev, 0.1)
            category_scores[cat] = category_scores.get(cat, 0.0) + weight

        for cat, score in category_scores.items():
            axis = self.CATEGORY_TO_AXIS.get(cat, 'epsilon')
            if axis == 'alpha':
                self._adapter.update_alpha(tension=min(1.0, score * 0.3))
            elif axis == 'beta':
                self._adapter.update_beta(confusion=min(1.0, score * 0.2))
            elif axis == 'epsilon':
                self._adapter.update_epsilon(complexity=min(1.0, score))

    def _trigger_fix_ripple(self, report: Any) -> Dict[str, Any]:
        """觸發修復漣漪"""
        if not hasattr(report, 'issues'):
            return {'status': 'no_issues'}

        auto_fixable = [
            issue for issue in report.issues
            if getattr(issue, 'auto_fixable', False)
        ]

        if not auto_fixable:
            return {'status': 'no_auto_fixable', 'count': 0}

        from core.ripple.node import MathOp

        ripple_count = min(len(auto_fixable), 5)
        ripple = self._adapter.apply_ripple(
            operator=MathOp.ADD,
            result=float(len(auto_fixable)),
            epsilon_delta=0.05 * ripple_count,
            alpha_arousal=0.02 * ripple_count,
            beta_focus=0.03 * ripple_count,
            cascade_targets=['alpha', 'beta', 'epsilon'],
        )

        return {
            'status': 'ripple_triggered',
            'auto_fixable_count': len(auto_fixable),
            'ripple_nodes': len(ripple),
        }

    def _decide_allocation(
        self,
        total_issues: int,
        critical: int,
        complexity_score: float,
    ) -> Any:
        """根據檢查結果做出分配決策"""
        vector = self._build_issue_vector(total_issues, critical, complexity_score)
        decision = self._adapter.allocation_decide(vector, 'code_inspect_report')
        return decision

    def _build_issue_vector(
        self, total: int, critical: int, complexity: float
    ) -> List[float]:
        """從檢查結果構建語義向量"""
        vector = [0.0] * 32
        vector[0] = min(1.0, total / 50.0)
        vector[1] = min(1.0, critical * 0.3)
        vector[2] = min(1.0, complexity)
        vector[3] = 1.0 if critical > 0 else 0.0
        return vector

    def _compute_complexity(self, inspect_result: Dict[str, Any]) -> float:
        """計算代碼複雜度分數"""
        score = 0.0
        for sev, weight in self.COMPLEXITY_WEIGHTS.items():
            count = inspect_result.get(sev, 0)
            score += weight * count
        return min(1.0, score)

    def _compute_stability(self, critical: int, high: int) -> float:
        """計算系統穩定性"""
        score = critical * 0.5 + high * 0.2
        return max(0.0, 1.0 - score)

    def _compute_clarity(self, medium: int, low: int) -> float:
        """計算代碼清晰度"""
        score = (medium + low) * 0.02
        return max(0.0, min(1.0, 1.0 - score))

    def get_quality_trend(self, window: int = 10) -> Dict[str, Any]:
        """
        查詢代碼質量趨勢

        使用 TemporalState.trend() 分析歷史檢查結果。
        """
        trend = self._adapter.temporal_trend(
            'code_inspect', 'total_issues', window=window
        )
        crit_trend = self._adapter.temporal_trend(
            'code_inspect', 'critical', window=window
        )

        return {
            'total_trend': {
                'direction': trend.direction,
                'slope': trend.slope,
                'mean': trend.mean,
            },
            'critical_trend': {
                'direction': crit_trend.direction,
                'slope': crit_trend.slope,
            },
            'window': window,
        }

    def get_quality_anomalies(self, threshold: float = 0.5) -> List[Any]:
        """檢測代碼質量異常"""
        return self._adapter.temporal_anomalies(
            'code_inspect', 'critical', threshold=threshold, window=50
        )


def create_bridge(state_adapter: "StateMatrixAdapter") -> CodeInspectorBridge:
    """工廠函數：創建整合橋接"""
    return CodeInspectorBridge(state_adapter)