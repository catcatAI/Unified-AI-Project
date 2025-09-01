"""
自适应学习控制器
实现完整的自适应学习控制功能，包括性能跟踪器、策略选择器和学习策略优化
"""

import asyncio
import logging
import json
import os
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)

@dataclass
class PerformanceRecord:
    """性能记录"""
    timestamp: float
    task_id: str
    success_rate: float
    response_time: float
    accuracy: float
    learning_progress: float

@dataclass
class LearningStrategy:
    """学习策略"""
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    effectiveness: float  # 策略有效性 (0-1)
    last_used: Optional[float] = None

@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    complexity_level: float  # 任务复杂度 (0-1)
    domain: str  # 任务领域
    description: str
    previous_performance: Optional[List[PerformanceRecord]] = None

class PerformanceTracker:
    """性能跟踪器"""
    
    def __init__(self, db_path: str = "performance_tracker.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                task_id TEXT NOT NULL,
                success_rate REAL NOT NULL,
                response_time REAL NOT NULL,
                accuracy REAL NOT NULL,
                learning_progress REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        
    async def record_performance(self, record: PerformanceRecord):
        """记录性能数据"""
        logger.debug(f"Recording performance for task {record.task_id}")
        await asyncio.sleep(0.005)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_records 
            (timestamp, task_id, success_rate, response_time, accuracy, learning_progress)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.timestamp,
            record.task_id,
            record.success_rate,
            record.response_time,
            record.accuracy,
            record.learning_progress
        ))
        conn.commit()
        conn.close()
        
    async def get_performance_history(self, task_id: str, limit: int = 50) -> List[PerformanceRecord]:
        """获取任务的性能历史"""
        logger.debug(f"Getting performance history for task {task_id}")
        await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, task_id, success_rate, response_time, accuracy, learning_progress
            FROM performance_records 
            WHERE task_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (task_id, limit))
        
        records = []
        for row in cursor.fetchall():
            record = PerformanceRecord(
                timestamp=row[0],
                task_id=row[1],
                success_rate=row[2],
                response_time=row[3],
                accuracy=row[4],
                learning_progress=row[5]
            )
            records.append(record)
            
        conn.close()
        return records
        
    async def analyze_trend(self, performance_history: List[PerformanceRecord]) -> Dict[str, Any]:
        """分析性能趋势"""
        logger.debug("Analyzing performance trend")
        await asyncio.sleep(0.01)
        
        if len(performance_history) < 2:
            return {"direction": "stable", "magnitude": 0.0, "slope": 0.0}
            
        # 使用最近N条记录进行趋势分析
        N = min(len(performance_history), 10)
        recent_success_rates = np.array([record.success_rate for record in performance_history[:N]])
        
        # 简单线性回归计算斜率
        x = np.arange(N)
        y = recent_success_rates
        
        if N > 1 and np.std(x) > 0:
            slope, intercept = np.polyfit(x, y, 1)
        else:
            slope = 0.0
            
        magnitude = abs(slope) * 100  # 缩放斜率以提高可读性
        
        if slope > 0.01:
            direction = "improving"
        elif slope < -0.01:
            direction = "degrading"
        else:
            direction = "stable"
            
        return {
            "direction": direction,
            "magnitude": magnitude,
            "slope": slope
        }

