#!/usr/bin/env python3
"""
性能回归检测器
用于检测和报告性能回归问题
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import logging
import numpy as np
import scipy.stats as stats


# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)


class PerformanceRegressionDetector:
    """性能回归检测器"""

    def __init__(self, project_root: str = None) -> None:
    """
    初始化性能回归检测器

    Args:
            project_root: 项目根目录
    """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent:
    self.benchmarks_dir = self.project_root / "benchmarks"
    self.db_path = self.benchmarks_dir / "benchmark_history.db"

    # 回归检测配置
    self.regression_config = {
            "time_window_days": 30,
            "regression_threshold": 0.05,  # 5%性能下降
            "statistical_significance": 0.05,  # 95%置信度
            "minimum_samples": 5,
            "alert_on_regression": True
    }

    def detect_performance_regressions(self, benchmark_names: List[...]
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
    _ = detection_results["regressions"].append(regression_result)
                        detection_results["regressions_found"] += 1
                    elif regression_result["status"] == "improvement":

    _ = detection_results["improvements"].append(regression_result)
                        detection_results["improvements_found"] += 1
                    else:

                        _ = detection_results["unchanged"].append(regression_result)
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

            return [row[0] for row in rows]
    except Exception as e:

    logger.error(f"Error getting benchmark names: {e}")
            return []

    def _analyze_benchmark_regression(self, benchmark_name: str) -> Dict[str, Any]:
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
                point for point in historical_data :
    if baseline_start_date <= datetime.fromisoformat(point["timestamp"]) <= baseline_end_date
            ]

            if len(baseline_data) < 2:


    return {
                    "benchmark_name": benchmark_name,
                    "status": "insufficient_baseline",
                    "message": f"Insufficient baseline data points ({len(baseline_data)} < 2)"
                }

            # 计算基线统计信息
            baseline_mean_times = [point["mean_time"] for point in baseline_data]:
    baseline_mean = np.mean(baseline_mean_times)
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
                    "p_value": float(p_value) if 'p_value' in locals() else None
                }
            }

            # 添加详细信息
            if status == "regression":

    result["severity"] = self._calculate_regression_severity(performance_change)
                result["recommendations"] = self._generate_regression_recommendations(benchmark_name, result)

            return result

        except Exception as e:


            logger.error(f"Error analyzing benchmark regression for {benchmark_name}: {e}")
            return {
                "benchmark_name": benchmark_name,
                "status": "error",
                "error": str(e)
            }

    def _get_historical_benchmark_data(self, benchmark_name: str) -> List[Dict[str, Any]]:
    """
    获取基准测试的历史数据

    Args:
            benchmark_name: 基准测试名称

    Returns:
            List: 历史数据点列表
    """
        try:

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, mean_time, ops_per_second, std_dev, iterations
                FROM benchmark_history
                WHERE name = ?
                ORDER BY timestamp ASC
            _ = """, (benchmark_name,))

            rows = cursor.fetchall()
            conn.close()

            historical_data = []
            for row in rows:

    historical_data.append({
                    "timestamp": row[0],
                    "mean_time": row[1],
                    "ops_per_second": row[2],
                    "std_dev": row[3],
                    "iterations": row[4]
                })

            return historical_data

        except Exception as e:


            logger.error(f"Error getting historical data for {benchmark_name}: {e}")
            return []

    def _calculate_regression_severity(self, performance_change: float) -> str:
    """
    计算回归严重程度

    Args:
            performance_change: 性能变化比例

    Returns: str 严重程度级别
    """
    abs_change = abs(performance_change)

        if abs_change >= 0.2:  # 20%以上
            return "critical"
        elif abs_change >= 0.1:  # 10%以上
            return "high"
        elif abs_change >= 0.05:  # 5%以上
            return "medium"
        else:

            return "low"

    def _generate_regression_recommendations(self, benchmark_name: str,
                                          regression_result: Dict[...]
    """
    生成回归改进建议

    Args:
            benchmark_name: 基准测试名称
            regression_result: 回归结果

    Returns:
            List: 改进建议列表
    """
    recommendations = []
    performance_change = regression_result["analysis"]["performance_change"]

        if "agent" in benchmark_name.lower()


    if performance_change > 0.1:
    recommendations.append("Investigate agent creation or initialization overhead")
                recommendations.append("Check for resource leaks in agent lifecycle management")
    else:

    recommendations.append("Review recent changes to agent implementation")
                recommendations.append("Consider profiling agent operations for bottlenecks")

    elif "hsp" in benchmark_name.lower()


    if performance_change > 0.1:



    recommendations.append("Analyze HSP message serialization/deserialization performance")
                recommendations.append("Check network I/O operations in HSP connector")
            else:

                recommendations.append("Review HSP protocol implementation for recent changes")
    recommendations.append("Consider message batching for high-frequency operations")

    elif "memory" in benchmark_name.lower()


    if performance_change > 0.1:



    recommendations.append("Investigate memory storage/retrieval algorithms")
                recommendations.append("Check for database connection pooling issues")
    else:

    recommendations.append("Review memory management implementation")
                recommendations.append("Consider caching strategies for frequently accessed data")

    elif "training" in benchmark_name.lower()


    if performance_change > 0.1:



    recommendations.append("Analyze model training iteration performance")
                recommendations.append("Check for GPU/CPU resource utilization")
    else:

    recommendations.append("Review training data preprocessing pipeline")
                recommendations.append("Consider optimizing training algorithms")

    # 通用建议
    recommendations.append("Profile the specific operation with detailed timing analysis")
    recommendations.append("Check system resource usage (CPU, memory, disk I/O) during the operation")
    recommendations.append("Review recent code changes that might affect performance")
        recommendations.append("Consider implementing performance monitoring for this operation")

    return recommendations

    def generate_regression_report(self, detection_results: Dict[str, Any],
                                 output_file: str = None) -> str:
    """
    生成回归检测报告

    Args:
            detection_results: 检测结果
            output_file: 输出文件路径

    Returns: str 生成的报告路径
    """
        if output_file is None:

    output_file = self.benchmarks_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:

            output_file = Path(output_file)

        try:


            with open(output_file, "w", encoding="utf-8") as f:
    json.dump(detection_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Regression report generated: {output_file}")
            return str(output_file)
        except Exception as e:

            logger.error(f"Error generating regression report: {e}")
            return ""

    def send_regression_alert(self, regression_result: Dict[str, Any])
    """
    发送回归警报

    Args:
            regression_result: 回归结果
    """
        if not self.regression_config["alert_on_regression"]:

    return

    try
            # 这里可以实现具体的警报机制
            # 例如：发送邮件、Slack通知、创建GitHub issue等

            logger.warning(
                f"PERFORMANCE REGRESSION DETECTED!\n"
                f"Benchmark: {regression_result['benchmark_name']}\n"
                _ = f"Severity: {regression_result.get('severity', 'unknown')}\n"
                f"Performance Change: {regression_result['analysis']['performance_change_percentage']}\n"
                f"Latest Time: {regression_result['latest']['mean_time']:.6f}s\n"
                f"Baseline Time: {regression_result['baseline']['mean_time']:.6f}s"
            )

            # 如果有改进建议，也一并输出
            recommendations = regression_result.get("recommendations", [])
            if recommendations:

    logger.info("Recommendations:")
                for i, rec in enumerate(recommendations, 1)

    logger.info(f"  {i}. {rec}")

        except Exception as e:


            logger.error(f"Error sending regression alert: {e}")

    def run_continuous_regression_monitoring(self)
    """
    运行持续回归监控
    """
    logger.info("Starting continuous performance regression monitoring...")

        try:
            # 检测所有基准测试的回归
            detection_results = self.detect_performance_regressions()

            # 发送回归警报
            for regression in detection_results.get("regressions", [])

    self.send_regression_alert(regression)

            # 生成报告
            report_file = self.generate_regression_report(detection_results)
            if report_file:

    logger.info(f"Regression monitoring report generated: {report_file}")

            return detection_results

        except Exception as e:


            logger.error(f"Error in continuous regression monitoring: {e}")
            return {"status": "error", "error": str(e)}


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Regression Detector")
    parser.add_argument(
    "action",
    choices=["detect", "monitor", "report"],
    help="Action to perform"
    )
    parser.add_argument(
    "--benchmarks",
    nargs="*",
    help="Specific benchmark names to analyze"
    )
    parser.add_argument(
    "--output",
        help="Output file for reports"
    )
    parser.add_argument(
    "--no-alert",
    action="store_true",
    help="Disable regression alerts"
    )

    args = parser.parse_args()

    # 创建回归检测器
    detector = PerformanceRegressionDetector()

    # 配置警报
    if args.no_alert:

    detector.regression_config["alert_on_regression"] = False

    # 执行操作
    if args.action == "detect":

    detection_results = detector.detect_performance_regressions(args.benchmarks)

    print(f"Performance Regression Detection Results")
    print(f"=====================================")
    print(f"Total Benchmarks Analyzed: {detection_results.get('total_benchmarks_analyzed', 0)}")
    print(f"Regressions Found: {detection_results.get('regressions_found', 0)}")
    print(f"Improvements Found: {detection_results.get('improvements_found', 0)}")
    print()

    # 显示回归详情
    regressions = detection_results.get("regressions", [])
        if regressions:

    print("Performance Regressions Detected:")
            for regression in regressions:

    print(f"  - {regression['benchmark_name']}:")
                print(f"    Performance Change: {regression['analysis']['performance_change_percentage']}")
                print(f"    Severity: {regression.get('severity', 'unknown')}")
                print(f"    Latest Time: {regression['latest']['mean_time']:.6f}s")
                print(f"    Baseline Time: {regression['baseline']['mean_time']:.6f}s")
                print()
        else:

            print("No performance regressions detected.")

    # 显示改进建议
        for regression in regressions:

    recommendations = regression.get("recommendations", [])
            if recommendations:

    print(f"Recommendations for {regression['benchmark_name']}:")
                for i, rec in enumerate(recommendations, 1)

    print(f"  {i}. {rec}")
                print()

    elif args.action == "monitor":


    detection_results = detector.run_continuous_regression_monitoring()
        if detection_results.get("status") == "error":

    print(f"Error in regression monitoring: {detection_results.get('error')}")
            sys.exit(1)
        else:

            print("Continuous regression monitoring completed successfully")

    elif args.action == "report":
    # 这个功能需要先运行检测
    detection_results = detector.detect_performance_regressions(args.benchmarks)
    report_file = detector.generate_regression_report(detection_results, args.output)
        if report_file:

    print(f"Regression report generated: {report_file}")
        else:

            print("Failed to generate regression report")
            sys.exit(1)


if __name__ == "__main__":



    main()