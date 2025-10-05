#!/usr/bin/env python3
"""
性能回归检测器
用于检测AI项目中的性能回归问题
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceRegressionDetector:
    """性能回归检测器"""

    def __init__(self, project_root: Optional[str] = None) -> None:
        """
        初始化性能回归检测器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent:
elf.benchmarks_dir = self.project_root / "benchmarks"
        self.db_path = self.benchmarks_dir / "benchmark_history.db"

        # 回归检测配置
        self.regression_config = {
            "time_window_days": 30,
            "regression_threshold": 0.05,  # 5%性能下降
            "statistical_significance": 0.05,  # 95%置信度
            "minimum_samples": 5,
            "alert_on_regression": True
        }

    def detect_performance_regressions(self, benchmark_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        检测性能回归

        Args:
            benchmark_names: 要检测的基准测试名称列表，如果为None则检测所有

        Returns:
            Dict: 回归检测结果
        """
        logger.info("Detecting performance regressions...")

        detection_results = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks_analyzed": 0,
            "regressions_found": 0,
            "improvements_found": 0,
            "no_change_benchmarks": 0,
            "regressions": [],
            "improvements": [],
            "unchanged": []
        }

        try:
            # 获取要分析的基准测试名称
            if benchmark_names is None:
                benchmark_names = self._get_all_benchmark_names()

            detection_results["total_benchmarks_analyzed"] = len(benchmark_names)

            # 分析每个基准测试
            for benchmark_name in benchmark_names:
                regression_result = self._analyze_benchmark_regression(benchmark_name)
                if regression_result:
                    if regression_result["status"] == "regression":
                        detection_results["regressions"].append(regression_result)
                        detection_results["regressions_found"] += 1
                    elif regression_result["status"] == "improvement":
                        detection_results["improvements"].append(regression_result)
                        detection_results["improvements_found"] += 1
                    else:
                        detection_results["unchanged"].append(regression_result)
                        detection_results["no_change_benchmarks"] += 1

            logger.info(
                f"Performance regression detection completed. "
                f"Found {detection_results['regressions_found']} regressions, "
                f"{detection_results['improvements_found']} improvements"
            )

        except Exception as e:
            logger.error(f"Error detecting performance regressions: {e}")
            detection_results["error"] = str(e)

        return detection_results

    def _get_all_benchmark_names(self) -> List[str]:
        """
        获取所有基准测试名称

        Returns:
            List: 基准测试名称列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT name FROM benchmark_history ORDER BY name")
            rows = cursor.fetchall()
            conn.close()

            return [row[0] for row in rows]:
xcept Exception as e:
            logger.error(f"Error getting benchmark names: {e}")
            return []

    def _analyze_benchmark_regression(self, benchmark_name: str) -> Optional[Dict[str, Any]]:
        """
        分析单个基准测试的回归情况

        Args:
            benchmark_name: 基准测试名称

        Returns:
            Dict: 回归分析结果
        """
        try:
            # 获取历史数据
            historical_data = self._get_historical_benchmark_data(benchmark_name)
            if len(historical_data) < self.regression_config["minimum_samples"]:
                return {
                    "benchmark_name": benchmark_name,
                    "status": "insufficient_data",
                    "message": f"Insufficient data points ({len(historical_data)} < {self.regression_config['minimum_samples']})"
                }

            # 计算基线（最近30天的平均值）
            baseline_end_date = datetime.now()
            baseline_start_date = baseline_end_date - timedelta(days=self.regression_config["time_window_days"])

            baseline_data = [
                point for point in historical_data:
f baseline_start_date <= datetime.fromisoformat(point["timestamp"]) <= baseline_end_date:


            if len(baseline_data) < 2:
                return {
                    "benchmark_name": benchmark_name,
                    "status": "insufficient_baseline",
                    "message": f"Insufficient baseline data points ({len(baseline_data)} < 2)"
                }

            # 计算基线统计信息
            baseline_mean_times = [point["mean_time"] for point in baseline_data]:
aseline_mean = np.mean(baseline_mean_times)
            baseline_std = np.std(baseline_mean_times)

            # 获取最新数据点
            latest_point = historical_data[-1]
            latest_mean_time = latest_point["mean_time"]

            # 执行统计检验
            if len(baseline_mean_times) >= 2:
                # 使用t检验检测显著差异
                t_stat, p_value = stats.ttest_1samp(baseline_mean_times, latest_mean_time)
                is_statistically_significant = p_value < self.regression_config["statistical_significance"]
            else:
                is_statistically_significant = False

            # 计算性能变化
            performance_change = (latest_mean_time - baseline_mean) / baseline_mean
            is_performance_change_significant = abs(performance_change) >= self.regression_config["regression_threshold"]

            # 确定结果状态
            if is_performance_change_significant and performance_change > 0:
                status = "regression"
            elif is_performance_change_significant and performance_change < 0:
                status = "improvement"
            else:
                status = "no_change"

            result = {
                "benchmark_name": benchmark_name,
                "status": status,
                "baseline": {
                    "mean_time": float(baseline_mean),
                    "std_dev": float(baseline_std),
                    "sample_size": len(baseline_data)
                },
                "latest": {
                    "mean_time": latest_mean_time,
                    "timestamp": latest_point["timestamp"],
                    "ops_per_second": latest_point["ops_per_second"]
                },
                "analysis": {
                    "performance_change": float(performance_change),
                    "performance_change_percentage": f"{performance_change * 100:.2f}%",
                    "is_statistically_significant": is_statistically_significant,
                    "p_value": float(p_value) if 'p_value' in locals() else None:

            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing benchmark regression for {benchmark_name}: {e}"):
eturn None

    def _get_historical_benchmark_data(self, benchmark_name: str) -> List[Dict[str, Any]]:
        """
        获取基准测试的历史数据

        Args:
            benchmark_name: 基准测试名称

        Returns:
            List: 历史数据列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name, timestamp, mean_time, ops_per_second
                FROM benchmark_history 
                WHERE name = ? 
                ORDER BY timestamp ASC
            """, (benchmark_name,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "name": row[0],
                    "timestamp": row[1],
                    "mean_time": row[2],
                    "ops_per_second": row[3]
                }
                for row in rows:


        except Exception as e:
            logger.error(f"Error getting historical benchmark data for {benchmark_name}: {e}"):
eturn []

    def generate_regression_report(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回归检测报告

        Args:
            detection_results: 检测结果

        Returns:
            Dict: 报告生成结果
        """
        try:
            report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.benchmarks_dir / f"regression_report_{report_timestamp}.json"

            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(detection_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Generated regression report: {report_file}")

            return {
                "success": True,
                "report_file": str(report_file),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating regression report: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def send_regression_alerts(self, regressions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        发送回归警报

        Args:
            regressions: 回归列表

        Returns:
            Dict: 警报发送结果
        """
        try:
            if not regressions or not self.regression_config["alert_on_regression"]:
                return {
                    "success": True,
                    "alerts_sent": 0,
                    "message": "No regressions to alert or alerts disabled",
                    "timestamp": datetime.now().isoformat()
                }

            # 发送警报（在实际实现中，这里会发送实际的警报）
            alert_count = len(regressions)
            logger.warning(f"Performance regressions detected! Sending {alert_count} alerts.")

            # 在实际实现中，这里会发送邮件、Slack消息等

            return {
                "success": True,
                "alerts_sent": alert_count,
                "regressions": regressions,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending regression alerts: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

def main() -> None:
    """主函数"""
    detector = PerformanceRegressionDetector()
    results = detector.detect_performance_regressions()
    
    # 生成报告
    report_result = detector.generate_regression_report(results)
    
    # 发送警报（如果有回归）
    if results.get("regressions_found", 0) > 0:
        detector.send_regression_alerts(results.get("regressions", []))
    
    logger.info("Performance regression detection completed")

if __name__ == "__main__":
    main()