class StrategySelector:
    """策略选择器"""
    
    def __init__(self):
        self.confidence_score = 0.7  # 初始置信度
        self.strategy_history = {}  # 策略使用历史
        # 添加策略选择神经网络
        self.policy_network = self._build_policy_network()
        self.optimizer = optim.Adam(self.policy_network.parameters(), lr=0.001)
        
    def _build_policy_network(self):
        """构建策略网络"""
        # 简单的策略选择网络
        model = nn.Sequential(
            nn.Linear(10, 64),  # 假设有10个输入特征
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3),    # 3种策略选择
            nn.Softmax(dim=-1)
        )
        return model
    
    async def select(self, task_context: TaskContext, 
                    performance_trend: Dict[str, Any]) -> str:
        """选择最优学习策略"""
        logger.debug(f"Selecting optimal strategy for task {task_context.task_id}")
        await asyncio.sleep(0.01)
        
        # 准备输入特征
        features = self._context_to_features(task_context, performance_trend)
        
        # 使用神经网络选择策略
        with torch.no_grad():
            policy_output = self.policy_network(features)
            strategy_idx = torch.argmax(policy_output).item()
        
        # 将索引转换为策略ID
        strategy_map = {0: "current_strategy", 1: "exploration_strategy", 2: "conservative_strategy"}
        selected_strategy = strategy_map.get(strategy_idx, "current_strategy")
        
        return selected_strategy

    def _context_to_features(self, task_context: TaskContext, 
                           performance_trend: Dict[str, Any]) -> torch.Tensor:
        """将任务上下文和性能趋势转换为特征向量"""
        features = []
        
        # 添加任务复杂度特征
        features.append(task_context.complexity_level)
        
        # 添加性能趋势特征
        trend_direction = 0.0
        if performance_trend.get("direction") == "improving":
            trend_direction = 1.0
        elif performance_trend.get("direction") == "degrading":
            trend_direction = -1.0
        features.append(trend_direction)
        
        features.append(performance_trend.get("magnitude", 0.0))
        features.append(performance_trend.get("slope", 0.0))
        
        # 添加历史性能特征（如果有）
        if task_context.previous_performance:
            recent_success_rates = [p.success_rate for p in task_context.previous_performance[:5]]
            avg_success_rate = np.mean(recent_success_rates) if recent_success_rates else 0.5
            features.append(avg_success_rate)
            
            success_rate_std = np.std(recent_success_rates) if len(recent_success_rates) > 1 else 0.0
            features.append(success_rate_std)
        else:
            features.extend([0.5, 0.0])  # 默认值
            
        # 添加置信度特征
        features.append(self.confidence_score)
        
        # 填充到固定长度（10个特征）
        while len(features) < 10:
            features.append(0.0)
            
        return torch.FloatTensor(features).unsqueeze(0)
        
    async def update_confidence(self, strategy_id: str, performance_result: Dict[str, Any]):
        """更新策略选择置信度"""
        logger.debug(f"Updating confidence for strategy {strategy_id}")
        await asyncio.sleep(0.005)
        
        success_rate = performance_result.get("success_rate", 0)
        if success_rate > 0.8:
            self.confidence_score = min(1.0, self.confidence_score + 0.05)
        else:
            self.confidence_score = max(0.0, self.confidence_score - 0.05)
            
        # 记录策略使用历史
        if strategy_id not in self.strategy_history:
            self.strategy_history[strategy_id] = []
        self.strategy_history[strategy_id].append({
            "timestamp": datetime.now().timestamp(),
            "success_rate": success_rate
        })
        
        # 更新策略网络
        await self._update_policy_network(strategy_id, success_rate)

    async def _update_policy_network(self, strategy_id: str, success_rate: float):
        """更新策略网络"""
        # 简化的强化学习更新
        strategy_map = {"current_strategy": 0, "exploration_strategy": 1, "conservative_strategy": 2}
        target_strategy_idx = strategy_map.get(strategy_id, 0)
        
        # 创建目标分布（one-hot）
        target = torch.zeros(3)
        target[target_strategy_idx] = 1.0
        
        # 简化的损失计算和更新
        # 在实际实现中，这里会使用更复杂的强化学习算法

