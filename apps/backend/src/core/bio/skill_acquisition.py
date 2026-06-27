"""
Angela AI v6.0 - Skill Acquisition System
技能习得系统

Implements power law learning curves for skill acquisition.
Models the transition from conscious effort to automatic execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SkillTrace:
    """技能痕迹 / Skill learning trace"""

    skill_id: str
    skill_name: str
    initial_performance: float  # 初始表现 (0-1)
    current_performance: float  # 当前表现
    practice_count: int  # 练习次数
    learning_curve_factor: float  # 学习曲线因子
    is_automatized: bool  # 是否自动化（习惯化）
    created_at: datetime = field(default_factory=datetime.now)
    last_practice: datetime = field(default_factory=datetime.now)


class SkillAcquisition:
    """
    技能习得系统 / Skill Acquisition System

    Implements power law learning curves for skill acquisition.
    Models the transition from conscious effort to automatic execution.

    Power Law of Learning: Performance = A * N^(-α)
    where N = practice count, α = learning rate

    Example:
        >>> skill_system = SkillAcquisition()
        >>>
        >>> # Start learning a skill
        >>> skill = skill_system.start_skill("typing", initial_performance=0.2)
        >>>
        >>> # Practice and improve
        >>> for _ in range(100):
        ...     skill_system.practice("typing", success=True)
        >>>
        >>> performance = skill_system.get_performance("typing")
        >>> print(f"Current performance: {performance:.2%}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Learning parameters
        self.learning_rate: float = self.config.get("learning_rate", 0.3)  # α in power law
        self.automatization_threshold: float = self.config.get("automatization", 0.8)
        self.max_performance: float = self.config.get("max_performance", 0.95)

        # Skill storage
        self.skills: Dict[str, SkillTrace] = {}

        # Performance history
        self.performance_history: Dict[str, List[Tuple[datetime, float]]] = {}

    def start_skill(
        self, skill_id: str, skill_name: str, initial_performance: float = 0.1
    ) -> SkillTrace:
        """
        开始学习新技能 / Start learning a new skill

        Args:
            skill_id: Unique skill identifier
            skill_name: Human-readable skill name
            initial_performance: Initial performance level (0-1)

        Returns:
            SkillTrace object
        """
        skill = SkillTrace(
            skill_id=skill_id,
            skill_name=skill_name,
            initial_performance=initial_performance,
            current_performance=initial_performance,
            practice_count=0,
            learning_curve_factor=self.learning_rate,
            is_automatized=False,
        )

        self.skills[skill_id] = skill
        self.performance_history[skill_id] = []

        return skill

    def practice(self, skill_id: str, success: bool = True, difficulty: float = 0.5) -> float:
        """
        练习技能 / Practice a skill

        Args:
            skill_id: Skill identifier
            success: Whether the practice was successful
            difficulty: Difficulty of the practice (0-1)

        Returns:
            Updated performance level
        """
        if skill_id not in self.skills:
            return 0.0

        skill = self.skills[skill_id]
        skill.practice_count += 1
        skill.last_practice = datetime.now()

        # Power law of learning: Improvement decreases with practice
        # New performance = Old + (Max - Old) * (N^(-α) - (N-1)^(-α))
        n = skill.practice_count
        alpha = skill.learning_curve_factor

        if n == 1:
            improvement = (self.max_performance - skill.initial_performance) * 0.1
        else:
            # Power law improvement
            improvement_factor = (n ** (-alpha)) - ((n - 1) ** (-alpha))
            improvement = (self.max_performance - skill.current_performance) * abs(
                improvement_factor
            )

        # Adjust for success/failure and difficulty
        if success:
            improvement *= 1.0 + difficulty * 0.5
        else:
            improvement *= -0.1  # Small penalty for failure

        skill.current_performance = max(
            skill.initial_performance,
            min(self.max_performance, skill.current_performance + improvement),
        )

        # Check for automatization (habit formation)
        if skill.current_performance > self.automatization_threshold and skill.practice_count > 50:
            skill.is_automatized = True

        # Record history
        self.performance_history[skill_id].append((datetime.now(), skill.current_performance))

        return skill.current_performance

    def get_performance(self, skill_id: str) -> float:
        """获取当前技能水平 / Get current skill performance"""
        if skill_id not in self.skills:
            return 0.0
        return self.skills[skill_id].current_performance

    def get_learning_curve(self, skill_id: str, n_points: int = 100) -> List[float]:
        """
        预测学习曲线 / Predict learning curve

        Returns projected performance over practice trials.
        """
        if skill_id not in self.skills:
            return []

        skill = self.skills[skill_id]
        curve = []

        for n in range(1, n_points + 1):
            # Power law prediction
            if n == 1:
                perf = (
                    skill.initial_performance
                    + (self.max_performance - skill.initial_performance) * 0.1
                )
            else:
                perf = self.max_performance - (self.max_performance - skill.initial_performance) * (
                    n ** (-self.learning_rate)
                )

            curve.append(max(skill.initial_performance, min(self.max_performance, perf)))

        return curve

    def get_all_skills(self) -> Dict[str, SkillTrace]:
        """获取所有技能 / Get all skills"""
        return self.skills.copy()
