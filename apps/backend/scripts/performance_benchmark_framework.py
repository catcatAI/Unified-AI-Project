#!/usr/bin/env python3
"""
性能基准测试框架
用于建立和管理系统的性能基准测试体系
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import logging
import asyncio
import psutil
import numpy as np


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceBenchmarkFramework:
    """性能基准测试框架"""
    
    def __init__(self, project_root: str = None):
        """
        初始化性能基准测试框架
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.benchmarks_dir = self.project_root / "benchmarks"
        self.benchmarks_dir.mkdir(exist_ok=True)
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
    
    def _init_database(self):
        """初始化基准测试数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
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
                    environment TEXT,
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
                    memory_mb REAL,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmark_history (id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Benchmark database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing benchmark database: {e}")
    
    def register_benchmark(self, name: str, func: Callable, **kwargs) -> Dict[str, Any]:
        """
        注册基准测试
        
        Args:
            name: 基准测试名称
            func: 基准测试函数
            **kwargs: 其他参数
            
        Returns:
            Dict: 基准测试信息
        """
        benchmark_info = {
            "name": name,
            "function": func,
            "config": kwargs,
            "registered_at": datetime.now().isoformat()
        }
        
        logger.info(f"Registered benchmark: {name}")
        return benchmark_info
    
    def run_benchmark(self, benchmark_info: Dict[str, Any], 
                     iterations: int = None, 
                     warmup: int = None,
                     tags: List[str] = None) -> Dict[str, Any]:
        """
        运行基准测试
        
        Args:
            benchmark_info: 基准测试信息
            iterations: 迭代次数
            warmup: 预热迭代次数
            tags: 标签列表
            
        Returns:
            Dict: 基准测试结果
        """
        name = benchmark_info["name"]
        func = benchmark_info["function"]
        config = benchmark_info.get("config", {})
        
        # 使用默认值
        iterations = iterations or config.get("iterations", self.benchmark_config["default_iterations"])
        warmup = warmup or config.get("warmup", self.benchmark_config["warmup_iterations"])
        timeout = config.get("timeout", self.benchmark_config["timeout_seconds"])
        
        logger.info(f"Running benchmark: {name} ({iterations} iterations)")
        
        try:
            # 预热
            if warmup > 0:
                logger.info(f"Warming up {name} with {warmup} iterations")
                for i in range(warmup):
                    func()
            
            # 监控系统资源
            monitor = SystemResourceMonitor()
            monitor.start_monitoring()
            
            # 执行基准测试
            execution_times = []
            start_time = time.time()
            
            for i in range(iterations):
                if time.time() - start_time > timeout:
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
            benchmark_result = self._calculate_benchmark_stats(
                name, execution_times, resource_stats, tags
            )
            
            # 保存结果到数据库
            self._save_benchmark_result(benchmark_result)
            
            logger.info(f"Benchmark {name} completed successfully")
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Error running benchmark {name}: {e}")
            return {
                "name": name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_benchmark_stats(self, name: str, execution_times: List[float], 
                                 resource_stats: Dict[str, Any], tags: List[str] = None) -> Dict[str, Any]:
        """
        计算基准测试统计信息
        
        Args:
            name: 基准测试名称
            execution_times: 执行时间列表
            resource_stats: 资源统计信息
            tags: 标签列表
            
        Returns:
            Dict: 统计信息
        """
        if not execution_times:
            return {
                "name": name,
                "status": "no_data",
                "timestamp": datetime.now().isoformat()
            }
        
        # 计算时间统计
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
            "ops_per_second": len(execution_times) / float(np.sum(times_array)) if np.sum(times_array) > 0 else 0,
            "percentiles": {
                "90th": float(np.percentile(times_array, 90)),
                "95th": float(np.percentile(times_array, 95)),
                "99th": float(np.percentile(times_array, 99))
            },
            "resource_usage": resource_stats,
            "tags": tags or []
        }
        
        return stats
    
    def _save_benchmark_result(self, benchmark_result: Dict[str, Any]):
        """
        保存基准测试结果到数据库
        
        Args:
            benchmark_result: 基准测试结果
        """
        if benchmark_result["status"] != "completed":
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 插入基准测试历史记录
            cursor.execute("""
                INSERT INTO benchmark_history 
                (name, timestamp, iterations, min_time, max_time, mean_time, median_time, std_dev,
                 total_time, ops_per_second, cpu_usage, memory_usage, disk_io_read, disk_io_write,
                 commit_hash, environment, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                benchmark_result["name"],
                benchmark_result["timestamp"],
                benchmark_result["iterations"],
                benchmark_result["min_time"],
                benchmark_result["max_time"],
                benchmark_result["mean_time"],
                benchmark_result["median_time"],
                benchmark_result["std_dev"],
                benchmark_result["total_time"],
                benchmark_result["ops_per_second"],
                benchmark_result["resource_usage"].get("cpu_percent", 0),
                benchmark_result["resource_usage"].get("memory_mb", 0),
                benchmark_result["resource_usage"].get("disk_io_read", 0),
                benchmark_result["resource_usage"].get("disk_io_write", 0),
                None,  # commit_hash
                "development",  # environment
                ",".join(benchmark_result["tags"]) if benchmark_result["tags"] else None
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Benchmark result saved for {benchmark_result['name']}")
            
        except Exception as e:
            logger.error(f"Error saving benchmark result: {e}")
    
    def run_benchmark_suite(self, benchmarks: List[Dict[str, Any]], 
                          iterations: int = None,
                          tags: List[str] = None) -> Dict[str, Any]:
        """
        运行基准测试套件
        
        Args:
            benchmarks: 基准测试列表
            iterations: 迭代次数
            tags: 标签列表
            
        Returns:
            Dict: 套件执行结果
        """
        logger.info(f"Running benchmark suite with {len(benchmarks)} benchmarks")
        
        suite_results = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks": len(benchmarks),
            "completed_benchmarks": 0,
            "failed_benchmarks": 0,
            "results": []
        }
        
        for i, benchmark in enumerate(benchmarks):
            logger.info(f"Running benchmark {i+1}/{len(benchmarks)}: {benchmark['name']}")
            
            result = self.run_benchmark(benchmark, iterations, tags=tags)
            suite_results["results"].append(result)
            
            if result["status"] == "completed":
                suite_results["completed_benchmarks"] += 1
            else:
                suite_results["failed_benchmarks"] += 1
        
        logger.info(f"Benchmark suite completed: {suite_results['completed_benchmarks']}/{suite_results['total_benchmarks']} successful")
        return suite_results
    
    def compare_with_baseline(self, benchmark_name: str, 
                            current_result: Dict[str, Any],
                            baseline_days: int = 30) -> Dict[str, Any]:
        """
        与基线进行比较
        
        Args:
            benchmark_name: 基准测试名称
            current_result: 当前结果
            baseline_days: 基线天数
            
        Returns:
            Dict: 比较结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = datetime.fromtimestamp(end_date.timestamp() - baseline_days * 24 * 3600)
            
            # 获取历史基线数据
            cursor.execute("""
                SELECT mean_time, std_dev, ops_per_second
                FROM benchmark_history
                WHERE name = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (benchmark_name, start_date.isoformat(), end_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return {
                    "status": "no_baseline",
                    "message": "No baseline data available"
                }
            
            # 计算基线统计
            baseline_mean_times = [row[0] for row in rows]
            baseline_ops = [row[2] for row in rows]
            
            baseline_stats = {
                "mean_time": np.mean(baseline_mean_times) if baseline_mean_times else 0,
                "std_dev": np.std(baseline_mean_times) if baseline_mean_times else 0,
                "ops_per_second": np.mean(baseline_ops) if baseline_ops else 0
            }
            
            # 比较当前结果与基线
            current_mean_time = current_result.get("mean_time", 0)
            current_ops = current_result.get("ops_per_second", 0)
            
            comparison = {
                "status": "completed",
                "benchmark_name": benchmark_name,
                "current": {
                    "mean_time": current_mean_time,
                    "ops_per_second": current_ops
                },
                "baseline": baseline_stats,
                "differences": {
                    "mean_time_diff": current_mean_time - baseline_stats["mean_time"],
                    "mean_time_ratio": current_mean_time / baseline_stats["mean_time"] if baseline_stats["mean_time"] > 0 else 0,
                    "ops_diff": current_ops - baseline_stats["ops_per_second"],
                    "ops_ratio": current_ops / baseline_stats["ops_per_second"] if baseline_stats["ops_per_second"] > 0 else 0
                },
                "regression_detected": False
            }
            
            # 检测性能回归（当前性能比基线差5%以上）
            if (current_mean_time > baseline_stats["mean_time"] * 1.05 or 
                current_ops < baseline_stats["ops_per_second"] * 0.95):
                comparison["regression_detected"] = True
                comparison["regression_severity"] = "high" if (
                    current_mean_time > baseline_stats["mean_time"] * 1.1 or 
                    current_ops < baseline_stats["ops_per_second"] * 0.9
                ) else "medium"
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing with baseline: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_benchmark_report(self, suite_results: Dict[str, Any], 
                                output_file: str = None) -> str:
        """
        生成基准测试报告
        
        Args:
            suite_results: 套件结果
            output_file: 输出文件路径
            
        Returns:
            str: 生成的报告路径
        """
        if output_file is None:
            output_file = self.benchmarks_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_file = Path(output_file)
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(suite_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Benchmark report generated: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error generating benchmark report: {e}")
            return ""


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        """初始化资源监控器"""
        self.monitoring = False
        self.monitoring_task = None
        self.stats = {
            "cpu_percent": [],
            "memory_mb": [],
            "disk_io_read": 0,
            "disk_io_write": 0
        }
        self.start_disk_io = None
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.start_disk_io = self._get_disk_io()
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        self._update_disk_io()
    
    async def _monitor_loop(self):
        """监控循环"""
        try:
            while self.monitoring:
                # 收集CPU和内存使用情况
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_mb = psutil.virtual_memory().used / (1024 * 1024)
                
                self.stats["cpu_percent"].append(cpu_percent)
                self.stats["memory_mb"].append(memory_mb)
                
                await asyncio.sleep(0.5)  # 每0.5秒收集一次
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
    
    def _get_disk_io(self) -> tuple:
        """获取磁盘IO统计"""
        try:
            disk_io = psutil.disk_io_counters()
            return (disk_io.read_bytes, disk_io.write_bytes)
        except Exception:
            return (0, 0)
    
    def _update_disk_io(self):
        """更新磁盘IO统计"""
        if self.start_disk_io:
            end_disk_io = self._get_disk_io()
            self.stats["disk_io_read"] = end_disk_io[0] - self.start_disk_io[0]
            self.stats["disk_io_write"] = end_disk_io[1] - self.start_disk_io[1]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.stats["cpu_percent"]:
            return self.stats
        
        return {
            "cpu_percent": np.mean(self.stats["cpu_percent"]) if self.stats["cpu_percent"] else 0,
            "memory_mb": np.mean(self.stats["memory_mb"]) if self.stats["memory_mb"] else 0,
            "disk_io_read": self.stats["disk_io_read"],
            "disk_io_write": self.stats["disk_io_write"]
        }


# 示例基准测试函数
def example_benchmark_function():
    """示例基准测试函数"""
    # 模拟一些计算工作
    result = 0
    for i in range(1000):
        result += i * i
    return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Benchmark Framework")
    parser.add_argument(
        "action",
        choices=["run", "suite", "compare", "report"],
        help="Action to perform"
    )
    parser.add_argument(
        "--name",
        help="Benchmark name"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Warmup iterations"
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        help="Tags for the benchmark"
    )
    parser.add_argument(
        "--output",
        help="Output file for reports"
    )
    
    args = parser.parse_args()
    
    # 创建基准测试框架
    framework = PerformanceBenchmarkFramework()
    
    # 执行操作
    if args.action == "run":
        if not args.name:
            print("Error: --name is required for run action")
            sys.exit(1)
        
        # 注册并运行单个基准测试
        benchmark = framework.register_benchmark(
            args.name, 
            example_benchmark_function,
            iterations=args.iterations,
            warmup=args.warmup
        )
        
        result = framework.run_benchmark(benchmark, tags=args.tags)
        print(f"Benchmark result for {args.name}:")
        print(json.dumps(result, indent=2))
        
    elif args.action == "suite":
        # 运行基准测试套件
        benchmarks = [
            framework.register_benchmark("example_benchmark_1", example_benchmark_function),
            framework.register_benchmark("example_benchmark_2", example_benchmark_function)
        ]
        
        suite_results = framework.run_benchmark_suite(benchmarks, args.iterations, args.tags)
        print(f"Benchmark suite results:")
        print(json.dumps(suite_results, indent=2))
        
        # 生成报告
        report_file = framework.generate_benchmark_report(suite_results, args.output)
        if report_file:
            print(f"Benchmark report generated: {report_file}")
        
    elif args.action == "compare":
        if not args.name:
            print("Error: --name is required for compare action")
            sys.exit(1)
        
        # 这里需要实际的基准测试结果来进行比较
        print(f"Comparison functionality would compare {args.name} with historical baseline")
        
    elif args.action == "report":
        # 生成报告功能已经在suite中包含
        print("Use 'suite' action with --output to generate reports")


if __name__ == "__main__":
    main()