class LearningStrategyOptimizer:
    """学习策略优化器"""
    
    def __init__(self):
        self.strategies: Dict[str, LearningStrategy] = self._initialize_strategies()
        
    def _initialize_strategies(self) -> Dict[str, LearningStrategy]:
        """初始化学习策略"""
        return {
            "current_strategy": LearningStrategy(
                id="current_strategy",
                name="当前策略",
                description="继续使用当前学习策略",
                parameters={
                    "learning_rate": 0.01,
                    "exploration_rate": 0.1,
                    "batch_size": 32
                },
                effectiveness=0.8
            ),
            "exploration_strategy": LearningStrategy(
                id="exploration_strategy",
                name="探索策略",
                description="增加探索率以发现更好的策略",
                parameters={
                    "learning_rate": 0.02,
                    "exploration_rate": 0.3,
                    "batch_size": 16
                },
                effectiveness=0.6
            ),
            "conservative_strategy": LearningStrategy(
                id="conservative_strategy",
                name="保守策略",
                description="降低学习率以稳定学习过程",
                parameters={
                    "learning_rate": 0.005,
                    "exploration_rate": 0.05,
                    "batch_size": 64
                },
                effectiveness=0.7
            )
        }
        
    async def get_strategy(self, strategy_id: str) -> Optional[LearningStrategy]:
        """获取学习策略"""
        logger.debug(f"Getting strategy {strategy_id}")
        await asyncio.sleep(0.005)
        
        return self.strategies.get(strategy_id)
        
    async def optimize_parameters(self, strategy: LearningStrategy, 
                                context: TaskContext) -> Dict[str, Any]:
        """优化学习参数"""
        logger.debug(f"Optimizing parameters for strategy {strategy.id}")
        await asyncio.sleep(0.01)
        
        base_params = strategy.parameters.copy()
        
        # 基于任务复杂度调整
        complexity_factor = context.complexity_level
        if "learning_rate" in base_params:
            base_params['learning_rate'] *= (1.0 / (complexity_factor + 0.1))  # 避免除零
            
        # 基于历史表现调整
        if context.previous_performance:
            recent_performance = context.previous_performance[:10]  # 最近10条记录
            avg_success_rate = np.mean([p.success_rate for p in recent_performance])
            
            if avg_success_rate < 0.7:  # 表现不佳
                if "exploration_rate" in base_params:
                    base_params['exploration_rate'] = min(0.5, base_params['exploration_rate'] * 1.5)
            else:
                if "exploration_rate" in base_params:
                    base_params['exploration_rate'] *= 0.9  # 表现良好，减少探索
                    
        return base_params
        
    async def update_strategy_effectiveness(self, strategy_id: str, 
                                          performance_result: Dict[str, Any]):
        """更新策略有效性"""
        logger.debug(f"Updating strategy effectiveness for {strategy_id}")
        await asyncio.sleep(0.005)
        
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            success_rate = performance_result.get("success_rate", 0)
            
            if success_rate > 0.8:
                strategy.effectiveness = min(1.0, strategy.effectiveness + 0.05)
            else:
                strategy.effectiveness = max(0.0, strategy.effectiveness - 0.05)
                
            strategy.last_used = datetime.now().timestamp()
            logger.info(f"Strategy {strategy_id} effectiveness updated to {strategy.effectiveness:.2f}")
            
    async def get_best_strategies(self, limit: int = 3) -> List[LearningStrategy]:
        """获取最佳策略"""
        logger.debug("Getting best strategies")
        await asyncio.sleep(0.01)
        
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.effectiveness,
            reverse=True
        )
        return sorted_strategies[:limit]

