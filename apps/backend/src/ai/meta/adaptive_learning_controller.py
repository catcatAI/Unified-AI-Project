import logging
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
try:
    import numpy as np
except ImportError:
    np = None

from .learning_log_db import LearningLogDB

logger = logging.getLogger(__name__)

class PerformanceTracker:
    async def analyze_trend(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.debug("Analyzing performance trend...")
        if not performance_history or len(performance_history) < 2:
            return {"direction": "stable", "magnitude": 0.0}

        if np is None:
            # Simple fallback trend analysis
            last = performance_history[-1].get("success_rate", 0.0)
            prev = performance_history[-2].get("success_rate", 0.0)
            diff = last - prev
            return {"direction": "improving" if diff > 0 else "degrading" if diff < 0 else "stable", "magnitude": abs(diff)}

        # Use last 10 entries
        N = min(len(performance_history), 10)
        recent_success_rates = np.array([entry.get("success_rate", 0.0) for entry in performance_history[-N:]])
        x = np.arange(N)
        y = recent_success_rates
        
        slope = 0.0
        if N > 1 and np.std(x) > 0:
            slope, _ = np.polyfit(x, y, 1)
        
        magnitude = abs(slope) * 100
        direction = "improving" if slope > 0.01 else "degrading" if slope < -0.01 else "stable"
        return {"direction": direction, "magnitude": magnitude, "slope": slope}

class StrategySelector:
    def __init__(self):
        self.confidence_score = 0.7

    async def select(self, task_context: Dict[str, Any], performance_trend: Dict[str, Any]) -> str:
        logger.debug("Selecting optimal strategy...")
        direction = performance_trend.get("direction", "stable")
        if direction == "degrading":
            return "new_exploration_strategy"
        return "current_strategy"

class AdaptiveLearningController:
    """自適應學習控制器 (Adaptive Learning Controller)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, storage_path: str = "logs/learning_controller") -> None:
        self.config = config or {}
        self.current_strategy = self.config.get("default_strategy", "balanced")
        self.performance_history: List[Dict[str, Any]] = []
        self.learning_rate = self.config.get("initial_learning_rate", 0.01)

    async def adapt_learning_strategy(self, task: Dict[str, Any], evolution_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根據演化指標調整學習策略。
        """
        logger.info(f"Adapting learning strategy based on {len(evolution_metrics)} metrics.")
        
        # 1. 追蹤表現
        avg_success = sum(m.get('success_rate', 0) for m in evolution_metrics) / max(1, len(evolution_metrics))
        
        # 2. 選擇最佳策略
        new_strategy = self._select_best_strategy(avg_success)
        
        # 3. 調整參數
        param_updates = self._adjust_parameters(avg_success)

        old_strategy = self.current_strategy
        self.current_strategy = new_strategy
        
        result = {
            "previous_strategy": old_strategy,
            "new_strategy": new_strategy,
            "parameter_updates": param_updates,
            "timestamp": datetime.now().isoformat()
        }
        
        self.performance_history.append(result)
        return result

    def _select_best_strategy(self, success_rate: float) -> str:
        """基於成功率選擇策略"""
        if success_rate < 0.5:
            return "conservative"  # 降低風險，專注於基礎穩定性
        elif success_rate > 0.9:
            return "aggressive"   # 嘗試更高難度的學習與探索
        return "balanced"

    def _adjust_parameters(self, success_rate: float) -> Dict[str, Any]:
        """動態調整超參數"""
        updates = {}
        if success_rate < 0.7:
            # 增加學習率以更快適應失敗
            self.learning_rate *= 1.1
            updates["learning_rate"] = self.learning_rate
        elif success_rate > 0.95:
            # 減少學習率以穩定成果
            self.learning_rate *= 0.9
            updates["learning_rate"] = self.learning_rate
            
        return updates

    def get_current_configuration(self) -> Dict[str, Any]:
        """返回當前配置"""
        return {
            "strategy": self.current_strategy,
            "learning_rate": self.learning_rate
        }
