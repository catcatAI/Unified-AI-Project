import asyncio
import logging
import json
import os
from .learning_log_db import LearningLogDB
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Placeholder classes
class PerformanceTracker:
    async def analyze_trend(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.debug("Analyzing performance trend...")
        await asyncio.sleep(0.01) # Simulate async work

        if len(performance_history) < 2: # Need at least 2 points for a trend
            return {"direction": "stable", "magnitude": 0.0}

        # Use last N entries for trend analysis
        N = min(len(performance_history), 10) # Analyze last 10 entries or fewer if not enough
        recent_success_rates = np.array([entry.get("success_rate", 0) for entry in performance_history[-N:]])
        
        # Simple linear regression to find the slope
        x = np.arange(N)
        y = recent_success_rates

        if N > 1 and np.std(x) > 0: # Ensure there's variance in x for slope calculation
            slope, intercept = np.polyfit(x, y, 1)
        else:
            slope = 0.0 # No meaningful slope if only one point or no variance

        magnitude = abs(slope) * 100 # Scale slope for better readability

        if slope > 0.01: # Positive slope indicates improving
            direction = "improving"
        elif slope < -0.01: # Negative slope indicates degrading
            direction = "degrading"
        else:
            direction = "stable" # Near zero slope

        return {"direction": direction, "magnitude": magnitude, "slope": slope}

class StrategySelector:
    def __init__(self):
        self.confidence_score = 0.7 # Initial confidence

    async def select(self, task_context: Dict[str, Any], performance_trend: Dict[str, Any]) -> str:
        logger.debug("Selecting optimal strategy...")
        await asyncio.sleep(0.01) # Simulate async work

        trend_direction = performance_trend.get("direction", "stable")
        trend_magnitude = performance_trend.get("magnitude", 0.0)
        task_complexity = task_context.get("complexity_level", 0.5) # Default to medium complexity

        # Define thresholds for decision making
        IMPROVING_THRESHOLD = 0.5 # Magnitude for significant improvement
        DEGRADING_THRESHOLD = 0.5 # Magnitude for significant degradation
        COMPLEX_TASK_THRESHOLD = 0.7
        LOW_CONFIDENCE_THRESHOLD = 0.6

        if trend_direction == "improving":
            if trend_magnitude > IMPROVING_THRESHOLD and self.confidence_score < 0.9:
                # If significantly improving and not highly confident, stick to current but consider minor adjustments
                return "current_strategy"
            else:
                return "current_strategy" # Continue with current strategy
        elif trend_direction == "degrading":
            if trend_magnitude > DEGRADING_THRESHOLD:
                if task_complexity > COMPLEX_TASK_THRESHOLD:
                    # Significant degradation on complex task, try new exploration
                    return "new_exploration_strategy"
                else:
                    # Significant degradation on simple task, try new exploration
                    return "new_exploration_strategy"
            else:
                # Minor degradation, might stick to current for a bit longer
                return "current_strategy"
        else: # Stable
            if task_complexity > COMPLEX_TASK_THRESHOLD and self.confidence_score < LOW_CONFIDENCE_THRESHOLD:
                # Stable but complex task and low confidence, try new exploration
                return "new_exploration_strategy"
            elif self.confidence_score < LOW_CONFIDENCE_THRESHOLD:
                # Stable but low confidence, try new exploration
                return "new_exploration_strategy"
            else:
                return "current_strategy"

class AdaptiveLearningController:
    """自適應學習控制器"""
    
    def __init__(self, config: Dict[str, Any], storage_path: str = "logs/learning_controller"):
        self.config = config
        self.learning_strategies = self._initialize_strategies() # Conceptual method
        self.performance_tracker = PerformanceTracker()
        self.strategy_selector = StrategySelector()
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.db = LearningLogDB(db_path=os.path.join(self.storage_path, "learning_logs.db"))

    async def adapt_learning_strategy(self, task_context: Dict[str, Any], performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """自適應調整學習策略"""
        # 分析當前性能趨勢
        performance_trend = await self.performance_tracker.analyze_trend(
            performance_history
        )
        
        # 選擇最適合的學習策略
        optimal_strategy_name = await self.strategy_selector.select(
            task_context, performance_trend
        )
        
        # 獲取實際的策略對象 (conceptual lookup)
        optimal_strategy = self.learning_strategies.get(optimal_strategy_name, {}) # type: ignore

        # 調整學習參數
        learning_params = await self._optimize_parameters(
            optimal_strategy_name, optimal_strategy, task_context
        )
        
        return {
            'strategy': optimal_strategy_name,
            'parameters': learning_params,
            'confidence': self.strategy_selector.confidence_score
        }
    
    async def _optimize_parameters(self, strategy_id: str, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """優化學習參數"""
        base_params = strategy.get("default_parameters", {"learning_rate": 0.01, "exploration_rate": 0.1})
        
        # 基於任務複雜度調整
        complexity_factor = await self._assess_task_complexity(context)
        base_params['learning_rate'] *= (1.0 / (complexity_factor + 0.1)) # Avoid division by zero
        
        # 基於歷史表現調整
        historical_performance = await self._get_historical_performance(strategy_id)
        if historical_performance < 0.7:  # 表現不佳
            base_params['exploration_rate'] = min(0.5, base_params['exploration_rate'] * 1.5)  # 增加探索，設定上限
        else:
            base_params['exploration_rate'] *= 0.9 # 表現良好，減少探索
        
        return base_params
    
    async def update_strategy_effectiveness(self, strategy_id: str, performance_result: Dict[str, Any]):
        """更新策略有效性"""
        strategy = self.learning_strategies.get(strategy_id) # type: ignore
        if strategy:
            # Conceptual: update strategy's internal effectiveness metric
            current_effectiveness = strategy.get("effectiveness", 0.5) # type: ignore
            if performance_result.get("success_rate", 0) > 0.8:
                strategy["effectiveness"] = min(1.0, current_effectiveness + 0.05) # type: ignore
            else:
                strategy["effectiveness"] = max(0.0, current_effectiveness - 0.05) # type: ignore

            self.logger.info(f"Strategy {strategy_id} effectiveness updated to {strategy['effectiveness']}") # type: ignore

            # 如果策略表現持續不佳，標記為需要改進
            if strategy["effectiveness"] < 0.5: # type: ignore
                await self._schedule_strategy_improvement(strategy_id, strategy)
        else:
            self.logger.warning(f"Strategy {strategy_id} not found for effectiveness update.")

    def _initialize_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Conceptual: Initializes a dictionary of available learning strategies."""
        return {
            "current_strategy": {"default_parameters": {"learning_rate": 0.01, "exploration_rate": 0.1}, "effectiveness": 0.8},
            "new_exploration_strategy": {"default_parameters": {"learning_rate": 0.02, "exploration_rate": 0.3}, "effectiveness": 0.6},
            # Add more strategies here
        }

    async def _assess_task_complexity(self, context: Dict[str, Any]) -> float:
        """Assesses the complexity of a task based on its context.
        For MVP, it checks for keywords in the task description or uses a complexity_level from context.
        """
        self.logger.debug("Assessing task complexity...")
        await asyncio.sleep(0.005) # Simulate work

        # Prioritize explicit complexity level from context
        if 'complexity_level' in context:
            return context['complexity_level']

        description = context.get("description", "").lower()

        if "complex" in description or "multi-step" in description:
            return 0.8 # High complexity
        elif "simple" in description or "single-step" in description:
            return 0.2 # Low complexity
        elif "research" in description or "explore" in description:
            return 0.7 # Medium-high complexity

        return 0.5 # Default to medium complexity

    async def _get_historical_performance(self, strategy_id: str) -> float:
        """Fetches historical performance for a given strategy from the database."""
        self.logger.debug(f"Fetching historical performance for strategy {strategy_id} from database...")
        await asyncio.sleep(0.005) # Simulate async read if needed
        
        all_logs = self.db.get_all_log_entries(strategy_id=strategy_id)
        if not all_logs:
            return 0.75 # Default if no history
        
        total_effectiveness = sum(log.get("current_effectiveness", 0.0) for log in all_logs)
        return total_effectiveness / len(all_logs)

    async def _schedule_strategy_improvement(self, strategy_id: str, strategy: Dict[str, Any]):
        """將需要改進的策略記錄到資料庫中。"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "strategy_id": strategy_id,
            "current_effectiveness": strategy.get("effectiveness"),
            "message": "Strategy requires review and improvement."
        }
        
        self.logger.warning(f"Scheduling improvement for strategy {strategy_id}")
        try:
            self.db.add_log_entry(log_entry)
            await asyncio.sleep(0.005) # Simulate async write if needed
        except Exception as e:
            self.logger.error(f"Failed to log strategy for improvement to database: {e}")
