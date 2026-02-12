"""
Angela AI v6.0 - 4D State Matrix System
4D状态矩阵系统

独立的4D状态矩阵管理系统，整合所有维度的状态。

Features:
- 4-dimensional state matrix (α, β, γ, δ)
- Inter-dimensional influence computation
- State persistence and history
- Comprehensive state analysis

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
import asyncio
import json
import logging
logger = logging.getLogger(__name__)


@dataclass
class DimensionState:
    """
    维度状态 / Dimension State
    
    Represents the state of a single dimension in the 4D matrix.
    """
    name: str
    cn_name: str
    values: Dict[str, float]
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_average(self) -> float:
        """获取维度平均值 / Get average value"""
        if not self.values:
            return 0.0
        return sum(self.values.values()) / len(self.values)
    
    def get_dominant(self) -> Tuple[str, float]:
        """获取主导指标 / Get dominant metric"""
        if not self.values:
            return ("", 0.0)
        return max(self.values.items(), key=lambda x: x[1])
    
    def update(self, **kwargs) -> None:
        """更新维度值 / Update dimension values"""
        for key, value in kwargs.items():
            if key in self.values:
                self.values[key] = max(0.0, min(1.0, float(value)))
        self.timestamp = datetime.now()


class StateMatrix4D:
    """
    4D状态矩阵系统 / 4D State Matrix System
    
    A comprehensive state management system that integrates all dimensions
    of Angela's internal state into a unified 4-dimensional matrix.
    
    Dimensions:
    - α (Alpha): Physiological (生理)
      - energy, comfort, arousal, rest_need
    - β (Beta): Cognitive (认知)
      - curiosity, focus, confusion, learning
    - γ (Gamma): Emotional (情感)
      - happiness, sadness, anger, fear, disgust, surprise, trust, anticipation
    - δ (Delta): Social (社交)
      - attention, bond, trust, presence
    
    Features:
    - Real-time state tracking
    - Inter-dimensional influence modeling
    - State history and persistence
    - Comprehensive state analysis
    - Event-driven state changes
    
    Example:
        >>> matrix = StateMatrix4D()
        >>> 
        >>> # Update individual dimensions
        >>> matrix.update_alpha(energy=0.8, comfort=0.7)
        >>> matrix.update_beta(curiosity=0.9, focus=0.8)
        >>> matrix.update_gamma(happiness=0.85, trust=0.8)
        >>> matrix.update_delta(attention=0.9, bond=0.7)
        >>> 
        >>> # Compute influences
        >>> matrix.compute_influences()
        >>> 
        >>> # Get comprehensive analysis
        >>> analysis = matrix.get_analysis()
        >>> print(f"Overall state: {analysis['overall_state']}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize 4D state matrix
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize dimensions
        self.alpha = DimensionState(
            name="alpha",
            cn_name="生理维度",
            values={
                "energy": 0.5,
                "comfort": 0.5,
                "arousal": 0.5,
                "rest_need": 0.5,
                "vitality": 0.5,
                "tension": 0.0,
            },
            weight=self.config.get("alpha_weight", 1.0)
        )
        
        self.beta = DimensionState(
            name="beta",
            cn_name="认知维度",
            values={
                "curiosity": 0.5,
                "focus": 0.5,
                "confusion": 0.0,
                "learning": 0.5,
                "clarity": 0.5,
                "creativity": 0.5,
            },
            weight=self.config.get("beta_weight", 1.0)
        )
        
        self.gamma = DimensionState(
            name="gamma",
            cn_name="情感维度",
            values={
                "happiness": 0.5,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "disgust": 0.0,
                "surprise": 0.0,
                "trust": 0.5,
                "anticipation": 0.5,
                "love": 0.0,
                "calm": 0.5,
            },
            weight=self.config.get("gamma_weight", 1.0)
        )
        
        self.delta = DimensionState(
            name="delta",
            cn_name="社交维度",
            values={
                "attention": 0.5,
                "bond": 0.5,
                "trust": 0.5,
                "presence": 0.5,
                "intimacy": 0.0,
                "engagement": 0.5,
            },
            weight=self.config.get("delta_weight", 1.0)
        )
        
        # Dimension lookup
        self.dimensions: Dict[str, DimensionState] = {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "delta": self.delta,
        }
        
        # Influence matrix (source -> target -> strength)
        self.influence_matrix: Dict[str, Dict[str, float]] = self.config.get(
            "influence_matrix",
            {
                "alpha": {"beta": 0.3, "gamma": 0.5, "delta": 0.2},
                "beta": {"alpha": 0.2, "gamma": 0.4, "delta": 0.3},
                "gamma": {"alpha": 0.4, "beta": 0.3, "delta": 0.5},
                "delta": {"alpha": 0.2, "beta": 0.3, "gamma": 0.6},
            }
        )
        
        # State history
        self.history: List[Dict[str, Any]] = []
        self.max_history: int = self.config.get("max_history", 1000)
        
        # Update tracking
        self.update_count: int = 0
        self.created_at: datetime = datetime.now()
        self.last_update: datetime = datetime.now()
        
        # Callbacks
        self._change_callbacks: List[Callable[[str, Dict[str, float]], None]] = []
        self._threshold_callbacks: Dict[str, List[Tuple[float, Callable[[], None]]]] = {}
    
    def update_alpha(self, **kwargs) -> None:
        """更新α维度 / Update alpha dimension (physiological)"""
        self.alpha.update(**kwargs)
        self._post_update("alpha")
    
    def update_beta(self, **kwargs) -> None:
        """更新β维度 / Update beta dimension (cognitive)"""
        self.beta.update(**kwargs)
        self._post_update("beta")
    
    def update_gamma(self, **kwargs) -> None:
        """更新γ维度 / Update gamma dimension (emotional)"""
        self.gamma.update(**kwargs)
        self._post_update("gamma")
    
    def update_delta(self, **kwargs) -> None:
        """更新δ维度 / Update delta dimension (social)"""
        self.delta.update(**kwargs)
        self._post_update("delta")
    
    def _post_update(self, dimension_name: str) -> None:
        """后更新处理 / Post-update processing"""
        self.update_count += 1
        self.last_update = datetime.now()
        
        # Record to history
        self._record_history()
        
        # Trigger callbacks
        dim_state = self.dimensions[dimension_name]
        for callback in self._change_callbacks:
            try:
                callback(dimension_name, dim_state.values.copy())
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        # Check thresholds
        self._check_thresholds(dimension_name)
    
    def _record_history(self) -> None:
        """记录历史 / Record state to history"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "alpha": self.alpha.values.copy(),
            "beta": self.beta.values.copy(),
            "gamma": self.gamma.values.copy(),
            "delta": self.delta.values.copy(),
        }
        
        self.history.append(snapshot)
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def _check_thresholds(self, dimension_name: str) -> None:
        """检查阈值 / Check thresholds for callbacks"""
        if dimension_name not in self._threshold_callbacks:
            return
        
        dim = self.dimensions[dimension_name]
        avg = dim.get_average()
        
        for threshold, callback in self._threshold_callbacks[dimension_name]:
            if avg >= threshold:
                try:
                    callback()
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

    
    def compute_influences(self) -> Dict[str, Dict[str, float]]:
        """
        计算维度间影响 / Compute inter-dimensional influences
        
        Calculates and applies how each dimension affects others.
        
        Returns:
            Dictionary of computed influences
        """
        computed: Dict[str, Dict[str, float]] = {}
        
        for source_name, targets in self.influence_matrix.items():
            computed[source_name] = {}
            source_dim = self.dimensions[source_name]
            source_avg = source_dim.get_average()
            
            for target_name, base_strength in targets.items():
                target_dim = self.dimensions[target_name]
                
                # Calculate actual influence
                influence = base_strength * source_avg * source_dim.weight * target_dim.weight
                computed[source_name][target_name] = influence
                
                # Apply influence
                self._apply_influence(source_name, target_name, influence)
        
        return computed
    
    def _apply_influence(self, source: str, target: str, amount: float) -> None:
        """应用影响 / Apply influence from source to target dimension"""
        source_dim = self.dimensions[source]
        target_dim = self.dimensions[target]
        
        # Dimension-specific influence logic
        if target == "alpha":  # Physiological
            if source == "gamma":  # Emotional -> Physiological
                happiness = source_dim.values.get("happiness", 0.5)
                target_dim.values["energy"] = min(1.0, target_dim.values["energy"] + amount * happiness * 0.1)
                target_dim.values["comfort"] = min(1.0, target_dim.values["comfort"] + amount * happiness * 0.08)
                target_dim.values["tension"] = max(0.0, target_dim.values["tension"] - amount * happiness * 0.1)
            
            if source == "beta":  # Cognitive -> Physiological
                focus = source_dim.values.get("focus", 0.5)
                target_dim.values["arousal"] = min(1.0, target_dim.values["arousal"] + amount * focus * 0.05)
        
        elif target == "beta":  # Cognitive
            if source == "alpha":  # Physiological -> Cognitive
                energy = source_dim.values.get("energy", 0.5)
                target_dim.values["focus"] = min(1.0, target_dim.values["focus"] + amount * energy * 0.1)
                target_dim.values["clarity"] = min(1.0, target_dim.values["clarity"] + amount * energy * 0.08)
            
            if source == "gamma":  # Emotional -> Cognitive
                calm = source_dim.values.get("calm", 0.5)
                target_dim.values["focus"] = min(1.0, target_dim.values["focus"] + amount * calm * 0.1)
                fear = source_dim.values.get("fear", 0.0)
                target_dim.values["confusion"] = min(1.0, target_dim.values["confusion"] + amount * fear * 0.15)
        
        elif target == "gamma":  # Emotional
            if source == "alpha":  # Physiological -> Emotional
                comfort = source_dim.values.get("comfort", 0.5)
                target_dim.values["happiness"] = min(1.0, target_dim.values["happiness"] + amount * comfort * 0.1)
                target_dim.values["calm"] = min(1.0, target_dim.values["calm"] + amount * comfort * 0.08)
            
            if source == "delta":  # Social -> Emotional
                bond = source_dim.values.get("bond", 0.5)
                target_dim.values["happiness"] = min(1.0, target_dim.values["happiness"] + amount * bond * 0.12)
                target_dim.values["trust"] = min(1.0, target_dim.values["trust"] + amount * bond * 0.1)
        
        elif target == "delta":  # Social
            if source == "gamma":  # Emotional -> Social
                happiness = source_dim.values.get("happiness", 0.5)
                target_dim.values["engagement"] = min(1.0, target_dim.values["engagement"] + amount * happiness * 0.1)
                target_dim.values["presence"] = min(1.0, target_dim.values["presence"] + amount * happiness * 0.08)
            
            if source == "beta":  # Cognitive -> Social
                curiosity = source_dim.values.get("curiosity", 0.5)
                target_dim.values["attention"] = min(1.0, target_dim.values["attention"] + amount * curiosity * 0.1)
    
    def get_state(self, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        获取状态 / Get current state
        
        Args:
            dimension: Optional dimension name (returns all if None)
            
        Returns:
            State dictionary
        """
        if dimension:
            if dimension in self.dimensions:
                return self.dimensions[dimension].values.copy()
            return {}
        
        return {
            "alpha": self.alpha.values.copy(),
            "beta": self.beta.values.copy(),
            "gamma": self.gamma.values.copy(),
            "delta": self.delta.values.copy(),
        }
    
    def get_dimension_averages(self) -> Dict[str, float]:
        """获取所有维度平均值 / Get averages for all dimensions"""
        return {
            "alpha": self.alpha.get_average(),
            "beta": self.beta.get_average(),
            "gamma": self.gamma.get_average(),
            "delta": self.delta.get_average(),
        }
    
    def get_analysis(self) -> Dict[str, Any]:
        """
        综合分析 / Comprehensive state analysis
        
        Returns:
            Analysis dictionary with computed metrics
        """
        averages = self.get_dimension_averages()
        
        # Overall state score
        overall = sum(averages.values()) / len(averages)
        
        # Wellbeing (weighted combination)
        wellbeing = (
            averages["alpha"] * 0.25 +
            averages["beta"] * 0.20 +
            averages["gamma"] * 0.35 +
            averages["delta"] * 0.20
        )
        
        # Arousal level
        arousal = (
            self.alpha.values["arousal"] * 0.4 +
            self.gamma.values["surprise"] * 0.3 +
            (1 - self.gamma.values["calm"]) * 0.3
        )
        
        # Valence (positive/negative)
        positive = self.gamma.values["happiness"] + self.gamma.values["trust"] + self.gamma.values["love"]
        negative = self.gamma.values["sadness"] + self.gamma.values["anger"] + self.gamma.values["fear"]
        valence = (positive - negative) / 3  # -1 to 1
        
        # Dominant dimension
        if averages:
            dominant_dim = max(averages.items(), key=lambda x: x[1])[0]
        else:
            dominant_dim = None
        
        # Dominant emotions
        dominant_emotion = self.gamma.get_dominant()
        
        return {
            "averages": averages,
            "overall": overall,
            "wellbeing": wellbeing,
            "arousal": arousal,
            "valence": valence,
            "dominant_dimension": dominant_dim,
            "dominant_emotion": dominant_emotion,
            "update_count": self.update_count,
            "last_update": self.last_update.isoformat(),
        }
    
    def get_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取历史记录 / Get state history
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of historical state snapshots
        """
        filtered = self.history.copy()
        
        if start_time:
            filtered = [h for h in filtered if datetime.fromisoformat(h["timestamp"]) >= start_time]
        
        if end_time:
            filtered = [h for h in filtered if datetime.fromisoformat(h["timestamp"]) <= end_time]
        
        return filtered
    
    def set_dimension_weight(self, dimension: str, weight: float) -> None:
        """设置维度权重 / Set dimension weight"""
        if dimension in self.dimensions:
            self.dimensions[dimension].weight = weight
    
    def set_influence_strength(self, source: str, target: str, strength: float) -> None:
        """设置影响强度 / Set influence strength between dimensions"""
        if source in self.influence_matrix and target in self.influence_matrix[source]:
            self.influence_matrix[source][target] = max(0.0, min(1.0, strength))
    
    def register_change_callback(self, callback: Callable[[str, Dict[str, float]], None]) -> None:
        """注册变化回调 / Register change callback"""
        self._change_callbacks.append(callback)
    
    def register_threshold_callback(
        self,
        dimension: str,
        threshold: float,
        callback: Callable[[], None]
    ) -> None:
        """注册阈值回调 / Register threshold callback"""
        if dimension not in self._threshold_callbacks:
            self._threshold_callbacks[dimension] = []
        self._threshold_callbacks[dimension].append((threshold, callback))
    
    def reset(self) -> None:
        """重置所有维度 / Reset all dimensions to default values"""
        for dim in self.dimensions.values():
            for key in dim.values:
                dim.values[key] = 0.5 if key not in ["sadness", "anger", "fear", "disgust", "confusion", "tension", "intimacy"] else 0.0
            dim.timestamp = datetime.now()
        
        self.update_count = 0
        self.history.clear()
        self.last_update = datetime.now()
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典 / Export state to dictionary"""
        return {
            "alpha": self.alpha.values,
            "beta": self.beta.values,
            "gamma": self.gamma.values,
            "delta": self.delta.values,
            "weights": {name: dim.weight for name, dim in self.dimensions.items()},
            "influence_matrix": self.influence_matrix,
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_update": self.last_update.isoformat(),
                "update_count": self.update_count,
            },
        }
    
    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入 / Import state from dictionary"""
        if "alpha" in data:
            self.alpha.values.update(data["alpha"])
        if "beta" in data:
            self.beta.values.update(data["beta"])
        if "gamma" in data:
            self.gamma.values.update(data["gamma"])
        if "delta" in data:
            self.delta.values.update(data["delta"])
        
        if "weights" in data:
            for name, weight in data["weights"].items():
                if name in self.dimensions:
                    self.dimensions[name].weight = weight
        
        if "influence_matrix" in data:
            self.influence_matrix = data["influence_matrix"]
        
        self.last_update = datetime.now()
    
    def export_to_json(self) -> str:
        """导出为JSON / Export state to JSON string"""
        return json.dumps(self.export_to_dict(), indent=2)
    
    def import_from_json(self, json_str: str) -> None:
        """从JSON导入 / Import state from JSON string"""
        data = json.loads(json_str)
        self.import_from_dict(data)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Angela AI v6.0 - 4D状态矩阵系统演示")
    print("4D State Matrix System Demo")
    print("=" * 60)
    
    # Initialize matrix
    matrix = StateMatrix4D()
    
    print("\n1. 初始维度状态 / Initial dimension states:")
    for name, dim in matrix.dimensions.items():
        print(f"   {name} ({dim.cn_name}): {dim.get_average():.2f}")
    
    print("\n2. 更新各维度 / Updating dimensions:")
    matrix.update_alpha(energy=0.8, comfort=0.7, arousal=0.6)
    matrix.update_beta(curiosity=0.9, focus=0.85, learning=0.7)
    matrix.update_gamma(happiness=0.85, trust=0.8, calm=0.75)
    matrix.update_delta(attention=0.9, bond=0.7, presence=0.6)
    
    for name, dim in matrix.dimensions.items():
        print(f"   {name}: {dim.get_average():.2f}")
    
    print("\n3. 计算维度间影响 / Computing inter-dimensional influences:")
    influences = matrix.compute_influences()
    for source, targets in influences.items():
        print(f"   {source} -> {targets}")
    
    print("\n4. 影响后的维度状态 / States after influences:")
    for name, dim in matrix.dimensions.items():
        print(f"   {name}: {dim.get_average():.2f}")
    
    print("\n5. 综合分析 / Comprehensive analysis:")
    analysis = matrix.get_analysis()
    print(f"   总体状态 / Overall: {analysis['overall']:.2f}")
    print(f"   幸福感 / Wellbeing: {analysis['wellbeing']:.2f}")
    print(f"   唤醒度 / Arousal: {analysis['arousal']:.2f}")
    print(f"   情感效价 / Valence: {analysis['valence']:.2f}")
    print(f"   主导维度 / Dominant dimension: {analysis['dominant_dimension']}")
    print(f"   主导情感 / Dominant emotion: {analysis['dominant_emotion']}")
    
    print("\n6. 历史记录 / History:")
    print(f"   记录数量 / Records: {len(matrix.history)}")
    print(f"   更新次数 / Updates: {matrix.update_count}")
    
    print("\n7. 导出状态 / Export state:")
    state_json = matrix.export_to_json()
    print(f"   JSON长度 / JSON length: {len(state_json)} chars")
    
    print("\n系统演示完成 / Demo complete")
