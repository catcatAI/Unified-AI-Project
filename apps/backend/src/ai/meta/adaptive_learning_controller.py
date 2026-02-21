import logging
import asyncio
import os
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """分析性能趨勢，為控制器提供優化依據。"""
    async def analyze_trend(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not performance_history or len(performance_history) < 3:
            return {"direction": "stable", "magnitude": 0.0, "slope": 0.0}

        # 提取最近的成功率
        recent_data = [h.get("success_rate", 0.0) for h in performance_history[-10:]]
        
        if np:
            x = np.arange(len(recent_data))
            y = np.array(recent_data)
            slope, _ = np.polyfit(x, y, 1)
        else:
            # 簡易線性回歸回退方案
            n = len(recent_data)
            x = list(range(n))
            y = recent_data
            mean_x = sum(x) / n
            mean_y = sum(y) / n
            num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            den = sum((x[i] - mean_x) ** 2 for i in range(n))
            slope = num / den if den != 0 else 0.0

        direction = "improving" if slope > 0.02 else "degrading" if slope < -0.02 else "stable"
        return {
            "direction": direction,
            "magnitude": abs(slope),
            "slope": slope
        }

class AdaptiveLearningController:
    """
    自適應學習控制器 (Adaptive Learning Controller)
    Level 5 ASI 核心組件：負責動態調整 AGI 的學習參數與策略。
    深度集成趨勢分析與趨準優化。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.current_strategy = self.config.get("default_strategy", "balanced")
        self.performance_history: List[Dict[str, Any]] = []
        self.learning_rate = self.config.get("initial_learning_rate", 0.05)
        self.tracker = PerformanceTracker()
        logger.info("AdaptiveLearningController (Advanced Trend-Aware) initialized.")

    async def adapt_learning_strategy(self, task: Dict[str, Any], evolution_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根據性能趨勢與當前指標調整學習參數。"""
        # 1. 記錄當前性能快照
        if evolution_metrics:
            latest = evolution_metrics[-1]
            self.performance_history.append({
                "success_rate": latest.get("success_rate", 0.0),
                "timestamp": datetime.now().timestamp() # Changed time.time() to datetime.now().timestamp()
            })

        # 2. 分析趨勢 (Deep Scrutiny)
        trend = await self.tracker.analyze_trend(self.performance_history)
        
        # 3. 執行策略選擇與參數優化
        new_strategy = self._determine_strategy(trend)
        param_updates = self._optimize_parameters(trend, evolution_metrics)

        old_strategy = self.current_strategy
        self.current_strategy = new_strategy
        
        result = {
            "previous_strategy": old_strategy,
            "new_strategy": new_strategy,
            "trend": trend["direction"],
            "parameter_updates": param_updates,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Strategy adapted: {old_strategy} -> {new_strategy} | Trend: {trend['direction']}")
        return result

    def _determine_strategy(self, trend: Dict[str, Any]) -> str:
        """基於趨勢方向選取策略。"""
        direction = trend["direction"]
        if direction == "degrading":
            return "explorative_recovery" # 趨勢下滑，切換到探索/修復模式
        elif direction == "improving" and trend["slope"] > 0.1:
            return "acceleration"         # 表現強勁，加速學習
        return "stable_optimization"      # 穩定或緩慢增長時的默認策略

    def _optimize_parameters(self, trend: Dict[str, Any], metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        精細化參數優化邏輯。
        使用趨勢斜率來調整學習率，而非簡單的閾值判斷。
        """
        updates = {}
        slope = trend.get("slope", 0.0)
        
        # 根據斜率動態調整 Learning Rate (LR)
        lr_factor = 1.0 - (slope * 0.5) 
        
        # 集成認知紅利與生命強度：高紅利允許更穩健的學習，低生命強度則需要更保守
        latest_metrics = metrics[-1] if metrics else {}
        cog_dividend = latest_metrics.get("cognitive_dividend", 0.5)
        life_intensity = latest_metrics.get("life_intensity_impact", 0.5)
        
        # 生命強度越低，學習率越趨於保守 (避免在低能量狀態下過度擬合錯誤)
        lr_factor *= (0.5 + life_intensity * 0.5)
        
        # 認知紅利越高，可以適度增加學習效率
        if cog_dividend > 0.7:
            lr_factor *= 1.1
            
        lr_factor = max(0.3, min(2.0, lr_factor))
        
        self.learning_rate *= lr_factor
        self.learning_rate = max(0.001, min(0.5, self.learning_rate))
        
        updates["learning_rate"] = round(self.learning_rate, 4)
        updates["adaptation_factor"] = lr_factor
        
        return updates

    def get_current_configuration(self) -> Dict[str, Any]:
        return {
            "strategy": self.current_strategy,
            "learning_rate": self.learning_rate,
            "history_depth": len(self.performance_history)
        }
