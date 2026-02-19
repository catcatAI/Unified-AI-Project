"""
Deviation Tracker - 偏差追踪器
==============================
记录预期与实际响应的偏差，优化 Token 消耗

核心功能：
1. 记录每次响应的路由决策（COMPOSED / HYBRID / LLM_FULL）
2. 追踪 Token 消耗
3. 追踪响应质量偏差
4. 生成优化建议

性能目标：记录开销 < 0.1ms
"""

import time
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ResponseRoute(Enum):
    """响应路由类型"""

    COMPOSED = "composed"
    HYBRID = "hybrid"
    LLM_FULL = "llm_full"
    FALLBACK = "fallback"


@dataclass
class ResponseMetrics:
    """响应指标"""

    timestamp: float
    user_input: str
    match_score: float
    route: ResponseRoute
    response_text: str
    tokens_used: int
    response_time_ms: float
    composition_time_ms: float
    match_time_ms: float
    quality_score: float = 0.0
    user_feedback: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeviationTracker:
    """
    偏差追踪器
    ===========

    设计目标：
    1. 实时追踪响应路由决策
    2. 记录 Token 消耗和时间开销
    3. 分析响应质量偏差
    4. 提供优化建议

    统计维度：
    - 路由分布（COMPOSED / HYBRID / LLM_FULL）
    - Token 节省率
    - 响应时间分布
    - 质量偏差
    """

    def __init__(self, log_dir: Optional[str] = None):
        self.metrics_history: List[ResponseMetrics] = []
        self.log_dir = Path(log_dir) if log_dir else Path("logs/deviation")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "total_responses": 0,
            "route_counts": {
                ResponseRoute.COMPOSED.value: 0,
                ResponseRoute.HYBRID.value: 0,
                ResponseRoute.LLM_FULL.value: 0,
                ResponseRoute.FALLBACK.value: 0,
            },
            "total_tokens_used": 0,
            "total_tokens_saved": 0,
            "average_match_score": 0.0,
            "average_response_time": 0.0,
            "average_quality_score": 0.0,
            "token_savings_rate": 0.0,
        }

        self.route_baselines = {
            ResponseRoute.COMPOSED: {"tokens": 50, "time": 5.0},
            ResponseRoute.HYBRID: {"tokens": 200, "time": 500.0},
            ResponseRoute.LLM_FULL: {"tokens": 600, "time": 1500.0},
            ResponseRoute.FALLBACK: {"tokens": 0, "time": 1.0},
        }

    def record(
        self,
        user_input: str,
        match_score: float,
        route: ResponseRoute,
        response_text: str,
        tokens_used: int,
        response_time_ms: float,
        composition_time_ms: float = 0.0,
        match_time_ms: float = 0.0,
        quality_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        记录响应指标

        Args:
            user_input: 用户输入
            match_score: 匹配分数
            route: 路由类型
            response_text: 响应文本
            tokens_used: 使用的 Token 数
            response_time_ms: 响应时间（毫秒）
            composition_time_ms: 组合时间（毫秒）
            match_time_ms: 匹配时间（毫秒）
            quality_score: 质量分数
            metadata: 额外元数据
        """
        start_time = time.time()

        metrics = ResponseMetrics(
            timestamp=time.time(),
            user_input=user_input,
            match_score=match_score,
            route=route,
            response_text=response_text,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            composition_time_ms=composition_time_ms,
            match_time_ms=match_time_ms,
            quality_score=quality_score,
            metadata=metadata or {},
        )

        self.metrics_history.append(metrics)

        self._update_stats(metrics)

        if len(self.metrics_history) % 100 == 0:
            self._persist_metrics()

        record_time = (time.time() - start_time) * 1000
        if record_time > 0.5:
            logger.warning(f"Deviation tracking took {record_time:.2f}ms (slow)")

    def _update_stats(self, metrics: ResponseMetrics):
        """更新统计信息"""
        self.stats["total_responses"] += 1
        total = self.stats["total_responses"]

        self.stats["route_counts"][metrics.route.value] += 1

        self.stats["total_tokens_used"] += metrics.tokens_used

        baseline_tokens = self.route_baselines[ResponseRoute.LLM_FULL]["tokens"]
        tokens_saved = baseline_tokens - metrics.tokens_used
        if tokens_saved > 0:
            self.stats["total_tokens_saved"] += tokens_saved

        self.stats["average_match_score"] = (
            self.stats["average_match_score"] * (total - 1) + metrics.match_score
        ) / total

        self.stats["average_response_time"] = (
            self.stats["average_response_time"] * (total - 1)
            + metrics.response_time_ms
        ) / total

        if metrics.quality_score > 0:
            self.stats["average_quality_score"] = (
                self.stats["average_quality_score"] * (total - 1)
                + metrics.quality_score
            ) / total

        if self.stats["total_tokens_used"] > 0:
            expected_tokens = total * baseline_tokens
            self.stats["token_savings_rate"] = (
                self.stats["total_tokens_saved"] / expected_tokens
            )

    def record_user_feedback(self, metrics_index: int, positive: bool):
        """
        记录用户反馈

        Args:
            metrics_index: 指标索引（最近 N 条）
            positive: 是否正面反馈
        """
        if 0 <= metrics_index < len(self.metrics_history):
            self.metrics_history[metrics_index].user_feedback = positive

            if positive:
                self.metrics_history[metrics_index].quality_score = 1.0
            else:
                self.metrics_history[metrics_index].quality_score = 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def get_recent_metrics(self, count: int = 10) -> List[ResponseMetrics]:
        """获取最近的指标"""
        return self.metrics_history[-count:]

    def get_optimization_suggestions(self) -> List[str]:
        """
        生成优化建议

        Returns:
            List[str]: 优化建议列表
        """
        suggestions = []

        composed_rate = (
            self.stats["route_counts"][ResponseRoute.COMPOSED.value]
            / self.stats["total_responses"]
            if self.stats["total_responses"] > 0
            else 0.0
        )

        if composed_rate < 0.3:
            suggestions.append(
                f"建议: 组合路由使用率仅 {composed_rate*100:.1f}%，考虑添加更多预定义模板"
            )

        avg_match_score = self.stats["average_match_score"]
        if avg_match_score < 0.5:
            suggestions.append(
                f"建议: 平均匹配分数为 {avg_match_score:.2f}，考虑优化匹配算法或扩展关键词"
            )

        token_savings = self.stats["token_savings_rate"]
        if token_savings < 0.5:
            suggestions.append(
                f"建议: Token 节省率为 {token_savings*100:.1f}%，目标为 60-80%"
            )

        avg_response_time = self.stats["average_response_time"]
        if avg_response_time > 2000:
            suggestions.append(
                f"建议: 平均响应时间为 {avg_response_time:.0f}ms，考虑优化 LLM 调用"
            )

        llm_full_rate = (
            self.stats["route_counts"][ResponseRoute.LLM_FULL.value]
            / self.stats["total_responses"]
            if self.stats["total_responses"] > 0
            else 0.0
        )

        if llm_full_rate > 0.5:
            suggestions.append(
                f"建议: 完整 LLM 调用占 {llm_full_rate*100:.1f}%，考虑增加混合路由使用"
            )

        if not suggestions:
            suggestions.append("系统运行良好，无需优化")

        return suggestions

    def _persist_metrics(self):
        """持久化指标到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"metrics_{timestamp}.json"

            recent_metrics = self.metrics_history[-100:]
            metrics_data = [asdict(m) for m in recent_metrics]

            for m in metrics_data:
                m["route"] = m["route"].value if isinstance(m["route"], Enum) else m["route"]

            log_data = {"timestamp": timestamp, "stats": self.stats, "metrics": metrics_data}

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Persisted metrics to {log_file}")

        except Exception as e:
            logger.warning(f"Failed to persist metrics: {e}")

    def generate_report(self) -> str:
        """
        生成偏差追踪报告

        Returns:
            str: 报告文本
        """
        report_lines = [
            "========================================",
            "偏差追踪报告 - Deviation Tracking Report",
            "========================================",
            "",
            f"总响应数: {self.stats['total_responses']}",
            "",
            "路由分布:",
        ]

        total = self.stats["total_responses"]
        if total > 0:
            for route, count in self.stats["route_counts"].items():
                percentage = (count / total) * 100
                report_lines.append(f"  - {route}: {count} ({percentage:.1f}%)")

        report_lines.extend(
            [
                "",
                f"Token 使用情况:",
                f"  - 总消耗: {self.stats['total_tokens_used']}",
                f"  - 总节省: {self.stats['total_tokens_saved']}",
                f"  - 节省率: {self.stats['token_savings_rate']*100:.1f}%",
                "",
                f"性能指标:",
                f"  - 平均匹配分数: {self.stats['average_match_score']:.2f}",
                f"  - 平均响应时间: {self.stats['average_response_time']:.0f}ms",
                f"  - 平均质量分数: {self.stats['average_quality_score']:.2f}",
                "",
                "优化建议:",
            ]
        )

        suggestions = self.get_optimization_suggestions()
        for i, suggestion in enumerate(suggestions, 1):
            report_lines.append(f"  {i}. {suggestion}")

        report_lines.append("")
        report_lines.append("========================================")

        return "\n".join(report_lines)

    def export_metrics(self, filepath: str):
        """
        导出指标到文件

        Args:
            filepath: 导出文件路径
        """
        try:
            metrics_data = [asdict(m) for m in self.metrics_history]

            for m in metrics_data:
                m["route"] = m["route"].value if isinstance(m["route"], Enum) else m["route"]

            export_data = {"stats": self.stats, "metrics": metrics_data}

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Exported metrics to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