class AdaptiveLearningController:
    """自适应学习控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 storage_path: str = "adaptive_learning_controller"):
        self.config = config or {}
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.performance_tracker = PerformanceTracker(
            db_path=os.path.join(self.storage_path, "performance.db")
        )
        self.strategy_selector = StrategySelector()
        self.strategy_optimizer = LearningStrategyOptimizer()
        self.logger = logging.getLogger(__name__)
        
    async def adapt_learning_strategy(self, task_context: TaskContext) -> Dict[str, Any]:
        """自适应调整学习策略"""
        # 获取性能历史
        performance_history = await self.performance_tracker.get_performance_history(
            task_context.task_id
        )
        task_context.previous_performance = performance_history
        
        # 分析性能趋势
        performance_trend = await self.performance_tracker.analyze_trend(performance_history)
        
        # 选择最优学习策略
        optimal_strategy_id = await self.strategy_selector.select(task_context, performance_trend)
        
        # 获取策略对象
        optimal_strategy = await self.strategy_optimizer.get_strategy(optimal_strategy_id)
        if not optimal_strategy:
            # 如果策略不存在，使用默认策略
            optimal_strategy = await self.strategy_optimizer.get_strategy("current_strategy")
            optimal_strategy_id = "current_strategy"
            
        # 优化学习参数
        learning_params = await self.strategy_optimizer.optimize_parameters(
            optimal_strategy, task_context
        )
        
        return {
            'strategy_id': optimal_strategy_id,
            'strategy_name': optimal_strategy.name if optimal_strategy else "Unknown",
            'parameters': learning_params,
            'confidence': self.strategy_selector.confidence_score,
            'trend': performance_trend
        }
    
    async def record_performance(self, record: PerformanceRecord):
        """记录性能数据"""
        await self.performance_tracker.record_performance(record)
        
    async def update_strategy_effectiveness(self, strategy_id: str, 
                                          performance_result: Dict[str, Any]):
        """更新策略有效性"""
        await self.strategy_optimizer.update_strategy_effectiveness(strategy_id, performance_result)
        await self.strategy_selector.update_confidence(strategy_id, performance_result)
        
    async def get_best_strategies(self, limit: int = 3) -> List[LearningStrategy]:
        """获取最佳策略"""
        return await self.strategy_optimizer.get_best_strategies(limit)
        
    async def get_performance_history(self, task_id: str, limit: int = 50) -> List[PerformanceRecord]:
        """获取性能历史"""
        return await self.performance_tracker.get_performance_history(task_id, limit)

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建自适应学习控制器
    controller = AdaptiveLearningController()
    
    # 创建测试数据
    async def test_adaptive_learning():
        # 创建任务上下文
        task_context = TaskContext(
            task_id="math_learning_task",
            complexity_level=0.6,
            domain="mathematics",
            description="Learning basic arithmetic operations"
        )
        
        # 记录一些性能数据
        for i in range(10):
            record = PerformanceRecord(
                timestamp=datetime.now().timestamp() - (10-i) * 60,  # 10分钟前到现在的数据
                task_id="math_learning_task",
                success_rate=0.7 + i * 0.03,  # 逐渐提高的成功率
                response_time=1.0 - i * 0.05,  # 逐渐减少的响应时间
                accuracy=0.75 + i * 0.02,  # 逐渐提高的准确率
                learning_progress=0.1 + i * 0.09  # 逐渐提高的学习进度
            )
            await controller.record_performance(record)
            
        # 自适应调整学习策略
        adaptation_result = await controller.adapt_learning_strategy(task_context)
        print("Adaptation result:")
        print(f"  Strategy: {adaptation_result['strategy_name']}")
        print(f"  Confidence: {adaptation_result['confidence']:.2f}")
        print(f"  Parameters: {adaptation_result['parameters']}")
        print(f"  Trend: {adaptation_result['trend']}")
        
        # 更新策略有效性
        performance_result = {
            "success_rate": 0.85,
            "response_time": 0.8,
            "accuracy": 0.88
        }
        await controller.update_strategy_effectiveness(
            adaptation_result['strategy_id'], 
            performance_result
        )
        
        # 获取最佳策略
        best_strategies = await controller.get_best_strategies()
        print(f"\nBest strategies:")
        for strategy in best_strategies:
            print(f"  - {strategy.name}: effectiveness={strategy.effectiveness:.2f}")
    
    # 运行测试
    asyncio.run(test_adaptive_learning())