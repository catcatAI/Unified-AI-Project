"""
Angela AI v6.0 - Physiological Tactile Analysis
生理触觉分析模块

Trajectory analysis, receptor adaptation mechanism, and related data structures.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import math
import logging
from core.system.config.magic_numbers import cache_value

from .physiological_tactile_types import (
    ReceptorType,
    TactileType,
    BodyRegion,
    BodyPart,
    Receptor,
    TactileStimulus,
    EmotionalTactileMapping,
    TactileResponse,
    Live2DTouchResponse,
    BODY_TO_LIVE2D_MAPPING,
)

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryPoint:
    """轨迹点 / Trajectory point"""

    x: float
    y: float
    timestamp: datetime = field(default_factory=datetime.now)
    pressure: float = 0.0  # 压力值 (0-1)


@dataclass
class TrajectoryAnalysis:
    """轨迹分析结果 / Trajectory analysis result"""

    velocity: float  # 速度 (px/s)
    acceleration: float  # 加速度 (px/s²)
    curvature: float  # 曲率
    movement_pattern: str  # 运动模式
    pattern_confidence: float  # 模式置信度 (0-1)
    total_distance: float  # 总距离 (px)
    duration: float  # 持续时间 (s)


class TrajectoryAnalyzer:
    """
    轨迹分析器 / Trajectory Analyzer

    Analyzes touch trajectory data to compute velocity, acceleration,
    curvature, and classify movement patterns.

    Features:
    - Velocity calculation (px/s)
    - Acceleration calculation (px/s²)
    - 7 movement pattern recognition (line, curve, fast, slow, jitter, slide, still)
    - Curvature analysis

    Example:
        >>> analyzer = TrajectoryAnalyzer()
        >>>
        >>> # Add trajectory points
        >>> analyzer.add_point(0, 0)
        >>> analyzer.add_point(10, 5)
        >>> analyzer.add_point(25, 12)
        >>>
        >>> # Analyze trajectory
        >>> analysis = analyzer.analyze()
        >>> print(f"Velocity: {analysis.velocity:.2f} px/s")
        >>> print(f"Pattern: {analysis.movement_pattern}")
    """

    # 运动模式定义 / Movement pattern definitions
    MOVEMENT_PATTERNS = {
        "line": {"cn": "直线", "velocity_var": 0.1, "curvature_max": 0.05},
        "curve": {"cn": "曲线", "velocity_var": 0.2, "curvature_min": 0.05},
        "fast": {"cn": "快速", "velocity_min": 300.0},
        "slow": {"cn": "慢速", "velocity_max": 50.0},
        "jitter": {"cn": "抖动", "accel_var": 5000.0, "direction_changes": 3},
        "slide": {"cn": "滑动", "velocity_stable": 0.15, "duration_min": 0.5},
        "still": {"cn": "静止", "velocity_max": 5.0, "duration_min": 1.0},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trajectory analyzer

        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}
        self.points: List[TrajectoryPoint] = []
        self.max_points: int = self.config.get("max_points", 1000)
        self.min_points_for_analysis: int = self.config.get("min_points", 3)

        # Analysis cache
        self._last_analysis: Optional[TrajectoryAnalysis] = None
        self._analysis_timestamp: Optional[datetime] = None

    def add_point(self, x: float, y: float, pressure: float = 0.0) -> None:
        """
        Add a trajectory point

        Args:
            x: X coordinate
            y: Y coordinate
            pressure: Pressure value (0-1)
        """
        point = TrajectoryPoint(x=x, y=y, pressure=pressure)
        self.points.append(point)

        # Maintain maximum size
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def add_points(self, points: List[Tuple[float, float, float]]) -> None:
        """
        Add multiple trajectory points at once

        Args:
            points: List of (x, y, pressure) tuples
        """
        for x, y, pressure in points:
            self.add_point(x, y, pressure)

    def clear(self) -> None:
        """Clear all trajectory points"""
        self.points.clear()
        self._last_analysis = None
        self._analysis_timestamp = None

    def analyze(self) -> TrajectoryAnalysis:
        """
        Analyze the complete trajectory and return analysis results

        Returns:
            TrajectoryAnalysis object containing computed metrics
        """
        if len(self.points) < self.min_points_for_analysis:
            return TrajectoryAnalysis(
                velocity=0.0,
                acceleration=0.0,
                curvature=0.0,
                movement_pattern="insufficient_data",
                pattern_confidence=0.0,
                total_distance=0.0,
                duration=0.0,
            )

        # Calculate basic metrics
        velocities = self._calculate_velocities()
        accelerations = self._calculate_accelerations()

        avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0
        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0.0

        # Calculate curvature
        curvature = self._calculate_curvature()

        # Calculate total distance and duration
        total_distance = self._calculate_total_distance()
        duration = self._calculate_duration()

        # Classify movement pattern
        pattern, confidence = self._classify_pattern(velocities, accelerations, curvature, duration)

        analysis = TrajectoryAnalysis(
            velocity=avg_velocity,
            acceleration=avg_acceleration,
            curvature=curvature,
            movement_pattern=pattern,
            pattern_confidence=confidence,
            total_distance=total_distance,
            duration=duration,
        )

        self._last_analysis = analysis
        self._analysis_timestamp = datetime.now()

        return analysis

    def _calculate_velocities(self) -> List[float]:
        """计算每段速度 / Calculate velocities between consecutive points"""
        velocities = []

        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]

            # Distance
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance = math.sqrt(dx**2 + dy**2)

            # Time
            dt = (p2.timestamp - p1.timestamp).total_seconds()
            if dt > 0:
                velocity = distance / dt
                velocities.append(velocity)

        return velocities

    def _calculate_accelerations(self) -> List[float]:
        """计算加速度 / Calculate accelerations"""
        velocities = self._calculate_velocities()
        accelerations = []

        for i in range(1, len(velocities)):
            dv = velocities[i] - velocities[i - 1]
            dt = (self.points[i + 1].timestamp - self.points[i].timestamp).total_seconds()
            if dt > 0:
                acceleration = dv / dt
                accelerations.append(acceleration)

        return accelerations

    def _calculate_curvature(self) -> float:
        """计算平均曲率 / Calculate average curvature"""
        if len(self.points) < 3:
            return 0.0

        curvatures = []

        for i in range(1, len(self.points) - 1):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            p3 = self.points[i + 1]

            # Calculate curvature using three points
            curvature = self._compute_curvature_three_points(p1, p2, p3)
            curvatures.append(curvature)

        return sum(curvatures) / len(curvatures) if curvatures else 0.0

    def _compute_curvature_three_points(
        self, p1: TrajectoryPoint, p2: TrajectoryPoint, p3: TrajectoryPoint
    ) -> float:
        """计算三点曲率 / Compute curvature from three points"""
        # Vector from p1 to p2
        v1x = p2.x - p1.x
        v1y = p2.y - p1.y

        # Vector from p2 to p3
        v2x = p3.x - p2.x
        v2y = p3.y - p2.y

        # Cross product magnitude (area of parallelogram)
        cross = abs(v1x * v2y - v1y * v2x)

        # Product of magnitudes
        mag1 = math.sqrt(v1x**2 + v1y**2)
        mag2 = math.sqrt(v2x**2 + v2y**2)

        if mag1 * mag2 == 0:
            return 0.0

        # Curvature = 2 * area / (|v1| * |v2| * |v1 + v2|)
        # Simplified: use cross product
        curvature = cross / (mag1 * mag2)

        return curvature

    def _calculate_total_distance(self) -> float:
        """计算总距离 / Calculate total trajectory distance"""
        total = 0.0

        for i in range(1, len(self.points)):
            dx = self.points[i].x - self.points[i - 1].x
            dy = self.points[i].y - self.points[i - 1].y
            total += math.sqrt(dx**2 + dy**2)

        return total

    def _calculate_duration(self) -> float:
        """计算持续时间 / Calculate total duration"""
        if len(self.points) < 2:
            return 0.0

        return (self.points[-1].timestamp - self.points[0].timestamp).total_seconds()

    def _classify_pattern(
        self, velocities: List[float], accelerations: List[float], curvature: float, duration: float
    ) -> Tuple[str, float]:
        """
        分类运动模式 / Classify movement pattern

        Returns:
            Tuple of (pattern_name, confidence)
        """
        if not velocities:
            return "insufficient_data", 0.0

        avg_velocity = sum(velocities) / len(velocities)
        max(velocities)
        min(velocities)
        velocity_variance = self._calculate_variance(velocities)

        sum(accelerations) / len(accelerations) if accelerations else 0.0
        accel_variance = self._calculate_variance(accelerations) if accelerations else 0.0

        # Count direction changes (for jitter detection)
        direction_changes = self._count_direction_changes()

        # Pattern scoring
        scores = {}

        # Still pattern
        if avg_velocity < 5.0 and duration > 0.5:
            scores["still"] = 1.0 - (avg_velocity / 5.0)

        # Fast pattern
        if avg_velocity > 300.0:
            scores["fast"] = min(1.0, avg_velocity / 500.0)

        # Slow pattern
        if avg_velocity < 50.0 and duration > 0.3:
            scores["slow"] = 1.0 - (avg_velocity / 50.0)

        # Jitter pattern
        if direction_changes >= 3 or accel_variance > 5000.0:
            jitter_score = min(1.0, direction_changes / 5.0)
            jitter_score = max(jitter_score, min(1.0, accel_variance / 10000.0))
            scores["jitter"] = jitter_score

        # Slide pattern
        if velocity_variance < 0.15 and duration > 0.5 and avg_velocity > 20.0:
            scores["slide"] = 1.0 - velocity_variance / 0.15

        # Line pattern
        if curvature < 0.05 and velocity_variance < 0.2:
            scores["line"] = 1.0 - curvature / 0.05

        # Curve pattern
        if curvature > 0.05:
            scores["curve"] = min(1.0, curvature / 0.2)

        # Select best pattern
        if not scores:
            return "unclassified", 0.0

        best_pattern = max(scores.items(), key=lambda x: x[1])[0]
        return best_pattern, scores[best_pattern]

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差 / Calculate variance"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        return sum(squared_diffs) / len(squared_diffs)

    def _count_direction_changes(self) -> int:
        """统计方向变化次数 / Count direction changes"""
        if len(self.points) < 3:
            return 0

        changes = 0

        for i in range(2, len(self.points)):
            # Vectors
            v1x = self.points[i - 1].x - self.points[i - 2].x
            v1y = self.points[i - 1].y - self.points[i - 2].y
            v2x = self.points[i].x - self.points[i - 1].x
            v2y = self.points[i].y - self.points[i - 1].y

            # Dot product
            dot = v1x * v2x + v1y * v2y

            # If dot product is negative, direction changed significantly
            mag1 = math.sqrt(v1x**2 + v1y**2)
            mag2 = math.sqrt(v2x**2 + v2y**2)

            if mag1 > 0 and mag2 > 0:
                cos_angle = dot / (mag1 * mag2)
                # Significant direction change (angle > 90 degrees)
                if cos_angle < 0:
                    changes += 1

        return changes

    def get_realtime_metrics(self) -> Dict[str, float]:
        """
        获取实时指标 / Get real-time trajectory metrics

        Returns:
            Dictionary with current velocity, acceleration, etc.
        """
        if len(self.points) < 2:
            return {"velocity": 0.0, "acceleration": 0.0, "curvature": 0.0}

        # Use last few points for real-time metrics
        recent_points = self.points[-10:] if len(self.points) >= 10 else self.points

        # Calculate velocity from last segment
        p1 = recent_points[-2]
        p2 = recent_points[-1]
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dt = (p2.timestamp - p1.timestamp).total_seconds()

        velocity = math.sqrt(dx**2 + dy**2) / dt if dt > 0 else 0.0

        # Calculate acceleration if possible
        acceleration = 0.0
        if len(recent_points) >= 3:
            p0 = recent_points[-3]
            dt1 = (p1.timestamp - p0.timestamp).total_seconds()
            dt2 = dt

            if dt1 > 0 and dt2 > 0:
                v1 = math.sqrt((p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2) / dt1
                v2 = velocity
                acceleration = (v2 - v1) / ((dt1 + dt2) / 2)

        return {
            "velocity": velocity,
            "acceleration": acceleration,
            "curvature": self._calculate_curvature(),
        }


@dataclass
class ReceptorAdaptationState:
    """受体适应状态 / Receptor adaptation state"""

    receptor_id: str
    base_sensitivity: float
    current_sensitivity: float
    habituation_level: float  # 习惯化水平 (0-1)
    last_stimulus_type: Optional[str] = None
    stimulus_count: int = 0
    last_adaptation_time: datetime = field(default_factory=datetime.now)


class AdaptationMechanism:
    """
    适应机制 / Adaptation Mechanism

    Implements dynamic receptor sensitivity adjustment, habituation (reduced
    sensitivity to repeated stimuli), dishabituation (recovery to new stimuli),
    and adaptation speed control.

    Features:
    - Dynamic receptor sensitivity adjustment
    - Habituation (reduced sensitivity to repeated stimuli)
    - Dishabituation (recovery when new stimulus detected)
    - Adaptation speed control

    Example:
        >>> mechanism = AdaptationMechanism()
        >>>
        >>> # Register a receptor
        >>> mechanism.register_receptor("hand_meissner", base_sensitivity=0.8)
        >>>
        >>> # Process repeated stimulus (habituation)
        >>> for _ in range(10):
        ...     state = mechanism.process_stimulus("hand_meissner", "touch")
        ...     print(f"Sensitivity: {state.current_sensitivity:.3f}")

        >>> # New stimulus triggers dishabituation
        >>> state = mechanism.process_stimulus("hand_meissner", "vibration")
        >>> print(f"Recovered sensitivity: {state.current_sensitivity:.3f}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptation mechanism

        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}

        # Adaptation parameters
        self.habituation_rate: float = self.config.get("habituation_rate", 0.05)
        self.dishabituation_boost: float = self.config.get("dishabituation_boost", 0.3)
        self.recovery_rate: float = self.config.get("recovery_rate", 0.02)
        self.min_sensitivity: float = self.config.get("min_sensitivity", 0.1)
        self.max_sensitivity: float = self.config.get("max_sensitivity", 1.0)

        # Receptor states
        self.receptor_states: Dict[str, ReceptorAdaptationState] = {}

        # Stimulus history for pattern detection
        self.stimulus_history: Dict[str, List[Tuple[str, datetime]]] = {}
        self.max_history: int = self.config.get("max_history", cache_value("tactile_stimulus_history", 50))

    def register_receptor(
        self, receptor_id: str, base_sensitivity: float = 0.5, initial_habituation: float = 0.0
    ) -> ReceptorAdaptationState:
        """
        注册受体 / Register a receptor for adaptation tracking

        Args:
            receptor_id: Unique receptor identifier
            base_sensitivity: Base sensitivity level (0-1)
            initial_habituation: Initial habituation level (0-1)

        Returns:
            ReceptorAdaptationState object
        """
        state = ReceptorAdaptationState(
            receptor_id=receptor_id,
            base_sensitivity=base_sensitivity,
            current_sensitivity=base_sensitivity * (1 - initial_habituation),
            habituation_level=initial_habituation,
        )

        self.receptor_states[receptor_id] = state
        self.stimulus_history[receptor_id] = []

        return state

    def process_stimulus(
        self, receptor_id: str, stimulus_type: str, intensity: float = 1.0
    ) -> ReceptorAdaptationState:
        """
        处理刺激并更新适应状态 / Process stimulus and update adaptation state

        Args:
            receptor_id: Receptor identifier
            stimulus_type: Type of stimulus
            intensity: Stimulus intensity (0-1)

        Returns:
            Updated ReceptorAdaptationState
        """
        # Ensure receptor is registered
        if receptor_id not in self.receptor_states:
            self.register_receptor(receptor_id)

        state = self.receptor_states[receptor_id]

        # Update history
        self._update_stimulus_history(receptor_id, stimulus_type)

        # Check for stimulus change (dishabituation trigger)
        if state.last_stimulus_type is not None and state.last_stimulus_type != stimulus_type:
            # Dishabituation - new stimulus type detected
            self._apply_dishabituation(state, intensity)
        else:
            # Habituation - repeated stimulus
            self._apply_habituation(state, stimulus_type, intensity)

        # Update metadata
        state.last_stimulus_type = stimulus_type
        state.stimulus_count += 1
        state.last_adaptation_time = datetime.now()

        return state

    def _update_stimulus_history(self, receptor_id: str, stimulus_type: str) -> None:
        """更新刺激历史 / Update stimulus history"""
        if receptor_id not in self.stimulus_history:
            self.stimulus_history[receptor_id] = []

        history = self.stimulus_history[receptor_id]
        history.append((stimulus_type, datetime.now()))

        # Maintain maximum size
        if len(history) > self.max_history:
            history.pop(0)

    def _apply_habituation(
        self, state: ReceptorAdaptationState, stimulus_type: str, intensity: float
    ) -> None:
        """
        应用习惯化 / Apply habituation (sensitivity reduction)

        Repeated stimuli reduce receptor sensitivity.
        """
        # Count recent repetitions
        history = self.stimulus_history.get(state.receptor_id, [])
        recent_repetitions = self._count_recent_repetitions(history, stimulus_type)

        # Calculate habituation amount based on repetition count
        # More repetitions = stronger habituation, but with diminishing returns
        habituation_factor = 1 - math.exp(-recent_repetitions * self.habituation_rate)

        # Apply habituation
        state.habituation_level = min(1.0, habituation_factor)

        # Calculate new sensitivity
        target_sensitivity = state.base_sensitivity * (1 - state.habituation_level)

        # Gradual adaptation (don't change too quickly)
        state.current_sensitivity = state.current_sensitivity * 0.7 + target_sensitivity * 0.3

        # Ensure bounds
        state.current_sensitivity = max(
            self.min_sensitivity, min(self.max_sensitivity, state.current_sensitivity)
        )

    def _apply_dishabituation(self, state: ReceptorAdaptationState, intensity: float) -> None:
        """
        应用去习惯化 / Apply dishabituation (sensitivity recovery)

        New stimuli trigger sensitivity recovery.
        """
        # Calculate recovery amount based on stimulus intensity
        recovery = self.dishabituation_boost * intensity

        # Reduce habituation level
        state.habituation_level = max(0.0, state.habituation_level - recovery)

        # Boost sensitivity
        target_sensitivity = state.base_sensitivity * (1 - state.habituation_level)
        boosted_sensitivity = target_sensitivity * (1 + recovery * 0.5)

        # Apply with some immediate effect and some gradual
        state.current_sensitivity = min(
            self.max_sensitivity, max(target_sensitivity, boosted_sensitivity)
        )

    def _count_recent_repetitions(
        self, history: List[Tuple[str, datetime]], stimulus_type: str, window_seconds: float = 30.0
    ) -> int:
        """统计近期重复次数 / Count recent repetitions of a stimulus type"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        return sum(1 for st, ts in history if st == stimulus_type and ts > cutoff)

    async def update(self, delta_time: float = 1.0) -> None:
        """
        更新适应状态（恢复） / Update adaptation states (recovery)

        Gradually recovers sensitivity when no stimuli present.

        Args:
            delta_time: Time since last update (seconds)
        """
        for state in self.receptor_states.values():
            # Calculate time since last stimulus
            time_since = (datetime.now() - state.last_adaptation_time).total_seconds()

            # Gradual recovery if no recent stimuli
            if time_since > 5.0:  # 5 seconds without stimulus
                # Gradually reduce habituation
                recovery_amount = self.recovery_rate * delta_time
                state.habituation_level = max(0.0, state.habituation_level - recovery_amount)

                # Gradually restore sensitivity toward base
                target = state.base_sensitivity * (1 - state.habituation_level)
                state.current_sensitivity = state.current_sensitivity * 0.95 + target * 0.05

    def get_adaptation_state(self, receptor_id: str) -> Optional[ReceptorAdaptationState]:
        """获取受体适应状态 / Get adaptation state for a receptor"""
        return self.receptor_states.get(receptor_id)

    def get_all_states(self) -> Dict[str, ReceptorAdaptationState]:
        """获取所有受体状态 / Get all receptor states"""
        return self.receptor_states.copy()

    def reset_receptor(self, receptor_id: str) -> None:
        """重置受体到初始状态 / Reset receptor to initial state"""
        if receptor_id in self.receptor_states:
            state = self.receptor_states[receptor_id]
            state.current_sensitivity = state.base_sensitivity
            state.habituation_level = 0.0
            state.stimulus_count = 0
            state.last_stimulus_type = None
            self.stimulus_history[receptor_id] = []

    def set_adaptation_speed(
        self, habituation_rate: Optional[float] = None, recovery_rate: Optional[float] = None
    ) -> None:
        """
        设置适应速度 / Set adaptation speed parameters

        Args:
            habituation_rate: New habituation rate (optional)
            recovery_rate: New recovery rate (optional)
        """
        if habituation_rate is not None:
            self.habituation_rate = habituation_rate
        if recovery_rate is not None:
            self.recovery_rate = recovery_rate
