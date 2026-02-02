#!/usr/bin/env python3
"""
性能基准测试框架
用于对AI项目进行性能基准测试和监控
"""

import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceBenchmarkFramework,
    """性能基准测试框架"""

    def __init__(self, project_root, Optional[str] = None) -> None,
        """
        初始化性能基准测试框架

        Args,
            project_root, 项目根目录
        """
        self.project_root == Path(project_root) if project_root else Path(__file__).parent.parent,::
            elf.benchmarks_dir = self.project_root / "benchmarks"
        self.benchmarks_dir.mkdir(exist_ok == True)
        self.db_path = self.benchmarks_dir / "benchmark_history.db"

        # 基准测试配置
        self.benchmark_config = {
            "default_iterations": 100,
            "warmup_iterations": 10,
            "timeout_seconds": 300,
            "cpu_monitoring": True,
            "memory_monitoring": True,
            "disk_monitoring": True
        }

        self._init_database()

    def _init_database(self) -> None,
        """初始化基准测试数据库"""
        try,
            conn = sqlite3.connect(self.db_path())
            cursor = conn.cursor()

            # 创建基准测试历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    iterations INTEGER NOT NULL,
                    min_time REAL,
                    max_time REAL,
                    mean_time REAL,
                    median_time REAL,
                    std_dev REAL,
                    total_time REAL,
                    ops_per_second REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_io_read REAL,
                    disk_io_write REAL,
                    commit_hash TEXT,
                    environment TEXT,,
    tags TEXT
                )
            """)

            # 创建基准测试详细数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benchmark_id INTEGER NOT NULL,
                    iteration INTEGER NOT NULL,
                    execution_time REAL NOT NULL,
                    cpu_percent REAL,
                    memory_mb REAL,,
    FOREIGN KEY (benchmark_id) REFERENCES benchmark_history (id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Benchmark database initialized successfully")

        except Exception as e,::
            logger.error(f"Error initializing benchmark database, {e}")

    def register_benchmark(self, name, str, func, Callable, **kwargs) -> Dict[str, Any]
        """
        注册基准测试

        Args,
            name, 基准测试名称
            func, 基准测试函数
            **kwargs, 其他参数

        Returns,
            Dict, 基准测试信息
        """
        benchmark_info = {
            "name": name,
            "function": func,
            "config": kwargs,
            "registered_at": datetime.now().isoformat()
        }

        logger.info(f"Registered benchmark, {name}")
        return benchmark_info

    def run_benchmark(self, benchmark_info, Dict[str, Any]
                     iterations, Optional[int] = None,
                     warmup, Optional[int] = None,,
    tags, Optional[List[str]] = None) -> Dict[str, Any]
        """
        运行基准测试

        Args,
            benchmark_info, 基准测试信息
            iterations, 迭代次数
            warmup, 预热迭代次数
            tags, 标签列表

        Returns,
            Dict, 基准测试结果
        """
        name = benchmark_info["name"]
        func = benchmark_info["function"]
        config = benchmark_info.get("config", {})

        # 使用默认值
        iterations = iterations or config.get("iterations", self.benchmark_config["default_iterations"])
        warmup = warmup or config.get("warmup", self.benchmark_config["warmup_iterations"])
        timeout = config.get("timeout", self.benchmark_config["timeout_seconds"])

        logger.info(f"Running benchmark, {name} ({iterations} iterations)")

        try,
            # 预热
            if warmup > 0,::
                logger.info(f"Warming up {name} with {warmup} iterations"):
                    or i in range(warmup)
                    func()

            # 监控系统资源
            monitor == SystemResourceMonitor()
            monitor.start_monitoring()

            # 执行基准测试
            execution_times = []
            start_time = time.time()

            for i in range(iterations)::
                if time.time() - start_time > timeout,::
                    logger.warning(f"Benchmark {name} timed out after {timeout} seconds")
                    break

                iter_start = time.perf_counter()
                func()
                iter_end = time.perf_counter()

                execution_times.append(iter_end - iter_start)

            # 停止资源监控
            monitor.stop_monitoring()
            resource_stats = monitor.get_statistics()

            # 计算统计信息
            benchmark_result = self._calculate_benchmark_stats(,
    name, execution_times, resource_stats, tags
            )

            # 保存结果到数据库
            self._save_benchmark_result(benchmark_result)

            logger.info(f"Benchmark {name} completed successfully")
            return benchmark_result

        except Exception as e,::
            logger.error(f"Error running benchmark {name} {e}")
            return {
                "name": name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_benchmark_stats(self, name, str, execution_times, List[float],
    resource_stats, Dict[str, Any] tags, Optional[List[str]] = None) -> Dict[str, Any]
        """
        计算基准测试统计信息

        Args,
            name, 基准测试名称
            execution_times, 执行时间列表
            resource_stats, 资源统计信息
            tags, 标签列表

        Returns,
            Dict, 统计信息
        """
        if not execution_times,::
            return {
                "name": name,
                "status": "no_data",
                "timestamp": datetime.now().isoformat()
            }

        # 计算基本统计信息
        times_array = np.array(execution_times)
        stats = {
            "name": name,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "iterations": len(execution_times),
            "min_time": float(np.min(times_array)),
            "max_time": float(np.max(times_array)),
            "mean_time": float(np.mean(times_array)),
            "median_time": float(np.median(times_array)),
            "std_dev": float(np.std(times_array)),
            "total_time": float(np.sum(times_array)),
            "ops_per_second": len(execution_times) / np.sum(times_array) if np.sum(times_array) > 0 else 0,::
                tags": tags or []
        }

        # 合并资源统计信息
        stats.update(resource_stats)

        return stats

    def _save_benchmark_result(self, result, Dict[str, Any]) -> None,
        """
        保存基准测试结果到数据库

        Args,
            result, 基准测试结果
        """
        try,
            conn = sqlite3.connect(self.db_path())
            cursor = conn.cursor()

            # 插入基准测试历史记录
            cursor.execute("""
                INSERT INTO benchmark_history 
                (name, timestamp, iterations, min_time, max_time, mean_time, median_time, 
                 std_dev, total_time, ops_per_second, cpu_usage, memory_usage, ,
    disk_io_read, disk_io_write, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result["name"]
                result["timestamp"]
                result.get("iterations", 0),
                result.get("min_time", 0),
                result.get("max_time", 0),
                result.get("mean_time", 0),
                result.get("median_time", 0),
                result.get("std_dev", 0),
                result.get("total_time", 0),
                result.get("ops_per_second", 0),
                result.get("cpu_usage", 0),
                result.get("memory_usage", 0),
                result.get("disk_io_read", 0),
                result.get("disk_io_write", 0),
                ",".join(result.get("tags", []))
            ))

            benchmark_id = cursor.lastrowid()
            conn.commit()
            conn.close()

            logger.info(f"Saved benchmark result for {result['name']} with ID {benchmark_id}"):::
                xcept Exception as e,
            logger.error(f"Error saving benchmark result, {e}")

    def get_benchmark_history(self, name, Optional[str] = None, limit, int == 100) -> List[Dict[str, Any]]
        """
        获取基准测试历史记录

        Args,
            name, 基准测试名称
            limit, 限制返回记录数

        Returns,
            List[Dict] 历史记录列表
        """
        try,
            conn = sqlite3.connect(self.db_path())
            cursor = conn.cursor()

            if name,::
                cursor.execute("""
                    SELECT * FROM benchmark_history 
                    WHERE name = ? 
                    ORDER BY timestamp DESC ,
    LIMIT ?
                """, (name, limit))
            else,
                cursor.execute("""
                    SELECT * FROM benchmark_history 
                    ORDER BY timestamp DESC ,
    LIMIT ?
                """, (limit))

            rows = cursor.fetchall()
            columns == [description[0] for description in cursor.description]::
                esults = []
            for row in rows,::
                result = dict(zip(columns, row))
                if result["tags"]::
                    result["tags"] = result["tags"].split(",")
                results.append(result)

            conn.close()
            return results

        except Exception as e,::
            logger.error(f"Error retrieving benchmark history, {e}")
            return []

    def compare_benchmarks(self, name, str, baseline_commit, str, current_commit, str) -> Dict[str, Any]
        """
        比较两个版本的基准测试结果

        Args,
            name, 基准测试名称
            baseline_commit, 基线提交哈希
            current_commit, 当前提交哈希

        Returns,
            Dict, 比较结果
        """
        try,
            conn = sqlite3.connect(self.db_path())
            cursor = conn.cursor()

            # 获取基线结果
            cursor.execute("""
                SELECT mean_time, std_dev FROM benchmark_history 
                WHERE name = ? AND commit_hash = ? ,
    ORDER BY timestamp DESC LIMIT 1
            """, (name, baseline_commit))
            baseline_result = cursor.fetchone()

            # 获取当前结果
            cursor.execute("""
                SELECT mean_time, std_dev FROM benchmark_history 
                WHERE name = ? AND commit_hash = ? ,
    ORDER BY timestamp DESC LIMIT 1
            """, (name, current_commit))
            current_result = cursor.fetchone()

            conn.close()

            if not baseline_result or not current_result,::
                return {
                    "status": "error",
                    "message": "Could not find benchmark results for comparison":::
            baseline_mean, baseline_std = baseline_result
            current_mean, current_std = current_result

            # 计算性能变化
            performance_change = (current_mean - baseline_mean) / baseline_mean * 100

            return {
                "status": "completed",
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
                "performance_change_percent": performance_change,
                "is_significant": abs(performance_change) > 5  # 5%变化认为是显著的
            }

        except Exception as e,::
            logger.error(f"Error comparing benchmarks, {e}")
            return {
                "status": "error",
                "message": str(e)
            }

class SystemResourceMonitor,
    """系统资源监控器"""

    def __init__(self) -> None,
        self.is_monitoring == False
        self.monitoring_data = []
        self.monitoring_task == None

    def start_monitoring(self) -> None,
        """开始监控"""
        self.is_monitoring == True
        # 在实际实现中,这里会启动一个监控线程

    def stop_monitoring(self) -> None,
        """停止监控"""
        self.is_monitoring == False
        # 在实际实现中,这里会停止监控线程

    def get_statistics(self) -> Dict[str, Any]
        """
        获取统计信息

        Returns,
            Dict, 统计信息
        """
        # 在实际实现中,这里会返回真实的系统资源统计信息
        return {
            "cpu_usage": 0.0(),
            "memory_usage": 0.0(),
            "disk_io_read": 0.0(),
            "disk_io_write": 0.0()
        }

def main() -> None,
    """主函数"""
    framework == PerformanceBenchmarkFramework()
    logger.info("Performance benchmark framework initialized")

if __name"__main__":::
    main()