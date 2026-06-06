"""
Angela AI v6.0 - Feedback Loop
反馈回路

Implements endocrine feedback regulation including:
- HPA axis (Hypothalamus-Pituitary-Adrenal axis)
- Negative feedback (cortisol inhibits CRH)
- Hormone antagonism (leptin vs ghrelin)
- Circadian rhythm (melatonin cycles)

Author: Angela AI Development Team
Version: 6.0.0
"""

# =============================================================================
# ANGELA-MATRIX: L1[生物层] α [A] L2+
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import math

from .endocrine_types import HormoneType


@dataclass
class FeedbackNode:
    """反馈节点 / Feedback node"""

    hormone_type: HormoneType
    setpoint: float  # 设定点
    current_level: float  # 当前水平
    gain: float  # 增益
    feedback_type: str  # "positive" or "negative"


class FeedbackLoop:
    """
    反馈回路 / Feedback Loop

    Implements endocrine feedback regulation including:
    - HPA axis (Hypothalamus-Pituitary-Adrenal axis)
    - Negative feedback (cortisol inhibits CRH)
    - Hormone antagonism (leptin vs ghrelin)
    - Circadian rhythm (melatonin cycles)

    Example:
        >>> feedback = FeedbackLoop()
        >>>
        >>> # Simulate HPA axis stress response
        >>> crh = 10.0  # Corticotropin-releasing hormone
        >>> acth = feedback.hpa_axis_step(crh)
        >>> cortisol = feedback.hpa_axis_step(acth, level_type="cortisol")
        >>>
        >>> # Apply negative feedback
        >>> cortisol += 50.0  # High cortisol
        >>> inhibition = feedback.negative_feedback(
        ...     HormoneType.CORTISOL,
        ...     target_hormone=HormoneType.ADRENALINE,
        ...     current_level=cortisol
        ... )
        >>> print(f"Inhibition: {inhibition:.2f}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feedback loop system

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # HPA axis parameters
        self.hpa_crh_to_acth_gain: float = self.config.get("hpa_crh_gain", 2.0)
        self.hpa_acth_to_cortisol_gain: float = self.config.get("hpa_acth_gain", 3.0)
        self.hpa_cortisol_feedback: float = self.config.get("hpa_feedback", 0.4)

        # Negative feedback parameters
        self.negative_feedback_gain: float = self.config.get("neg_feedback_gain", 0.3)
        self.positive_feedback_gain: float = self.config.get("pos_feedback_gain", 0.2)

        # Circadian parameters
        self.melatonin_peak_hour: float = self.config.get("melatonin_peak", 2.0)  # 2 AM
        self.melatonin_amplitude: float = self.config.get("melatonin_amp", 40.0)
        self.cortisol_peak_hour: float = self.config.get("cortisol_peak", 8.0)  # 8 AM
        self.cortisol_amplitude: float = self.config.get("cortisol_amp", 30.0)

        # Feedback nodes tracking
        self.feedback_nodes: Dict[HormoneType, FeedbackNode] = {}
        self._initialize_nodes()

    def _initialize_nodes(self) -> None:
        """Initialize feedback nodes for all hormones"""
        for hormone_type in HormoneType:
            self.feedback_nodes[hormone_type] = FeedbackNode(
                hormone_type=hormone_type,
                setpoint=50.0,
                current_level=50.0,
                gain=0.5,
                feedback_type="negative",
            )

    def hpa_axis_step(
        self, input_level: float, level_type: str = "crh", cortisol_level: float = 20.0
    ) -> float:
        """
        HPA轴单步模拟 / HPA axis single step simulation

        Simulates: CRH -> ACTH -> Cortisol with negative feedback

        Args:
            input_level: Input hormone level (CRH or ACTH)
            level_type: "crh", "acth", or "cortisol"
            cortisol_level: Current cortisol level (for feedback calculation)

        Returns:
            Output hormone level
        """
        if level_type == "crh":
            # CRH stimulates ACTH release
            # Apply cortisol negative feedback
            feedback_inhibition = self.hpa_cortisol_feedback * (cortisol_level / 100.0)
            output = input_level * self.hpa_crh_to_acth_gain * (1 - feedback_inhibition)
            return max(0.0, output)

        elif level_type == "acth":
            # ACTH stimulates cortisol release
            output = input_level * self.hpa_acth_to_cortisol_gain
            return max(0.0, min(100.0, output))

        elif level_type == "cortisol":
            # Cortisol has self-inhibitory effects
            # High cortisol suppresses further production
            inhibition = (cortisol_level / 100.0) ** 2
            output = input_level * (1 - inhibition * 0.5)
            return max(0.0, output)

        return input_level

    def simulate_hpa_axis(
        self, stress_input: float, simulation_hours: float = 2.0, time_step: float = 0.1
    ) -> Dict[str, List[float]]:
        """
        完整HPA轴模拟 / Full HPA axis simulation

        Args:
            stress_input: Initial stress level (triggers CRH)
            simulation_hours: Duration of simulation
            time_step: Time step in hours

        Returns:
            Dictionary with time series for CRH, ACTH, and cortisol
        """
        n_steps = int(simulation_hours / time_step)

        crh_levels = [stress_input]
        acth_levels = [5.0]  # Baseline ACTH
        cortisol_levels = [20.0]  # Baseline cortisol

        for i in range(n_steps):
            # CRH (stimulated by stress, inhibited by cortisol)
            crh_feedback = self.hpa_cortisol_feedback * (cortisol_levels[-1] / 100.0)
            crh_new = stress_input * (1 - crh_feedback)
            crh_levels.append(crh_new)

            # ACTH (stimulated by CRH)
            acth_new = crh_new * self.hpa_crh_to_acth_gain
            acth_levels.append(max(0.0, acth_new))

            # Cortisol (stimulated by ACTH, natural decay)
            decay = 0.1  # 10% decay per step
            cortisol_new = (
                cortisol_levels[-1] * (1 - decay)
                + acth_new * self.hpa_acth_to_cortisol_gain * time_step
            )
            cortisol_levels.append(max(0.0, min(100.0, cortisol_new)))

        return {
            "crh": crh_levels,
            "acth": acth_levels,
            "cortisol": cortisol_levels,
            "time": [i * time_step for i in range(len(crh_levels))],
        }

    def negative_feedback(
        self,
        source_hormone: HormoneType,
        target_hormone: HormoneType,
        current_level: float,
        setpoint: Optional[float] = None,
    ) -> float:
        """
        负反馈调节 / Negative feedback regulation

        High levels of source hormone inhibit target hormone production.

        Args:
            source_hormone: Hormone providing feedback
            target_hormone: Hormone being regulated
            current_level: Current level of source hormone
            setpoint: Target setpoint (uses default if not provided)

        Returns:
            Inhibition factor (0-1, where 1 = full inhibition)
        """
        node = self.feedback_nodes.get(target_hormone)
        sp = setpoint or (node.setpoint if node else 50.0)

        # Calculate deviation from setpoint
        deviation = (current_level - sp) / sp

        # Inhibition increases with deviation
        if deviation > 0:
            inhibition = min(1.0, deviation * self.negative_feedback_gain)
        else:
            inhibition = 0.0

        return inhibition

    def hormone_antagonism(
        self,
        hormone_a: HormoneType,
        hormone_b: HormoneType,
        level_a: float,
        level_b: float,
        antagonism_strength: float = 0.5,
    ) -> Tuple[float, float]:
        """
        激素拮抗 / Hormone antagonism (e.g., leptin vs ghrelin)

        Two hormones with opposing effects influence each other.

        Args:
            hormone_a: First hormone
            hormone_b: Second hormone (opposing)
            level_a: Level of hormone A
            level_b: Level of hormone B
            antagonism_strength: Strength of antagonism (0-1)

        Returns:
            Tuple of (adjusted_level_a, adjusted_level_b)
        """
        # Normalize levels to 0-1
        norm_a = level_a / 100.0
        norm_b = level_b / 100.0

        # Mutual suppression
        adjusted_a = level_a * (1 - norm_b * antagonism_strength * 0.5)
        adjusted_b = level_b * (1 - norm_a * antagonism_strength * 0.5)

        return max(0.0, adjusted_a), max(0.0, adjusted_b)

    def circadian_rhythm(
        self, hormone_type: HormoneType, hour_of_day: float, base_level: float = 20.0
    ) -> float:
        """
        昼夜节律 / Circadian rhythm modulation

        Calculates hormone level based on circadian phase.

        Args:
            hormone_type: Type of hormone
            hour_of_day: Current hour (0-24)
            base_level: Baseline level without circadian influence

        Returns:
            Adjusted hormone level
        """
        if hormone_type == HormoneType.MELATONIN:
            # Melatonin peaks at night
            # Gaussian-like peak around peak hour
            distance_from_peak = min(
                abs(hour_of_day - self.melatonin_peak_hour),
                abs(hour_of_day - (self.melatonin_peak_hour + 24)),
            )
            circadian_factor = math.exp(-(distance_from_peak**2) / 20)
            return base_level + self.melatonin_amplitude * circadian_factor

        elif hormone_type == HormoneType.CORTISOL:
            # Cortisol peaks in morning (wake response)
            distance_from_peak = min(
                abs(hour_of_day - self.cortisol_peak_hour),
                abs(hour_of_day - (self.cortisol_peak_hour + 24)),
            )
            circadian_factor = math.exp(-(distance_from_peak**2) / 18)
            return base_level + self.cortisol_amplitude * circadian_factor

        # No circadian modulation for other hormones
        return base_level

    def get_feedback_node(self, hormone_type: HormoneType) -> FeedbackNode:
        """获取反馈节点 / Get feedback node for a hormone"""
        return self.feedback_nodes.get(
            hormone_type,
            FeedbackNode(
                hormone_type=hormone_type,
                setpoint=50.0,
                current_level=50.0,
                gain=0.5,
                feedback_type="negative",
            ),
        )

    def set_setpoint(self, hormone_type: HormoneType, setpoint: float) -> None:
        """设定目标值 / Set setpoint for a hormone"""
        if hormone_type in self.feedback_nodes:
            self.feedback_nodes[hormone_type].setpoint = setpoint
