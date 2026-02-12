#!/usr/bin/env python3
# Angela Matrix Annotation:
# α (Alpha): Cognition - Database query optimization and analysis
# β (Beta): Emotion - Neutral (query processing)
# γ (Gamma): Perception - Query pattern detection
# δ (Delta): Volition - Optimization decision making

"""
数据库查询优化器 - 企业级数据库性能优化
"""

import asyncio
import json
import logging
import time
import hashlib
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# from enhanced_realtime_monitoring import  # Fixed: commented out incomplete import
# from tests.tools.test_tool_dispatcher_logging import  # Fixed: commented out incomplete import
# from tests.test_json_fix import  # Fixed: commented out incomplete import
# from tests.core_ai import  # Fixed: commented out incomplete import
# from sqlalchemy import text  # Fixed: commented out - may not be available
# from sqlalchemy.orm import sessionmaker  # Fixed: commented out - may not be available
# from sqlalchemy.pool import StaticPool  # Fixed: commented out - may not be available
# import aioredis  # Fixed: commented out - may not be available

logger = logging.getLogger(__name__)

@dataclass
class QueryPlan:
    """查询计划"""
    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    index_used: Optional[str]
    optimization_suggestions: List[str] = field(default_factory=list)

@dataclass
class QueryMetrics:
    """查询指标"""
    query_hash: str
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_executed: datetime
    error_count: int

