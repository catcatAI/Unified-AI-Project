# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L3+
# =============================================================================
#
# 职责: 数据分析代理，处理数值和统计数据
# 维度: 涉及认知维度 (β) 的逻辑分析和数据处理
# 安全: 使用 Key A (后端控制) 进行数据隐私保护
# 成熟度: L3+ 等级可以进行复杂的数据分析
#
# 能力:
# - statistical_analysis: 统计分析
# - data_visualization: 数据可视化
# - pattern_recognition: 模式识别
# - trend_analysis: 趋势分析
#
# =============================================================================

import logging
import statistics
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataAnalysisAgent:
    """Agent for dataset analysis, report generation, and correlation finding."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        logger.info(f"DataAnalysisAgent initialized with config: {self.config}")

    def analyze_dataset(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dataset and return basic statistics for numeric fields."""
        if not data:
            return {"status": "error", "message": "No data provided", "stats": {}}
        numeric_fields = {}
        for row in data:
            for key, val in row.items():
                if isinstance(val, (int, float)):
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(val)
        stats = {}
        for field, values in numeric_fields.items():
            if len(values) > 1:
                stats[field] = {
                    "mean": round(statistics.mean(values), 4),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
                    "count": len(values),
                }
            else:
                stats[field] = {
                    "mean": values[0],
                    "median": values[0],
                    "min": values[0],
                    "max": values[0],
                    "stdev": 0.0,
                    "count": 1,
                }
        logger.info(f"analyze_dataset: {len(data)} rows, {len(stats)} numeric fields")
        return {"status": "success", "message": f"Analyzed {len(data)} rows with {len(stats)} numeric fields", "stats": stats}

    def generate_report(self, data: List[Dict[str, Any]], report_type: str = "summary") -> Dict[str, Any]:
        """Generate a report from the dataset."""
        if not data:
            return {"status": "error", "message": "No data provided"}
        row_count = len(data)
        field_count = len(data[0]) if data else 0
        field_names = list(data[0].keys()) if data else []
        logger.info(f"generate_report: type={report_type}, {row_count} rows, {field_count} fields")
        return {
            "status": "success",
            "message": f"Generated {report_type} report for {row_count} rows",
            "report_type": report_type,
            "row_count": row_count,
            "field_count": field_count,
            "field_names": field_names,
        }

    def find_correlations(self, data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """Find correlations between specified columns in the dataset."""
        if not data or len(columns) < 2:
            return {"status": "error", "message": "Need data and at least 2 columns", "correlations": []}
        series = {col: [] for col in columns}
        for row in data:
            for col in columns:
                val = row.get(col)
                if isinstance(val, (int, float)):
                    series[col].append(val)
        correlations = []
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                a, b = columns[i], columns[j]
                if len(series[a]) > 1 and len(series[b]) > 1 and len(series[a]) == len(series[b]):
                    n = len(series[a])
                    mean_a = statistics.mean(series[a])
                    mean_b = statistics.mean(series[b])
                    num = sum((series[a][k] - mean_a) * (series[b][k] - mean_b) for k in range(n))
                    den_a = sum((series[a][k] - mean_a) ** 2 for k in range(n)) ** 0.5
                    den_b = sum((series[b][k] - mean_b) ** 2 for k in range(n)) ** 0.5
                    if den_a and den_b:
                        corr = round(num / (den_a * den_b), 4)
                        correlations.append({"columns": [a, b], "correlation": corr})
        logger.info(f"find_correlations: computed {len(correlations)} correlations")
        return {
            "status": "success",
            "message": f"Found {len(correlations)} correlations",
            "correlations": correlations,
        }

