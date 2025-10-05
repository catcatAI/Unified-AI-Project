#!/usr/bin/env python3
"""
测试覆盖率监控器
用于监控测试覆盖率趋势并设置告警机制
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoverageMonitor:
    """测试覆盖率监控器"""

    def __init__(self, project_root: Optional[str] = None, db_path: Optional[str] = None) -> None:
        """
        初始化覆盖率监控器

        Args:
                project_root: 项目根目录
                db_path: 数据库文件路径
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent:
elf.db_path = Path(db_path) if db_path else self.project_root / "coverage_history.db":
elf._init_database()

    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建覆盖率历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coverage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    line_rate REAL NOT NULL,
                    branch_rate REAL NOT NULL,
                    complexity REAL,
                    lines_valid INTEGER,
                    lines_covered INTEGER,
                    branches_valid INTEGER,
                    branches_covered INTEGER,
                    commit_hash TEXT,
                    build_number INTEGER,
                    environment TEXT
                )
            """)

            # 创建模块覆盖率表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS module_coverage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id INTEGER NOT NULL,
                    module_name TEXT NOT NULL,
                    line_rate REAL NOT NULL,
                    branch_rate REAL,
                    class_count INTEGER,
                    FOREIGN KEY (history_id) REFERENCES coverage_history (id)
                )
            """)

            # 创建低覆盖率区域表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS low_coverage_areas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id INTEGER NOT NULL,
                    package TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    filename TEXT,
                    line_rate REAL NOT NULL,
                    branch_rate REAL,
                    FOREIGN KEY (history_id) REFERENCES coverage_history (id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Coverage database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing coverage database: {e}")

    def record_coverage_data(self, coverage_data: Dict[str, Any],
                           commit_hash: Optional[str] = None, build_number: Optional[int] = None,
                           environment: str = "development") -> bool:
        """
        记录覆盖率数据

        Args:
                coverage_data: 覆盖率数据
                commit_hash: Git提交哈希
                build_number: 构建编号
                environment: 环境名称

        Returns: bool 记录是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 插入覆盖率历史记录
            summary = coverage_data.get("summary", {})
            timestamp = datetime.now()

            cursor.execute("""
                INSERT INTO coverage_history
                (timestamp, line_rate, branch_rate, complexity, lines_valid, lines_covered,
                 branches_valid, branches_covered, commit_hash, build_number, environment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                summary.get("line_rate", 0),
                summary.get("branch_rate", 0),
                summary.get("complexity", 0),
                summary.get("lines_valid", 0),
                summary.get("lines_covered", 0),
                summary.get("branches_valid", 0),
                summary.get("branches_covered", 0),
                commit_hash,
                build_number,
                environment
            ))

            history_id = cursor.lastrowid

            # 插入模块覆盖率数据
            module_coverage = coverage_data.get("module_coverage", {})
            for module_name, module_data in module_coverage.items():
                cursor.execute("""
                    INSERT INTO module_coverage
                    (history_id, module_name, line_rate, branch_rate, class_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    history_id,
                    module_name,
                    module_data.get("average_line_rate", 0),
                    module_data.get("branch_rate", 0),
                    module_data.get("class_count", 0)
                ))

            # 插入低覆盖率区域数据
            low_coverage_areas = coverage_data.get("low_coverage_areas", [])
            for area in low_coverage_areas:
                cursor.execute("""
                    INSERT INTO low_coverage_areas
                    (history_id, package, class_name, filename, line_rate, branch_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    history_id,
                    area.get("package", ""),
                    area.get("class", ""),
                    area.get("filename", ""),
                    area.get("line_rate", 0),
                    area.get("branch_rate", 0)
                ))

            conn.commit()
            conn.close()

            logger.info(f"Coverage data recorded successfully (ID: {history_id})")
            return True

        except Exception as e:
            logger.error(f"Error recording coverage data: {e}")
            return False

    def get_coverage_trend(self, days: int = 30, environment: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取覆盖率趋势数据

        Args:
                days: 天数范围
                environment: 环境名称

        Returns:
                List: 覆盖率趋势数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 构建查询条件
            query_conditions = ["timestamp >= ? AND timestamp <= ?"]
            query_params = [start_date, end_date]

            if environment:
                query_conditions.append("environment = ?")
                query_params.append(environment)  # type: ignore

            # 查询覆盖率历史数据
            query = f"""
                SELECT timestamp, line_rate, branch_rate, complexity, commit_hash, build_number
                FROM coverage_history
                WHERE {" AND ".join(query_conditions)}
                ORDER BY timestamp ASC
            """

            cursor.execute(query, query_params)
            rows = cursor.fetchall()

            trend_data = []
            for row in rows:
                trend_data.append({
                    "timestamp": row[0],
                    "line_rate": row[1],
                    "branch_rate": row[2],
                    "complexity": row[3],
                    "commit_hash": row[4],
                    "build_number": row[5]
                })

            conn.close()
            return trend_data

        except Exception as e:
            logger.error(f"Error getting coverage trend: {e}")
            return []

    def check_coverage_threshold(self, line_rate_threshold: float = 0.8,
                               branch_rate_threshold: float = 0.7) -> Dict[str, Any]:
        """
        检查覆盖率阈值

        Args:
                line_rate_threshold: 行覆盖率阈值
                branch_rate_threshold: 分支覆盖率阈值

        Returns:
                Dict: 阈值检查结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取最新的覆盖率数据
            cursor.execute("""
                SELECT line_rate, branch_rate, timestamp
                FROM coverage_history
                ORDER BY timestamp DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            conn.close()

            if not row:
                return {"status": "no_data", "message": "No coverage data available"}

            line_rate, branch_rate, timestamp = row

            # 检查阈值
            violations = []
            if line_rate < line_rate_threshold:
                violations.append(f"Line rate {line_rate:.2%} below threshold {line_rate_threshold:.2%}")
            if branch_rate < branch_rate_threshold:
                violations.append(f"Branch rate {branch_rate:.2%} below threshold {branch_rate_threshold:.2%}")

            if violations:
                return {
                    "status": "violation",
                    "timestamp": timestamp,
                    "line_rate": line_rate,
                    "branch_rate": branch_rate,
                    "violations": violations
                }
            else:
                return {
                    "status": "ok",
                    "timestamp": timestamp,
                    "line_rate": line_rate,
                    "branch_rate": branch_rate,
                    "message": "Coverage meets all thresholds"
                }

        except Exception as e:
            logger.error(f"Error checking coverage threshold: {e}")
            return {"status": "error", "message": str(e)}

    def get_module_coverage_comparison(self, module_name: str, days: int = 30) -> Dict[str, Any]:
        """
        获取模块覆盖率对比

        Args:
                module_name: 模块名称
                days: 天数范围

        Returns:
                Dict: 模块覆盖率对比数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 查询模块覆盖率历史数据
            cursor.execute("""
                SELECT h.timestamp, m.line_rate, m.branch_rate
                FROM coverage_history h
                JOIN module_coverage m ON h.id = m.history_id
                WHERE h.timestamp >= ? AND h.timestamp <= ? AND m.module_name = ?
                ORDER BY h.timestamp ASC
            """, (start_date, end_date, module_name))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return {"status": "no_data", "module": module_name, "message": "No data for this module"}:
omparison_data = {
                "module": module_name,
                "data_points": []
            }

            for row in rows:
                comparison_data["data_points"].append({
                    "timestamp": row[0],
                    "line_rate": row[1],
                    "branch_rate": row[2]
                })

            # 计算统计信息
            line_rates = [point["line_rate"] for point in comparison_data["data_points"]]:
ranch_rates = [point["branch_rate"] for point in comparison_data["data_points"]]:
omparison_data["statistics"] = {
                "line_rate": {
                    "current": line_rates[-1] if line_rates else 0,:
average": sum(line_rates) / len(line_rates) if line_rates else 0,:
min": min(line_rates) if line_rates else 0,:
max": max(line_rates) if line_rates else 0,:
trend": "improving" if len(line_rates) > 1 and line_rates[-1] > line_rates[0] else "declining" if len(line_rates) > 1 and line_rates[-1] < line_rates[0] else "stable":
,
                "branch_rate": {
                    "current": branch_rates[-1] if branch_rates else 0,:
average": sum(branch_rates) / len(branch_rates) if branch_rates else 0,:
min": min(branch_rates) if branch_rates else 0,:
max": max(branch_rates) if branch_rates else 0,:
trend": "improving" if len(branch_rates) > 1 and branch_rates[-1] > branch_rates[0] else "declining" if len(branch_rates) > 1 and branch_rates[-1] < branch_rates[0] else "stable":

            }

            return comparison_data

        except Exception as e:
            logger.error(f"Error getting module coverage comparison: {e}")
            return {"status": "error", "message": str(e)}

    def generate_trend_report(self, days: int = 30, output_file: Optional[str] = None) -> str:
        """
        生成趋势报告

        Args:
                days: 天数范围
                output_file: 输出文件路径

        Returns: str 生成的报告路径
        """
        if output_file is None:
            output_file = str(self.project_root / f"coverage_trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        else:
            output_file = str(Path(output_file))

        # 获取趋势数据
        trend_data = self.get_coverage_trend(days)

        # 获取阈值检查结果
        threshold_result = self.check_coverage_threshold()

        # 构建报告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "trend_data": trend_data,
            "threshold_check": threshold_result,
            "summary": {
                "total_records": len(trend_data),
                "date_range": {
                    "start": trend_data[0]["timestamp"] if trend_data else None,:
end": trend_data[-1]["timestamp"] if trend_data else None:

            }
        }

        # 计算趋势统计
        if trend_data:
            line_rates = [point["line_rate"] for point in trend_data]:
ranch_rates = [point["branch_rate"] for point in trend_data]:
eport_data["summary"]["line_rate"] = {
                "current": line_rates[-1] if line_rates else 0,:
average": sum(line_rates) / len(line_rates) if line_rates else 0,:
min": min(line_rates) if line_rates else 0,:
max": max(line_rates) if line_rates else 0,:
trend": "improving" if len(line_rates) > 1 and line_rates[-1] > line_rates[0] else "declining" if len(line_rates) > 1 and line_rates[-1] < line_rates[0] else "stable":


            report_data["summary"]["branch_rate"] = {
                "current": branch_rates[-1] if branch_rates else 0,:
average": sum(branch_rates) / len(branch_rates) if branch_rates else 0,:
min": min(branch_rates) if branch_rates else 0,:
max": max(branch_rates) if branch_rates else 0,:
trend": "improving" if len(branch_rates) > 1 and branch_rates[-1] > branch_rates[0] else "declining" if len(branch_rates) > 1 and branch_rates[-1] < branch_rates[0] else "stable":


        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Trend report generated: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating trend report: {e}")
            return ""

    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """
        清理旧数据

        Args:
                days_to_keep: 保留天数

        Returns: bool 清理是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 计算删除截止日期
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # 删除旧的覆盖率历史数据
            cursor.execute("""
                DELETE FROM coverage_history
                WHERE timestamp < ?
            """, (cutoff_date,))

            deleted_count = cursor.rowcount

            # 外键约束会自动删除相关的模块覆盖率和低覆盖率区域数据
            conn.commit()
            conn.close()

            logger.info(f"Cleaned up {deleted_count} old coverage records")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage Monitor")
    parser.add_argument(
        "action",
        choices=["record", "trend", "threshold", "module-comparison", "report", "cleanup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--data-file",
        help="Coverage data file (JSON) for recording":

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days for trend analysis":

    parser.add_argument(
        "--module",
        help="Module name for comparison":

    parser.add_argument(
        "--threshold-line",
        type=float,
        default=0.8,
        help="Line coverage threshold"
    )
    parser.add_argument(
        "--threshold-branch",
        type=float,
        default=0.7,
        help="Branch coverage threshold"
    )
    parser.add_argument(
        "--output",
        help="Output file for reports":

    parser.add_argument(
        "--keep-days",
        type=int,
        default=365,
        help="Days to keep for cleanup":


    args = parser.parse_args()

    # 创建覆盖率监控器
    monitor = CoverageMonitor()

    # 执行操作
    if args.action == "record":
        if not args.data_file:
            print("Error: --data-file is required for record action"):
ys.exit(1)

        try:
            with open(args.data_file, "r", encoding="utf-8") as f:
                coverage_data = json.load(f)

            success = monitor.record_coverage_data(coverage_data)
            sys.exit(0 if success else 1):
xcept Exception as e:
            print(f"Error reading coverage data: {e}")
            sys.exit(1)

    elif args.action == "trend":
        trend_data = monitor.get_coverage_trend(args.days)
        if trend_data:
            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(trend_data, f, indent=2, ensure_ascii=False)
                    print(f"Trend data saved to: {args.output}")
                except Exception as e:
                    print(f"Error saving trend data: {e}")
                    sys.exit(1)
            else:
                print(f"Coverage trend for last {args.days} days:"):
or point in trend_data:
                    print(f"  {point['timestamp']}: Line Rate {point['line_rate']:.2%}, "
                          f"Branch Rate {point['branch_rate']:.2%}")
        else:
            print("No trend data available")
            sys.exit(1)

    elif args.action == "threshold":
        result = monitor.check_coverage_threshold(args.threshold_line, args.threshold_branch)
        print(f"Coverage threshold check: {result['status']}")
        if "message" in result:
            print(f"  {result['message']}")
        if "violations" in result:
            for violation in result["violations"]:
                print(f"  - {violation}")
        if "line_rate" in result:
            print(f"  Line Rate: {result['line_rate']:.2%}")
        if "branch_rate" in result:
            print(f"  Branch Rate: {result['branch_rate']:.2%}")

    elif args.action == "module-comparison":
        if not args.module:
            print("Error: --module is required for module-comparison action"):
ys.exit(1)

        comparison_data = monitor.get_module_coverage_comparison(args.module, args.days)
        if comparison_data.get("status") == "error":
            print(f"Error: {comparison_data['message']}")
            sys.exit(1)
        elif comparison_data.get("status") == "no_data":
            print(f"No data for module: {args.module}"):
ys.exit(1)
        else:
            print(f"Coverage comparison for module: {args.module}"):
tats = comparison_data["statistics"]
            print(f"  Line Rate - Current: {stats['line_rate']['current']:.2%}, "
                  f"Average: {stats['line_rate']['average']:.2%}, "
                  f"Trend: {stats['line_rate']['trend']}")
            print(f"  Branch Rate - Current: {stats['branch_rate']['current']:.2%}, "
                  f"Average: {stats['branch_rate']['average']:.2%}, "
                  f"Trend: {stats['branch_rate']['trend']}")

    elif args.action == "report":
        report_file = monitor.generate_trend_report(args.days, args.output)
        if report_file:
            print(f"Trend report generated: {report_file}")
        else:
            print("Failed to generate trend report")
            sys.exit(1)

    elif args.action == "cleanup":
        success = monitor.cleanup_old_data(args.keep_days)
        sys.exit(0 if success else 1):
f __name__ == "__main__":
    main()