class QueryOptimizer:
    """查询优化器"""

    def __init__(self, db_url: str, redis_url: str = "redis://localhost:6379"):
        self.db_url = db_url
        self.redis_url = redis_url
        self.engine = None
        self.session_factory = None
        self.redis = None
        self.query_metrics = {}
        self.slow_query_threshold = 1.0  # 慢查询阈值(秒)

        # 查询模式分析
        self.query_patterns = {
            "select_all": r"SELECT\s+\*\s+FROM",
            "missing_where": r"SELECT.*FROM\s+\w+\s*(?!.*WHERE)",
            "n_plus_one": r"SELECT.*FROM.*WHERE.*IN\s*\(",
            "cartesian_product": r"FROM\s+\w+\s*,\s+\w+.*WHERE",
            "like_leading_wildcard": r"LIKE\s+'%.*%'",
            "order_by_without_limit": r"ORDER\s+BY.*(?!.*)LIMIT",
            "missing_index": None  # 需要实际执行计划分析
        }

        logger.info("查询优化器初始化完成")

    async def initialize(self):
        """初始化连接"""
        # Simplified version - actual implementation would use SQLAlchemy
        logger.info("查询优化器初始化完成")

    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话"""
        # Simplified - actual implementation would use SQLAlchemy session
        yield None

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """执行查询并记录指标"""
        query_hash = self._hash_query(query)
        start_time = time.time()

        try:
            # Simplified - actual implementation would execute the query
            async with self.get_session() as session:
                # result = await session.execute(text(query), params or {})
                # rows = result.fetchall()
                # data = [dict(row._mapping) for row in rows]
                data = []

                # 记录成功指标
                execution_time = time.time() - start_time
                await self._record_query_metrics(query_hash, execution_time, True)

                # 检查是否为慢查询
                if execution_time > self.slow_query_threshold:
                    await self._analyze_slow_query(query, execution_time)

                return data

        except Exception as e:
           logger.error(f'Error in {__name__}: {e}', exc_info=True)
           
# 记录错误指标
            execution_time = time.time() - start_time
            await self._record_query_metrics(query_hash, execution_time, False)
            logger.error(f"查询执行失败: {e}")
            raise

    def _hash_query(self, query: str) -> str:
        """生成查询哈希"""
        normalized_query = re.sub(r'\s+', ' ', query.strip().upper())
        return hashlib.md5(normalized_query.encode()).hexdigest()

    async def _record_query_metrics(self, query_hash: str, execution_time: float, success: bool):
        """记录查询指标"""
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                execution_count=0,
                total_time=0.0,
                avg_time=0.0,
                min_time=float('inf'),
                max_time=0.0,
                last_executed=datetime.now(),
                error_count=0
            )

        metrics = self.query_metrics[query_hash]
        metrics.execution_count += 1

        if success:
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.execution_count
            metrics.min_time = min(metrics.min_time, execution_time)
            metrics.max_time = max(metrics.max_time, execution_time)
        else:
            metrics.error_count += 1

        metrics.last_executed = datetime.now()

        # 保存到Redis
        await self._save_metrics_to_redis(query_hash, metrics)

    async def _save_metrics_to_redis(self, query_hash: str, metrics: QueryMetrics):
        """保存指标到Redis"""
        try:
            metrics_data = {
                "execution_count": metrics.execution_count,
                "total_time": metrics.total_time,
                "avg_time": metrics.avg_time,
                "min_time": metrics.min_time,
                "max_time": metrics.max_time,
                "last_executed": metrics.last_executed.isoformat(),
                "error_count": metrics.error_count
            }
            # Simplified - actual implementation would use Redis
            # await self.redis.hset(f"query_metrics:{query_hash}", mapping=metrics_data)
        except Exception as e:
            logger.error(f"保存指标到Redis失败: {e}")

    async def _analyze_slow_query(self, query: str, execution_time: float):
        """分析慢查询"""
        logger.warning(f"检测到慢查询 ({execution_time:.2f}s): {query[:100]}...")

        # 分析查询模式
        issues = []
        for pattern_name, pattern in self.query_patterns.items():
            if pattern and re.search(pattern, query, re.IGNORECASE):
                issues.append(pattern_name)

        # 生成优化建议
        suggestions = self._generate_optimization_suggestions(query, issues)

        # 记录慢查询
        slow_query_data = {
            "query": query,
            "execution_time": execution_time,
            "issues": issues,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }

        # Simplified - actual implementation would use Redis
        # await self.redis.lpush("slow_queries", json.dumps(slow_query_data))
        # await self.redis.ltrim("slow_queries", 0, 999)

    def _generate_optimization_suggestions(self, query: str, issues: List[str]) -> List[str]:
        """生成优化建议"""
        suggestions = []

        if "select_all" in issues:
            suggestions.append("避免使用SELECT *，只查询需要的列")

        if "missing_where" in issues:
            suggestions.append("添加WHERE条件限制查询范围")

        if "n_plus_one" in issues:
            suggestions.append("使用JOIN替代N+1查询")

        if "cartesian_product" in issues:
            suggestions.append("添加适当的JOIN条件避免笛卡尔积")

        if "like_leading_wildcard" in issues:
            suggestions.append("避免使用前导通配符的LIKE查询")

        if "order_by_without_limit" in issues:
            suggestions.append("ORDER BY应配合LIMIT使用")

        # 通用建议
        if self.slow_query_threshold > 5.0:
            suggestions.append("考虑分页查询")
            suggestions.append("检查是否缺少适当的索引")

        return suggestions

    async def get_query_plan(self, query: str) -> QueryPlan:
        """获取查询执行计划"""
        try:
            async with self.get_session() as session:
                # Simplified - actual implementation would use EXPLAIN ANALYZE
                execution_time = 0.0
                rows_examined = 0
                index_used = None
                suggestions = []

                return QueryPlan(
                    query=query,
                    execution_time=execution_time,
                    rows_examined=rows_examined,
                    rows_returned=0,
                    index_used=index_used,
                    optimization_suggestions=suggestions
                )

        except Exception as e:
            logger.error(f"获取查询计划失败: {e}")
            return QueryPlan(
                query=query,
                execution_time=0.0,
                rows_examined=0,
                rows_returned=0,
                index_used=None,
                optimization_suggestions=["无法获取执行计划"]
            )

    def _extract_execution_time(self, plan_text: str) -> float:
        """提取执行时间"""
        match = re.search(r'Execution Time:\s*([\d.]+)\s*ms', plan_text)
        if match:
            return float(match.group(1)) / 1000  # 转换为秒
        return 0.0

    def _extract_rows_examined(self, plan_text: str) -> int:
        """提取扫描行数"""
        match = re.search(r'rows=(\d+)', plan_text)
        if match:
            return int(match.group(1))
        return 0

    def _extract_index_used(self, plan_text: str) -> Optional[str]:
        """提取使用的索引"""
        match = re.search(r'Index\s+Scan\s+using\s+(\w+)', plan_text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _analyze_execution_plan(self, plan_text: str) -> List[str]:
        """分析执行计划"""
        suggestions = []

        if "Seq Scan" in plan_text:
            suggestions.append("考虑添加索引以避免全表扫描")

        if "Sort" in plan_text and "Index Scan" not in plan_text:
            suggestions.append("考虑添加排序索引")

        if "Hash Join" in plan_text:
            suggestions.append("考虑使用嵌套循环或合并连接")

        if "Materialize" in plan_text:
            suggestions.append("考虑重写查询避免物化")

        return suggestions

    async def get_slow_queries(self, limit: int = 100) -> List[Dict]:
        """获取慢查询列表"""
        try:
            # Simplified - actual implementation would use Redis
            # slow_queries = await self.redis.lrange("slow_queries", 0, limit - 1)
            # return [json.loads(q) for q in slow_queries]
            return []
        except Exception as e:
            logger.error(f"获取慢查询失败: {e}")
            return []

    async def get_query_metrics(self, query_hash: str = None) -> Union[QueryMetrics, Dict[str, QueryMetrics]]:
        """获取查询指标"""
        if query_hash:
            return self.query_metrics.get(query_hash)
        return self.query_metrics

    def get_slowest_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """获取最慢的查询"""
        sorted_queries = sorted(
            self.query_metrics.values(),
            key=lambda x: x.avg_time,
            reverse=True
        )
        return sorted_queries[:limit]

    def get_most_frequent_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """获取最频繁的查询"""
        sorted_queries = sorted(
            self.query_metrics.values(),
            key=lambda x: x.execution_count,
            reverse=True
        )
        return sorted_queries[:limit]

    async def optimize_table_indexes(self, table_name: str) -> List[str]:
        """优化表索引"""
        suggestions = []

        try:
            async with self.get_session() as session:
                # Simplified - actual implementation would analyze table indexes
                suggestions = ["需要实现实际的表索引分析"]

        except Exception as e:
            logger.error(f"优化表索引失败: {e}")
            suggestions.append("无法分析表索引")

        return suggestions

    async def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """分析表性能"""
        try:
            async with self.get_session() as session:
                # Simplified - actual implementation would analyze table performance
                return {
                    "table_name": table_name,
                    "size": "N/A",
                    "column_stats": []
                }

        except Exception as e:
            logger.error(f"分析表性能失败: {e}")
            return {"error": str(e)}

# 全局查询优化器
query_optimizer = None

async def get_query_optimizer() -> QueryOptimizer:
    """获取查询优化器实例"""
    global query_optimizer
    if query_optimizer is None:
        db_url = "sqlite+aiosqlite:///./data/unified_ai.db"
        query_optimizer = QueryOptimizer(db_url)
        await query_optimizer.initialize()
    return query_optimizer

# 便捷函数
async def execute_optimized_query(query: str, params: Dict = None) -> List[Dict]:
    """执行优化查询"""
    optimizer = await get_query_optimizer()
    return await optimizer.execute_query(query, params)

async def get_slow_queries(limit: int = 100) -> List[Dict]:
    """获取慢查询"""
    optimizer = await get_query_optimizer()
    return await optimizer.get_slow_queries(limit)

async def analyze_query_performance(query: str) -> QueryPlan:
    """分析查询性能"""
    optimizer = await get_query_optimizer()
    return await optimizer.get_query_plan(query)